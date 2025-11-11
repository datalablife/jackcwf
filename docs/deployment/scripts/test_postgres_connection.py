#!/usr/bin/env python3
"""
Test script for PostgreSQL connection verification
Part of Phase 1 Setup - Task T010
Tests connection to Coolify PostgreSQL (Lantern Suite)
"""

import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

load_dotenv()


async def test_connection():
    """Test connection to Coolify PostgreSQL database"""
    try:
        import asyncpg
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ ERROR: DATABASE_URL not found in .env")
            return False

        # Extract readable connection info
        postgres_host = os.getenv("POSTGRES_HOST")
        postgres_port = os.getenv("POSTGRES_PORT")
        postgres_user = os.getenv("POSTGRES_USER")

        print(f"Testing connection to Coolify PostgreSQL:")
        print(f"  Host: {postgres_host}")
        print(f"  Port: {postgres_port}")
        print(f"  User: {postgres_user}")
        print("⏳ Connecting...")

        # Create async engine
        engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            connect_args={
                "timeout": 10,
                "command_timeout": 10,
            }
        )

        # Test connection
        async with engine.begin() as connection:
            # Test basic connectivity
            result = await connection.execute(text("SELECT version();"))
            version = result.scalar()

            # Test if pgvector is available (Lantern Suite feature)
            try:
                pgvector_result = await connection.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector';"))
                pgvector_version = pgvector_result.scalar()
                print(f"✅ Connection successful!")
                print(f"📊 PostgreSQL version: {version}")
                print(f"🧬 pgvector extension: {pgvector_version} (Lantern Suite feature available)")
            except Exception:
                print(f"✅ Connection successful!")
                print(f"📊 PostgreSQL version: {version}")
                print(f"⚠️  pgvector extension: Not installed (optional)")

        await engine.dispose()
        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install with: cd backend && poetry install")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        if "password authentication failed" in str(e).lower():
            print("   💡 Tip: Check your password in .env (DATABASE_URL)")
            print("           Verify with: echo $DATABASE_URL")
        elif "timeout" in str(e).lower() or "refused" in str(e).lower():
            print("   💡 Tip: Make sure Coolify PostgreSQL is running")
            print("           Check with: coolify app get ok0s0cgw8ck0w8kgs8kk4kk8")
        elif "host.docker.internal" in str(e):
            print("   💡 Tip: host.docker.internal might not be available")
            print("           Try connecting directly to PostgreSQL port 5432")
        return False


if __name__ == "__main__":
    import asyncio

    print("=" * 70)
    print("PostgreSQL Connection Test - Coolify Lantern Suite")
    print("=" * 70)

    success = asyncio.run(test_connection())

    print("=" * 70)
    if success:
        print("✅ Phase 1 Task T010 PASSED: Coolify PostgreSQL connection verified")
        print("\n📌 Connection Info:")
        print(f"   Database: {os.getenv('POSTGRES_DB')}")
        print(f"   User: {os.getenv('POSTGRES_USER')}")
        print(f"   Host: {os.getenv('POSTGRES_HOST')}")
        print(f"   Port: {os.getenv('POSTGRES_PORT')}")
        print(f"   UUID: {os.getenv('COOLIFY_APP_UUID')}")
        sys.exit(0)
    else:
        print("❌ Phase 1 Task T010 FAILED: PostgreSQL connection could not be verified")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Verify Coolify PostgreSQL app is running:")
        print("      coolify app get ok0s0cgw8ck0w8kgs8kk4kk8")
        print("   2. Check your .env file has correct DATABASE_URL")
        print("   3. Verify network connectivity to host.docker.internal:5432")
        print("   4. Check PostgreSQL logs in Coolify dashboard")
        sys.exit(1)

