from __future__ import annotations
from typing import Callable, Any, Type, Dict
from pydantic import BaseModel
from fastapi.responses import Response
from plank.descriptor.backend import BackendDescriptor
from plank.server.backend.wrapper import WrapperBackend


class ExceptionCatcherDescriptor:
    def __init__(self, route_backend_descriptor: RouteBackendDescriptor,
                 unbound_exception_catcher: Callable[[Exception], Response]):
        self.__route_backend_descriptor = route_backend_descriptor
        self.__unbound_exception_catcher = unbound_exception_catcher

    def __get__(self, instance, owner):
        backend = self.__route_backend_descriptor.__get__(instance, owner)
        backend.set_exception_catcher(self.__unbound_exception_catcher.__get__(instance, owner))
        return backend

class ResponseHandledDescriptor:
    def __init__(self, route_backend_descriptor: RouteBackendDescriptor, response_model:Type[BaseModel], unbound_response_handler: Callable[[Any], Response]):
        self.__route_backend_descriptor = route_backend_descriptor
        self.__response_model = response_model
        self.__unbound_response_handler = unbound_response_handler

    def __get__(self, instance, owner):
        backend = self.__route_backend_descriptor.__get__(instance, owner)
        backend.set_response_handler(self.__unbound_response_handler.__get__(instance, owner))
        backend.set_response_model(self.__response_model)
        return backend



class RouteBackendDescriptor(BackendDescriptor):

    def make_backend(self, path: str, end_point: Callable, **kwargs)->WrapperBackend:
        from plank.server.backend.fastapi import RoutableWrapperBackend
        return RoutableWrapperBackend(path=path, end_point=end_point, descriptor=self, **kwargs)

    def response(self, response_model: Type[BaseModel])->Callable[[Callable[[Any], Response]], ResponseHandledDescriptor]:
        def wrapper(unbound_method: Callable[[Any], Response]):
            return ResponseHandledDescriptor(
                route_backend_descriptor=self,
                response_model=response_model,
                unbound_response_handler=unbound_method
            )
        return wrapper

    def catch(self, unbound_method: Callable[[Exception], Response]):
        return ExceptionCatcherDescriptor(
            route_backend_descriptor=self,
            unbound_exception_catcher=unbound_method
        )
