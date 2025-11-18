# Python 升级执行清单

本文档为Python 3.12 → 3.13 → 3.14的分阶段升级提供实际执行步骤。

---

## 阶段1: 升级到Python 3.13 (立即执行)

### 1.1 本地环境准备

```bash
# 检查当前Python版本
python3 --version
# 输出: Python 3.12.3

# 安装Python 3.13 (如果尚未安装)
# macOS
brew install python@3.13

# Ubuntu/Debian
sudo apt-get install python3.13 python3.13-venv python3.13-dev

# Windows
# 从 https://www.python.org/downloads/ 下载3.13安装程序

# 验证安装
python3.13 --version
```

### 1.2 创建测试虚拟环境

```bash
# 创建Python 3.13虚拟环境
python3.13 -m venv venv_py313

# 激活虚拟环境
source venv_py313/bin/activate  # Linux/macOS
# 或
venv_py313\Scripts\activate  # Windows

# 验证
python --version  # 应该显示3.13.x
which python     # 应该指向venv_py313
```

### 1.3 安装依赖并测试

```bash
# 升级pip和相关工具
pip install --upgrade pip setuptools wheel

# 安装项目依赖
pip install -e ".[dev]"

# 监控输出，特别注意编译错误:
# - asyncpg 编译
# - cryptography 编译
# - greenlet 编译

# 记录安装结果
pip list > py313_packages.txt
pip check  # 检查版本冲突
```

### 1.4 运行测试

```bash
# 单元测试
pytest tests/unit/ -v --tb=short

# 集成测试
pytest tests/integration/ -v --tb=short

# 异步测试
pytest tests/ -v --asyncio-mode=auto

# 覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 类型检查
mypy src/

# 代码风格检查
black --check src/ tests/
isort --check-only src/ tests/
```

### 1.5 性能基准测试

```bash
# 创建基准测试脚本
cat > benchmark_py313.py << 'EOF'
import asyncio
import time
import sys
from src.api.routes.rag import rag_query

async def benchmark_rag():
    """基准测试RAG查询"""
    query = "What is the main topic of the documents?"

    start = time.time()
    for _ in range(10):
        # 模拟RAG查询
        await rag_query(query)
    elapsed = time.time() - start

    print(f"Python {sys.version_info.major}.{sys.version_info.minor}")
    print(f"10 queries took {elapsed:.2f}s")
    print(f"Average: {elapsed/10*1000:.2f}ms per query")

if __name__ == "__main__":
    asyncio.run(benchmark_rag())
EOF

# 运行基准测试
python benchmark_py313.py

# 与Python 3.12对比
python3.12 -m venv venv_py312
source venv_py312/bin/activate
pip install -e ".[dev]"
python benchmark_py313.py  # 实际上运行3.12版本

# 对比结果
echo "性能改进:"
echo "3.12: X ms"
echo "3.13: Y ms (改进: (X-Y)/X * 100%)"
```

### 1.6 更新项目配置

```bash
# 编辑 pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
requires-python = ">=3.13,<4.0"

classifiers = [
    ...
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",  # 添加3.14声明(可选)
]

[tool.black]
target-version = ['py313']

[tool.mypy]
python_version = "3.13"

# 更新依赖版本约束
dependencies = [
    "fastapi>=0.110.0",        # 升级
    "uvicorn[standard]>=0.27.0",  # 升级
    "asyncpg>=0.29.0",         # 保持或升级到0.30+
    # 其他依赖保持不变
]
EOF
```

### 1.7 更新CI/CD配置

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version:
          - "3.13"     # 更新到3.13
          - "3.14"     # 添加3.14实验性测试

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/ -v --cov

      - name: Type checking
        run: mypy src/
        if: matrix.python-version == '3.13'  # 仅在3.13上运行

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: matrix.python-version == '3.13'
```

### 1.8 Docker更新

```dockerfile
# Dockerfile
# 当前
FROM python:3.12-slim

# 更新到
FROM python:3.13-slim

# 重建镜像
docker build -t myapp:py313 .

# 测试镜像
docker run -it myapp:py313 python --version
docker run myapp:py313 pytest tests/ -x
```

### 1.9 环境验证清单

```markdown
## Python 3.13升级验证清单

