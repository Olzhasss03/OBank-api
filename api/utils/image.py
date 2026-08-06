from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import UploadFile

from api.utils.errors import APIException, ErrorDetail

MAX_FILE_SIZE = 10 * 1024 * 1024
AVATAR_SIZE = (512, 512)
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


async def process_avatar(file: UploadFile) -> BytesIO:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise APIException(ErrorDetail.IMAGE_INVALID_FORMAT)

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise APIException(ErrorDetail.IMAGE_TOO_LARGE)

    try:
        image = Image.open(BytesIO(contents))
    except UnidentifiedImageError:
        raise APIException(ErrorDetail.IMAGE_NOT_VALID)

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    width, height = image.size
    crop_size = min(width, height)

    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size

    image = image.crop((left, top, right, bottom))
    image = image.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)

    output = BytesIO()

    image.save(
        output,
        format="WEBP",
        quality=85,
        method=6,
    )

    output.seek(0)

    return output
