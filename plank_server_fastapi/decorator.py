import copy
from functools import wraps
from typing import Callable, List, Type, Optional, Union

from plank.decorator.server import api
from plank.server.api import CommonAPI
from plank.service import Service

from plank_server_fastapi.service import RoutableService, RoutingSetting
from plank_server_fastapi.scheme import FastAPIHelper


def routable(path: str):
    attrs = {"__routing_setting__": RoutingSetting(path=path)}

    def wrap(cls: Type[Service]):
        routable_service_cls: Type[RoutableService] = type(f"_{cls.__name__}", (cls, RoutableService), attrs)
        return routable_service_cls

    return wrap


def http(path: str, methods: List[str], name: Optional[str] = None, tags: Optional[List[str]] = None, **kwargs):
    def wrap(func_or_api: Union[Callable, CommonAPI]):
        _api = func_or_api
        if not isinstance(_api, CommonAPI):
            _api = api(_api)
        scheme = FastAPIHelper(api=_api)
        scheme.set_attrs(path=path, methods=methods, name=name, tags=tags, **kwargs)
        _api.set_scheme(scheme=scheme, protocol=FastAPIHelper.__protocol__)
        return _api
    return wrap
