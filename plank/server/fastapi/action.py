from __future__ import annotations

import inspect
from functools import wraps
from typing import List, Optional, Type, Callable, Any, TYPE_CHECKING

from fastapi.responses import Response
from fastapi.routing import APIRoute
from plank.server.action.serving import ServingAction
from plank.server.action.wrapper import WrapperAction
from plank.serving import Serving
from pydantic import BaseModel

from .interface import Routable

if TYPE_CHECKING:
    pass


class FastAPIRouteAction(ServingAction, Routable):
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

    def name(self) -> str:
        return self.__name

    def methods(self) -> List[str]:
        return self.__methods

    def tags(self) -> List[str]:
        return self.__tags

    def description(self) -> Optional[str]:
        return self.__description

    def response_model(self) -> Optional[Type[BaseModel]]:
        return self.__response_model

    def include_in_schema(self) -> bool:
        return self.__include_in_schema

    def route(self, path_prefix: Optional[str] = None) -> APIRoute:
        return self.get_route(end_point=self.serving.perform, path_prefix=path_prefix)


class RoutableWrapperAction(WrapperAction, Routable):

    def __init__(
            self,
            path: str,
            end_point: Callable,
            name: Optional[str] = None,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[Type[BaseModel]] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None,
            response_reverser: Optional[Callable] = None
    ):
        super().__init__(path=path, end_point=end_point, response_reverser=response_reverser)
        self.__name = name or (end_point.__name__ if hasattr(end_point, "__name__") else None)
        self.__methods = methods
        self.__include_in_schema = include_in_schema if include_in_schema is not None else True
        self.__tags = tags
        self.__description = description
        self.__response_model = response_model
        self.__response_handler = None
        self.__exception_catchers = {}

        self.__call__ = wraps(end_point)(lambda *args, **kwargs: end_point(*args, **kwargs))

    def name(self) -> str:
        return self.__name

    def methods(self) -> List[str]:
        return self.__methods

    def tags(self) -> List[str]:
        return self.__tags

    def description(self) -> Optional[str]:
        return self.__description

    def set_exception_catcher(self, exception_catcher: Callable[[Exception], Response],
                              exception_type: Type[Exception]):
        self.__exception_catchers[exception_type] = exception_catcher

    def set_response_handler(self, response_handler: Callable[[Any], Response]):
        self.__response_handler = response_handler

    def response_handler(self, *args, **kwargs):
        sig = inspect.signature(self.__response_handler)
        arguments = sig.bind(*args, **kwargs)
        arguments.apply_defaults()
        return self.__response_handler(**arguments.arguments)

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

    def route(self, path_prefix: Optional[str] = None) -> APIRoute:
        end_point = self.end_point()
        end_point_sig = inspect.signature(end_point)

        # resolve the annotation is str and can't catch in endpoint.__global__
        globals().update({
            parameter.annotation: end_point.__globals__[parameter.annotation]
            for parameter in end_point_sig.parameters.values()
            if isinstance(parameter.annotation, str) and parameter.annotation in end_point.__globals__
        })

        @wraps(end_point)
        async def wrapped_end_point(*args, **kwargs):
            try:
                result = end_point(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
                if self.__response_handler is not None:

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
                exception_type = type(error)
                catcher = self.__exception_catchers.get(exception_type) or self.__exception_catchers.get(Exception)
                if catcher is None:
                    raise error
                else:
                    return catcher(error)

        return self.get_route(end_point=wrapped_end_point, path_prefix=path_prefix)
