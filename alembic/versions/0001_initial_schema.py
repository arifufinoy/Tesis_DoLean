"""Create the initial DoLean data model."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("user", "admin", name="user_role", create_type=False)
processing_status = postgresql.ENUM("pending", "processing", "completed", "failed", name="processing_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    processing_status.create(bind, checkfirst=True)
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(255)), sa.Column("role", user_role, nullable=False, server_default="user"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("profiles", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("display_name", sa.String(120)), sa.Column("bio", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id", name="uq_profiles_user_id"))
    op.create_table("projects", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_table("audio_files", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("storage_key", sa.String(512), nullable=False), sa.Column("size_bytes", sa.BigInteger(), nullable=False), sa.Column("duration_seconds", sa.Float()), sa.Column("sample_rate", sa.Integer()), sa.Column("channels", sa.Integer()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"), sa.UniqueConstraint("storage_key", name="uq_audio_files_storage_key"))
    op.create_index("ix_audio_files_project_id", "audio_files", ["project_id"])
    op.create_table("analyses", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("audio_file_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("status", processing_status, nullable=False, server_default="pending"), sa.Column("sample_rate", sa.Integer()), sa.Column("duration_seconds", sa.Float()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["audio_file_id"], ["audio_files.id"], ondelete="CASCADE"))
    op.create_index("ix_analyses_audio_file_id", "analyses", ["audio_file_id"])
    op.create_table("note_segments", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("segment_index", sa.Integer(), nullable=False), sa.Column("start_time", sa.Float(), nullable=False), sa.Column("end_time", sa.Float(), nullable=False), sa.Column("detected_midi", sa.Float()), sa.Column("note_name", sa.String(8)), sa.Column("frequency_hz", sa.Float()), sa.Column("deviation_cents", sa.Float()), sa.Column("confidence", sa.Float()), sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"), sa.UniqueConstraint("analysis_id", "segment_index", name="uq_note_segments_analysis_index"))
    op.create_index("ix_note_segments_analysis_id", "note_segments", ["analysis_id"])
    op.create_table("processing_jobs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("job_type", sa.String(50), nullable=False), sa.Column("status", processing_status, nullable=False, server_default="pending"), sa.Column("celery_task_id", sa.String(255)), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_table("correction_requests", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("parameters", postgresql.JSONB(), nullable=False), sa.Column("status", processing_status, nullable=False, server_default="pending"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"))
    op.create_index("ix_correction_requests_analysis_id", "correction_requests", ["analysis_id"])
    op.create_table("processed_versions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("source_audio_file_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("correction_request_id", postgresql.UUID(as_uuid=True)), sa.Column("storage_key", sa.String(512), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("size_bytes", sa.BigInteger()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["source_audio_file_id"], ["audio_files.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["correction_request_id"], ["correction_requests.id"], ondelete="SET NULL"), sa.UniqueConstraint("storage_key", name="uq_processed_versions_storage_key"))
    op.create_index("ix_processed_versions_source_audio_file_id", "processed_versions", ["source_audio_file_id"])
    op.create_table("recovery_tokens", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("token_hash", sa.String(255), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("used_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("token_hash", name="uq_recovery_tokens_token_hash"))
    op.create_index("ix_recovery_tokens_user_id", "recovery_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("recovery_tokens")
    op.drop_table("processed_versions")
    op.drop_table("correction_requests")
    op.drop_table("processing_jobs")
    op.drop_table("note_segments")
    op.drop_table("analyses")
    op.drop_table("audio_files")
    op.drop_table("projects")
    op.drop_table("profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    processing_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)

