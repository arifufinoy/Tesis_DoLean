"""Valida persistencia y ejecución directa del task de análisis sobre infraestructura local."""

import json
import os
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Analysis, AudioFile, ProcessingJob
from app.tasks.analysis import analyze_audio_task


def main() -> None:
    audio_file_id = os.getenv("DOLEAN_AUDIO_FILE_ID")
    if not audio_file_id:
        raise SystemExit("Define DOLEAN_AUDIO_FILE_ID con un audio normalizado existente.")

    db = SessionLocal()
    try:
        audio_file = db.get(AudioFile, uuid.UUID(audio_file_id))
        if audio_file is None:
            raise SystemExit(f"No existe el audio {audio_file_id}")
        analysis = Analysis(audio_file_id=audio_file.id)
        db.add(analysis)
        db.flush()
        job = ProcessingJob(analysis_id=analysis.id, job_type="pitch_analysis")
        db.add(job)
        db.commit()
        analysis_id = analysis.id
        job_id = job.id
    finally:
        db.close()

    analyze_audio_task.run(str(analysis_id), str(job_id))

    db = SessionLocal()
    try:
        analysis = db.scalar(select(Analysis).where(Analysis.id == analysis_id))
        job = db.get(ProcessingJob, job_id)
        if analysis is None or job is None:
            raise SystemExit("No se pudo recuperar el resultado persistido")
        print(
            json.dumps(
                {
                    "analysis_id": str(analysis.id),
                    "job_id": str(job.id),
                    "analysis_status": analysis.status.value,
                    "job_status": job.status.value,
                    "sample_rate": analysis.sample_rate,
                    "duration_seconds": analysis.duration_seconds,
                    "notes_count": len(analysis.notes),
                    "notes": [
                        {
                            "note_name": note.note_name,
                            "frequency_hz": note.frequency_hz,
                            "deviation_cents": note.deviation_cents,
                            "confidence": note.confidence,
                        }
                        for note in analysis.notes
                    ],
                },
                indent=2,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
