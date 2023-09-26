from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from plank import logger
from plank.app import Application
from plank.configuration import Configuration
from plank.context import Context
from plank.server import ApplicationServer

from plank_server_fastapi.scheme import FastAPIHelper
from plank_server_fastapi.support.builtin import BuiltinService
from plank_server_fastapi.support.settings import SwaggerSettings


class FastAPIServer(ApplicationServer):
    __protocol__ = FastAPIHelper.__protocol__

    @classmethod
    def build(cls, configuration: Configuration, delegate: ApplicationServer.Delegate,
              path_prefix: Optional[str] = None,
              api_version: Optional[str] = None, **fastapi_arguments) -> FastAPIServer:
        app = Application(delegate=delegate, configuration=configuration)
        api_version = api_version or configuration.app.build_version
        server = FastAPIServer(application=app, version=api_version, delegate=delegate, path_prefix=path_prefix,
                               **fastapi_arguments)
        return server

    @property
    def path_prefix(self) -> str:
        return self.__path_prefix

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
        super().__init__(application=application, delegate=delegate)
        self.__api_version = version
        self.__path_prefix = path_prefix
        self.__swagger_settings = SwaggerSettings.default()
        self.__include_swagger = include_swagger if include_swagger is not None else True
        self.__startup_handler = lambda self: None
        self.__shutdown_handler = lambda self: None

        standard_context = Context.standard()
        standard_context.set("path_prefix", (path_prefix or ""))

        self.__fastapi = FastAPI(
            docs_url=None,
            redoc_url=None,
            version=f"{version}-{application.configuration.name}",
            **fastapi_arguments
        )

        self.__fastapi.router.add_event_handler("startup", lambda: self.did_startup())
        self.__fastapi.router.add_event_handler("shutdown", lambda: self.did_shutdown())

        builtin_apis_service = BuiltinService(app=self.application)
        self.add_api(builtin_apis_service.version)

        if self.__include_swagger:
            self.add_api(builtin_apis_service.swagger)

    def launch(self, **options):
        super(FastAPIServer, self).launch(**options)
        context = Context.standard()
        context.set("swagger_path", self.__swagger_settings.path)

        self.__fastapi.title = context.reword(self.__swagger_settings.title)
        self.__fastapi.openapi_url = context.reword(self.__swagger_settings.openapi_url)
        self.__fastapi.setup()

    def did_launch(self):
        for name, helper in self.scheme_helpers:
            configuration = Configuration.default()

            service_name = helper.api.get_meta_info(key="service_name")
            service_path = helper.api.get_meta_info(key="service_path")
            if service_path is not None:
                service_prefix = configuration.context.reword(service_path)
            else:
                service_prefix = None
            route = helper.build_route(service_name=service_name, service_prefix=service_prefix,
                                       path_prefix=self.path_prefix)
            logger.debug(f"[Server.FastAPI] Added route at path: {route.path} by {helper}")
            self.__fastapi.routes.append(route)

    async def __call__(self, scope, receive, send):
        if not self.launched:
            launch_options = self.launch_options or {}
            self.launch(**launch_options)
        await self.__fastapi(scope=scope, receive=receive, send=send)


