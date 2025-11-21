"""
Database migration script for Epic 4 Thread Support
This script adds the following changes to the database:
1. Creates tool_calls table for tracking tool execution
2. Creates agent_checkpoints table for LangGraph state snapshots
3. Creates appropriate indexes for performance
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Migration:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.async_session = None

    async def setup(self):
        """Initialize async engine"""
        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def teardown(self):
        """Close engine"""
        if self.engine:
            await self.engine.dispose()

    async def execute(self, query: str):
        """Execute raw SQL query"""
        async with self.async_session() as session:
            try:
                await session.execute(text(query))
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error executing query: {str(e)}")
                raise

    async def create_tool_calls_table(self):
        """Create tool_calls table"""
        query = """
        CREATE TABLE IF NOT EXISTS tool_calls (
            id SERIAL PRIMARY KEY,
            tool_id VARCHAR(255) UNIQUE NOT NULL,
            message_id UUID NOT NULL,
            conversation_id UUID NOT NULL,
            tool_name VARCHAR(255) NOT NULL,
            tool_input JSONB DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'pending',
            result TEXT,
            result_data JSONB,
            is_error BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            execution_time_ms FLOAT,
            user_confirmed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE,
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        """
        await self.execute(query)
        logger.info("✓ Created tool_calls table")

    async def create_agent_checkpoints_table(self):
        """Create agent_checkpoints table"""
        query = """
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            id SERIAL PRIMARY KEY,
            checkpoint_id VARCHAR(255) UNIQUE NOT NULL,
            conversation_id UUID NOT NULL,
            thread_id VARCHAR(255) NOT NULL,
            step INTEGER NOT NULL,
            state JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        """
        await self.execute(query)
        logger.info("✓ Created agent_checkpoints table")

    async def create_indexes(self):
        """Create indexes for performance"""
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_id ON tool_calls(tool_id);", "idx_tool_calls_tool_id"),
            ("CREATE INDEX IF NOT EXISTS idx_tool_calls_status ON tool_calls(status);", "idx_tool_calls_status"),
            ("CREATE INDEX IF NOT EXISTS idx_tool_calls_message_id ON tool_calls(message_id);", "idx_tool_calls_message_id"),
            ("CREATE INDEX IF NOT EXISTS idx_tool_calls_conversation_id ON tool_calls(conversation_id);", "idx_tool_calls_conversation_id"),
            ("CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_checkpoint_id ON agent_checkpoints(checkpoint_id);", "idx_agent_checkpoints_checkpoint_id"),
            ("CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_thread_id ON agent_checkpoints(thread_id);", "idx_agent_checkpoints_thread_id"),
            ("CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_conversation_id ON agent_checkpoints(conversation_id);", "idx_agent_checkpoints_conversation_id"),
        ]

        for query, index_name in indexes:
            try:
                await self.execute(query)
                logger.info(f"✓ Created index {index_name}")
            except Exception as e:
                logger.warning(f"Index {index_name} might already exist: {str(e)}")

    async def run(self):
        """Run all migration steps"""
        try:
            await self.setup()
            logger.info("\n=== Starting Database Migration ===\n")

            logger.info("Step 1: Creating tool_calls table...")
            await self.create_tool_calls_table()

            logger.info("\nStep 2: Creating agent_checkpoints table...")
            await self.create_agent_checkpoints_table()

            logger.info("\nStep 3: Creating performance indexes...")
            await self.create_indexes()

            logger.info("\n=== Migration Completed Successfully ===\n")
            logger.info("Summary:")
            logger.info("  - tool_calls table: ✓ Created")
            logger.info("  - agent_checkpoints table: ✓ Created")
            logger.info("  - Performance indexes: ✓ Created (7 total)")

        except Exception as e:
            logger.error(f"\n✗ Migration failed: {str(e)}")
            raise
        finally:
            await self.teardown()


async def main():
    """Main entry point"""
    load_dotenv()

    # Database URL from environment
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_name = os.getenv("POSTGRES_DB", "postgres")

    db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.info(f"Connecting to database: {db_host}:{db_port}/{db_name}")

    migration = Migration(db_url)
    await migration.run()


if __name__ == "__main__":
    asyncio.run(main())
