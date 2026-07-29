"""Baseline: create institutions table

Revision ID: 0f4c1a7b9e23
Revises:
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f4c1a7b9e23'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'institutions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('bank_id', sa.Integer(), nullable=False),
        sa.Column('email_to', sa.String(length=255), nullable=False),
        sa.Column('email_cc', sa.String(length=255), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('1'),
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        op.f('ix_institutions_id'), 'institutions', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_institutions_bank_id'),
        'institutions',
        ['bank_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_institutions_bank_id'), table_name='institutions')
    op.drop_index(op.f('ix_institutions_id'), table_name='institutions')
    op.drop_table('institutions')
