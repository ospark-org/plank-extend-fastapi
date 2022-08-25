from __future__ import annotations
from typing import Callable, Any, Type, Optional
from pydantic import BaseModel
from fastapi.responses import Response
from plank.serving.service import Service
from plank.descriptor.action import ActionDescriptor
from plank.server.action import Action
from plank.server.fastapi.action import RoutableWrapperAction

class RouteActionDescriptor(ActionDescriptor):

    def __init__(self,
                 path: str,
                 end_point: Callable,
                 **kwargs):
        super().__init__(path=path, end_point=end_point, **kwargs)
        self.__response_model = None
        self.__unbound_response_handler = None
        self.__unbound_exception_catchers = {}

    def make_action(self, instance:Service, owner:Type[Service]) ->Action:
        end_point = self.end_point(instance=instance, owner=owner)
        path = self.serving_path(instance=instance, owner=owner)

        #prepare args of RoutableWrapperAction.
        extra_args = self.action_extra_args(instance=instance, owner=owner)
        extra_args["response_model"] = self.__response_model or extra_args.get("response_model")
        if extra_args.get("tags") is not None:
            extra_args["tags"] += [instance.name()]

        action = RoutableWrapperAction(path=path, end_point=end_point, **extra_args)
        if self.__unbound_response_handler is not None:
            action.set_response_handler(self.__unbound_response_handler.__get__(instance, owner))
        if len(self.__unbound_exception_catchers) > 0:
            for exception_type, unbound_exception_catcher in self.__unbound_exception_catchers.items():
                action.set_exception_catcher(unbound_exception_catcher.__get__(instance, owner), exception_type=exception_type)
        return action

    def response(self, response_model: Type[BaseModel])->Callable[[Callable[[Any], Response]], RouteActionDescriptor]:
        self.__response_model = response_model
        def wrapper(unbound_method: Callable[[Any], Response]):
            self.__unbound_response_handler = unbound_method
            return self
        return wrapper

    def catch(self, *exception_types: Type[Exception])->Callable[[Callable[[Exception], Response]], RouteActionDescriptor]:
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
