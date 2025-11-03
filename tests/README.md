# 测试中心

本目录包含所有项目测试，遵循标准化的测试结构和命名规范。

## 📂 目录结构

```
tests/
├── README.md                 # 本文件
├── conftest.py               # pytest 全局配置
├── unit/                     # 单元测试
│   ├── backend/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_utils.py
│   │   └── __init__.py
│   └── frontend/
│       ├── test_components.tsx
│       ├── test_hooks.ts
│       └── __init__.ts
├── integration/              # 集成测试
│   ├── test_api_endpoints.py
│   ├── test_database_integration.py
│   ├── test_external_services.py
│   └── __init__.py
├── e2e/                      # 端到端测试
│   ├── test_user_workflows.py
│   ├── test_critical_paths.py
│   └── __init__.py
└── fixtures/                 # 测试数据和 fixtures
    ├── data/
    │   ├── users.json
    │   ├── products.json
    │   └── sample-data.sql
    ├── mocks/
    │   ├── mock-api.py
    │   ├── mock-database.py
    │   └── __init__.py
    └── __init__.py
```

---

## 🧪 测试分类

### 单元测试 (`unit/`)
测试单个函数或组件的功能

**特点**:
- 快速执行（毫秒级）
- 隔离测试（无外部依赖）
- 覆盖率要求高 (>80%)
- 每个功能应有对应的测试

**后端测试** (`unit/backend/`):
```bash
# 测试数据模型
tests/unit/backend/test_models.py

# 测试业务逻辑
tests/unit/backend/test_services.py

# 测试工具函数
tests/unit/backend/test_utils.py
```

**前端测试** (`unit/frontend/`):
```bash
# 测试 React 组件
tests/unit/frontend/test_components.tsx

# 测试 React Hooks
tests/unit/frontend/test_hooks.ts
```

### 集成测试 (`integration/`)
测试多个模块之间的交互

**特点**:
- 测试速度中等（秒级）
- 涉及外部服务（数据库、API）
- 验证模块间集成
- 覆盖关键业务流程

**集成测试类型**:
```bash
# API 端点集成
tests/integration/test_api_endpoints.py

# 数据库集成
tests/integration/test_database_integration.py

# 外部服务集成
tests/integration/test_external_services.py
```

### 端到端测试 (`e2e/`)
测试完整的用户工作流

**特点**:
- 执行速度慢（分钟级）
- 测试完整业务流程
- 验证用户端到端体验
- 覆盖关键用户场景

**E2E 测试类型**:
```bash
# 用户工作流测试
tests/e2e/test_user_workflows.py

# 关键路径测试
tests/e2e/test_critical_paths.py
```

---

## 🔧 使用 pytest

### 基本命令

```bash
# 运行所有测试
pytest

# 运行特定目录的测试
pytest tests/unit/

# 运行特定文件的测试
pytest tests/unit/backend/test_models.py

# 运行特定测试函数
pytest tests/unit/backend/test_models.py::test_user_creation

# 运行并显示打印输出
pytest -s

# 运行并显示详细信息
pytest -v

# 运行失败的测试
pytest --lf

# 只运行最后一次失败的测试
pytest -x
```

### 高级选项

```bash
# 并行运行测试（需要 pytest-xdist）
pytest -n auto

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 显示最慢的 10 个测试
pytest --durations=10

# 交互式调试
pytest --pdb

# 只运行标记为特定标签的测试
pytest -m "unit"
```

---

## 📝 编写测试

### 单元测试示例

```python
"""测试数据模型"""

import pytest
from src.models import User


class TestUserModel:
    """User 模型测试类"""

    def test_user_creation(self):
        """测试用户创建"""
        user = User(name="John", email="john@example.com")
        assert user.name == "John"
        assert user.email == "john@example.com"

    def test_user_email_validation(self):
        """测试邮箱验证"""
        with pytest.raises(ValueError):
            User(name="John", email="invalid-email")

    @pytest.fixture
    def sample_user(self):
        """创建示例用户的 fixture"""
        return User(name="Jane", email="jane@example.com")

    def test_user_update(self, sample_user):
        """测试用户更新（使用 fixture）"""
        sample_user.name = "Jane Doe"
        assert sample_user.name == "Jane Doe"
```

### 集成测试示例

```python
"""测试 API 端点集成"""

import pytest
from app import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app('testing')
    with app.test_client() as client:
        yield client


class TestUserAPI:
    """用户 API 集成测试"""

    def test_create_user(self, client):
        """测试创建用户 API"""
        response = client.post('/api/users', json={
            'name': 'John',
            'email': 'john@example.com'
        })
        assert response.status_code == 201
        assert response.json['name'] == 'John'

    def test_get_user(self, client):
        """测试获取用户 API"""
        response = client.get('/api/users/1')
        assert response.status_code == 200

    def test_update_user(self, client):
        """测试更新用户 API"""
        response = client.put('/api/users/1', json={
            'name': 'Jane'
        })
        assert response.status_code == 200
        assert response.json['name'] == 'Jane'
```

