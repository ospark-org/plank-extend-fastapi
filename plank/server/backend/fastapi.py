from __future__ import annotations
import inspect
import asyncio
from typing import List, Optional, Type, Callable, Dict, Any
from fastapi.routing import APIRoute
from fastapi import Depends
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from plank.server.backend.serving import ServingBackend
from plank.server.backend.wrapper import WrapperBackend
from plank.descriptor.fastapi import RouteBackendDescriptor
from plank.serving import Serving
from plank.utils.path import clearify
from plank.app.context import Context
from functools import wraps


class Routable:
    def name(self)->str:
        raise NotImplementedError

    def routing_path(self) -> str:
        raise NotImplementedError

    def methods(self)->List[str]:
        raise NotImplementedError

    def tags(self)->List[str]:
        raise NotImplementedError

    def description(self)->Optional[str]:
        raise NotImplementedError

    def response_model(self):
        raise NotImplementedError

    def include_in_schema(self)->bool:
        raise NotImplementedError

    def get_route(self, end_point:Callable, path_prefix: Optional[str]=None)->APIRoute:
        path = clearify(self.routing_path())
        if path_prefix is not None:
            path_prefix = clearify(path_prefix)
            path = f"{path_prefix}/{path}"
        path = f"/{path}"

        name = self.name() or \
               getattr(end_point, "__name__") if hasattr(end_point, "__name__") else path.split("/")[-1]
        methods = self.methods()
        tags = self.tags()
        response_model = self.response_model()
        description = self.description()
        include_in_schema = self.include_in_schema()
        return APIRoute(path=path, name=name, endpoint=end_point, methods=methods, tags=tags,
                        response_model=response_model, description=description, include_in_schema=include_in_schema)

    def route(self, path_prefix: Optional[str] = None) -> APIRoute:
        raise NotImplementedError()



class FastAPIRouteBackend(ServingBackend, Routable):
    def __init__(
            self,
            name: str,
            path: str,
            serving: Serving,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[BaseModel] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None
    ):
        super().__init__(path=path, serving=serving)
        self.__name = name
        self.__methods = methods
        self.__include_in_schema = include_in_schema if include_in_schema is not None else True
        self.__tags = tags
        self.__response_model = response_model
        self.__description = description

    def routing_path(self) -> str:
        return self.path

    def name(self)->str:
        return self.__name

    def methods(self)->List[str]:
        return self.__methods

    def tags(self)->List[str]:
        return self.__tags

    def description(self)->Optional[str]:
        return self.__description

    def response_model(self)->Optional[Type[BaseModel]]:
        return self.__response_model

    def include_in_schema(self)->bool:
        return self.__include_in_schema

    def route(self, path_prefix: Optional[str]=None) -> APIRoute:
        return self.get_route(end_point=self.serving.perform, path_prefix=path_prefix)



class RoutableWrapperBackend(WrapperBackend, Routable):
    def __init__(
            self,
            path: str,
            end_point: Callable,
            descriptor: RouteBackendDescriptor,
            name: Optional[str] = None,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[Type[BaseModel]] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None
    ):
        super().__init__(path=path, end_point=end_point, descriptor=descriptor)
        self.__name = name
        self.__methods = methods
        self.__include_in_schema = include_in_schema if include_in_schema is not None else True
        self.__tags = tags
        self.__description = description
        self.__response_model = response_model
        self.__response_handler = None
        self.__exception_catcher = None

    def name(self) -> str:
        return self.__name

    def methods(self) -> List[str]:
        return self.__methods

    def tags(self) -> List[str]:
        return self.__tags

    def description(self) -> Optional[str]:
        return self.__description

    def set_exception_catcher(self, exception_catcher: Callable[[Exception], Response]):
        self.__exception_catcher = exception_catcher

    def set_response_handler(self, response_handler: Callable[[Any], Response]):
        self.__response_handler = response_handler

    def set_response_model(self, response_model: BaseModel):
        self.__response_model = response_model

    def response_model(self) -> Optional[Type[BaseModel]]:
        end_point = self.end_point()

        if self.__response_model is not None:
            return self.__response_model

        sig = inspect.signature(end_point)
        if sig.return_annotation == inspect.Signature.empty:
            response_model = None
        else:
            # deal with the return annotation become str by __future__.annotations
            if isinstance(sig.return_annotation, str):
                response_model = end_point.__globals__.get(sig.return_annotation)
            else:
                if not isinstance(sig.return_annotation, Response):
                    response_model = sig.return_annotation

        return response_model


    def include_in_schema(self) -> bool:
        return self.__include_in_schema
    
    def route(self, path_prefix: Optional[str]=None) ->APIRoute:
        end_point = self.end_point()
        @wraps(end_point)
        async def endpoint(*args, **kwargs):
            try:
                result = end_point(*args, **kwargs)

                if inspect.isawaitable(result):
                    result = await result
                if self.__response_handler is not None:
                    end_point_sig = inspect.signature(end_point)
                    end_point_request_args = end_point_sig.bind(*args, **kwargs)

                    response_handler_sig = inspect.signature(self.__response_handler)
                    if len(response_handler_sig.parameters) > 1:
                        handled_result = self.__response_handler(result, **end_point_request_args.arguments)
                    elif len(response_handler_sig.parameters) > 0:
                        handled_result = self.__response_handler(result)
                    else:
                        handled_result = self.__response_handler()

                    if inspect.isawaitable(handled_result):
                        return await handled_result
                    else:
                        return handled_result
                else:
                    return result

            except Exception as error:
                if self.__exception_catcher is not None:
                    return self.__exception_catcher(error)
                else:
                    raise error

        return self.get_route(end_point=endpoint, path_prefix=path_prefix)
