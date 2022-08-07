from typing import Callable, Optional, Type, Any
from fastapi import Depends
from polymath.descriptor.backend import *
from fastapi.responses import Response, JSONResponse
from polymath.server.backend.wrapper import WrapperBackend

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
        from polymath.server.backend.fastapi import RoutableWrapperBackend
        return RoutableWrapperBackend(path=path, end_point=end_point, descriptor=self, **kwargs)

    def response(self, unbound_func: Callable[[Any], Response]):
        self.unbound_handle_response = unbound_func

    def middleware(self):
        pass

# class BackendDescriptor:
#     def __init__(self,
#                  path: str,
#                  end_point: Callable,
#                  backend_class:Optional[Type[WrapperBackend]]=None,
#                  **kwargs
#                  ):
#         self.__path = path
#         self.__meta_args = kwargs
#         self.__end_point = end_point
#         self.__backend_class = backend_class
#         self.__api_instances = {}
#
#     def __get__(self, instance:Service, owner:Type[Service]):
#         key = id(instance)
#         end_point = self.__end_point.__get__(instance, owner)
#         self.__meta_args["end_point"] = end_point
#         if key not in self.__api_instances.keys():
#             args = copy(self.__meta_args)
#             instance_serving_path = instance.serving_path()
#             if instance_serving_path is not None:
#                 args["path"] = f"/{clearify(instance.serving_path())}/{clearify(self.__path)}"
#             else:
#                 args["path"] = f"/{clearify(self.__path)}"
#             api = self.__backend_class(**args)
#             self.__api_instances[key] = api
#         return self.__api_instances[key]