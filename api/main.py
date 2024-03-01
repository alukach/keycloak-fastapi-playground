from typing import Annotated, Any, Dict, List, Optional

import jwt
from fastapi import FastAPI, HTTPException, Security, security, status
from pydantic import Field
from pydantic_settings import BaseSettings


#
# Settings
#
class Settings(BaseSettings):
    keycloak_url: str
    keycloak_internal_url: Optional[str] = None
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: Optional[str] = Field(None, repr=False)
    permitted_jwt_audiences: List[str] = ["account"]

    @property
    def keycloak_oidc_api_url(self):
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect"
        )

    @property
    def keycloak_jwks_url(self):
        base_url = self.keycloak_internal_url or self.keycloak_url
        return f"{base_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"


settings = Settings()
jwks_client = jwt.PyJWKClient(settings.keycloak_jwks_url)  # Caches JWKs


#
# Dependencies
#
oauth2_scheme = security.OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.keycloak_oidc_api_url}/auth",
    tokenUrl=f"{settings.keycloak_oidc_api_url}/token",
    scopes={
        f"stac:{resource}:{action}": f"{action.title()} {resource}"
        for resource in ["collection", "item"]
        for action in ["create", "update", "delete"]
    },
)


def user_token(
    token_str: Annotated[str, Security(oauth2_scheme)],
    required_scopes: security.SecurityScopes,
):
    # Parse & validate token
    token = jwt.decode(
        token_str,
        jwks_client.get_signing_key_from_jwt(token_str).key,
        algorithms=["RS256"],
        audience=settings.permitted_jwt_audiences,
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
