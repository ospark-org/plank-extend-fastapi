from typing import Callable, Optional, List, Type
from pydantic import BaseModel
from plank.decorator.action import action
from plank.descriptor.fastapi import RouteActionDescriptor

def routable(path: str,
            name: Optional[str] = None,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[Type[BaseModel]] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None)->Callable[[Callable], RouteActionDescriptor]:
    return action(
        path=path,
        name=name,
        methods=methods,
        tags=tags,
        response_model=response_model,
        description=description,
        include_in_schema=include_in_schema,
        wrapper_descriptor_type=RouteActionDescriptor
    )