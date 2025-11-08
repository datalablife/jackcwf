"""add_file_metadata_table

Revision ID: 002_add_file_metadata
Revises: 001_add_file_uploads
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_file_metadata'
down_revision = '001_add_file_uploads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create file_metadata table."""
    op.create_table(
        'file_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('file_upload_id', sa.Integer(), nullable=False),
        sa.Column('rows_count', sa.Integer(), nullable=True),
        sa.Column('columns_count', sa.Integer(), nullable=True),
        sa.Column('column_names', sa.JSON(), nullable=True),
        sa.Column('data_types', sa.JSON(), nullable=True),
        sa.Column('storage_path', sa.String(length=1024), nullable=True),
        sa.Column('additional_metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['file_upload_id'], ['file_uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_upload_id'),
    )
    op.create_index(op.f('ix_file_metadata_file_upload_id'), 'file_metadata', ['file_upload_id'], unique=True)


def downgrade() -> None:
    """Drop file_metadata table."""
    op.drop_index(op.f('ix_file_metadata_file_upload_id'), table_name='file_metadata')
    op.drop_table('file_metadata')
