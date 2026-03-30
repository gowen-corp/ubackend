"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create entities table
    op.create_table('entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=dict),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_entities_tenant_id'), 'entities', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_entities_is_active'), 'entities', ['is_active'], unique=False)

    # Create records table
    op.create_table('records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=dict),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_records_entity_id'), 'records', ['entity_id'], unique=False)
    op.create_index(op.f('ix_records_tenant_id'), 'records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_records_deleted_at'), 'records', ['deleted_at'], unique=False)
    # GIN index for JSONB data
    op.create_index('ix_records_data_gin', 'records', ['data'], unique=False, postgresql_using='gin')

    # Create event_outbox table
    op.create_table('event_outbox',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), default='pending'),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_outbox_status'), 'event_outbox', ['status'], unique=False)
    op.create_index(op.f('ix_event_outbox_event_type'), 'event_outbox', ['event_type'], unique=False)
    op.create_index(op.f('ix_event_outbox_next_retry_at'), 'event_outbox', ['next_retry_at'], unique=False)

    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('trigger_event', sa.String(length=255), nullable=False),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=list),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflows_trigger_event'), 'workflows', ['trigger_event'], unique=False)
    op.create_index(op.f('ix_workflows_is_active'), 'workflows', ['is_active'], unique=False)
    op.create_index(op.f('ix_workflows_tenant_id'), 'workflows', ['tenant_id'], unique=False)

    # Create workflow_runs table
    op.create_table('workflow_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('status', sa.String(length=50), default='running'),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=dict),
        sa.Column('current_step', sa.Integer(), default=0),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_runs_workflow_id'), 'workflow_runs', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_workflow_runs_status'), 'workflow_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('workflow_runs')
    op.drop_table('workflows')
    op.drop_table('event_outbox')
    op.drop_table('records')
    op.drop_table('entities')