- [ ] Python 3.13在本地安装且可验证 (`python3.13 --version`)
- [ ] 虚拟环境创建成功 (`which python` 指向venv_py313)
- [ ] 依赖安装成功，无编译错误
- [ ] `pip check` 无版本冲突
- [ ] 单元测试全部通过
- [ ] 集成测试全部通过
- [ ] 异步测试全部通过 (`pytest --asyncio-mode=auto`)
- [ ] mypy类型检查通过
- [ ] 代码风格检查通过 (black, isort)
- [ ] 性能基准测试完成，结果记录
- [ ] pyproject.toml已更新 (requires-python, target-version, classifiers)
- [ ] CI/CD配置已更新
- [ ] Dockerfile已更新
- [ ] GitHub Actions工作流已测试
- [ ] 所有变更已提交到feature分支
```

### 1.10 提交变更

```bash
# 创建feature分支
git checkout -b feat/python-3.13-upgrade

# 提交所有变更
git add -A
git commit -m "chore: upgrade to Python 3.13

- Update requires-python to >=3.13,<4.0
- Update tool.black target-version
- Update tool.mypy python_version
- Update CI/CD matrix to test Python 3.13
- Update Dockerfile to use python:3.13-slim
- Update FastAPI to 0.110.0+
- Update uvicorn to 0.27.0+
- All tests pass on Python 3.13
- Performance baseline recorded"

# 推送到远程
git push origin feat/python-3.13-upgrade

# 创建Pull Request
gh pr create --title "Upgrade to Python 3.13" --body "..."
```

---

## 阶段2: 监控Python 3.14支持 (2026年1月-3月)

### 2.1 关键库的支持状态监控

创建一个监控脚本来跟踪库的支持状态:

```python
# scripts/check_py314_support.py
import json
import subprocess
from datetime import datetime

CRITICAL_LIBS = [
    "langchain",
    "langchain-core",
    "langchain-community",
    "fastapi",
    "asyncpg",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
]

def check_library_support(lib_name):
    """检查库的Python 3.14支持"""
    try:
        # 获取PyPI上的库信息
        result = subprocess.run(
            ["pip", "index", "versions", lib_name],
            capture_output=True,
            text=True
        )

        # 解析输出查找Python 3.14
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Programming Language :: Python :: 3.14' in line:
                return 'SUPPORTED'
            if '3.14' in line:
                return 'PARTIAL'

        return 'NOT_LISTED'
    except Exception as e:
        return f'ERROR: {e}'

def main():
    print(f"Python 3.14 Support Check - {datetime.now().isoformat()}")
    print("=" * 60)

    results = {}
    for lib in CRITICAL_LIBS:
        status = check_library_support(lib)
        results[lib] = status
        print(f"{lib:20} : {status}")

    # 保存结果
    with open('py314_support.json', 'a') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f)
        f.write('\n')

if __name__ == "__main__":
    main()
```

运行:
```bash
# 每月运行一次
python scripts/check_py314_support.py

# 查看历史
cat py314_support.json | jq .
```

### 2.2 GitHub Issue关注

```markdown
## 关注的关键GitHub Issues

1. **LangChain**
   - Issue #5253: "Add support for Python 3.14"
   - https://github.com/langchain-ai/langgraph/issues/5253
   - 设置notifications

2. **asyncpg**
   - Watch for Python 3.14 wheel releases
   - https://github.com/MagicStack/asyncpg/releases

3. **FastAPI**
   - Already has Python 3.14 support (0.115.0+)

4. **Pydantic**
   - Already has Python 3.14 support (2.5.0+)

5. **aiohttp**
   - https://github.com/aio-libs/aiohttp
   - Check for Python 3.14 wheel releases
```

### 2.3 设置自动化通知

```yaml
# .github/dependabot.yml - 已有，但确保配置正确
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    allow:
      - dependency-type: "direct"
      - dependency-type: "indirect"
```

### 2.4 定期(每月)测试报告

```markdown
## Python 3.14 Compatibility Report - [月份]

### LangChain 1.0 Status
- Current version: 1.0.x
- Python 3.14 support: [✅ Confirmed / ⚠️ Experimental / ❌ Not supported]
- Known issues: [列出任何已知问题]
- Workarounds: [如果有的话]

