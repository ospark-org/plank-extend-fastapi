import secrets
from pydantic import BaseModel
from typing import Optional, Callable
from fastapi import Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from polymath.serving.service import Service
from polymath.app import Application
from polymath.decorator.fastapi import routable
from polymath.support.fastapi.settings import SwaggerSettings

class VersionResponse(BaseModel):
    app_version: str = "0.1.0"
    build_version: str = "2022-08-05.00002"

def get_current_username(credentials: HTTPBasicCredentials = Depends(HTTPBasic()))->Callable[[Optional[str], Optional[str]], bool]:
    def _f(secrets_username: Optional[str]=None, secrets_password: Optional[str]=None):
        if secrets_username is None:
            return True
        correct_username = secrets.compare_digest(credentials.username, secrets_username)
        correct_password = secrets.compare_digest(credentials.password, secrets_password)
        return (correct_username and correct_password)
    return _f

class BuiltinService(Service):

    def __init__(self, name:str, app:Application, swagger_setting: SwaggerSettings, serving_path: Optional[str]=None):
        super().__init__(name=name, serving_path=serving_path)
        self.__build_version = app.build_version
        self.__app_version = app.version
        self.__swagger_settings = swagger_setting

    @routable(path="/version", tags=["default"], methods=["GET"])
    async def version(self) -> VersionResponse:
        return VersionResponse(
            build_version=self.__build_version,
            app_version=self.__app_version
        )

    @routable(path="/${swagger_path}", tags=["default"], methods=["GET"], include_in_schema=False)
    async def swagger(self, check_user: Callable[[Optional[str], Optional[str]], bool] = Depends(get_current_username)):
        user_passed = check_user(self.__swagger_settings.secrets_username, self.__swagger_settings.secrets_password)
        if not user_passed:
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password',
                headers={'WWW-Authenticate': 'Basic'},
            )

        return get_swagger_ui_html(
            openapi_url=self.__swagger_settings.openapi_url,
            title=self.__swagger_settings.title
        )
