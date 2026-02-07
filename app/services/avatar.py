import uuid
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def save_avatar_file(upload: UploadFile, user_id: str, uploads_dir: str, max_bytes: int) -> str:
    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported file type. Use JPEG, PNG, or WEBP")

    payload = await upload.read(max_bytes + 1)
    if not payload:
        raise ValueError("Empty file")
    if len(payload) > max_bytes:
        raise ValueError(f"File too large. Max size is {max_bytes} bytes")

    try:
        image = Image.open(BytesIO(payload))
        image.verify()
        file_format = image.format
    except UnidentifiedImageError as exc:
        raise ValueError("Invalid image payload") from exc

    extension = ALLOWED_IMAGE_FORMATS.get(file_format or "")
    if not extension:
        raise ValueError("Unsupported file type. Use JPEG, PNG, or WEBP")

    user_dir = Path(uploads_dir) / "avatars" / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = user_dir / filename
    destination.write_bytes(payload)

    return f"/uploads/avatars/{user_id}/{filename}"


def delete_avatar_file(avatar_url: str | None, uploads_dir: str) -> None:
    if not avatar_url or not avatar_url.startswith("/uploads/"):
        return

    relative_path = avatar_url.removeprefix("/uploads/")
    base_dir = Path(uploads_dir).resolve()
    avatar_path = (base_dir / relative_path).resolve()

    if base_dir not in avatar_path.parents:
        return
    if avatar_path.exists() and avatar_path.is_file():
        avatar_path.unlink()
