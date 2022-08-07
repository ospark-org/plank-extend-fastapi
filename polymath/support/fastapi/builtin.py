import secrets
from pydantic import BaseModel
from typing import Dict, Optional, Any
from fastapi import Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from polymath.serving.service import Service
from polymath.decorator.fastapi import routable

class VersionResponse(BaseModel):
    app_version: str = "0.1.0"
    build_version: str = "2022-08-05.00002"


class BuiltinService(Service):

    def __init__(self, name: str, build_version: str, app_version: str, title: str, openapi_path: str,serving_path: Optional[str]=None, user: Optional[str]=None, password: Optional[str]=None):
        super().__init__(name=name, serving_path=serving_path)
        self.__build_version = build_version
        self.__app_version = app_version
        self.__title = title
        self.__openapi_path = openapi_path
        self.__user = user
        self.__password = password or ""

    @routable(path="/version", tags=["default"], methods=["GET"])
    async def version(self) -> VersionResponse:
        return VersionResponse(
            build_version=self.__build_version,
            app_version=self.__app_version
        )

    def get_current_username(self, credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
        if self.__user is None:
            return "no secrets"
        correct_username = secrets.compare_digest(credentials.username, self.__user)
        correct_password = secrets.compare_digest(credentials.password, self.__password)
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password',
                headers={'WWW-Authenticate': 'Basic'},
            )
        return credentials.username

    @routable(path="/swagger", tags=["default"], methods=["GET"], include_in_schema=False)
    async def swagger(self) -> Any:
        return get_swagger_ui_html(
            openapi_url=self.__openapi_path,
            title=self.__title
        )
