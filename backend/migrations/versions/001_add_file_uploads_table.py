"""add_file_uploads_table

Revision ID: 001_add_file_uploads
Revises:
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_file_uploads'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create file_uploads table."""
    op.create_table(
        'file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('data_source_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=1024), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_format', sa.String(length=20), nullable=False),
        sa.Column('file_size', sa.Float(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('parse_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('parse_error', sa.Text(), nullable=True),
        sa.Column('parse_warnings', sa.Text(), nullable=True),
        sa.Column('is_indexed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path'),
    )
    op.create_index(op.f('ix_file_uploads_data_source_id'), 'file_uploads', ['data_source_id'], unique=False)


def downgrade() -> None:
    """Drop file_uploads table."""
    op.drop_index(op.f('ix_file_uploads_data_source_id'), table_name='file_uploads')
    op.drop_table('file_uploads')
