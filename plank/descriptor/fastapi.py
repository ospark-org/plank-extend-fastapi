from typing import Callable, Any
from fastapi.responses import Response
from plank.descriptor.backend import BackendDescriptor
from plank.server.backend.wrapper import WrapperBackend

class RouteBackendDescriptor(BackendDescriptor):

    @property
    def response_handler(self):
        return self.__response_handler

    def __handle_response(self, value: Any)->Response:
        return value

    def __get__(self, instance, owner):
        if hasattr(self, "unbound_handle_response"):
            self.__response_handler = self.unbound_handle_response.__get__(instance, owner)
        else:
            self.__response_handler = None
        return super(RouteBackendDescriptor, self).__get__(instance, owner)


    def make_backend(self, path: str, end_point: Callable, **kwargs)->WrapperBackend:
        from plank.server.backend.fastapi import RoutableWrapperBackend
        return RoutableWrapperBackend(path=path, end_point=end_point, descriptor=self, **kwargs)

    def response(self, unbound_func: Callable[[Any], Response]):
        self.unbound_handle_response = unbound_func

    def middleware(self):
        pass
