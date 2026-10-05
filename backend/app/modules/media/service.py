import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.modules.media import storage
from app.modules.media.models import Media
from app.modules.media.schemas import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES
from app.modules.users import repository as users_repository


def upload_media(db: Session, owner_id: uuid.UUID, file: UploadFile, visibility: str = "RESTRICTED") -> Media:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type: {file.content_type}",
        )

    file_bytes = file.file.read()
    size_bytes = len(file_bytes)

    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file")

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File exceeds maximum allowed size")

    object_key = storage.build_object_key(owner_id, file.filename or "upload")
    storage.upload_file(object_key, file_bytes, file.content_type)

    media = Media(
        owner_id=owner_id,
        object_key=object_key,
        mime_type=file.content_type,
        size_bytes=size_bytes,
        visibility=visibility,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_media_or_404(db: Session, media_id: uuid.UUID) -> Media:
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    return media


def check_media_view_access(db: Session, media: Media, current_user_id: uuid.UUID) -> None:
    if media.owner_id == current_user_id:
        return
    if media.visibility == "PUBLIC":
        return
    permission_codes = users_repository.get_user_permission_codes(db, current_user_id)
    if "campaign:review" in permission_codes:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to view this file",
    )


def get_media_content(db: Session, media_id: uuid.UUID, current_user_id: uuid.UUID) -> tuple[bytes, str]:
    media = get_media_or_404(db, media_id)
    check_media_view_access(db, media, current_user_id)
    file_bytes = storage.download_file(media.object_key)
    return file_bytes, media.mime_type