### 前端组件测试示例

```typescript
/**
 * 测试 Button 组件
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

describe('Button Component', () => {
    test('renders button with text', () => {
        render(<Button>Click me</Button>);
        expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
    });

    test('calls onClick handler when clicked', () => {
        const handleClick = jest.fn();
        render(<Button onClick={handleClick}>Click me</Button>);

        fireEvent.click(screen.getByRole('button'));
        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('disables button when disabled prop is true', () => {
        render(<Button disabled>Click me</Button>);
        expect(screen.getByRole('button')).toBeDisabled();
    });
});
```

---

## 🎯 测试标记（Tags）

使用 pytest markers 分类测试：

```python
import pytest

@pytest.mark.unit
def test_some_function():
    """单元测试"""
    pass

@pytest.mark.integration
def test_api_integration():
    """集成测试"""
    pass

@pytest.mark.e2e
def test_user_workflow():
    """端到端测试"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """标记为慢速测试"""
    pass

@pytest.mark.skip(reason="未实现")
def test_future_feature():
    """跳过测试"""
    pass
```

在 `conftest.py` 中配置：

```python
# conftest.py

import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )

# 运行特定标记的测试
# pytest -m unit
# pytest -m "not slow"
```

---

## 📊 覆盖率

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=src --cov-report=html

# 生成终端覆盖率报告
pytest --cov=src --cov-report=term-missing

# 设置最低覆盖率阈值
pytest --cov=src --cov-fail-under=80
```

### 覆盖率目标

| 代码类型 | 目标 | 说明 |
|---------|------|------|
| 业务逻辑 | >85% | 核心功能 |
| API 端点 | >80% | 所有端点 |
| 组件 | >70% | UI 组件 |
| 工具函数 | >90% | 辅助函数 |

---

## 🔍 Fixtures 和模拟数据

### 创建 Fixtures

```python
# tests/conftest.py

import pytest
from src.database import db
from src.models import User


@pytest.fixture
def sample_user():
    """创建示例用户"""
    user = User(name="Test User", email="test@example.com")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


@pytest.fixture
def sample_users():
    """创建多个示例用户"""
    users = [
        User(name=f"User {i}", email=f"user{i}@example.com")
        for i in range(5)
    ]
    db.session.add_all(users)
    db.session.commit()
    yield users
    for user in users:
        db.session.delete(user)
    db.session.commit()
```

### 使用 Mock 对象

```python
from unittest.mock import Mock, patch
import pytest


@pytest.fixture
def mock_external_api():
    """模拟外部 API"""
    with patch('src.services.external_api.call') as mock:
        mock.return_value = {'status': 'ok', 'data': []}
        yield mock


def test_with_mock_api(mock_external_api):
    """使用模拟 API 的测试"""
    result = some_function_that_calls_api()
    mock_external_api.assert_called_once()
```

---

## ⚙️ 配置文件

### pytest.ini 或 pyproject.toml

```toml
[tool.pytest.ini_options]
# 测试文件位置
testpaths = ["tests"]

# Python 文件搜索路径
pythonpath = ["src"]

# 显示最慢的 10 个测试
addopts = "--durations=10 -v"

# 覆盖率配置
[tool.coverage.run]
source = ["src"]
omit = ["*/__init__.py", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## 📋 最佳实践

### ✓ 推荐做法

- ✓ 为每个函数编写测试
- ✓ 使用有意义的测试名称
- ✓ 每个测试只测试一个事情
- ✓ 使用 fixtures 复用测试数据
- ✓ 及时更新过期的测试
- ✓ 编写文档字符串说明测试目的
- ✓ 使用 AAA 模式（Arrange-Act-Assert）

### ✗ 避免做法

- ✗ 编写过长的测试函数
- ✗ 跳过或注释掉测试
- ✗ 在测试中有随机行为
- ✗ 依赖测试执行顺序
- ✗ 测试实现而不是行为
- ✗ 忽略错误情况

### AAA 模式示例

```python
def test_calculate_total():
    # Arrange - 准备数据
    items = [
        {'price': 10, 'quantity': 2},
        {'price': 20, 'quantity': 1}
    ]

    # Act - 执行被测试的代码
    result = calculate_total(items)

    # Assert - 验证结果
    assert result == 40
```

---

## 🚀 运行完整测试套件

```bash
# 1. 运行所有测试
pytest tests/

# 2. 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 3. 查看覆盖率报告
open htmlcov/index.html

# 4. 运行快速测试（跳过慢速测试）
pytest tests/ -m "not slow"

# 5. 并行运行（加快测试）
pytest tests/ -n auto
```

---

## 📚 相关文档

- [测试指南](../docs/guides/developer/testing.md)
- [开发指南](../docs/guides/developer/)
- [贡献指南](../docs/guides/developer/contributing.md)

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
