import asyncio
import copy
import inspect
from functools import wraps
from typing import Dict, Type, Any, Callable, Optional, List, Union

from fastapi import Depends
from fastapi.routing import APIRoute
from plank.server.api import CommonAPI, BoundedAPI, CallableAPI, MirrorAPI
from plank.server.scheme import SchemeHelper
from plank.utils.function import bound_if_needed
from plank.utils.path import clearify
from pydantic import BaseModel


class FastAPIHelper(SchemeHelper):
    __protocol__ = "http"

    class RequestHelper:
        @property
        def argument_types(self) -> Dict[str, Type[Any]]:
            return self.__argument_types

        @property
        def packer(self) -> Callable[[Any], Any]:
            return self.__packer

        @property
        def unpacker(self) -> Callable[[Any], Any]:
            return self.__unpacker

        def __init__(self, scheme_helper: SchemeHelper):
            self.__scheme_helper = scheme_helper
            self.__argument_types = None
            self.__packer = None
            self.__unpacker = None

        def pack(self, func: Callable[[Any, inspect.Signature], Any])->Union[CommonAPI, BoundedAPI]:
            self.__packer = func
            return self.__scheme_helper.api

        def unpack(self, func: Callable[[Any], Any])->Union[CommonAPI, BoundedAPI]:
            self.__reverser = func
            return self.__scheme_helper.api

    class ResponseHelper:
        @property
        def response_model(self) -> Type[Any]:
            return self.__response_model

        @property
        def packer(self) -> Callable[[Any], Any]:
            return self.__packer

        @property
        def unpacker(self) -> Callable[[Any], Any]:
            return self.__unpacker

        def __init__(self, scheme_helper: SchemeHelper):
            self.__scheme_helper = scheme_helper
            self.__response_model = None
            self.__packer = lambda value: value
            self.__unpacker = lambda response: response

        def pack(self, response_model: Optional[Type[BaseModel]] = None):
            def wrapper(handler: Callable[[Any], Any])->Union[CommonAPI, BoundedAPI]:
                self.__response_model = response_model
                self.__packer = handler

                if handler.__name__ == self.__scheme_helper.api.name:
                    return self.__scheme_helper.api
                else:
                    return MirrorAPI(self.__scheme_helper.api)

            return wrapper

        def unpack(self, func: Callable[[Any], Any])->Union[CommonAPI, BoundedAPI]:
            self.__unpacker = func
            if func.__name__ == self.__scheme_helper.api.name:
                return self.__scheme_helper.api
            else:
                return MirrorAPI(self.__scheme_helper.api)

    @property
    def request(self) -> RequestHelper:
        return self.__request_helper

    @property
    def response(self) -> ResponseHelper:
        return self.__response_helper

    def __init__(self, api: CommonAPI, request_helper=None, response_helper=None):
        super().__init__(api=api)
        self.__request_helper = request_helper or self.__class__.RequestHelper(self)
        self.__response_helper = response_helper or self.__class__.ResponseHelper(self)

    def set_attrs(self, path: str, methods: List[str], name: Optional[str] = None, tags: Optional[List[str]] = None,
                  **kwargs):
        if name is not None:
            kwargs.setdefault("name", name)

        if tags is not None:
            kwargs.setdefault("tags", tags)

        return self.set(
            path=path,
            methods=methods,
            **kwargs
        )

    def concat_path(self, path: str, path_prefix: Optional[str] = None) -> str:
        path = clearify(path)
        if path_prefix is not None:
            path_prefix = clearify(path_prefix)
            path = f"{path_prefix}/{path}"
        return path

    def call(self, *args, **kwargs):
        pass

    def build_route(self, service_name: str, service_prefix: Optional[str] = None,
                    path_prefix: Optional[str] = None) -> APIRoute:
        assert isinstance(self.api, (BoundedAPI,
                                     CallableAPI)), f"`build_route` with api in {self.__class__.__name__} should be type of BoundedAPI or CallableAPI"
        attrs = copy.copy(self.attributes)
        path = self.concat_path(path=attrs["path"], path_prefix=service_prefix)
        path = self.concat_path(path=path, path_prefix=path_prefix)
        attrs["path"] = f"/{path}"
        
        # set end point
        endpoint = self.api.end_point
        annotations = inspect.get_annotations(endpoint, eval_str=True)
        for name, annotation in annotations.items():
            endpoint.__annotations__[name] = annotation

        attrs.setdefault("name", endpoint.__name__)

        if isinstance(self.api, BoundedAPI):
            instance = self.api.instance
            owner = self.api.owner
        else:
            instance = None
            owner = None

        # bound handlers
        if self.request.packer is not None:
            request_handler = bound_if_needed(self.request.packer, instance, owner)
        else:
            request_handler = wraps(endpoint)(lambda **kwargs: kwargs)

        response_handler = bound_if_needed(self.response.packer, instance, owner)
        response_sig = inspect.signature(response_handler)
        response_parameter_keys = response_sig.parameters.keys()

        async def end_point(args_dict=Depends(request_handler)):
            args_dict = args_dict or {}
            value = endpoint(**args_dict)
            if asyncio.iscoroutine(value):
                value = await value

            reserved_request_parameters = {   
                key: value
                for key, value in args_dict.items()
                if key in response_parameter_keys
            }
            return response_handler(value, **reserved_request_parameters)

        attrs["endpoint"] = end_point
        attrs["response_model"] = self.response.response_model

        tags = attrs.get("tags") or []
        if len(tags) == 0:
            attrs["tags"] = [service_name]
        return APIRoute(**attrs)

