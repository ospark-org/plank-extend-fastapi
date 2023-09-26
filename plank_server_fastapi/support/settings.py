from __future__ import annotations

from typing import Optional

from pydantic import BaseSettings, Field


class SwaggerSettings(BaseSettings):
    title: str = Field(default="${app.name} - Documentations", env="SWAGGER_TITLE")
    description: Optional[str] = Field(default=None, env="SWAGGER_DESCRIPTON")
    path: str = Field(default="/docs", env="SWAGGER_PATH")
    openapi_url: str = Field(default="/swagger/openapi.json", env="SWAGGER_OPENAPI_URL")
    secrets_username: Optional[str] = Field(default=None, env="SWAGGER_SECRETS_USERSNAME")
    secrets_password: Optional[str] = Field(default=None, env="SWAGGER_SECRETS_PASSWORD")

    @classmethod
    def default(cls) -> SwaggerSettings:
        singleton_key = "__signleton__"
        if not hasattr(cls, singleton_key):
            setattr(cls, singleton_key, cls())
        return getattr(cls, singleton_key)
