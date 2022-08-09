from __future__ import annotations
from fastapi import FastAPI
from typing import Optional, NoReturn
from pathlib import Path
from polymath.app import Application
from polymath.app.context import Context
from polymath.server.base import *
from polymath.server.backend.fastapi import FastAPIRouteBackend, Routable
from polymath.support.fastapi.settings import SwaggerSettings
from polymath.support.fastapi.builtin import BuiltinService

class FastAPIServer(Server):
    class Delegate(Server.Delegate):
        def server_did_startup(self, server: FastAPIServer): pass
        def server_did_shutdown(self, server: FastAPIServer): pass

    @classmethod
    def build(cls, name: str, version: str, delegate: FastAPIServer.Delegate, workspace: Path, path_prefix:Optional[str]=None, build_version: Optional[str] = None, configuration_path:Optional[Path]=None, include_swagger: Optional[bool]=None, **fastapi_arguments)->FastAPIServer:
        return super().build(name=name, version=version, delegate=delegate, build_version=build_version, path_prefix=path_prefix, workspace=workspace, configuration_path=configuration_path, include_swagger=include_swagger, **fastapi_arguments)


    @property
    def build_version(self)->str:
        return self.__build_version

    @property
    def path_prefix(self) -> str:
        return self.__path_prefix

    @path_prefix.setter
    def path_prefix(self, new_value: str) -> NoReturn:
        self.__path_prefix = new_value

    @property
    def include_swagger(self)->bool:
        return self.__include_swagger

    @property
    def fastapi(self)->FastAPI:
        return self.__fastapi

    @property
    def swagger_settings(self)->SwaggerSettings:
        return self.__swagger_settings

    def __init__(self, application: Application,
                 path_prefix: Optional[str]=None,
                 delegate: Optional[FastAPIServer.Delegate]=None,
                 include_swagger: Optional[bool]=None,
                **fastapi_arguments):
        super().__init__(application=application, delegate=delegate)
        self.__path_prefix = path_prefix
        self.__swagger_settings = SwaggerSettings()
        self.__include_swagger = include_swagger if include_swagger is not None else True

        self.__fastapi = FastAPI(
            docs_url=None,
            redoc_url=None,
            version=application.build_version,
            **fastapi_arguments
        )

        def startup():
            self.did_startup()

            for path, backend in self.backends.items():
                if isinstance(backend, Routable):
                    routing_backend:Routable = backend
                    route = routing_backend.route(path_prefix=self.path_prefix)
                    self.__fastapi.routes.append(route)

        def shutdown():
            self.did_shutdown()

        self.__fastapi.router.add_event_handler("startup", startup)
        self.__fastapi.router.add_event_handler("shutdown", shutdown)


    def launch(self, **options):
        super(FastAPIServer, self).launch(**options)

        context = Context.standard()
        context.set("swagger_path", self.__swagger_settings.path)

        self.__fastapi.title = context.reword(self.__swagger_settings.title)
        self.__fastapi.openapi_url = context.reword(self.__swagger_settings.openapi_url)
        self.__fastapi.setup()

        builtin_apis_service = BuiltinService(name="builtin", app=self.application, swagger_setting=self.swagger_settings)
        self.add_backends(builtin_apis_service.version)
        if self.__include_swagger:
            self.add_backends(builtin_apis_service.swagger)


    async def __call__(self, scope, receive, send):
        await self.__fastapi(scope=scope, receive=receive, send=send)