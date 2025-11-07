"""
PostgreSQL database connection service.

Provides functionality for connecting to PostgreSQL databases,
executing queries, retrieving schema information, and managing connections.
"""

import asyncio
from typing import Any, Dict, List, Optional
import asyncpg
from asyncpg import Pool, Connection


class PostgresService:
    """
    Service for connecting to and querying PostgreSQL databases.

    Handles connection management, schema inspection, and query execution.
    """

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Initialize PostgreSQL service with connection parameters.

        Args:
            host: PostgreSQL server hostname
            port: PostgreSQL server port
            database: Database name
            user: Database user
            password: Database password (unencrypted for connection)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._pool: Optional[Pool] = None
        self._connection: Optional[Connection] = None

    async def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            Exception: If connection fails
        """
        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=5,
                max_size=20,
                command_timeout=10,
            )
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection test successful

        Raises:
            Exception: If connection test fails
        """
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1

    async def get_database_schema(self) -> Dict[str, Any]:
        """
        Retrieve database schema information (tables and columns).

        Returns:
            dict: Database schema with tables and columns
                {
                    'tables': [
                        {
                            'name': 'users',
                            'schema': 'public',
                            'columns': [
                                {'name': 'id', 'type': 'bigint', 'nullable': False},
                                {'name': 'email', 'type': 'character varying', 'nullable': True}
                            ],
                            'row_count': 1000
                        }
                    ]
                }

        Raises:
            Exception: If schema retrieval fails
        """
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            # Get tables
            tables_query = """
            SELECT
                t.table_schema,
                t.table_name,
                (SELECT count(*) FROM information_schema.columns WHERE table_schema = t.table_schema AND table_name = t.table_name) as column_count,
                (SELECT n_live_tup FROM pg_stat_user_tables WHERE schemaname = t.table_schema AND relname = t.table_name) as row_count
            FROM information_schema.tables t
            WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY t.table_schema, t.table_name;
            """

            tables = await conn.fetch(tables_query)

            result = {"tables": []}

            for table in tables:
                # Get columns for each table
                columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position;
                """

                columns = await conn.fetch(columns_query, table["table_schema"], table["table_name"])

                table_info = {
                    "name": table["table_name"],
                    "schema": table["table_schema"],
                    "columns": [
                        {
                            "name": col["column_name"],
                            "type": col["data_type"],
                            "nullable": col["is_nullable"] == "YES",
                        }
                        for col in columns
                    ],
                    "row_count": table["row_count"] or 0,
                }

                result["tables"].append(table_info)

            return result

    async def query_database(
        self, query: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query on the database.

        Args:
            query: SQL query to execute
            limit: Maximum number of rows to return (default: 100)

        Returns:
            list: Query results as list of dicts

        Raises:
            Exception: If query execution fails
        """
        if not self._pool:
            await self.connect()

        # Add LIMIT clause if not present
        query_upper = query.strip().upper()
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit};"

        async with self._pool.acquire() as conn:
            try:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
            except Exception as e:
                print(f"❌ Query execution failed: {e}")
                raise

    async def get_table_preview(
        self, table_name: str, schema: str = "public", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get preview data from a table.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)
            limit: Number of rows to preview (default: 10)

        Returns:
            list: Preview rows as list of dicts

        Raises:
            Exception: If preview retrieval fails
        """
        query = f'SELECT * FROM "{schema}"."{table_name}" LIMIT {limit};'
        return await self.query_database(query, limit=limit)
