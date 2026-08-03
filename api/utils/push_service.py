from collections import defaultdict

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select, delete

from api.database import SessionDep
from api.models import DeviceTokenModel
from api.utils.translations import t
from config import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


async def send_push_to_user(
    user_id: int,
    title_key: str,
    body_key: str,
    session: SessionDep,
    **kwargs
) -> None:
    query = select(DeviceTokenModel.fcm_token, DeviceTokenModel.locale).where(DeviceTokenModel.user_id == user_id)
    result = await session.execute(query)
    devices = result.all()

    if not devices:
        return

    locale_groups = defaultdict(list)
    for token, locale in devices:
        locale_groups[locale].append(token)

    invalid_tokens = []

    for locale, tokens in locale_groups.items():
        title = t(locale, title_key, **kwargs)
        body = t(locale, body_key, **kwargs)

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
        )

        response = messaging.send_each_for_multicast(message)

        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    if resp.exception.code in ['invalid-registration-token', 'registration-token-not-registered']:
                        invalid_tokens.append(tokens[idx])

    if invalid_tokens:
        delete_query = delete(DeviceTokenModel).where(
            DeviceTokenModel.fcm_token.in_(invalid_tokens)
        )
        await session.execute(delete_query)
        await session.commit()