### Other Critical Libraries
| Library | Version | Python 3.14 | Status |
|---------|---------|-------------|--------|
| asyncpg | x.x.x | ? | [Testing/Not tested] |
| FastAPI | x.x.x | ✅ | Ready |
| Pydantic | x.x.x | ✅ | Ready |

### Test Results (if attempted)
- Local testing: [Not started / In progress / Completed]
- Findings: [如果有的话]

### Recommendation
- Upgrade to Python 3.14: [Yes / No / Wait until X]
- Estimated readiness: [日期或里程碑]

### Next Steps
1. [ ] Continue monitoring LangChain releases
2. [ ] Test asyncpg 0.30+ when available
3. [ ] Review any new Python 3.14 compatibility issues
```

---

## 阶段3: 升级到Python 3.14 (2026年Q2+)

### 3.1 前置条件检查

```bash
# 创建升级前检查脚本
cat > scripts/pre_upgrade_check.sh << 'EOF'
#!/bin/bash

echo "Python 3.14 Upgrade Pre-Check"
echo "=============================="

# 检查1: Python 3.14可用性
echo -n "1. Python 3.14 available: "
python3.14 --version 2>/dev/null && echo "✅" || echo "❌"

# 检查2: LangChain官方支持
echo -n "2. LangChain 1.0.15+ (Python 3.14 support): "
pip show langchain | grep Version

# 检查3: asyncpg支持
echo -n "3. asyncpg 0.30+ available: "
pip index versions asyncpg | grep 0.30

# 检查4: FastAPI现状
echo -n "4. FastAPI 0.115.0+ available: "
pip index versions fastapi | grep 0.115

# 检查5: 所有依赖可安装
echo "5. Testing dependency resolution..."
python3.14 -m venv /tmp/test_venv_py314
source /tmp/test_venv_py314/bin/activate
pip install --dry-run -e ".[dev]" 2>&1 | grep -E "ERROR|error" && echo "❌ Conflicts found" || echo "✅ No conflicts"
deactivate
rm -rf /tmp/test_venv_py314

echo "=============================="
echo "If all checks pass, proceed with upgrade"
EOF

chmod +x scripts/pre_upgrade_check.sh
./scripts/pre_upgrade_check.sh
```

### 3.2 实际升级步骤

```bash
# 1. 创建Python 3.14虚拟环境
python3.14 -m venv venv_py314
source venv_py314/bin/activate

# 2. 升级依赖
pip install --upgrade pip setuptools wheel

# 3. 尝试安装
pip install -e ".[dev]"

# 4. 如果失败，记录错误并解决
# 例如，如果asyncpg无法编译:
# pip install --upgrade asyncpg
# 或等待更新的版本

# 5. 如果成功，运行完整测试
pytest tests/ -v --cov

# 6. 性能对比
python benchmark_py314.py
```

### 3.3 更新项目配置(阶段3)

```toml
# pyproject.toml - 最终版本
[project]
requires-python = ">=3.14,<4.0"

classifiers = [
    "Programming Language :: Python :: 3.14",
]

[tool.black]
target-version = ['py314']

[tool.mypy]
python_version = "3.14"

dependencies = [
    "langchain>=1.0.15+",      # 必须支持3.14
    "fastapi>=0.115.0+",
    "asyncpg>=0.30.0+",
    # 其他依赖相应更新
]
```

### 3.4 蓝绿部署步骤

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
        version: py314
    spec:
      containers:
      - name: app
        image: app:py314-latest  # 新镜像
        env:
        - name: PYTHON_VERSION
          value: "3.14"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    app: app
  ports:
  - port: 80
    targetPort: 8000
  # 使用蓝绿部署选择器
  # 初始指向 version: py313
  # 后续切换到 version: py314
```

切换命令:
```bash
# 当前(Python 3.13)
kubectl set selector service app version=py313

# 切换到Python 3.14
kubectl set selector service app version=py314

# 监控
kubectl get pods -l version=py314
kubectl logs -l version=py314 --tail=100

# 如果失败，回滚
kubectl set selector service app version=py313
```

