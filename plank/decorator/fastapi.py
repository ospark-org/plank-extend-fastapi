from __future__ import annotations
from typing import Callable, Optional, List, Type, TYPE_CHECKING
from pydantic import BaseModel
from plank.decorator.action import action

if TYPE_CHECKING:
    from plank.descriptor.fastapi import RouteActionDescriptor

def routable(path: str,
            name: Optional[str] = None,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[Type[BaseModel]] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None)->Callable[[Callable], RouteActionDescriptor]:
    from plank.descriptor.fastapi import RouteActionDescriptor
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