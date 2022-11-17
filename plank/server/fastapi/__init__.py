from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from fastapi import FastAPI
from plank import logger
from plank.context import Context
from plank.configuration import Configuration
from plank.server import Server
from plank.support.fastapi.builtin import BuiltinService
from plank.support.fastapi.settings import SwaggerSettings
from plank.support.fastapi.swagger import SwaggerAction
from .action import FastAPIRouteAction
from .interface import Routable

if TYPE_CHECKING:
    from plank.app import Application


class FastAPIServer(Server):
    class Delegate(Server.Delegate):
        def server_did_startup(self, server: FastAPIServer): pass

        def server_did_shutdown(self, server: FastAPIServer): pass

    @classmethod
    def build(cls, configuration: Configuration, delegate: FastAPIServer.Delegate, path_prefix: Optional[str] = None,
                     api_version: Optional[str] = None, **fastapi_arguments) -> FastAPIServer:
        from plank.app import Application
        app = Application(delegate=delegate, configuration=configuration)
        api_version = api_version or configuration.app.build_version
        server = FastAPIServer(application=app, version=api_version, delegate=delegate, path_prefix=path_prefix, **fastapi_arguments)
        return server

    @property
    def build_version(self) -> str:
        return self.application.build_version

    @property
    def include_swagger(self) -> bool:
        return self.__include_swagger

    @property
    def fastapi(self) -> FastAPI:
        return self.__fastapi

    @property
    def swagger_settings(self) -> SwaggerSettings:
        return self.__swagger_settings

    @property
    def api_version(self) -> Optional[str]:
        return self.__api_version

    def __init__(self, application: Application,
                 version: Optional[str] = None,
                 path_prefix: Optional[str] = None,
                 delegate: Optional[FastAPIServer.Delegate] = None,
                 include_swagger: Optional[bool] = None,
                 **fastapi_arguments):
        super().__init__(application=application, delegate=delegate, path_prefix=path_prefix)
        self.__api_version = version
        self.__swagger_settings = SwaggerSettings()
        self.__include_swagger = include_swagger if include_swagger is not None else True

        self.__fastapi = FastAPI(
            docs_url=None,
            redoc_url=None,
            version=f"{version}-{application.configuration.name}",
            **fastapi_arguments
        )

        def startup():
            self.did_startup()

            for path, action in self.actions.items():
                if isinstance(action, Routable):
                    routing_action: Routable = action
                    route = routing_action.route(path_prefix=self.path_prefix)
                    logger.debug(f"Added route: {route} at path: {route.path}")
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

        builtin_apis_service = BuiltinService(name=None, app=self.application)
        self.add_action(builtin_apis_service.version)
        if self.__include_swagger:
            action = SwaggerAction(settings=self.swagger_settings)
            self.add_action(action)

    async def __call__(self, scope, receive, send):
        await self.__fastapi(scope=scope, receive=receive, send=send)
