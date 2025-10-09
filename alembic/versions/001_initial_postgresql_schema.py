"""initial postgresql schema

Revision ID: 001_initial_postgresql
Revises:
Create Date: 2025-10-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_postgresql'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tenants',
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('tenant_name', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('tenant_id'),
    sa.UniqueConstraint('tenant_name')
    )

    op.create_table('backendusers',
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('username')
    )

    op.create_table('knowledge_sources',
    sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('source_type', sa.String(), nullable=False),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('source_content', sa.Text(), nullable=True),
    sa.Column('file_name', sa.String(), nullable=True),
    sa.Column('file_content', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('source_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('source_id')
    )

    op.create_index('idx_users_tenant_id', 'backendusers', ['tenant_id'])
    op.create_index('idx_knowledge_sources_tenant_id', 'knowledge_sources', ['tenant_id'])
    op.create_index('idx_knowledge_sources_status', 'knowledge_sources', ['status'])


def downgrade() -> None:
    op.drop_index('idx_knowledge_sources_status', table_name='knowledge_sources')
    op.drop_index('idx_knowledge_sources_tenant_id', table_name='knowledge_sources')
    op.drop_index('idx_users_tenant_id', table_name='backendusers')
    op.drop_table('knowledge_sources')
    op.drop_table('backendusers')
    op.drop_table('tenants')
