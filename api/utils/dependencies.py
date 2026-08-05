from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
import jwt

from api.database import SessionDep
from api.models import UserModel
from api.utils.errors import APIException, ErrorDetail
from config import settings

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: SessionDep = None
) -> UserModel:
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    query = select(UserModel).where(UserModel.id == int(user_id))
    result = await session.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_admin:
        raise APIException(ErrorDetail.AUTH_INSUFFICIENT_PERMISSIONS)
    return current_user
