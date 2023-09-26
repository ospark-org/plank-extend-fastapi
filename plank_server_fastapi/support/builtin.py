import secrets

from fastapi import Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.requests import Request
from fastapi.security import HTTPBasic
from plank.app import Application
from plank.context import Context
from plank.service import Service
from pydantic import BaseModel

from plank_server_fastapi.decorator import routable, http
from plank_server_fastapi.support.settings import SwaggerSettings


class VersionResponse(BaseModel):
    app_version: str = "0.1.0"
    build_version: str = "2022-08-05.00002"


class CheckableHTTPBasic(HTTPBasic):
    async def __call__(  # type: ignore
            self, request: Request
    ) -> bool:
        settings = SwaggerSettings.default()
        if settings.secrets_username is not None:
            credentials = await super().__call__(request=request)

            correct_username = settings.secrets_username is None \
                               or secrets.compare_digest(credentials.username, settings.secrets_username)
            correct_password = settings.secrets_password is None \
                               or secrets.compare_digest(credentials.password, settings.secrets_password)
            user_passed = (correct_username and correct_password)
            return user_passed
        else:
            return True


@routable(path="/")
class BuiltinService(Service):

    def __init__(self, app: Application):
        self.__build_version = app.build_version
        self.__app_version = app.version

    @http(path="/version", methods=["GET"], tags=["default"])
    def version(self):
        return {
            "build_version": self.__build_version,
            "app_version": self.__app_version
        }

    @http(path="/docs", methods=["GET"], tags=["default"], include_in_schema=False)
    def swagger(self, user_passed: bool):
        if not user_passed:
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password',
                headers={'WWW-Authenticate': 'Basic'},
            )
        settings = SwaggerSettings.default()
        defaults = Context.standard()
        return get_swagger_ui_html(
            openapi_url=settings.openapi_url,
            title=defaults.reword(settings.title)
        )


@BuiltinService.version.http.response.pack(response_model=VersionResponse)
def version(value):
    return VersionResponse.construct(**value)


@BuiltinService.swagger.http.request.pack
def swagger(user_passed: bool = Depends(CheckableHTTPBasic())):
    return {
        "user_passed": user_passed
    }
