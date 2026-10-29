import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=enum_values), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    recovery_tokens: Mapped[list["RecoveryToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    user: Mapped[User] = relationship(back_populates="profile")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_owner_id", "owner_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[User] = relationship(back_populates="projects")
    audio_files: Mapped[list["AudioFile"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class AudioFile(TimestampMixin, Base):
    __tablename__ = "audio_files"
    __table_args__ = (Index("ix_audio_files_project_id", "project_id"), UniqueConstraint("storage_key"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    sample_rate: Mapped[int | None] = mapped_column(Integer)
    channels: Mapped[int | None] = mapped_column(Integer)
    project: Mapped[Project] = relationship(back_populates="audio_files")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="audio_file", cascade="all, delete-orphan")
    versions: Mapped[list["ProcessedVersion"]] = relationship(back_populates="source_audio_file", cascade="all, delete-orphan")


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"
    __table_args__ = (Index("ix_analyses_audio_file_id", "audio_file_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus, name="processing_status", values_callable=enum_values), default=ProcessingStatus.PENDING, nullable=False)
    sample_rate: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    audio_file: Mapped[AudioFile] = relationship(back_populates="analyses")
    notes: Mapped[list["NoteSegment"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    correction_requests: Mapped[list["CorrectionRequest"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class NoteSegment(Base):
    __tablename__ = "note_segments"
    __table_args__ = (UniqueConstraint("analysis_id", "segment_index"), Index("ix_note_segments_analysis_id", "analysis_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    detected_midi: Mapped[float | None] = mapped_column(Float)
    note_name: Mapped[str | None] = mapped_column(String(8))
    frequency_hz: Mapped[float | None] = mapped_column(Float)
    deviation_cents: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    analysis: Mapped[Analysis] = relationship(back_populates="notes")


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (Index("ix_processing_jobs_status", "status"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus, name="processing_status", values_callable=enum_values), default=ProcessingStatus.PENDING, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)


class CorrectionRequest(TimestampMixin, Base):
    __tablename__ = "correction_requests"
    __table_args__ = (Index("ix_correction_requests_analysis_id", "analysis_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus, name="processing_status", values_callable=enum_values), default=ProcessingStatus.PENDING, nullable=False)
    analysis: Mapped[Analysis] = relationship(back_populates="correction_requests")
    version: Mapped["ProcessedVersion | None"] = relationship(back_populates="correction_request", uselist=False)


class ProcessedVersion(Base):
    __tablename__ = "processed_versions"
    __table_args__ = (Index("ix_processed_versions_source_audio_file_id", "source_audio_file_id"), UniqueConstraint("storage_key"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_audio_file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    correction_request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("correction_requests.id", ondelete="SET NULL"))
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    source_audio_file: Mapped[AudioFile] = relationship(back_populates="versions")
    correction_request: Mapped[CorrectionRequest | None] = relationship(back_populates="version")


class RecoveryToken(Base):
    __tablename__ = "recovery_tokens"
    __table_args__ = (Index("ix_recovery_tokens_user_id", "user_id"), UniqueConstraint("token_hash"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="recovery_tokens")


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (Index("ix_refresh_sessions_user_id", "user_id"), UniqueConstraint("token_hash"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="refresh_sessions")

