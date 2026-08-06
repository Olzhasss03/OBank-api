from io import BytesIO
from uuid import uuid4
import boto3

from config import settings

client = boto3.client(
    "s3",
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
)


def upload_avatar(file: BytesIO, user_id: int) -> str:
    key = f"avatars/{user_id}/{uuid4().hex}.webp"

    client.upload_fileobj(
        Fileobj=file,
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        ExtraArgs={
            "ContentType": "image/webp"
        }
    )

    return key


def delete_avatar(key: str) -> None:
    client.delete_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
    )


def build_avatar_url(key: str | None) -> str | None:
    if not key:
        return None

    return f"{settings.R2_PUBLIC_URL}/{key}"
