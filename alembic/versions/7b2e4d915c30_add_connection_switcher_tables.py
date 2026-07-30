"""Add institution connection switcher tables

Revision ID: 7b2e4d915c30
Revises: 0f4c1a7b9e23
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2e4d915c30'
down_revision: Union[str, Sequence[str], None] = '0f4c1a7b9e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'connection_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('institution_name', sa.String(length=100), nullable=False),
        sa.Column('interchange_id', sa.Integer(), nullable=False),
        sa.Column('interchange_type', sa.String(length=60), nullable=False),
        sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')
        ),
        sa.Column('institution_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'interchange_id', name='uq_connection_configs_interchange_id'
        ),
    )
    op.create_index(
        op.f('ix_connection_configs_id'), 'connection_configs', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_connection_configs_interchange_id'),
        'connection_configs',
        ['interchange_id'],
        unique=False,
    )

    op.create_table(
        'connection_routes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        # VPN_GCP | VPN_AWS | LEASED_LINE | OTHER
        sa.Column('medium', sa.String(length=30), nullable=False),
        sa.Column('medium_note', sa.String(length=255), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ['config_id'], ['connection_configs.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'config_id', 'name', name='uq_connection_routes_config_name'
        ),
    )
    op.create_index(
        op.f('ix_connection_routes_id'), 'connection_routes', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_connection_routes_config_id'),
        'connection_routes',
        ['config_id'],
        unique=False,
    )

    op.create_table(
        'connection_route_endpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('host', sa.String(length=64), nullable=True),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column(
            'sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')
        ),
        sa.ForeignKeyConstraint(
            ['route_id'], ['connection_routes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_connection_route_endpoints_id'),
        'connection_route_endpoints',
        ['id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_connection_route_endpoints_route_id'),
        'connection_route_endpoints',
        ['route_id'],
        unique=False,
    )

    op.create_table(
        'connection_switch_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=True),
        sa.Column('interchange_id', sa.Integer(), nullable=False),
        sa.Column('institution_name', sa.String(length=100), nullable=False),
        sa.Column('from_route', sa.String(length=20), nullable=True),
        sa.Column('to_route', sa.String(length=20), nullable=False),
        sa.Column('from_medium', sa.String(length=30), nullable=True),
        sa.Column('to_medium', sa.String(length=30), nullable=True),
        sa.Column('from_value', sa.String(length=255), nullable=True),
        sa.Column('to_value', sa.String(length=255), nullable=True),
        sa.Column('outcome', sa.String(length=20), nullable=False),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(['config_id'], ['connection_configs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_connection_switch_logs_id'),
        'connection_switch_logs',
        ['id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_connection_switch_logs_id'), table_name='connection_switch_logs'
    )
    op.drop_table('connection_switch_logs')

    op.drop_index(
        op.f('ix_connection_route_endpoints_route_id'),
        table_name='connection_route_endpoints',
    )
    op.drop_index(
        op.f('ix_connection_route_endpoints_id'),
        table_name='connection_route_endpoints',
    )
    op.drop_table('connection_route_endpoints')

    op.drop_index(
        op.f('ix_connection_routes_config_id'), table_name='connection_routes'
    )
    op.drop_index(op.f('ix_connection_routes_id'), table_name='connection_routes')
    op.drop_table('connection_routes')

    op.drop_index(
        op.f('ix_connection_configs_interchange_id'), table_name='connection_configs'
    )
    op.drop_index(op.f('ix_connection_configs_id'), table_name='connection_configs')
    op.drop_table('connection_configs')
