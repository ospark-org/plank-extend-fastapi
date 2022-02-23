from fastapi.routing import APIRoute
from typing import Optional, Callable, List
from pydantic import BaseModel
from polymath.app.defaults import UserDefaults

def route(path:str, methods:List[str], name:Optional[str]=None, tags:Optional[List[str]]=None, response_model:Optional[BaseModel]=None, description:Optional[str]=None, include_in_schema:bool=True):
    def _f(endpoint_func: Callable):
        from polymath.app._fastapi import Application
        app = Application.main()
        _name = name or endpoint_func.__name__
        prefix_name:str = app.prefix_name
        _path = path
        if prefix_name is not None:
            prefix_name = prefix_name.removesuffix("/").removeprefix("/")
            removed_path = path.removeprefix("/")
            _path = f"/{prefix_name}/{removed_path}"
        return APIRoute(path=_path, name=_name, endpoint=endpoint_func, methods=methods, tags=tags, response_model=response_model, description=description, include_in_schema=include_in_schema)
    return _f