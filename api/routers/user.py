from fastapi import APIRouter, status, Depends, File, UploadFile
from sqlalchemy import select

from api.database import SessionDep
from api.models import UserModel
from api.schemas import UserInfoResponseSchema, AvatarResponseSchema
from api.utils.dependencies import get_current_user, get_current_admin_user
from api.utils.errors import APIException, ErrorDetail
from api.utils.image import process_avatar
from api.utils.storage import upload_avatar, delete_avatar, build_avatar_url

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserInfoResponseSchema, status_code=status.HTTP_200_OK)
async def get_me(
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user)
):
    avatar_url = build_avatar_url(current_user.avatar_key)

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


@router.post(
    "/avatar",
    response_model=AvatarResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def upload_user_avatar(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
    file: UploadFile = File(...),
):
    processed_image = await process_avatar(file)

    if current_user.avatar_key:
        delete_avatar(current_user.avatar_key)

    avatar_key = upload_avatar(
        processed_image,
        current_user.id,
    )

    current_user.avatar_key = avatar_key

    await session.commit()
    await session.refresh(current_user)

    return {
        "status": "success",
        "avatar_url": build_avatar_url(current_user.avatar_key),
    }


@router.delete(
    "/avatar",
    status_code=status.HTTP_200_OK,
)
async def delete_user_avatar(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.avatar_key is None:
        raise APIException(ErrorDetail.AVATAR_NOT_FOUND)

    delete_avatar(current_user.avatar_key)

    current_user.avatar_key = None

    await session.commit()

    return {
        "status": "success",
    }
