"""Add Memori memory tables for Claude context management.

Revision ID: 002
Revises: 001
Create Date: 2024-11-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Memori memory tables."""

    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False),  # short_term, long_term, rule, entity
        sa.Column('importance', sa.Float(), nullable=False, default=0.5),
        sa.Column('embedding', sa.JSON(), nullable=True),  # Vector embedding for semantic search
        sa.Column('tags', sa.JSON(), nullable=True),  # JSON array of tags
        sa.Column('metadata', sa.JSON(), nullable=True),  # Additional metadata
        sa.Column('tenant_id', sa.String(36), nullable=True),  # Multi-tenant support
        sa.Column('conversation_id', sa.String(36), nullable=True),  # Associate with conversation
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('accessed_at', sa.DateTime(), nullable=True),  # For LRU cache
        sa.Column('expires_at', sa.DateTime(), nullable=True),  # For TTL
    )

    # Create indexes for performance
    op.create_index('idx_memories_type', 'memories', ['memory_type'])
    op.create_index('idx_memories_importance', 'memories', ['importance'])
    op.create_index('idx_memories_tenant_id', 'memories', ['tenant_id'])
    op.create_index('idx_memories_conversation_id', 'memories', ['conversation_id'])
    op.create_index('idx_memories_created_at', 'memories', ['created_at'])
    op.create_index('idx_memories_expires_at', 'memories', ['expires_at'])

    # Create memory relationships table for entity linking
    op.create_table(
        'memory_relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_memory_id', sa.String(36), nullable=False),
        sa.Column('target_memory_id', sa.String(36), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),  # related_to, cause_of, etc.
        sa.Column('strength', sa.Float(), nullable=False, default=1.0),  # Relationship strength
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['source_memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_memory_id'], ['memories.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_memory_relationships_source', 'memory_relationships', ['source_memory_id'])
    op.create_index('idx_memory_relationships_target', 'memory_relationships', ['target_memory_id'])

    # Create conversations table for tracking conversation contexts
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),  # Conversation context
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('idx_conversations_tenant_id', 'conversations', ['tenant_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])

    # Create memory search index table for fast retrieval
    op.create_table(
        'memory_search_index',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('memory_id', sa.String(36), nullable=False),
        sa.Column('search_vector', sa.String(500), nullable=False),  # Tokenized content for FTS
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_memory_search_index_memory_id', 'memory_search_index', ['memory_id'])

    # Create memory statistics table for monitoring
    op.create_table(
        'memory_stats',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=True),
        sa.Column('total_memories', sa.Integer(), nullable=False, default=0),
        sa.Column('short_term_count', sa.Integer(), nullable=False, default=0),
        sa.Column('long_term_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rules_count', sa.Integer(), nullable=False, default=0),
        sa.Column('entities_count', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_importance', sa.Float(), nullable=False, default=0.5),
        sa.Column('database_size_mb', sa.Float(), nullable=False, default=0),
        sa.Column('last_cleanup_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('idx_memory_stats_tenant_id', 'memory_stats', ['tenant_id'])


def downgrade() -> None:
    """Drop Memori memory tables."""

    # Drop tables in reverse order of creation
    op.drop_index('idx_memory_stats_tenant_id')
    op.drop_table('memory_stats')

    op.drop_index('idx_memory_search_index_memory_id')
    op.drop_table('memory_search_index')

    op.drop_index('idx_memory_relationships_target')
    op.drop_index('idx_memory_relationships_source')
    op.drop_table('memory_relationships')

    op.drop_index('idx_conversations_created_at')
    op.drop_index('idx_conversations_tenant_id')
    op.drop_table('conversations')

    op.drop_index('idx_memories_expires_at')
    op.drop_index('idx_memories_created_at')
    op.drop_index('idx_memories_conversation_id')
    op.drop_index('idx_memories_tenant_id')
    op.drop_index('idx_memories_importance')
    op.drop_index('idx_memories_type')
    op.drop_table('memories')
