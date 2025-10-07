"""Make hashed_password nullable

Revision ID: 933335145f1b
Revises: 
Create Date: 2025-10-06 18:08:42.048812
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '933335145f1b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for SQLite (drop NOT NULL)"""
    # Create a new temp table without NOT NULL constraint
    # conn = op.get_bind()
    # conn.execute(sa.text("DROP TABLE users_tmp;"))
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String),
        sa.Column('hashed_password', sa.String, nullable=True),
        sa.Column('name', sa.String),
        # add any other columns your users table had
    )

  

    op.drop_table('users')
    op.rename_table('users_tmp', 'users')


def downgrade() -> None:
    """Downgrade schema (not implemented)"""
    pass
