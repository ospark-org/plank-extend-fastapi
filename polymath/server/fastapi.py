from __future__ import annotations
from fastapi import FastAPI
from typing import Optional
from polymath.app import Application
from polymath.app.context import Context
from polymath.server import Server, ServerDelegate
from polymath.server.backend.fastapi import FastAPIRouteBackend, Routable
from polymath.support.fastapi.settings import SwaggerSettings
from polymath.support.fastapi.builtin import BuiltinService

class FastAPIServerDelegate(ServerDelegate):
    def server_did_startup(self, server: FastAPIServer): pass
    def server_did_shutdown(self, server: FastAPIServer): pass

class FastAPIServer(Server):

    @classmethod
    def build(cls, name: str, version: str, delegate: ServerDelegate, build_version: Optional[str] = None,
              path_prefix:Optional[str]=None, **fastapi_arguments) -> Server:
        return super().build(name=name, version=version, delegate=delegate, build_version=build_version, path_prefix=path_prefix, **fastapi_arguments)


    @property
    def build_version(self)->str:
        return self.__build_version

    @property
    def path_prefix(self) -> str:
        return self.__path_prefix

    @property
    def fastapi(self)->FastAPI:
        return self.__fastapi

    @property
    def swagger_settings(self)->SwaggerSettings:
        return self.__swagger_settings

    def __init__(self, application: Application,
                 path_prefix: Optional[str]=None,
                 delegate: Optional[FastAPIServerDelegate]=None,
                **fastapi_arguments):
        super().__init__(application=application, delegate=delegate)
        self.__path_prefix = path_prefix
        self.__swagger_settings = SwaggerSettings()

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
        context.set("server.swagger_path", self.__swagger_settings.path)

        builtin_apis_service = BuiltinService(name="builtin", app=self.application, swagger_setting=self.swagger_settings)
        self.add_backends_by_service(service=builtin_apis_service)


    async def __call__(self, scope, receive, send):
        await self.__fastapi(scope=scope, receive=receive, send=send)