"""rename session_state to state and update enum

Revision ID: 3e1a2b3c4d5e
Revises: c0a3f7e1d5b2
Create Date: 2026-05-17 17:37:40.897444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3e1a2b3c4d5e'
down_revision: Union[str, Sequence[str], None] = 'c0a3f7e1d5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the new enum type for ExamState
    exam_state_enum = sa.Enum('preparing', 'running', 'closed_and_capture', 'warning_handling', 'validation', 'completed', name='examstate')
    exam_state_enum.create(op.get_bind(), checkfirst=True)

    # 2. Rename the column session_state to state
    op.alter_column('exam_config', 'session_state', new_column_name='state')

    # 3. Drop old default, migrate type, set new default
    op.execute("ALTER TABLE exam_config ALTER COLUMN state DROP DEFAULT")
    op.execute("""
        ALTER TABLE exam_config 
        ALTER COLUMN state TYPE examstate 
        USING (
            CASE 
                WHEN state::text = 'preparation' THEN 'preparing'::examstate
                WHEN state::text = 'running' THEN 'running'::examstate
                WHEN state::text = 'closed' THEN 'closed_and_capture'::examstate
                ELSE 'preparing'::examstate
            END
        )
    """)
    op.execute("ALTER TABLE exam_config ALTER COLUMN state SET DEFAULT 'preparing'::examstate")


def downgrade() -> None:
    # 1. Recreate the old enum type if it was dropped
    session_state_enum = sa.Enum('preparation', 'running', 'closed', name='sessionstate')
    session_state_enum.create(op.get_bind(), checkfirst=True)

    # 2. Rename the column state back to session_state
    op.alter_column('exam_config', 'state', new_column_name='session_state')

    # 3. Migrate data back and change type
    op.execute("""
        ALTER TABLE exam_config 
        ALTER COLUMN session_state TYPE sessionstate 
        USING (
            CASE 
                WHEN session_state::text = 'preparing' THEN 'preparation'::sessionstate
                WHEN session_state::text = 'running' THEN 'running'::sessionstate
                WHEN session_state::text = 'closed_and_capture' THEN 'closed'::sessionstate
                ELSE 'preparation'::sessionstate
            END
        )
    """)
    
    # 4. Set the old default
    op.execute("ALTER TABLE exam_config ALTER COLUMN session_state SET DEFAULT 'preparation'")
    
    # 5. Drop the new enum type
    op.execute("DROP TYPE examstate")
