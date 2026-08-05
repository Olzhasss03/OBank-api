from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from api.database import SessionDep
from api.models import UserModel, DeviceTokenModel
from api.schemas import FCMTokenRequest, BroadcastPushRequestSchema
from api.utils.dependencies import get_current_user, get_current_admin_user
from api.utils.push_service import send_broadcast_push

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/fcm-token", status_code=status.HTTP_200_OK)
async def save_fcm_token(
        data: FCMTokenRequest,
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user)
):
    query = select(DeviceTokenModel).where(DeviceTokenModel.fcm_token == data.fcm_token)
    result = await session.execute(query)
    existing_token = result.scalar_one_or_none()

    if existing_token:
        existing_token.user_id = current_user.id
        existing_token.locale = data.locale
        await session.commit()
    else:
        new_token = DeviceTokenModel(
            user_id=current_user.id,
            fcm_token=data.fcm_token,
            locale=data.locale
        )
        session.add(new_token)
        await session.commit()

    return {"detail": "FCM token saved successfully"}


@router.post("/broadcast", status_code=status.HTTP_200_OK)
async def send_broadcast(
        data: BroadcastPushRequestSchema,
        session: SessionDep,
        admin_user: UserModel = Depends(get_current_admin_user)
):
    await send_broadcast_push(data, session)
    return {"detail": "The broadcast has been successfully sent."}



