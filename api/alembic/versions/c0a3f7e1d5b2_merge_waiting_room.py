"""merge waiting room into exam config

Revision ID: c0a3f7e1d5b2
Revises: 92216ae3b654
Create Date: 2026-05-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'c0a3f7e1d5b2'
down_revision: Union[str, Sequence[str], None] = '92216ae3b654'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create the new enum type for session_state
    session_state_enum = sa.Enum('preparation', 'running', 'closed', name='sessionstate')
    session_state_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add columns to exam_config
    op.add_column('exam_config', sa.Column('session_state', sa.Enum('preparation', 'running', 'closed', name='sessionstate'), nullable=False, server_default='preparation'))
    op.add_column('exam_config', sa.Column('associations', sa.JSON(), nullable=False, server_default='[]'))

    # 3. Migrate data from waiting_room to exam_config
    # Note: we need to handle the enum conversion carefully if types are different
    op.execute("""
        UPDATE exam_config 
        SET session_state = CAST(waiting_room.state AS text)::sessionstate,
            associations = waiting_room.associations
        FROM waiting_room
        WHERE waiting_room.exam_config_id = exam_config.id
    """)

    # 4. Drop waiting_room table
    op.drop_table('waiting_room')
    
    # We leave the old enum 'waitingroomstate' for now to avoid dependency issues if something still refers to it
    # or just drop it if we are sure.
    # op.execute("DROP TYPE waitingroomstate")

def downgrade() -> None:
    # 1. Recreate waitingroomstate enum if needed
    waiting_room_state_enum = sa.Enum('preparation', 'running', 'closed', name='waitingroomstate')
    waiting_room_state_enum.create(op.get_bind(), checkfirst=True)

    # 2. Recreate waiting_room table
    op.create_table('waiting_room',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_config_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.Enum('preparation', 'running', 'closed', name='waitingroomstate'), nullable=False),
        sa.Column('associations', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['exam_config_id'], ['exam_config.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Migrate data back
    op.execute("""
        INSERT INTO waiting_room (exam_config_id, state, associations)
        SELECT id, CAST(session_state AS text)::waitingroomstate, associations
        FROM exam_config
    """)

    # 4. Drop columns from exam_config
    op.drop_column('exam_config', 'associations')
    op.drop_column('exam_config', 'session_state')
    
    # 5. Drop sessionstate enum
    # op.execute("DROP TYPE sessionstate")
