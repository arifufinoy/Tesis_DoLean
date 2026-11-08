import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Analysis, AudioFile, NoteSegment, ProcessingJob, ProcessingStatus, Project, User
from app.schemas.audio import AnalysisNotesResponse, AnalysisResponse, AnalysisStartResponse, ProcessingJobResponse
from app.tasks.analysis import analyze_audio_task


router = APIRouter(tags=["analyses"])


def owned_audio(audio_file_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> AudioFile:
    audio_file = db.scalar(
        select(AudioFile)
        .join(Project, Project.id == AudioFile.project_id)
        .where(AudioFile.id == audio_file_id, Project.owner_id == user_id)
    )
    if audio_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo de audio no encontrado")
    return audio_file


def owned_analysis(analysis_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Analysis:
    analysis = db.scalar(
        select(Analysis)
        .join(AudioFile, AudioFile.id == Analysis.audio_file_id)
        .join(Project, Project.id == AudioFile.project_id)
        .where(Analysis.id == analysis_id, Project.owner_id == user_id)
        .options(selectinload(Analysis.notes))
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")
    return analysis


@router.post(
    "/audio-files/{audio_file_id}/analyses",
    response_model=AnalysisStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar análisis de afinación",
)
def create_analysis(
    audio_file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisStartResponse:
    audio_file = owned_audio(audio_file_id, current_user.id, db)
    active_analysis = db.scalar(
        select(Analysis)
        .where(
            Analysis.audio_file_id == audio_file.id,
            Analysis.status.in_([ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]),
        )
        .order_by(Analysis.created_at.desc())
    )
    if active_analysis is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un análisis en ejecución")

    analysis = Analysis(audio_file_id=audio_file.id, status=ProcessingStatus.PENDING)
    db.add(analysis)
    db.flush()
    job = ProcessingJob(analysis_id=analysis.id, job_type="pitch_analysis", status=ProcessingStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(analysis)
    db.refresh(job)
    try:
        task = analyze_audio_task.delay(str(analysis.id), str(job.id))
        job.celery_task_id = task.id
        db.commit()
    except Exception as exc:
        db.rollback()
        analysis = db.get(Analysis, analysis.id)
        job = db.get(ProcessingJob, job.id)
        if analysis is not None:
            analysis.status = ProcessingStatus.FAILED
            analysis.error_message = "No fue posible encolar el análisis."
        if job is not None:
            job.status = ProcessingStatus.FAILED
            job.error_message = "No fue posible encolar el análisis."
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No se pudo iniciar el procesamiento") from exc

    return AnalysisStartResponse(
        analysis_id=analysis.id,
        job_id=job.id,
        status=analysis.status,
        analysis_url=f"/api/v1/analyses/{analysis.id}",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse, summary="Consultar un análisis")
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Analysis:
    return owned_analysis(analysis_id, current_user.id, db)


@router.get("/analyses/{analysis_id}/notes", response_model=AnalysisNotesResponse, summary="Listar notas detectadas")
def list_analysis_notes(
    analysis_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisNotesResponse:
    owned_analysis(analysis_id, current_user.id, db)
    total = db.scalar(select(func.count()).select_from(NoteSegment).where(NoteSegment.analysis_id == analysis_id)) or 0
    notes = list(
        db.scalars(
            select(NoteSegment)
            .where(NoteSegment.analysis_id == analysis_id)
            .order_by(NoteSegment.segment_index)
            .offset(offset)
            .limit(limit)
        )
    )
    return AnalysisNotesResponse(items=notes, analysis_id=analysis_id, total=total, limit=limit, offset=offset)


@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse, summary="Consultar estado de un trabajo")
def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcessingJob:
    job = db.scalar(
        select(ProcessingJob)
        .join(Analysis, Analysis.id == ProcessingJob.analysis_id)
        .join(AudioFile, AudioFile.id == Analysis.audio_file_id)
        .join(Project, Project.id == AudioFile.project_id)
        .where(ProcessingJob.id == job_id, Project.owner_id == current_user.id)
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trabajo no encontrado")
    return job
