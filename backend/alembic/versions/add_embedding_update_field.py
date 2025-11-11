"""Add last_embedding_update field to users table

Revision ID: 001_add_embedding_update
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_embedding_update'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add last_embedding_update column to users table."""
    # Check if column already exists before adding
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'last_embedding_update' not in columns:
        op.add_column('users', 
            sa.Column('last_embedding_update', 
                     sa.DateTime(timezone=True), 
                     nullable=True)
        )
        print("✅ Added last_embedding_update column to users table")
    else:
        print("ℹ️  Column last_embedding_update already exists")


def downgrade() -> None:
    """Remove last_embedding_update column from users table."""
    op.drop_column('users', 'last_embedding_update')