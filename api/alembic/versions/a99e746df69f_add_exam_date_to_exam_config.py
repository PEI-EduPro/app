"""add exam_date to exam_config

Revision ID: a99e746df69f
Revises: 3e1a2b3c4d5e
Create Date: 2026-05-18 00:29:50.956942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a99e746df69f'
down_revision: Union[str, Sequence[str], None] = '3e1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('exam_config', sa.Column('exam_date', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('exam_config', 'exam_date')
