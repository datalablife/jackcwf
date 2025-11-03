# uv 包管理器使用指南

本项目已迁移到使用 **uv** 作为 Python 包管理器，uv 是一个快速、高效的 Python 包管理工具。

## 什么是 uv？

**uv** 是由 Astral 公司开发的现代 Python 包管理器，比 pip 快 10-100 倍。它提供了以下优势：

- ⚡ **超快速**: 使用 Rust 实现，比 pip 快得多
- 🔒 **可靠**: 锁定依赖版本，确保可重复构建
- 📦 **功能完整**: 支持虚拟环境、依赖解析、包安装等
- 🐍 **Python 管理**: 可以安装和管理 Python 版本本身

## 项目配置

### pyproject.toml

项目的所有配置都在 `pyproject.toml` 中定义：

```toml
[project]
name = "working"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    # 生产依赖
    "reflex==0.8.16",
    "sqlalchemy==2.0.44",
    # ...
]

[project.optional-dependencies]
dev = [
    # 开发依赖
    "pytest>=7.4.0",
    "black>=23.0.0",
    # ...
]
```

### uv.lock

`uv.lock` 文件记录了所有已安装包的精确版本和源：

```
version = 1
revision = 3

[[package]]
name = "reflex"
version = "0.8.16"
# ...
```

## 常用命令

### 虚拟环境管理

```bash
# 同步虚拟环境（安装/更新依赖）
uv sync

# 清除缓存并重新同步
uv sync --refresh

# 清除所有缓存
uv sync --clear-cache

# 只同步特定依赖组
uv sync --group dev     # 同步开发依赖
uv sync --no-dev        # 只同步生产依赖
```

### 激活虚拟环境

```bash
# 激活虚拟环境
source .venv/bin/activate

# 或在 Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 查看虚拟环境信息
uv venv --help
```

### 不激活虚拟环境运行命令

```bash
# 直接运行 Python 脚本
uv run python script.py

# 运行 pytest
uv run pytest

# 运行任何命令
uv run black .
uv run isort .
```

### 管理依赖

```bash
# 添加新的依赖
uv add package_name

# 添加特定版本
uv add 'package_name==1.0.0'

# 添加开发依赖
uv add --dev pytest

# 移除依赖
uv remove package_name

# 更新所有依赖
uv sync --upgrade

# 更新特定依赖
uv sync --upgrade-package package_name

# 列出已安装的包
uv pip list

# 导出 requirements.txt
uv export --output-file requirements.txt

# 导出开发依赖
uv export --with dev --output-file requirements-dev.txt
```

### 版本管理

```bash
# 查看 uv 版本
uv --version

# 更新 uv 本身
uv self update

# 安装特定 Python 版本
uv python install 3.12

# 列出已安装的 Python 版本
uv python list
```

## 工作流示例

### 新开发者设置

```bash
# 1. 克隆项目
git clone <repository>
cd working

# 2. 同步虚拟环境
uv sync

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 验证安装
python --version
pip list | grep reflex
```

### 添加新的依赖

```bash
# 1. 添加依赖
uv add new-package

# 2. 自动更新 uv.lock
# (uv 会自动更新 uv.lock 文件)

# 3. 提交更改
git add pyproject.toml uv.lock
git commit -m "Add new-package dependency"
```

### 更新所有依赖

```bash
# 1. 更新所有依赖并重新生成 uv.lock
uv sync --upgrade

# 2. 运行测试确保兼容性
uv run pytest

# 3. 提交更改
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
```

### 运行测试和检查

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_db.py

# 运行带覆盖率的测试
uv run pytest --cov

# 代码格式化
uv run black .

# 导入排序
uv run isort .

# 代码质量检查
uv run flake8 src/
```

## 虚拟环境结构

```
.venv/                      # uv 管理的虚拟环境
├── bin/                     # 可执行文件
│   ├── python               # Python 解释器
│   ├── pip                  # pip 命令
│   ├── activate             # 激活脚本 (Bash/Zsh)
│   ├── activate.fish        # 激活脚本 (Fish)
│   └── Activate.ps1         # 激活脚本 (PowerShell)
├── lib/                     # Python 包
│   └── python3.12/
│       └── site-packages/   # 已安装的包
├── include/                 # 包含文件
├── pyvenv.cfg               # 虚拟环境配置
├── .lock                    # uv 锁文件
└── .gitignore               # Git 忽略文件
```

## 重要文件

| 文件 | 用途 |
|------|------|
| `pyproject.toml` | 项目配置和依赖声明 |
| `uv.lock` | 锁定的依赖版本（必须提交到 Git） |
| `.venv/` | 虚拟环境目录（不提交到 Git） |

## 与 pip 的区别

### 安装依赖

```bash
# pip
pip install -r requirements.txt
pip freeze > requirements.txt

