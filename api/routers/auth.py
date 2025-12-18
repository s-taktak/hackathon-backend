from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import api.schemas.users as UserSchema
from api.schemas.token import Token, TokenData
import api.cruds.users as user_crud
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await user_crud.get_user_by_email(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(username=email) 
    except InvalidTokenError:
        raise credentials_exception
        
    user = await user_crud.get_user_by_email(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/auth/signup", response_model=UserSchema.UserMeResponse, operation_id="signUp", tags=["Auth"])
async def register_user(
    user_in: UserSchema.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_user = await user_crud.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_in.password)
    new_user = await user_crud.create_user(db, user_in, hashed_password)

    return new_user

@router.post("/auth/login", response_model=Token, operation_id="login", tags=["Auth"])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
) -> Token:    
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")