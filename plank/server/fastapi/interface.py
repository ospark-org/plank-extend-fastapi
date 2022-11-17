from __future__ import annotations

from typing import List, Optional, Callable

from fastapi.routing import APIRoute
from plank.utils.path import clearify


class Routable:
    def name(self) -> str:
        raise NotImplementedError

    def routing_path(self) -> str:
        raise NotImplementedError

    def methods(self) -> List[str]:
        raise NotImplementedError

    def tags(self) -> List[str]:
        raise NotImplementedError

    def description(self) -> Optional[str]:
        raise NotImplementedError

    def response_model(self):
        raise NotImplementedError

    def include_in_schema(self) -> bool:
        raise NotImplementedError

    def get_route(self, end_point: Callable, path_prefix: Optional[str] = None) -> APIRoute:
        path = clearify(self.routing_path())
        if path_prefix is not None:
            path_prefix = clearify(path_prefix)
            path = f"{path_prefix}/{path}"
        path = f"/{path}"

        name = self.name() or \
               getattr(end_point, "__name__") if hasattr(end_point, "__name__") else path.split("/")[-1]
        methods = self.methods()
        tags = self.tags()
        response_model = self.response_model()
        description = self.description()
        include_in_schema = self.include_in_schema()
        return APIRoute(path=path, name=name, endpoint=end_point, methods=methods, tags=tags,
                        response_model=response_model, description=description, include_in_schema=include_in_schema)

    def route(self, path_prefix: Optional[str] = None) -> APIRoute:
        raise NotImplementedError()
