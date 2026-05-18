"""empty message

Revision ID: e2d2ed0022c9
Revises: 86fd624a8e22
Create Date: 2026-05-18 15:18:05.692264

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2d2ed0022c9'
down_revision: Union[str, Sequence[str], None] = '86fd624a8e22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Required: ALTER TYPE ADD VALUE cannot run inside a transaction
def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE examstate ADD VALUE IF NOT EXISTS 'sent'")


def downgrade() -> None:
    pass
