from typing import Annotated
from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .database import init_db
from .config import settings
import logging, yaml

from .routes.products.product_router import router as products_router
from .routes.products.prices_router import router as prices_router
from .routes.analytics.router import router as analytics_router
from .routes.auth.router import router as auth_router
from .routes.rebates.router import router as rebates_router
from .routes.ctc import router as ctc_router
from .routes.distributors.router import router as distributors_router
from .routes.brands.router import router as brands_router
from .routes.features_benefits_router import router as features_benefits_router
from .models import User, Token


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

app = FastAPI()

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# with open('python_server/logging.yaml') as f:
#     cfg = yaml.safe_load(f)
# logging.config.dictConfig(cfg)

logger = logging.getLogger('uvicorn.error')

# TODO add for porduction env 
# app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=[
    "example.com",
    "*.example.com",
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "testserver",
])
# # CORS configuration

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(prices_router)
app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(rebates_router)
app.include_router(ctc_router)
app.include_router(distributors_router)
app.include_router(brands_router)
app.include_router(features_benefits_router)

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    
def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user




async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# @app.post("/token")
# async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     user_dict = fake_users_db.get(form_data.username)
#     if not user_dict:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
#     user = UserInDB(**user_dict)
#     hashed_password = fake_hash_password(form_data.password)
#     if not hashed_password == user.hashed_password:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")

#     return {"access_token": user.username, "token_type": "bearer"}


# @app.get("/users/me")
# async def read_users_me(
#     current_user: Annotated[User, Depends(get_current_active_user)],
# ):
#     return current_user

# @app.get("/users/me")
# async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
#     return current_user


@app.on_event("startup")
async def startup():
    await init_db(load_ctc_data=True, load_brands_data=True)
    
    # Initialize features and benefits data
    try:
        logger.info("Initializing features and benefits data...")
        from .init_features_benefits import initialize_features_benefits_data
        
        success = await initialize_features_benefits_data()
        if success:
            logger.info("Features and benefits data initialized successfully")
        else:
            logger.warning("Features and benefits initialization failed or not needed")
    except Exception as e:
        logger.error(f"Failed to initialize features and benefits data: {e}")
        # Don't fail the entire startup if features/benefits loading fails


@app.get("/")
async def main():
    return {"message": "Application alive"}

