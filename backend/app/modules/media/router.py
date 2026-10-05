import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.media import service
from app.modules.media.schemas import MediaPublic
from app.modules.users.models import User

router = APIRouter(prefix="/media", tags=["media"])


@router.post("", response_model=MediaPublic, status_code=201)
def upload_media(
    file: UploadFile = File(...),
    visibility: str = Form(default="RESTRICTED"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.upload_media(db, current_user.id, file, visibility)


@router.get("/{media_id}", response_model=MediaPublic)
def get_media(
    media_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    media = service.get_media_or_404(db, media_id)
    service.check_media_view_access(db, media, current_user.id)
    return media


@router.get("/{media_id}/content")
def get_media_content(
    media_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes, mime_type = service.get_media_content(db, media_id, current_user.id)
    return Response(content=file_bytes, media_type=mime_type)
