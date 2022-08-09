from typing import Optional, Callable, NoReturn
from pydantic import BaseSettings, Field

class SwaggerSettings(BaseSettings):
    title: str                      = Field(default="${application.name} - Documentations", env="SWAGGER_TITLE")
    path: str                       = Field(default="/docs", env="SWAGGER_PATH")
    openapi_path: str               = Field(default="/swagger/openapi.json", env="SWAGGER_OPENAPI_PATH")
    secrets_username: Optional[str] = Field(default=None, env="SWAGGER_SECRETS_USERSNAME")
    secrets_password: Optional[str] = Field(default=None, env="SWAGGER_SECRETS_PASSWORD")
