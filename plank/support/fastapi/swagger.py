import secrets
from typing import List, Optional, Callable

from fastapi import Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.routing import APIRoute
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from plank.context import Context
from plank.server.action import Action
from plank.server.fastapi.action import Routable
from plank.support.fastapi.settings import SwaggerSettings


def check_current_username(secrets_username: Optional[str] = None, secrets_password: Optional[str] = None) -> Callable[
    [Optional[str], Optional[str]], bool]:
    def check(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
        correct_username = secrets.compare_digest(credentials.username, secrets_username)
        correct_password = secrets.compare_digest(credentials.password, secrets_password)
        return (correct_username and correct_password)

    def no_check():
        return True

    if secrets_username == None:
        return no_check
    return check


class SwaggerAction(Action, Routable):
    def __init__(self, settings: SwaggerSettings):
        self.__settings = settings

    def name(self) -> str:
        return "swagger"

    def __routing_path__(self) -> str:
        return self.__settings.path

    def routing_path(self) -> str:
        return self.__settings.path

    def methods(self) -> List[str]:
        return ["GET"]

    def tags(self) -> List[str]:
        return []

    def description(self) -> Optional[str]:
        defaults = Context.standard()
        return defaults.reword(self.__settings.description)

    def response_model(self):
        return None

    def include_in_schema(self) -> bool:
        return False

    def route(self, path_prefix: Optional[str] = None) -> APIRoute:
        check_func = check_current_username(self.__settings.secrets_username, self.__settings.secrets_password)

        async def end_point(user_passed=Depends(check_func)):
            if not user_passed:
                raise HTTPException(
                    status_code=401,
                    detail='Incorrect email or password',
                    headers={'WWW-Authenticate': 'Basic'},
                )

            defaults = Context.standard()
            return get_swagger_ui_html(
                openapi_url=self.__settings.openapi_url,
                title=defaults.reword(self.__settings.title)
            )

        return self.get_route(end_point, path_prefix=path_prefix)
