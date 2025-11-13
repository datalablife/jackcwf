# Constitution 实施指南

**版本**: v1.0.0
**日期**: 2025-11-12
**目的**: 使代码库与项目章程保持一致的实践步骤

---

## 📋 快速导航

- [前端现代化 (Tremor + shadcn/ui)](#前端现代化)
- [后端标准 (FastAPI + PostgreSQL)](#后端标准)
- [DevOps 与部署](#devops-与部署)
- [合规性检查清单](#合规性检查清单)

---

## 前端现代化

### 步骤 1: 安装依赖

```bash
cd frontend
npm install @tremor/react @radix-ui/react-dialog @radix-ui/react-popover \
  shadcn-ui tailwindcss autoprefixer lucide-react
```

### 步骤 2: 配置 Tailwind 与暗色模式

**`frontend/tailwind.config.js`**:

```js
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        slate: {
          900: '#0f172a',
          800: '#1e293b',
          // ... 使用 design-specification.md 调色板扩展
        },
        cyan: {
          500: '#06b6d4',
        },
      },
      fontSize: {
        hero: '36px',
        title: '24px',
        card: '18px',
        body: '14px',
        small: '12px',
        caps: '10px',
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        '2xl': '48px',
      },
      borderRadius: {
        sm: '8px',
        md: '16px',
        lg: '20px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
```

### 步骤 3: 组件库结构

```
frontend/src/components/
├── shared/                    # 通用 UI (shadcn/ui)
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Dialog.tsx
│   ├── Sidebar.tsx
│   └── Navigation.tsx
├── analytics/                 # 仪表板分析 (Tremor)
│   ├── KPICard.tsx
│   ├── BarChart.tsx
│   ├── LineChart.tsx
│   └── DataTable.tsx
├── layouts/                   # 页面布局
│   ├── DashboardLayout.tsx
│   └── AppShell.tsx
└── stories/                   # Storybook 故事
    ├── Button.stories.tsx
    └── KPICard.stories.tsx
```

### 步骤 4: 构建核心组件

#### 示例 1: KPI 卡片 (Tremor)

```tsx
// frontend/src/components/analytics/KPICard.tsx
import React from 'react';
import { Card, Metric, Text } from '@tremor/react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  className?: string;
  variant?: 'default' | 'success' | 'warning';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  className = '',
  variant = 'default',
}) => {
  return (
    <Card className={`bg-gradient-to-br from-slate-800 to-slate-700 ${className}`}>
      <Text className="text-gray-400 text-sm">{title}</Text>
      <Metric className="text-cyan-500 text-4xl font-bold mt-2">{value}</Metric>
      {subtitle && <Text className="text-gray-500 text-xs mt-1">{subtitle}</Text>}
    </Card>
  );
};
```

#### 示例 2: 按钮 (shadcn/ui)

```tsx
// frontend/src/components/shared/Button.tsx
import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className = '', ...props }, ref) => {
    const baseStyles = 'rounded-lg font-medium transition-all duration-200';
    const variantStyles = {
      primary: 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-600',
      secondary: 'bg-transparent hover:bg-slate-800/50 text-gray-200 border border-slate-600',
      outline: 'border-2 border-cyan-500 text-cyan-500 hover:bg-cyan-500/10',
    };
    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={props.disabled || isLoading}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
```

### 步骤 5: 响应式导航布局

```tsx
// frontend/src/components/layouts/DashboardLayout.tsx
import React, { useState } from 'react';
import { Sidebar } from '../shared/Sidebar';
import { Header } from '../shared/Header';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-slate-900">
      {/* 侧边栏: 桌面端固定,移动端隐藏 */}
      <div
        className={`${
          sidebarOpen ? 'w-72' : 'w-0'
        } transition-all duration-300 hidden md:block bg-slate-800`}
      >
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* 移动端侧边栏: 抽屉/覆盖层 */}
      {sidebarOpen && (
        <div className="fixed inset-0 md:hidden bg-black/50 z-40">
          <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-auto bg-slate-900 p-6">{children}</main>
      </div>
    </div>
  );
};
```

---

## 后端标准

### 步骤 1: 使用 Alembic 进行数据库迁移

```bash
cd backend
alembic init -t async alembic
```

**`backend/alembic/env.py`**: 配置异步 SQLAlchemy

```python
from sqlalchemy.ext.asyncio import create_async_engine

# 加载配置
config = context.config
database_url = os.getenv('DATABASE_URL')
# 转换为异步驱动
async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = async_database_url

    connectable = create_async_engine(async_database_url, echo=True)

    with connectable.begin() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### 步骤 2: 具有类型安全的 SQLAlchemy 模型

```python
# backend/src/models/user.py
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import uuid

from .base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 明确加载策略的关系
    transactions: Mapped[list['Transaction']] = relationship(
        'Transaction',
        back_populates='user',
        lazy='selectin',  # 急切加载事务
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_created_at', 'created_at'),
    )
```

### 步骤 3: 结构化日志

```python
# backend/src/logging_config.py
import json
import logging
from typing import Any, Dict
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **context: Any) -> None:
        """发出结构化 JSON 日志"""
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'service': 'backend',
            'message': message,
            **context,
        }
        log_message = json.dumps(log_entry)
        getattr(self.logger, level.lower())(log_message)

    def info(self, message: str, **context: Any) -> None:
        self.log('info', message, **context)

    def error(self, message: str, exc_info: Exception | None = None, **context: Any) -> None:
        self.log(
            'error',
            message,
            error_type=type(exc_info).__name__ if exc_info else None,
            traceback=str(exc_info) if exc_info else None,
            **context,
        )

logger = StructuredLogger(__name__)
```

### 步骤 4: 具有可观测性的 FastAPI 端点

```python
# backend/src/api/users.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import uuid
import time

from ..models import User
from ..logging_config import logger
from ..database import get_session

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str, session: AsyncSession = Depends(get_session)):
    """获取用户及其事务(急切加载)"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 显式使用 selectinload 防止 N+1 问题
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.transactions))
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "User fetched",
            request_id=request_id,
            user_id=user_id,
            duration_ms=round(duration_ms, 2),
        )

        return user.to_dict()

    except Exception as e:
        logger.error(
            "Failed to fetch user",
            request_id=request_id,
            user_id=user_id,
            exc_info=e,
        )
        raise
```

### 步骤 5: Prometheus 指标

```python
# backend/src/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    labelnames=['method', 'endpoint', 'status_code'],
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    labelnames=['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0),
)

# 数据库指标
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    labelnames=['query_type'],
)
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
)
```

### 步骤 6: 类型安全的 API 响应

```python
# backend/src/schemas/responses.py
from pydantic import BaseModel
from typing import Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """标准 API 响应包装器"""
    success: bool
    data: T | None = None
    error: str | None = None
    timestamp: datetime
    request_id: str

class UserResponse(BaseModel):
    """用户 API 响应"""
    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## DevOps 与部署

### 步骤 1: 健康检查端点

```python
# backend/src/api/health.py
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """存活探测"""
    return {"status": "healthy"}

@router.get("/readiness")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """就绪探测: 检查数据库连接"""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}, 503
```

### 步骤 2: Docker 配置

**`Dockerfile`**:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
COPY pyproject.toml pyproject.lock* ./
RUN pip install --user --no-cache-dir uv && uv pip install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "src.main"]
```

### 步骤 3: GitHub Actions CI/CD

**`.github/workflows/ci.yml`**:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
          pip install uv
          uv sync
      - run: uv run pytest --cov=src
      - run: uv run mypy --strict src/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm install
          npm run lint
          npm run type-check
```

---

## 合规性检查清单

### 前端检查清单

- [ ] 已安装并配置 Tremor + shadcn/ui
- [ ] 已启用 Tailwind 暗色模式,使用 design-specification.md 颜色
- [ ] 已使用 TypeScript 接口创建组件库
- [ ] 已设置 Storybook 及组件文档
- [ ] 响应式导航(侧边栏在 < 768px 时折叠)
- [ ] 可访问性审计(WAVE, axe, Lighthouse 无障碍得分 100)
- [ ] 性能审计(Lighthouse 性能得分 80+)
- [ ] 已在所有组件中测试暗色模式 CSS 变量
- [ ] 已测试键盘导航(Tab, Enter, Escape)

### 后端检查清单

- [ ] 已配置并版本化 Alembic 迁移
- [ ] SQLAlchemy 模型使用显式加载策略(无延迟加载)
- [ ] 结构化日志(JSON 格式带上下文)
- [ ] 已暴露 Prometheus 指标(`/metrics` 端点)
- [ ] 健康检查端点(`/health`, `/readiness`)
- [ ] 请求 ID 追踪(`X-Request-ID` 传播)
- [ ] 所有函数都有类型提示(mypy --strict 通过)
- [ ] 已配置连接池
- [ ] 慢查询日志(> 100ms 警告)

### DevOps 检查清单

- [ ] 已配置 Docker 多阶段构建
- [ ] Dockerfile 中的健康检查
- [ ] GitHub Actions CI/CD 流水线
- [ ] 代码检查(Black, isort, flake8)
- [ ] 类型检查(mypy, TypeScript strict)
- [ ] 带覆盖率报告的单元测试
- [ ] 已配置 Coolify 部署
- [ ] 已在 `.env.example` 中记录环境变量

---

## 参考链接

- **设计规范**: `docs/prd/desgin/design-specification.md`
- **项目章程**: `.specify/memory/constitution.md`
- **组件文档**: `frontend/src/components/README.md` (待创建)
- **后端架构**: `backend/README.md` (待更新)

---

**版本**: v1.0.0
**最后更新**: 2025-11-12
