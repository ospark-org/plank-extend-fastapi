from __future__ import annotations
from typing import Optional, Callable, NoReturn, List
from asgiref.typing import ASGI2Protocol
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.requests import Request
from fastapi.responses import Response
from typing import Optional, Callable, NoReturn, List
from pathlib import Path
from polymath.support.fastapi import route
from polymath.app import Application as _Application, ApplicationDelegate

class FastAPIDelegate(ApplicationDelegate):
    def api_did_startup(self, app: Application): pass
    def api_did_shutdown(self, app: Application): pass

    def api_add_middlewares(self, app: Application)->Optional[List[Middleware]]:
        return None
    def api_add_http_middleware_funcs(self, app: Application)->Optional[
        List[
            Callable[[Request, Callable[[Request], Response]], NoReturn]
        ]]:
        return None


class Application(_Application, ASGI2Protocol):

    @property
    def delegate(self) ->FastAPIDelegate:
        return super().delegate

    @property
    def fastapi(self)->FastAPI:
        return self.__fastapi

    @property
    def prefix_name(self)->str:
        return self.__prefix_name

    @property
    def openapi_path(self)->str:
        return self.__openapi_path or f"/{self.prefix_name}/openapi.json"

    @property
    def swagger_secrets_username(self)->Optional[str]:
        return self.__swagger_secrets_username

    @property
    def swagger_secrets_password(self)->Optional[str]:
        return self.__swagger_secrets_password

    @property
    def swagger_path(self)->str:
        return self.__swagger_path

    def __init__(self,
                name: str, version: str, delegate: FastAPIDelegate,
                prefix_name: Optional[str]=None,
                openapi_path: Optional[str] = None,
                swagger_secrets_username: Optional[str]=None,
                swagger_secrets_password: Optional[str] = None,
                swagger_path: Optional[str] = None,
                **fastapi_arguments):

        super().__init__(name=name, version=version, delegate=delegate)
        self.__prefix_name = prefix_name or name
        self.__openapi_path = openapi_path
        self.__swagger_secrets_username = swagger_secrets_username
        self.__swagger_secrets_password = swagger_secrets_password
        self.__swagger_path = swagger_path or "/docs"

        self.__fastapi = FastAPI(
            docs_url=None,
            redoc_url=None,
            openapi_url=self.openapi_path,
            **fastapi_arguments
        )


    def add_route(self, route):
        self.api_app.routes.append(route)

    def launch(self, **options):
        from polymath.support.fastapi.builtin_apis.swagger import swagger_api
        from polymath.support.fastapi.builtin_apis.version import version_api, VersionResponseSchema

        def startup():
            super(Application, self).launch(**options)
            self.delegate.api_did_startup(app=self)

        def shutdown():
            self.delegate.api_did_shutdown(app=self)

        self.fastapi.router.add_event_handler("startup", startup)
        self.fastapi.router.add_event_handler("shutdown", shutdown)

        swagger_route = route(path=self.swagger_path, methods=["GET"], include_in_schema=False)(swagger_api)
        version_route = route(path="/version", methods=["GET"], tags=["default"], response_model=VersionResponseSchema)(
            version_api)
        self.fastapi.routes.append(swagger_route)
        self.fastapi.routes.append(version_route)



    async def __call__(self, scope, receive, send):
        await self.fastapi(scope=scope, receive=receive, send=send)