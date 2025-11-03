#!/usr/bin/env python3
"""
PostgreSQL 连接测试脚本
用于验证 Coolify 部署的 PostgreSQL 实例连接

使用方法:
    python test_postgres_connection.py
"""

import psycopg2
from psycopg2 import sql
import sys

# 连接参数 - 从 Coolify 获取
DB_CONFIG = {
    "host": "host.docker.internal",
    "port": 5432,
    "database": "postgres",
    "user": "jackcwf888",
    "password": "Jack_00492300",
}


def test_connection():
    """测试 PostgreSQL 连接"""
    print("=" * 60)
    print("PostgreSQL 连接测试")
    print("=" * 60)
    print()

    print("连接参数:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print()

    try:
        print("正在连接到 PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ 连接成功！")
        print()

        # 获取服务器信息
        with conn.cursor() as cur:
            # PostgreSQL 版本
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"PostgreSQL 版本:\n  {version}")
            print()

            # 当前用户
            cur.execute("SELECT current_user;")
            current_user = cur.fetchone()[0]
            print(f"当前用户: {current_user}")
            print()

            # 数据库列表
            cur.execute("""
                SELECT datname, pg_size_pretty(pg_database.dblength(datname)) as size
                FROM pg_database
                ORDER BY dblength(datname) DESC;
            """)
            databases = cur.fetchall()
            print("数据库列表:")
            for db_name, db_size in databases:
                print(f"  {db_name}: {db_size}")
            print()

            # 检查 pgvector 扩展（Lantern 特有）
            cur.execute("""
                SELECT * FROM pg_extension WHERE extname IN ('vector', 'lantern');
            """)
            extensions = cur.fetchall()
            print("已安装扩展:")
            if extensions:
                for ext in extensions:
                    print(f"  ✓ {ext[1]}")
            else:
                print("  (未找到 vector/lantern 扩展)")
            print()

            # 活跃连接数
            cur.execute("""
                SELECT count(*) FROM pg_stat_activity;
            """)
            conn_count = cur.fetchone()[0]
            print(f"活跃数据库连接数: {conn_count}")
            print()

        conn.close()
        print("=" * 60)
        print("✓ 所有测试通过！PostgreSQL 连接正常")
        print("=" * 60)
        return True

    except psycopg2.OperationalError as e:
        print(f"✗ 连接失败: {e}")
        print()
        print("可能的解决方案:")
        print("  1. 检查主机地址是否正确")
        print("  2. 检查端口是否可访问")
        print("  3. 检查用户名和密码是否正确")
        print("  4. 检查防火墙规则")
        print("  5. 检查 PostgreSQL 服务是否运行")
        return False

    except psycopg2.DatabaseError as e:
        print(f"✗ 数据库错误: {e}")
        return False

    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
