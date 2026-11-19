from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audio import ProcessingStatus


class CorrectionEdit(BaseModel):
    note_id: UUID
    target_midi: float = Field(ge=0, le=127)


class CorrectionRequestCreate(BaseModel):
    analysis_id: UUID
    edits: list[CorrectionEdit] = Field(min_length=1, max_length=64)
    output_format: str = Field(default="wav", pattern="^wav$")


class CorrectionStartResponse(BaseModel):
    correction_request_id: UUID
    job_id: UUID
    status: ProcessingStatus
    status_url: str


class ProcessedVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_audio_file_id: UUID
    correction_request_id: UUID | None
    storage_key: str
    content_type: str
    size_bytes: int | None
    created_at: datetime
