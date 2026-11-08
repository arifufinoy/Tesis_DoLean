"""Celery task for persisted pitch analysis."""

import logging
import tempfile
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.dsp.pitch import analyze_pitch
from app.models import Analysis, NoteSegment, ProcessingJob, ProcessingStatus
from app.storage.minio_storage import StorageError, download_file
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="dolean.analysis.pitch")
def analyze_audio_task(self, analysis_id: str, job_id: str) -> None:
    del self
    db = SessionLocal()
    analysis_uuid = uuid.UUID(analysis_id)
    job_uuid = uuid.UUID(job_id)
    try:
        analysis = db.get(Analysis, analysis_uuid)
        job = db.get(ProcessingJob, job_uuid)
        if analysis is None or job is None or job.analysis_id != analysis.id:
            raise ValueError("El trabajo de análisis no existe")
        job.status = ProcessingStatus.PROCESSING
        analysis.status = ProcessingStatus.PROCESSING
        db.commit()

        if not analysis.audio_file or not analysis.audio_file.normalized_storage_key:
            raise ValueError("El archivo no tiene una representación normalizada")

        with tempfile.TemporaryDirectory(prefix="dolean-analysis-") as directory:
            source = Path(directory) / "normalized.wav"
            download_file(analysis.audio_file.normalized_storage_key, source)
            result = analyze_pitch(source)

        analysis.sample_rate = result.sample_rate
        analysis.duration_seconds = result.duration_seconds
        analysis.error_message = None
        analysis.status = ProcessingStatus.COMPLETED
        for note in result.notes:
            db.add(
                NoteSegment(
                    analysis_id=analysis.id,
                    segment_index=note.segment_index,
                    start_time=note.start_time,
                    end_time=note.end_time,
                    detected_midi=note.detected_midi,
                    note_name=note.note_name,
                    frequency_hz=note.frequency_hz,
                    deviation_cents=note.deviation_cents,
                    confidence=note.confidence,
                )
            )
        job.status = ProcessingStatus.COMPLETED
        job.error_message = None
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Audio analysis failed", extra={"analysis_id": analysis_id, "job_id": job_id})
        analysis = db.get(Analysis, analysis_uuid)
        job = db.get(ProcessingJob, job_uuid)
        if analysis is not None:
            analysis.status = ProcessingStatus.FAILED
            analysis.error_message = "No fue posible completar el análisis de audio."
        if job is not None:
            job.status = ProcessingStatus.FAILED
            job.error_message = "No fue posible completar el análisis de audio."
        db.commit()
    finally:
        db.close()
