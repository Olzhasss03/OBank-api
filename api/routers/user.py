from fastapi import APIRouter, status, Depends

from api.database import SessionDep
from api.models import UserModel
from api.schemas import UserInfoResponseSchema
from api.utils.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserInfoResponseSchema, status_code=status.HTTP_200_OK)
async def get_me(session: SessionDep, current_user: UserModel = Depends(get_current_user)):
    return current_user