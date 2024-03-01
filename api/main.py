from typing import Annotated, Any, Dict, Optional

import jwt
from fastapi import FastAPI, HTTPException, Security, security, status
from pydantic import Field
from pydantic_settings import BaseSettings


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


def user_token(
    token_str: Annotated[str, Security(oauth2_scheme)],
    required_scopes: security.SecurityScopes,
):
    # Parse & validate token
    token = jwt.decode(
        token_str,
        options={
            # TODO: This is purely for illustrative purposes, for production you would want to verify the signature
            "verify_signature": False
        },
    )

    # Validate scopes (if required)
    for scope in required_scopes.scopes:
        if scope not in token["scope"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{required_scopes.scope_str}"'
                },
            )

    return token


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
def basic(user_token: Annotated[Dict[Any, Any], Security(user_token)]):
    """View auth token."""
    return user_token


@app.get("/scopes")
def scopes(user_token: Annotated[Dict[Any, Any], Security(user_token)]):
    """View auth token scopes."""
    return user_token["scope"].split(" ")


@app.get(
    "/create-collection",
    dependencies=[Security(user_token, scopes=["stac:collection:create"])],
)
def create_collection():
    """Mock endpoint to create a collection. Requires `stac:collection:create` scope."""
    return {
        "success": True,
        "details": "🚀 You have the required scope to create a collection",
    }
