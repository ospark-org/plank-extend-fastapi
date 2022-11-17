from __future__ import annotations

import inspect
from typing import Callable, Any, Type

from fastapi.responses import Response
from plank.descriptor.action import ActionDescriptor
from plank.server.action import Action
from plank.serving.service import Service
from pydantic import BaseModel


def bounding_if_needed(f: Callable, instance: Any, owner: Type[Any]):
    if f is None:
        return None

    if "." in f.__qualname__ and inspect.isfunction(f):
        # need bounding
        return f.__get__(instance, owner)
    else:
        return f


class RouteActionResponser:

    @property
    def descriptor(self) -> RouteActionDescriptor:
        return self.__descriptor

    @property
    def response_model(self) -> BaseModel:
        return self.__response_model

    def get_response_handler(self, instance, owner):
        return bounding_if_needed(self.__unbound_response_handler, instance=instance, owner=owner)

    def get_response_reverser(self, instance, owner):
        return bounding_if_needed(self.__unbound_response_reverser, instance=instance, owner=owner)

    def __init__(self, descriptor: RouteActionDescriptor):
        self.__descriptor = descriptor
        self.__unbound_response_handler = None
        self.__unbound_response_reverser = None
        self.__response_model = None

    def __call__(self, response_model: Type[BaseModel]) -> Callable[[Callable[[Any], Response]], RouteActionDescriptor]:
        self.__response_model = response_model

        def wrapper(unbound_method: Callable[[Any], Response]):
            self.__unbound_response_handler = unbound_method
            return self.descriptor

        return wrapper

    def reverse(self, unbound_method: Callable[[Any, Type[BaseModel]], Any]) -> RouteActionDescriptor:
        self.__unbound_response_reverser = unbound_method
        return self.descriptor


class RouteActionDescriptor(ActionDescriptor):

    @property
    def response(self) -> RouteActionResponser:
        return self.__responser

    def __init__(self,
                 path: str,
                 end_point: Callable,
                 **kwargs):
        super().__init__(path=path, end_point=end_point, **kwargs)
        self.__responser = RouteActionResponser(descriptor=self)
        self.__unbound_exception_catchers = {}

    def make_action(self, instance: Service, owner: Type[Service]) -> Action:
        from plank.server.fastapi.action import RoutableWrapperAction

        end_point = self.end_point(instance=instance, owner=owner)
        path = self.serving_path(instance=instance, owner=owner)

        # prepare args of RoutableWrapperAction.
        extra_args = self.action_extra_args(instance=instance, owner=owner)
        extra_args["response_model"] = self.__responser.response_model or extra_args.get("response_model")
        service_tags = []
        if isinstance(instance, Service) and instance.name() is not None:
            service_tags = [instance.name().title()]
        extra_args["tags"] = (extra_args.get("tags") or []) + service_tags

        action = RoutableWrapperAction(path=path, end_point=end_point, **extra_args)
        response_handler = self.__responser.get_response_handler(instance, owner)
        response_reverser = self.__responser.get_response_reverser(instance, owner)
        if response_handler is not None:
            action.set_response_handler(response_handler)
        if len(self.__unbound_exception_catchers) > 0:
            for exception_type, unbound_exception_catcher in self.__unbound_exception_catchers.items():
                action.set_exception_catcher(unbound_exception_catcher.__get__(instance, owner),
                                             exception_type=exception_type)
        if response_reverser is not None:
            action.set_response_reverser(response_reverser)
        return action

    def catch(self, *exception_types: Type[Exception]) -> Callable[
        [Callable[[Exception], Response]], RouteActionDescriptor]:
        if len(exception_types) == 0:
            exception_types += [Exception]

        def wrapper(unbound_method: Callable[[Exception], Response]):
            for exception_type in exception_types:
                self.__unbound_exception_catchers[exception_type] = unbound_method
            return self

        return wrapper
