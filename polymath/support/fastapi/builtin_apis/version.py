from polymath.support.fastapi import route
from pydantic import BaseModel, Field
from polymath.app.defaults import UserDefaults
from polymath.app._fastapi import Application

class VersionResponseSchema(BaseModel):
    api_version: str = Field(example='2020.12.29.174720')
    app_version: str = Field(example='1.0.1')

async def version_api():
    app = Application.main()
    response = {
        "api_version": app.version,
        "app_version": app.version
    }
    return response