---

## 附录A: 常见问题与解决方案

### A.1 asyncpg编译失败

```bash
# 错误:
# error: Microsoft Visual C++ 14.0 or greater is required

# 解决方案:
# 1. Windows: 安装Visual Studio Build Tools
# 2. Linux: sudo apt-get install build-essential python3-dev
# 3. macOS: xcode-select --install

# 3. 或升级到已编译的asyncpg版本
pip install --upgrade asyncpg
```

### A.2 导入错误: No module named 'X'

```bash
# 检查虚拟环境是否正确激活
which python  # 应该指向venv目录

# 重新安装依赖
pip install -e ".[dev]"

# 确保使用正确的Python
/path/to/venv/bin/python -c "import X"
```

### A.3 asyncio事件循环警告

```python
# 警告: DeprecationWarning: asyncio.get_event_loop()

# 解决方案: 使用asyncio.run()
# 而不是:
# loop = asyncio.get_event_loop()
# loop.run_until_complete(...)

# 使用:
asyncio.run(async_function())
```

### A.4 Pydantic兼容性问题

```python
# 错误: ImportError: cannot import name 'ValidationError' from 'pydantic.v1'

# 原因: Pydantic v2中，v1兼容层可能被移除

# 解决方案: 使用pydantic v2 API
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    name: str
    age: int
```

---

## 附录B: 性能基准测试模板

```python
# benchmark_template.py
import asyncio
import time
import statistics
from typing import List

import httpx

async def benchmark_rag_query(query: str, iterations: int = 10) -> List[float]:
    """基准测试单个RAG查询的延迟"""

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        times = []

        for i in range(iterations):
            start = time.perf_counter()

            response = await client.post(
                "/api/rag/query",
                json={"query": query}
            )

            elapsed = time.perf_counter() - start
            times.append(elapsed)

            print(f"Iteration {i+1}: {elapsed*1000:.2f}ms")

        return times

async def benchmark_concurrent_queries(
    query: str,
    concurrent_count: int = 10,
    iterations: int = 5
) -> List[float]:
    """基准测试并发查询"""

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            # 并发执行查询
            tasks = [
                client.post("/api/rag/query", json={"query": query})
                for _ in range(concurrent_count)
            ]

            await asyncio.gather(*tasks)

            elapsed = time.perf_counter() - start
            times.append(elapsed / concurrent_count)  # 平均每个查询的时间

            print(f"Concurrent batch (n={concurrent_count}): {elapsed*1000:.2f}ms, "
                  f"avg per query: {(elapsed/concurrent_count)*1000:.2f}ms")

        return times

async def main():
    """运行所有基准测试"""

    print("=" * 60)
    print(f"RAG Pipeline Benchmark")
    print("=" * 60)

    query = "What are the main topics in the documents?"

    # 测试1: 单个查询
    print("\nTest 1: Sequential Queries (10 iterations)")
    print("-" * 60)
    times = await benchmark_rag_query(query, iterations=10)

    print(f"\nStatistics:")
    print(f"  Min:    {min(times)*1000:.2f}ms")
    print(f"  Max:    {max(times)*1000:.2f}ms")
    print(f"  Mean:   {statistics.mean(times)*1000:.2f}ms")
    print(f"  Median: {statistics.median(times)*1000:.2f}ms")
    print(f"  StdDev: {statistics.stdev(times)*1000:.2f}ms")

    # 测试2: 并发查询
    print("\n\nTest 2: Concurrent Queries (10 concurrent, 5 batches)")
    print("-" * 60)
    times = await benchmark_concurrent_queries(query, concurrent_count=10, iterations=5)

    print(f"\nStatistics (per query):")
    print(f"  Min:    {min(times)*1000:.2f}ms")
    print(f"  Max:    {max(times)*1000:.2f}ms")
    print(f"  Mean:   {statistics.mean(times)*1000:.2f}ms")
    print(f"  Median: {statistics.median(times)*1000:.2f}ms")
    print(f"  StdDev: {statistics.stdev(times)*1000:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```bash
# 启动应用
python -m uvicorn src.main:app --reload

# 在另一个终端运行基准测试
python benchmark_template.py
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-18
