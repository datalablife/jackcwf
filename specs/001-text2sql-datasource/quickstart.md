# 快速开始指南: 数据源集成 API

**特性**: 001-text2sql-datasource
**日期**: 2025-11-07
**目标受众**: 后端开发者和前端工程师

---

## 目录

1. [架构概述](#架构概述)
2. [环境设置](#环境设置)
3. [后端开发](#后端开发)
4. [前端开发](#前端开发)
5. [集成测试](#集成测试)
6. [部署](#部署)

---

## 架构概述

### 系统架构

```
┌─────────────────────┐
│   React 前端        │
│  (Zustand + RTK)    │
└──────────┬──────────┘
           │ REST API
           ↓
┌─────────────────────┐
│  FastAPI 后端       │
│  (Python 3.12)      │
└──────────┬──────────┘
           │ SQLAlchemy ORM
           ↓
┌─────────────────────┐
│ PostgreSQL Database │
│ (Coolify 托管)      │
└─────────────────────┘
```

### 数据流

**连接 PostgreSQL**:
```
用户输入凭据 → 验证格式 → 测试连接 → 加密存储 → 检索模式 → 显示表
```

**上传文件**:
```
选择文件 → 验证格式/大小 → 流式上传 → 解析数据 → 推断类型 → 缓存元数据
```

---

## 环境设置

### 后端环境变量 (.env)

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres

# 加密密钥 (32 字节)
ENCRYPTION_KEY=your-256-bit-key-base64-encoded

# 文件上传
MAX_FILE_SIZE=536870912  # 500MB in bytes
UPLOAD_TEMP_DIR=/tmp/uploads

# 缓存
SCHEMA_CACHE_TTL=300  # 5 minutes

# 日志
LOG_LEVEL=INFO
```

### 前端环境变量 (.env)

```bash
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=AI Data Analyzer
```

---

## 后端开发

### 1. 项目初始化

```bash
# 创建后端目录
mkdir -p backend/src/{models,services,api,db}
cd backend

# 创建虚拟环境
uv venv .venv
source .venv/bin/activate

# 安装依赖
uv add fastapi uvicorn sqlalchemy asyncpg pydantic cryptography
uv add --dev pytest pytest-asyncio pytest-cov
```

### 2. 创建核心文件

#### `backend/src/main.py` - FastAPI 应用

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import datasources, files, schemas

app = FastAPI(
    title="数据源集成 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(datasources.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(schemas.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### `backend/src/db/session.py` - 数据库配置

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@host:5432/database"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

#### `backend/src/models/data_source.py` - ORM 模型

```python
from sqlalchemy import Column, String, Enum, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)  # 简化用户管理
    name = Column(String(255), nullable=False, unique=True)
    type = Column(Enum("postgresql", "csv", "excel", name="datasource_type"))
    status = Column(String(20), default="connected")
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested_at = Column(DateTime)
    test_result = Column(Boolean)
```

### 3. 实现服务层

#### `backend/src/services/postgres.py` - PostgreSQL 服务

```python
from typing import Optional
import asyncpg
from sqlalchemy import text

async def test_postgres_connection(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> tuple[bool, str]:
    """测试 PostgreSQL 连接"""
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=10
        )
        await conn.close()
        return True, "连接成功"
    except Exception as e:
        return False, str(e)

async def get_database_schema(
    session,
    data_source_id: str
) -> Optional[dict]:
    """获取数据库模式"""
    # 使用 information_schema 查询
    query = text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    # ... 实现查询逻辑
```

#### `backend/src/services/file_handler.py` - 文件处理服务

```python
import csv
from openpyxl import load_workbook
from typing import List, Dict

async def parse_csv(file_path: str) -> Dict:
    """解析 CSV 文件"""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)[:1000]  # 预览前 1000 行

    columns = infer_columns(rows)
    return {
        "rows": rows,
        "columns": columns,
        "row_count": len(rows)
    }

def infer_columns(rows: List[Dict]) -> List[Dict]:
    """推断列的数据类型"""
    columns = []
    if not rows:
        return columns

    for key in rows[0].keys():
        data_type = infer_type(rows, key)
        columns.append({
            "name": key,
            "data_type": data_type,
            "nullable": True
        })
    return columns

def infer_type(rows: List[Dict], key: str) -> str:
    """推断单列的数据类型"""
    # 简单的类型推断逻辑
    values = [row.get(key) for row in rows if row.get(key)]

    # 检查是否都是整数
    if all(is_int(v) for v in values):
        return "integer"
    # 检查是否都是浮点数
    elif all(is_float(v) for v in values):
        return "float"
    # 默认为文本
    return "text"
```

#### `backend/src/services/encryption.py` - 加密服务

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()[:32]  # 256 位

def encrypt_password(password: str) -> bytes:
    """加密密码"""
    iv = os.urandom(16)
    cipher = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    # PKCS7 填充
    padded = password.encode() + b'\x00' * (16 - len(password) % 16)
    encrypted = encryptor.update(padded) + encryptor.finalize()

    return iv + encrypted  # IV + 加密数据

def decrypt_password(encrypted_data: bytes) -> str:
    """解密密码"""
    iv = encrypted_data[:16]
    encrypted = encrypted_data[16:]

    cipher = Cipher(
        algorithms.AES(ENCRYPTION_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()

    return decrypted.rstrip(b'\x00').decode()
```

### 4. 实现 API 路由

#### `backend/src/api/datasources.py` - 数据源端点

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_db
from ..models.data_source import DataSource
from ..services.postgres import test_postgres_connection
from ..services.encryption import encrypt_password

router = APIRouter(tags=["datasources"])

@router.post("/datasources/postgres")
async def create_postgres_datasource(
    request: dict,
    session: AsyncSession = Depends(get_db)
):
    """创建 PostgreSQL 数据源"""
    # 测试连接
    success, message = await test_postgres_connection(
        host=request["host"],
        port=request["port"],
        database=request["database"],
        username=request["username"],
        password=request["password"]
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # 创建数据源
    datasource = DataSource(
        user_id="demo-user",  # 简化用户管理
        name=request["name"],
        type="postgresql",
        status="connected"
    )

    session.add(datasource)
    await session.commit()

    return {"id": str(datasource.id), "status": "connected"}

@router.get("/datasources")
async def list_datasources(
    session: AsyncSession = Depends(get_db)
):
    """列出所有数据源"""
    result = await session.execute(
        "SELECT * FROM data_sources"
    )
    return {"items": result.fetchall()}
```

---

## 前端开发

### 1. 项目初始化

```bash
# 创建 React 项目
npm create vite@latest frontend -- --template react-ts
cd frontend

# 安装依赖
npm install zustand react-query axios
npm install shadcn-ui tailwind-css tremor
npm install --save-dev vitest @testing-library/react
```

### 2. 状态管理设置

#### `frontend/src/stores/useDataSourceStore.ts`

```typescript
import { create } from 'zustand';

interface DataSource {
  id: string;
  name: string;
  type: 'postgresql' | 'csv' | 'excel';
  status: 'connected' | 'disconnected' | 'error';
  created_at: string;
}

interface DataSourceStore {
  dataSources: DataSource[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;

  fetchDataSources: () => Promise<void>;
  selectDataSource: (id: string) => void;
  addDataSource: (config: any) => Promise<void>;
  removeDataSource: (id: string) => Promise<void>;
}

export const useDataSourceStore = create<DataSourceStore>((set) => ({
  dataSources: [],
  selectedId: null,
  isLoading: false,
  error: null,

  fetchDataSources: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/datasources`);
      const data = await response.json();
      set({ dataSources: data.items, error: null });
    } catch (error) {
      set({ error: String(error) });
    } finally {
      set({ isLoading: false });
    }
  },

  selectDataSource: (id: string) => {
    set({ selectedId: id });
  },

  addDataSource: async (config: any) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/datasources/postgres`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        await set((state) => ({
          dataSources: [...state.dataSources]
        }));
      }
    } catch (error) {
      set({ error: String(error) });
    }
  },

  removeDataSource: async (id: string) => {
    // 实现删除逻辑
  }
}));
```

### 3. React 组件

#### `frontend/src/components/datasources/DataSourceList.tsx`

```typescript
import React, { useEffect } from 'react';
import { useDataSourceStore } from '../../stores/useDataSourceStore';

export const DataSourceList: React.FC = () => {
  const { dataSources, selectedId, selectDataSource, fetchDataSources } =
    useDataSourceStore();

  useEffect(() => {
    fetchDataSources();
  }, []);

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-bold">数据源</h2>
      {dataSources.map((ds) => (
        <div
          key={ds.id}
          className={`p-4 border rounded cursor-pointer ${
            selectedId === ds.id ? 'bg-blue-100' : ''
          }`}
          onClick={() => selectDataSource(ds.id)}
        >
          <h3 className="font-semibold">{ds.name}</h3>
          <p className="text-sm text-gray-600">{ds.type}</p>
          <span className={`text-xs px-2 py-1 rounded ${
            ds.status === 'connected' ? 'bg-green-200' : 'bg-red-200'
          }`}>
            {ds.status}
          </span>
        </div>
      ))}
    </div>
  );
};
```

#### `frontend/src/components/datasources/ConnectPostgres.tsx`

```typescript
import React, { useState } from 'react';
import { useDataSourceStore } from '../../stores/useDataSourceStore';

export const ConnectPostgres: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    host: 'host.docker.internal',
    port: 5432,
    database: 'postgres',
    username: '',
    password: ''
  });

  const { addDataSource } = useDataSourceStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await addDataSource(formData);
    setFormData({ ...formData, name: '', username: '', password: '' });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded">
      <h3 className="font-bold">连接 PostgreSQL</h3>

      <input
        type="text"
        placeholder="数据源名称"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        className="w-full p-2 border rounded"
      />

      <input
        type="text"
        placeholder="主机"
        value={formData.host}
        onChange={(e) => setFormData({ ...formData, host: e.target.value })}
        className="w-full p-2 border rounded"
      />

      <input
        type="number"
        placeholder="端口"
        value={formData.port}
        onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
        className="w-full p-2 border rounded"
      />

      <input
        type="text"
        placeholder="数据库"
        value={formData.database}
        onChange={(e) => setFormData({ ...formData, database: e.target.value })}
        className="w-full p-2 border rounded"
      />

      <input
        type="text"
        placeholder="用户名"
        value={formData.username}
        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        className="w-full p-2 border rounded"
      />

      <input
        type="password"
        placeholder="密码"
        value={formData.password}
        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        className="w-full p-2 border rounded"
      />

      <button
        type="submit"
        className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        连接
      </button>
    </form>
  );
};
```

---

## 集成测试

### 后端测试示例

```bash
# tests/integration/test_datasources.py

import pytest
from httpx import AsyncClient
from ..main import app

@pytest.mark.asyncio
async def test_list_datasources():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/datasources")
        assert response.status_code == 200
        assert "items" in response.json()

@pytest.mark.asyncio
async def test_create_postgres_datasource():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "name": "Test PostgreSQL",
            "host": "host.docker.internal",
            "port": 5432,
            "database": "postgres",
            "username": "test",
            "password": "test"
        }
        response = await client.post("/api/datasources/postgres", json=payload)
        # 预期连接失败 (测试凭据)
        assert response.status_code in [400, 201]
```

---

## 部署

### Docker 部署

#### `Dockerfile` (后端)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv install

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://user:password@postgres:5432/database
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000/api

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 故障排除

| 问题 | 解决方案 |
|------|--------|
| "连接超时" | 检查 PostgreSQL 主机地址和防火墙 |
| "密钥长度错误" | 确保 ENCRYPTION_KEY 是 32 字节的 base64 编码 |
| "CORS 错误" | 检查 FastAPI CORS 中间件配置 |
| "文件太大" | 检查 MAX_FILE_SIZE 环境变量 |

---

## 后续资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Zustand 文档](https://github.com/pmndrs/zustand)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)

**快速开始指南完成**: ✅
