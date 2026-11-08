"""Associate processing jobs with their analysis for ownership checks."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_processing_job_analysis"
down_revision: Union[str, None] = "0003_audio_normalized_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_jobs",
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_processing_jobs_analysis_id", "processing_jobs", ["analysis_id"])
    op.create_foreign_key(
        "fk_processing_jobs_analysis_id",
        "processing_jobs",
        "analyses",
        ["analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_processing_jobs_analysis_id", "processing_jobs", type_="foreignkey")
    op.drop_index("ix_processing_jobs_analysis_id", table_name="processing_jobs")
    op.drop_column("processing_jobs", "analysis_id")
