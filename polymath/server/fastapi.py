from __future__ import annotations
from fastapi import FastAPI
from typing import Optional, Callable, NoReturn
from polymath.app import Application
from polymath.server import Server, BindAddress, ServerDelegate
from polymath.server.backend import Backend
from polymath.server.backend.fastapi import FastAPIRouteBackend, Routable
from polymath.support.fastapi.builtin import BuiltinService

class FastAPIServerDelegate(ServerDelegate):
    def server_did_startup(self, server: FastAPIServer): pass
    def server_did_shutdown(self, server: FastAPIServer): pass

class FastAPIServer(Server):

    @property
    def build_version(self)->str:
        return self.__build_version

    @property
    def path_prefix(self) -> str:
        return self.__path_prefix

    @property
    def openapi_path(self) -> str:
        return self.__openapi_path

    @property
    def swagger_secrets_username(self) -> Optional[str]:
        return self.__swagger_secrets_username

    @property
    def swagger_secrets_password(self) -> Optional[str]:
        return self.__swagger_secrets_password

    @property
    def swagger_path(self) -> str:
        return self.__swagger_path

    @property
    def fastapi(self)->FastAPI:
        return self.__fastapi

    def __init__(self, application: Application,
                 build_version: Optional[str]=None,
                 path_prefix: Optional[str]=None,
                 openapi_path: Optional[str] = None,
                 swagger_secrets_username: Optional[str]=None,
                 swagger_secrets_password: Optional[str] = None,
                 swagger_path: Optional[str] = None,
                 delegate: Optional[FastAPIServerDelegate]=None,
                **fastapi_arguments):
        super().__init__(application=application, delegate=delegate)
        self.__build_version = build_version or application.version
        self.__path_prefix = path_prefix
        self.__openapi_path = openapi_path or "/swagger/openapi.json"
        self.__swagger_secrets_username = swagger_secrets_username
        self.__swagger_secrets_password = swagger_secrets_password
        self.__swagger_path = swagger_path or "/docs"


        self.__fastapi = FastAPI(
            docs_url=None,
            redoc_url=None,
            openapi_url=self.openapi_path,
            version=build_version,
            title=f"{application.name} - Documentations",
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

        title = self.application.name + ' - Swagger UI'
        service = BuiltinService(name="builtin", build_version=self.build_version, app_version=self.application.version,
                       title=title, openapi_path=self.openapi_path, user=self.swagger_secrets_username, password=self.swagger_secrets_password)
        self.add_backends_by_service(service=service)


    async def __call__(self, scope, receive, send):
        await self.__fastapi(scope=scope, receive=receive, send=send)