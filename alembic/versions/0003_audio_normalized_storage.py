"""Store the normalized audio object separately from the original upload."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_audio_normalized_storage"
down_revision: Union[str, None] = "0002_authentication_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audio_files", sa.Column("normalized_storage_key", sa.String(length=512), nullable=True))
    op.add_column("audio_files", sa.Column("normalized_sample_rate", sa.Integer(), nullable=True))
    op.add_column("audio_files", sa.Column("normalized_channels", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("audio_files", "normalized_channels")
    op.drop_column("audio_files", "normalized_sample_rate")
    op.drop_column("audio_files", "normalized_storage_key")
