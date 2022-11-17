from typing import Optional

from plank.app import Application
from plank.decorator.fastapi import routable
from plank.serving.service import Service
from pydantic import BaseModel


class VersionResponse(BaseModel):
    app_version: str = "0.1.0"
    build_version: str = "2022-08-05.00002"


class BuiltinService(Service):

    def __init__(self, name: str, app: Application, serving_path: Optional[str] = None):
        super().__init__(name=name, serving_path=serving_path)
        self.__build_version = app.build_version
        self.__app_version = app.version

    @routable(path="/version", tags=["default"], methods=["GET"])
    async def version(self) -> VersionResponse:
        return VersionResponse(
            build_version=self.__build_version,
            app_version=self.__app_version
        )
