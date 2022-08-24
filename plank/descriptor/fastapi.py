from __future__ import annotations
from typing import Callable, Any, Type, Optional
from pydantic import BaseModel
from fastapi.responses import Response
from plank.descriptor.backend import BackendDescriptor
from plank.server.backend.wrapper import WrapperBackend
from plank.server.backend.fastapi import RoutableWrapperBackend

class RouteBackendDescriptor(BackendDescriptor):

    def __init__(self,
                 path: str,
                 end_point: Callable,
                 **kwargs):
        super().__init__(path=path, end_point=end_point, **kwargs)
        self.__response_model = None
        self.__unbound_response_handler = None
        self.__unbound_exception_catchers = {}

    def make_backend(self, path: str, end_point: Callable, **kwargs)->WrapperBackend:
        backend = RoutableWrapperBackend(path=path, end_point=end_point, descriptor=self, **kwargs)
        backend.set_response_model(self.__response_model)
        return backend

    def __get__(self, instance, owner):
        backend: RoutableWrapperBackend = super().__get__(instance, owner)

        if self.__unbound_response_handler is not None:
            backend.set_response_handler(self.__unbound_response_handler.__get__(instance, owner))
        if len(self.__unbound_exception_catchers) > 0:
            for exception_type, unbound_exception_catcher in self.__unbound_exception_catchers.items():
                backend.set_exception_catcher(unbound_exception_catcher.__get__(instance, owner), exception_type=exception_type)
        return backend

    def response(self, response_model: Type[BaseModel])->Callable[[Callable[[Any], Response]], RouteBackendDescriptor]:
        self.__response_model = response_model
        def wrapper(unbound_method: Callable[[Any], Response]):
            self.__unbound_response_handler = unbound_method
            return self
        return wrapper

    def catch(self, *exception_types: Type[Exception])->Callable[[Callable[[Exception], Response]], RouteBackendDescriptor]:
        if len(exception_types) == 0:
            exception_types += [Exception]
        def wrapper(unbound_method: Callable[[Exception], Response]):
            for exception_type in exception_types:
                self.__unbound_exception_catchers[exception_type] = unbound_method
            return self
        return wrapper




        # return ExceptionCatcherDescriptor(
        #     route_backend_descriptor=self,
        #     unbound_exception_catcher=unbound_method
        # )