# uv
uv sync
# uv 自动从 pyproject.toml 读取依赖
```

### 添加依赖

```bash
# pip
pip install package_name
# 手动更新 requirements.txt

# uv
uv add package_name
# 自动更新 pyproject.toml 和 uv.lock
```

### 创建虚拟环境

```bash
# pip
python -m venv .venv
source .venv/bin/activate

# uv
uv sync
# 虚拟环境自动创建
```

## 性能对比

```
操作              | pip    | uv
----------------|--------|--------
安装依赖         | ~60s   | ~6s
更新依赖         | ~45s   | ~4s
解析依赖冲突     | ~30s   | ~1s
```

## 常见问题

### Q: uv.lock 应该提交到 Git 吗？

**A:** 是的，`uv.lock` 应该提交到 Git。它确保所有开发者和 CI/CD 使用相同的依赖版本。

### Q: 如何在 CI/CD 中使用 uv？

**A:** 在 CI/CD 中只需要运行 `uv sync`，它会自动读取 `uv.lock` 文件并安装精确的依赖版本。

```yaml
# GitHub Actions 示例
- name: Install dependencies
  run: uv sync
```

### Q: 如何处理平台特定的依赖？

**A:** uv 自动处理平台特定的依赖。在 `pyproject.toml` 中可以使用 `markers` 指定条件：

```toml
dependencies = [
    'pywin32>=300 ; sys_platform == "win32"',
    'gnureadline ; sys_platform == "darwin"',
]
```

### Q: 如何升级特定的包？

**A:** 使用 `--upgrade-package` 选项：

```bash
uv sync --upgrade-package sqlalchemy
```

### Q: 虚拟环境在哪里？

**A:** 默认在项目根目录的 `.venv/` 文件夹中。

### Q: 如何删除虚拟环境？

**A:** 直接删除 `.venv/` 文件夹，使用 `uv sync` 时会自动重新创建。

```bash
rm -rf .venv
uv sync  # 重新创建虚拟环境
```

### Q: 如何使用不同的 Python 版本？

**A:** 在 `pyproject.toml` 中指定，或使用 `uv python install`：

```bash
# 安装 Python 3.11
uv python install 3.11

# 使用特定 Python 版本运行
uv run --python 3.11 script.py
```

## 故障排除

### 硬链接警告

```
warning: Failed to hardlink files; falling back to full copy.
```

**解决方案**: 设置环境变量告诉 uv 使用复制模式：

```bash
export UV_LINK_MODE=copy
uv sync
```

### 虚拟环境损坏

**解决方案**: 删除并重新创建：

```bash
rm -rf .venv
uv sync
```

### 依赖冲突

**解决方案**: 更新所有依赖到兼容版本：

```bash
uv sync --upgrade
```

## 资源链接

- [uv 官方文档](https://docs.astral.sh/uv/)
- [uv GitHub 仓库](https://github.com/astral-sh/uv)
- [pyproject.toml 规范](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [PEP 517 - 构建后端](https://peps.python.org/pep-0517/)

## 最佳实践

1. **提交 uv.lock**: 始终提交 `uv.lock` 到 Git
2. **不提交 .venv**: `.venv/` 应该在 `.gitignore` 中
3. **定期更新**: 定期运行 `uv sync --upgrade` 更新依赖
4. **使用版本约束**: 在 `pyproject.toml` 中指定版本范围

```toml
dependencies = [
    "package>=1.0.0,<2.0.0",  # 兼容版本
    "another-package==1.2.3",  # 精确版本
]
```

5. **分离开发依赖**: 使用 `[project.optional-dependencies]` 分离开发依赖

---

**更新时间**: 2025-10-27
**uv 版本**: 0.9.2+
