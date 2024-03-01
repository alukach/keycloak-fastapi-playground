from typing import Annotated, Optional, AsyncGenerator, Dict, Any

import jwt
import httpx
from pydantic import Field
from pydantic_settings import BaseSettings
from fastapi import FastAPI, security, Security, HTTPException, Depends


#
# Settings
#
class Settings(BaseSettings):
    keycloak_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: Optional[str] = Field(None, repr=False)

    @property
    def oidc_api(self):
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect"
        )


settings = Settings()


#
# Dependencies
#
oauth2_scheme = security.OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.oidc_api}/auth",
    tokenUrl=f"{settings.oidc_api}/token",
    scopes={
        "stac:collection:create": "Create collection",
        "stac:collection:update": "Update collection",
        "stac:collection:delete": "Delete collection",
        "stac:item:create": "Create item",
        "stac:item:update": "Update item",
        "stac:item:delete": "Delete item",
    },
)


async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Dependency to create async http requests and to gracefully handle any response
    errors.
    """
    async with httpx.AsyncClient() as client:
        try:
            yield client
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    **e.response.json(),
                    "message": str(e),
                },
            )


def user_token(token: Annotated[str, Security(oauth2_scheme)]):
    return jwt.decode(token, options={"verify_signature": False})


#
# App
#
app = FastAPI(
    swagger_ui_init_oauth={
        "appName": "JupyterHub",
        "clientId": settings.keycloak_client_id,
        "usePkceWithAuthorizationCodeGrant": True,
    }
)


@app.get("/")
def basic(user_token: Annotated[Dict[Any, Any], Depends(user_token)]):
    return user_token


@app.get("/scopes")
def scopes(user_token: Annotated[Dict[Any, Any], Depends(user_token)]):
    return user_token["scope"].split(" ")
