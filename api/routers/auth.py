from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy import select, or_
from datetime import datetime, timedelta, timezone
import jwt

from api.database import SessionDep
from api.schemas import UserRegisterSchema, UserLoginSchema, TokenRefreshRequestSchema
from api.models import UserModel, RefreshTokenModel
from api.utils.security import hash_password, verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterSchema, session: SessionDep):
    query = select(UserModel).where(
        (UserModel.username == data.username) | (UserModel.email == data.email)
    )
    result = await session.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered",
        )

    password_hash = hash_password(data.password)
    new_user = UserModel(
        username=data.username,
        email=data.email,
        hashed_password=password_hash,
    )
    session.add(new_user)
    await session.commit()
    return {"status": "success", "detail": "User registered successfully"}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(data: UserLoginSchema, session: SessionDep):
    query = select(UserModel).where(
        or_(
            UserModel.username == data.login_field,
            UserModel.email == data.login_field
        )
    )
    result = await session.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )

    if not verify_password(data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    access_token = create_access_token(db_user.id)
    refresh_token = create_refresh_token(db_user.id)


