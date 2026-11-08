import shutil
import tempfile
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import AudioFile, Project, User
from app.schemas.audio import AudioFileListResponse, AudioFileResponse
from app.services.audio import AudioToolError, AudioValidationError, inspect_audio, normalize_audio, safe_filename
from app.storage.minio_storage import StorageError, put_file, remove_file, stream_file

router = APIRouter(tags=["audio-files"])


def owned_project(project_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def owned_audio_file(audio_file_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> AudioFile:
    audio_file = db.scalar(
        select(AudioFile)
        .join(Project, Project.id == AudioFile.project_id)
        .where(AudioFile.id == audio_file_id, Project.owner_id == user_id)
    )
    if audio_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo de audio no encontrado")
    return audio_file


def raise_audio_error(exc: Exception) -> None:
    if isinstance(exc, AudioValidationError):
        raise HTTPException(status_code=exc.status_code, detail=exc.args[0]) from exc
    if isinstance(exc, AudioToolError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if isinstance(exc, StorageError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise exc


@router.post(
    "/projects/{project_id}/audio-files",
    response_model=AudioFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar un archivo de audio",
)
def upload_audio_file(
    project_id: uuid.UUID,
    upload: UploadFile = File(..., description="Archivo WAV o MP3 de máximo 50 MB y 3 minutos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AudioFile:
    owned_project(project_id, current_user.id, db)
    filename = safe_filename(upload.filename)
    audio_file_id = uuid.uuid4()
    original_key = f"projects/{project_id}/original/{audio_file_id}/{filename}"
    normalized_key = f"projects/{project_id}/normalized/{audio_file_id}.wav"
    stored_objects: list[str] = []
    source_size = 0

    try:
        with tempfile.TemporaryDirectory(prefix="dolean-audio-") as directory:
            source = Path(directory) / filename
            normalized = Path(directory) / "normalized.wav"
            upload.file.seek(0)
            with source.open("wb") as destination:
                shutil.copyfileobj(upload.file, destination, length=1024 * 1024)
            source_size = source.stat().st_size
            metadata = inspect_audio(source, filename, upload.content_type)
            normalize_audio(source, normalized)
            put_file(source, original_key, upload.content_type or "application/octet-stream")
            stored_objects.append(original_key)
            put_file(normalized, normalized_key, "audio/wav")
            stored_objects.append(normalized_key)

        record = AudioFile(
            id=audio_file_id,
            project_id=project_id,
            original_filename=filename,
            content_type=upload.content_type or "application/octet-stream",
            storage_key=original_key,
            normalized_storage_key=normalized_key,
            size_bytes=source_size,
            duration_seconds=metadata.duration_seconds,
            sample_rate=metadata.sample_rate,
            channels=metadata.channels,
            normalized_sample_rate=settings.audio_normalized_sample_rate,
            normalized_channels=1,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except (AudioValidationError, AudioToolError, StorageError) as exc:
        for object_name in stored_objects:
            try:
                remove_file(object_name)
            except StorageError:
                pass
        raise_audio_error(exc)
    except Exception:
        db.rollback()
        for object_name in stored_objects:
            try:
                remove_file(object_name)
            except StorageError:
                pass
        raise
    finally:
        upload.file.close()


@router.get(
    "/projects/{project_id}/audio-files",
    response_model=AudioFileListResponse,
    summary="Listar archivos de audio de un proyecto",
)
def list_audio_files(
    project_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AudioFileListResponse:
    owned_project(project_id, current_user.id, db)
    filter_clause = AudioFile.project_id == project_id
    total = db.scalar(select(func.count()).select_from(AudioFile).where(filter_clause)) or 0
    files = list(
        db.scalars(select(AudioFile).where(filter_clause).order_by(AudioFile.created_at.desc()).offset(offset).limit(limit))
    )
    return AudioFileListResponse(items=files, total=total, limit=limit, offset=offset)


@router.get("/audio-files/{audio_file_id}", response_model=AudioFileResponse, summary="Consultar metadatos de audio")
def get_audio_file(
    audio_file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AudioFile:
    return owned_audio_file(audio_file_id, current_user.id, db)


@router.delete("/audio-files/{audio_file_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar archivo de audio")
def delete_audio_file(
    audio_file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    audio_file = owned_audio_file(audio_file_id, current_user.id, db)
    try:
        remove_file(audio_file.storage_key)
        if audio_file.normalized_storage_key:
            remove_file(audio_file.normalized_storage_key)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    db.delete(audio_file)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audio-files/{audio_file_id}/download", summary="Descargar el archivo de audio original")
def download_audio_file(
    audio_file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    audio_file = owned_audio_file(audio_file_id, current_user.id, db)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(audio_file.original_filename)}"}
    return StreamingResponse(stream_file(audio_file.storage_key), media_type=audio_file.content_type, headers=headers)
