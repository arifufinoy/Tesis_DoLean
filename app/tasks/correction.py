import logging
import tempfile
import uuid
from pathlib import Path

from app.db.session import SessionLocal
from app.models import CorrectionRequest, ProcessedVersion, ProcessingJob, ProcessingStatus
from app.services.correction import correct_segments
from app.storage.minio_storage import download_file, put_file
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="dolean.correction.pitch")
def correct_audio_task(self, correction_id: str, job_id: str) -> None:
    del self
    db = SessionLocal()
    correction_uuid = uuid.UUID(correction_id)
    job_uuid = uuid.UUID(job_id)
    try:
        correction = db.get(CorrectionRequest, correction_uuid)
        job = db.get(ProcessingJob, job_uuid)
        if correction is None or job is None:
            raise ValueError("La solicitud de corrección no existe")
        job.status = ProcessingStatus.PROCESSING
        correction.status = ProcessingStatus.PROCESSING
        db.commit()
        source_audio = correction.analysis.audio_file
        if source_audio is None or not source_audio.normalized_storage_key:
            raise ValueError("El archivo no tiene una representación normalizada")
        with tempfile.TemporaryDirectory(prefix="dolean-correction-") as directory:
            source = Path(directory) / "source.wav"
            output = Path(directory) / "corrected.wav"
            download_file(source_audio.normalized_storage_key, source)
            correct_segments(source, output, correction.parameters["edits"])
            storage_key = f"projects/{source_audio.project_id}/versions/{uuid.uuid4()}.wav"
            put_file(output, storage_key, "audio/wav")
            version = ProcessedVersion(
                source_audio_file_id=source_audio.id,
                correction_request_id=correction.id,
                storage_key=storage_key,
                content_type="audio/wav",
                size_bytes=output.stat().st_size,
            )
            db.add(version)
        correction.status = ProcessingStatus.COMPLETED
        job.status = ProcessingStatus.COMPLETED
        job.error_message = None
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Audio correction failed", extra={"correction_id": correction_id, "job_id": job_id})
        correction = db.get(CorrectionRequest, correction_uuid)
        job = db.get(ProcessingJob, job_uuid)
        if correction is not None:
            correction.status = ProcessingStatus.FAILED
        if job is not None:
            job.status = ProcessingStatus.FAILED
            job.error_message = "No fue posible completar la corrección de audio."
        db.commit()
    finally:
        db.close()
