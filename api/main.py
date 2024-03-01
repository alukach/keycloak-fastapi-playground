from typing import Annotated, Optional, AsyncGenerator, Dict, Any

import jwt
import httpx
from pydantic import Field
from pydantic_settings import BaseSettings
from fastapi import FastAPI, security, Security, Form, HTTPException, Depends


#
# Settings
#
class Settings(BaseSettings):
    keycloak_url: str
    keycloak_internal_url: Optional[str] = None
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: Optional[str] = Field(None, repr=False)

    @property
    def oidc_api(self):
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect"
        )

    @property
    def internal_oidc_api(self):
        return f"{self.keycloak_internal_url or self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect"


settings = Settings(
    keycloak_realm="stac-api-playground-1",
    keycloak_client_id="stac-api",
)

oauth2_scheme = security.OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.oidc_api}/auth",
    tokenUrl=f"{settings.oidc_api}/token",
    scopes={
        "stac:create": "Create STAC Items",
        "stac:read": "Read STAC Items",
        "stac:update": "Update STAC Items",
        "stac:delete": "Delete STAC Items",
    },
)


#
# Dependencies
#
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


@app.get("/scope")
def basic(user_token: Annotated[Dict[Any, Any], Depends(user_token)]):
    return user_token["scope"].split(" ")
