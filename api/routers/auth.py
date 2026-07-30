from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy import select, or_
from datetime import datetime, timezone
import jwt

from api.database import SessionDep
from api.schemas import UserRegisterSchema, UserLoginSchema, TokenRefreshRequestSchema, UserPinLoginSchema, UserPinSetupSchema
from api.models import UserModel, RefreshTokenModel, AccountModel
from api.utils.dependencies import get_current_user
from api.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterSchema, session: SessionDep):
    username = data.username.lower()
    email = data.email.lower()

    query = select(UserModel).where(
        (UserModel.username == username) | (UserModel.email == email)
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
        username=username,
        email=email,
        hashed_password=password_hash,
    )
    session.add(new_user)

    await session.flush()
    new_account = AccountModel(
        user_id=new_user.id,
        balance=500.00
    )
    session.add(new_account)

    await session.commit()
    return {"status": "success", "detail": "User registered successfully"}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(data: UserLoginSchema, session: SessionDep):
    loginfield = data.login_field.lower()

    query = select(UserModel).where(
        or_(
            UserModel.username == loginfield,
            UserModel.email == loginfield
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
    refresh_token, token_expire = create_refresh_token(db_user.id)

    new_db_token = RefreshTokenModel(
        token=refresh_token,
        user_id=db_user.id,
        expires_at=token_expire
    )
    session.add(new_db_token)
    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_tokens(data: TokenRefreshRequestSchema, session: SessionDep):
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "refresh" or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    query = select(RefreshTokenModel).where(RefreshTokenModel.token == data.refresh_token)
    result = await session.execute(query)
    db_token = result.scalars().first()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found in database")

    if db_token.is_used:
        delete_query = select(RefreshTokenModel).where(RefreshTokenModel.user_id == int(user_id))
        tokens_to_delete = await session.execute(delete_query)
        for t in tokens_to_delete.scalars().all():
            await session.delete(t)
        await session.commit()

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Security alert: Token reuse detected. All sessions revoked.")

    if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired in database")

    db_token.is_used = True

    new_access_token = create_access_token(int(user_id))
    new_refresh_token, new_token_expire = create_refresh_token(int(user_id))

    new_db_token = RefreshTokenModel(
        token=new_refresh_token,
        user_id=int(user_id),
        expires_at=new_token_expire
    )
    session.add(new_db_token)
    await session.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer"
    }


@router.post("/set-pin", status_code=status.HTTP_200_OK)
async def set_pincode(data: UserPinSetupSchema, session: SessionDep, current_user: UserModel = Depends(get_current_user)):
    pincode_hash = hash_password(data.pincode)
    current_user.hashed_pin = pincode_hash
    await session.commit()
    return {"status": "success", "detail": "PIN code successfully set"}


@router.post("/login-pin", status_code=status.HTTP_200_OK)
async def login_pincode(data: UserPinLoginSchema, session: SessionDep):
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "refresh" or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    query = select(RefreshTokenModel).where(RefreshTokenModel.token == data.refresh_token)
    result = await session.execute(query)
    db_token = result.scalars().first()

    if db_token is None or db_token.is_used:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found or already used (Session expired)")

    user_query = select(UserModel).where(UserModel.id == int(user_id))
    user_result = await session.execute(user_query)
    db_user = user_result.scalars().first()

    if db_user is None or db_user.hashed_pin is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or PIN not set")

    if not verify_password(data.pincode, db_user.hashed_pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect PIN code")

    db_token.is_used = True

    access_token = create_access_token(db_user.id)
    refresh_token_str, token_expire = create_refresh_token(db_user.id)

    new_db_token = RefreshTokenModel(
        token=refresh_token_str,
        user_id=db_user.id,
        expires_at=token_expire
    )
    session.add(new_db_token)
    await session.commit()

    return {
        "status": "success",
        "detail": "PIN verified successfully",
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "Bearer",
    }
