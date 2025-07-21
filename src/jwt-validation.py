import json
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from pydantic import BaseModel
from typing import List
from .database import get_async_session
from .db_models import User
from src import storage 

# This is used for fastapi docs authentification
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=settings.authorization_url, # https://sso.example.com/auth/
    tokenUrl=settings.token_url, # https://sso.example.com/auth/realms/example-realm/protocol/openid-connect/token
)

# TODO move this to read from env 
KEYCLOAK_CLIENT=  "fastapi-api"
KEYCLOAK_SERVER= "http://localhost:8080"
REALM= "ammaar"

keycloak_openid = KeycloakOpenID(
    server_url=settings.server_url, # https://sso.example.com/auth/
    client_id=settings.client_id, # backend-client-id
    realm_name=settings.realm, # example-realm
    client_secret_key=settings.client_secret, # your backend client secret
    verify=True
)



# Get user infos from the payload
async def get_user_info(payload: dict = Depends(get_payload)) -> User:
    try:
        return User(
            id=payload.get("sub"),
            username=payload.get("preferred_username"),
            email=payload.get("email"),
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name"),
            realm_roles=payload.get("realm_access", {}).get("roles", []),
            client_roles=payload.get("realm_access", {}).get("roles", [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e), # "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

async def get_idp_public_key():
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        f"{keycloak_openid.public_key()}"
        "\n-----END PUBLIC KEY-----"
    )

# Get the payload/token from keycloak
async def get_payload(token: str = Security(oauth2_scheme)) -> dict:
    try:
        return keycloak_openid.decode_token(
            token,
            key= await get_idp_public_key(),
            options={
                "verify_signature": True,
                "verify_aud": False,
                "exp": True
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e), # "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    


class TokenData(BaseModel):
    sub: str
    realm_access: dict
    groups: List[str] = []


async def get_current_user(token=Depends(auth_scheme)):
    credentials = token.credentials
    # Fetch JWKS from: {KEYCLOAK_SERVER}/realms/{REALM}/protocol/openid-connect/certs
    with open('keycloak-values.json', 'r') as f:
        public_keys = json.load(f)
    payload = jwt.decode(
        credentials,
        public_keys["keys"],
        algorithms=["RS256"],
        audience=KEYCLOAK_CLIENT,
    )
    data = TokenData(**payload)

    # Upsert into Postgres
    async with get_async_session() as session:
        user = await storage.get_user(data.sub)
        if not user:
            user = await storage.create_user(User(keycloak_id=data.sub, email=payload.get("email")))
            await session.commit()
            await session.refresh(user)
    return user, data
