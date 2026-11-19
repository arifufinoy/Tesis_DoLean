import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Analysis, AudioFile, CorrectionRequest, ProcessedVersion, ProcessingJob, ProcessingStatus, Project, User
from app.schemas.corrections import CorrectionRequestCreate, CorrectionStartResponse, ProcessedVersionResponse
from app.tasks.correction import correct_audio_task
from app.storage.minio_storage import stream_file

router = APIRouter(tags=["corrections"])


def owned_audio(audio_file_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> AudioFile:
    audio = db.scalar(select(AudioFile).join(Project).where(AudioFile.id == audio_file_id, Project.owner_id == user_id))
    if audio is None:
        raise HTTPException(status_code=404, detail="Archivo de audio no encontrado")
    return audio


@router.post("/audio-files/{audio_file_id}/corrections", response_model=CorrectionStartResponse, status_code=status.HTTP_202_ACCEPTED, summary="Solicitar corrección de afinación")
def create_correction(audio_file_id: uuid.UUID, payload: CorrectionRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CorrectionStartResponse:
    audio = owned_audio(audio_file_id, current_user.id, db)
    analysis = db.scalar(select(Analysis).where(Analysis.id == payload.analysis_id, Analysis.audio_file_id == audio.id).options(selectinload(Analysis.notes)))
    if analysis is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado para el archivo indicado")
    if analysis.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="El análisis debe estar completado")
    notes = {note.id: note for note in analysis.notes}
    edits: list[dict] = []
    intervals: list[tuple[float, float]] = []
    for edit in payload.edits:
        note = notes.get(edit.note_id)
        if note is None or note.detected_midi is None:
            raise HTTPException(status_code=422, detail="Una nota no pertenece al análisis o no tiene tono detectable")
        interval = (note.start_time, note.end_time)
        if any(interval[0] < other[1] and other[0] < interval[1] for other in intervals):
            raise HTTPException(status_code=422, detail="Los segmentos de corrección no pueden superponerse")
        intervals.append(interval)
        edits.append({"note_id": str(note.id), "start_time": note.start_time, "end_time": note.end_time, "n_steps": edit.target_midi - note.detected_midi, "target_midi": edit.target_midi})
    correction = CorrectionRequest(analysis_id=analysis.id, parameters={"analysis_id": str(analysis.id), "edits": edits, "output_format": payload.output_format}, status=ProcessingStatus.PENDING)
    db.add(correction)
    db.flush()
    job = ProcessingJob(analysis_id=analysis.id, job_type="pitch_correction", status=ProcessingStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(correction)
    db.refresh(job)
    task = correct_audio_task.delay(str(correction.id), str(job.id))
    job.celery_task_id = task.id
    db.commit()
    return CorrectionStartResponse(correction_request_id=correction.id, job_id=job.id, status=correction.status, status_url=f"/api/v1/jobs/{job.id}")


@router.get("/audio-files/{audio_file_id}/versions", response_model=list[ProcessedVersionResponse], summary="Listar versiones corregidas")
def list_versions(audio_file_id: uuid.UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProcessedVersion]:
    owned_audio(audio_file_id, current_user.id, db)
    return list(db.scalars(select(ProcessedVersion).where(ProcessedVersion.source_audio_file_id == audio_file_id).order_by(ProcessedVersion.created_at.desc()).offset(offset).limit(limit)))


@router.get("/versions/{version_id}", response_model=ProcessedVersionResponse, summary="Consultar una versión corregida")
def get_version(version_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProcessedVersion:
    version = db.scalar(select(ProcessedVersion).join(AudioFile).join(Project).where(ProcessedVersion.id == version_id, Project.owner_id == current_user.id))
    if version is None:
        raise HTTPException(status_code=404, detail="Versión no encontrada")
    return version


@router.get("/versions/{version_id}/download", summary="Descargar una versión corregida")
def download_version(version_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StreamingResponse:
    version = get_version(version_id, current_user, db)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(f'corrected-{version.id}.wav')}"}
    return StreamingResponse(stream_file(version.storage_key), media_type=version.content_type, headers=headers)
