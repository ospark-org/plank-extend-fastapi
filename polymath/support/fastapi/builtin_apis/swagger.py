import secrets
from fastapi import Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from polymath.support.fastapi import route
from polymath.app._fastapi import Application

def get_current_username(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    app = Application.main()

    api_username = app.swagger_secrets_username
    api_password = app.swagger_secrets_password
    if api_username is None:
        return "no secrets"
    correct_username = secrets.compare_digest(credentials.username, api_username)
    correct_password = secrets.compare_digest(credentials.password, api_password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return credentials.username

def swagger_api(username: str = Depends(get_current_username)):
    app = Application.main()
    return get_swagger_ui_html(
        openapi_url=app.openapi_path,
        title=app.name + ' - Swagger UI'
    )
