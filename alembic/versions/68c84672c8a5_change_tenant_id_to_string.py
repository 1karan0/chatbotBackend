"""change tenant_id to string

Revision ID: 68c84672c8a5
Revises: 001_initial_postgresql
Create Date: 2025-10-09 16:56:49.311154
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '68c84672c8a5'
down_revision: Union[str, Sequence[str], None] = '001_initial_postgresql'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # STEP 1: Drop all foreign keys first
    op.drop_constraint('backendusers_tenant_id_fkey', 'backendusers', type_='foreignkey')
    op.drop_constraint('knowledge_sources_tenant_id_fkey', 'knowledge_sources', type_='foreignkey')

    # STEP 2: Convert all tenant_id columns from UUID to VARCHAR
    # Convert tenants table
    op.alter_column(
        'tenants',
        'tenant_id',
        existing_type=postgresql.UUID(),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using='tenant_id::text'
    )

    # Convert backendusers table
    op.alter_column(
        'backendusers',
        'tenant_id',
        existing_type=postgresql.UUID(),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using='tenant_id::text'
    )

    # Convert knowledge_sources table
    op.alter_column(
        'knowledge_sources',
        'tenant_id',
        existing_type=postgresql.UUID(),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using='tenant_id::text'
    )

    # STEP 3: Recreate all foreign keys
    op.create_foreign_key(
        'backendusers_tenant_id_fkey',
        'backendusers', 'tenants',
        ['tenant_id'], ['tenant_id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'knowledge_sources_tenant_id_fkey',
        'knowledge_sources', 'tenants',
        ['tenant_id'], ['tenant_id'],
        ondelete='CASCADE'
    )


def downgrade():
    # ### tenants table ###
    op.alter_column(
        'tenants',
        'tenant_id',
        existing_type=sa.String(),
        type_=postgresql.UUID(),
        existing_nullable=False
    )

    # ### backendusers table ###
    op.drop_constraint('backendusers_tenant_id_fkey', 'backendusers', type_='foreignkey')
    op.alter_column(
        'backendusers',
        'tenant_id',
        existing_type=sa.String(),
        type_=postgresql.UUID(),
        existing_nullable=False
    )
    op.create_foreign_key(
        'backendusers_tenant_id_fkey',
        'backendusers', 'tenants',
        ['tenant_id'], ['tenant_id'],
        ondelete='CASCADE'
    )

    # ### knowledge_sources table ###
    op.drop_constraint('knowledge_sources_tenant_id_fkey', 'knowledge_sources', type_='foreignkey')
    op.alter_column(
        'knowledge_sources',
        'tenant_id',
        existing_type=sa.String(),
        type_=postgresql.UUID(),
        existing_nullable=False
    )
    op.create_foreign_key(
        'knowledge_sources_tenant_id_fkey',
        'knowledge_sources', 'tenants',
        ['tenant_id'], ['tenant_id'],
        ondelete='CASCADE'
    )
