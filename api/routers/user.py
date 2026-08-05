from fastapi import APIRouter, status, Depends
from sqlalchemy import select

from api.database import SessionDep
from api.models import UserModel
from api.schemas import UserInfoResponseSchema
from api.utils.dependencies import get_current_user, get_current_admin_user
from api.utils.errors import APIException, ErrorDetail

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserInfoResponseSchema, status_code=status.HTTP_200_OK)
async def get_me(
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user)
):
    return current_user


@router.post("/make-admin/{username}", status_code=status.HTTP_200_OK)
async def make_admin(
    username: str,
    session: SessionDep,
    current_admin_user: UserModel = Depends(get_current_admin_user)
):
    user_query = select(UserModel).where(UserModel.username == username)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
        raise APIException(ErrorDetail.USER_NOT_FOUND)
    if user.is_admin:
        raise APIException(ErrorDetail.USER_ALREADY_ADMIN)

    user.is_admin = True
    await session.commit()
    return {
        "success": True,
        "detail": f"User @{user.username} is now an admin."
    }


@router.post("/remove-admin/{username}", status_code=status.HTTP_200_OK)
async def remove_admin(
    username: str,
    session: SessionDep,
    current_admin_user: UserModel = Depends(get_current_admin_user)
):
    user_query = select(UserModel).where(UserModel.username == username)
    user_result = await session.execute(user_query)
    user = user_result.scalars().first()

    if not user:
        raise APIException(ErrorDetail.USER_NOT_FOUND)
    if not user.is_admin:
        raise APIException(ErrorDetail.USER_NOT_ADMIN)

    user.is_admin = False
    await session.commit()
    return {
        "success": True,
        "detail": f"User @{user.username} is no longer an admin."
    }


