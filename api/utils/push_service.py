from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select, delete
from typing import Sequence, Tuple

from api.database import SessionDep
from api.models import DeviceTokenModel
from api.schemas import UserPushRequestSchema, BroadcastPushRequestSchema
from api.utils.translations import t
from config import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


async def _process_and_send_pushes(
    devices: Sequence[Tuple[str, str]],
    title_key: str,
    body_key: str,
    session: SessionDep,
    **kwargs
) -> None:
    if not devices:
        return

    locale_groups = defaultdict(list)
    for token, locale in devices:
        locale_groups[locale].append(token)

    invalid_tokens = []
    CHUNK_SIZE = 500

    for locale, tokens in locale_groups.items():
        title = t(locale, title_key, **kwargs)
        body = t(locale, body_key, **kwargs)

        for i in range(0, len(tokens), CHUNK_SIZE):
            chunk = tokens[i : i + CHUNK_SIZE]

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                tokens=chunk,
            )

            response = messaging.send_each_for_multicast(message)

            print(f"Firebase response: Success {response.success_count}, Error {response.failure_count}")

            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        print(f"[-] Removing dead token. Reason: {type(resp.exception).__name__} - {resp.exception}")
                        invalid_tokens.append(chunk[idx])

    if invalid_tokens:
        delete_query = delete(DeviceTokenModel).where(
            DeviceTokenModel.fcm_token.in_(invalid_tokens)
        )
        await session.execute(delete_query)
        await session.commit()


async def send_push_to_user(
        request: UserPushRequestSchema,
        session: SessionDep,
        **kwargs
) -> None:
    query = select(DeviceTokenModel.fcm_token, DeviceTokenModel.locale).where(DeviceTokenModel.user_id == request.user_id)
    result = await session.execute(query)
    devices = result.all()

    await _process_and_send_pushes(
        devices=devices,
        title_key=request.title_key,
        body_key=request.body_key,
        session=session,
        **kwargs
    )


async def send_broadcast_push(
    request: BroadcastPushRequestSchema,
    session: SessionDep,
    **kwargs
) -> None:
    query = select(DeviceTokenModel.fcm_token, DeviceTokenModel.locale)
    result = await session.execute(query)
    devices = result.all()

    await _process_and_send_pushes(
        devices=devices,
        title_key=request.title_key,
        body_key=request.body_key,
        session=session,
        **kwargs
    )
