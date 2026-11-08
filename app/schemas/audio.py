from datetime import datetime
from uuid import UUID

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AudioFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    normalized_sample_rate: int | None
    normalized_channels: int | None
    created_at: datetime
    updated_at: datetime


class AudioFileListResponse(BaseModel):
    items: list[AudioFileResponse]
    total: int
    limit: int
    offset: int


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NoteSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    segment_index: int
    start_time: float
    end_time: float
    detected_midi: float | None
    note_name: str | None
    frequency_hz: float | None
    deviation_cents: float | None
    confidence: float | None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_file_id: UUID
    status: ProcessingStatus
    sample_rate: int | None
    duration_seconds: float | None
    error_message: str | None
    notes: list[NoteSegmentResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AnalysisStartResponse(BaseModel):
    analysis_id: UUID
    job_id: UUID
    status: ProcessingStatus
    analysis_url: str
    status_url: str


class AnalysisNotesResponse(BaseModel):
    analysis_id: UUID
    items: list[NoteSegmentResponse]
    total: int
    limit: int
    offset: int


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID | None
    job_type: str
    status: ProcessingStatus
    celery_task_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
