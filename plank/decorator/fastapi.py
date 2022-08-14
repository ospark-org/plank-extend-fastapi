from typing import Callable, Optional, List, Type
from pydantic import BaseModel
from plank.decorator.backend import backend
from plank.descriptor.fastapi import RouteBackendDescriptor

from plank.server.backend.fastapi import RoutableWrapperBackend

def routable(path: str,
            name: Optional[str] = None,
            methods: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            response_model: Optional[Type[BaseModel]] = None,
            description: Optional[str] = None,
            include_in_schema: Optional[bool] = None)->Callable[[Callable], RouteBackendDescriptor]:
    return backend(
        path=path,
        name=name,
        methods=methods,
        tags=tags,
        response_model=response_model,
        description=description,
        include_in_schema=include_in_schema,
        wrapper_descriptor_type=RouteBackendDescriptor
    )