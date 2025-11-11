"""add_data_sources_table

Revision ID: 000_add_data_sources
Revises:
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_add_data_sources'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create data_sources table."""
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='postgresql'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='disconnected'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_data_sources_name'), 'data_sources', ['name'], unique=False)
    op.create_index(op.f('ix_data_sources_type'), 'data_sources', ['type'], unique=False)
    op.create_index(op.f('ix_data_sources_status'), 'data_sources', ['status'], unique=False)


def downgrade() -> None:
    """Drop data_sources table."""
    op.drop_index(op.f('ix_data_sources_status'), table_name='data_sources')
    op.drop_index(op.f('ix_data_sources_type'), table_name='data_sources')
    op.drop_index(op.f('ix_data_sources_name'), table_name='data_sources')
    op.drop_table('data_sources')
