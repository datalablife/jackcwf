#!/usr/bin/env bash
#
# 脚本名称: create-directory-structure.sh
# 描述: 创建完整的文件归档系统目录结构
# 用法: ./create-directory-structure.sh
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
cd "$ROOT_DIR"

echo "======================================"
echo "  创建文件归档系统目录结构"
echo "======================================"
echo ""

# 创建 docs 目录结构
echo "1. 创建 docs/ 目录结构..."
mkdir -p docs/{api/{endpoints,schemas,errors},architecture/{diagrams,decisions},guides/{user,developer,operations},deployment,integrations,reference,changelog/versions,archived,templates}
echo "   ✓ docs/ 目录创建完成"

# 创建 scripts 目录结构
echo "2. 创建 scripts/ 目录结构..."
mkdir -p scripts/{dev,test,deploy,maintenance,tools,database,ci,utils,templates}
echo "   ✓ scripts/ 目录创建完成"

# 创建 tests 目录结构
echo "3. 创建 tests/ 目录结构..."
mkdir -p tests/{unit,integration,e2e,fixtures}
echo "   ✓ tests/ 目录创建完成"

# 创建其他必要目录
echo "4. 创建其他必要目录..."
mkdir -p .temp
mkdir -p logs
echo "   ✓ 其他目录创建完成"

# 创建 README.md 文件
echo ""
echo "5. 创建索引文件..."

# docs/README.md
cat > docs/README.md << 'EOF'
# 项目文档

欢迎查阅项目文档。本文档系统按功能和受众组织，方便快速找到所需信息。

## 快速导航

### 🚀 快速开始
- [用户快速开始](guides/user/getting-started.md)
- [开发环境搭建](guides/developer/setup.md)

### 📚 主要文档类别

#### API 文档
- [API 概览](api/README.md)
- [端点文档](api/endpoints/)
- [数据模型](api/schemas/)
- [错误码](api/errors/)

#### 架构设计
- [系统架构](architecture/system-overview.md)
- [数据库设计](architecture/database-schema.md)
- [组件设计](architecture/component-design.md)
- [架构决策记录](architecture/decisions/)

#### 使用指南
- [用户指南](guides/user/)
- [开发者指南](guides/developer/)
- [运维指南](guides/operations/)

#### 部署
- [部署概览](deployment/README.md)
- [生产环境部署](deployment/production.md)
- [Coolify 部署](deployment/coolify.md)

#### 集成
- [PostgreSQL](integrations/postgresql-connection.md)
- [ChromeDevTools MCP](integrations/chrome-devtools.md)
- [CrewAI 代码审查](integrations/crewai.md)

### 📖 参考资料
- [配置参考](reference/configuration.md)
- [环境变量](reference/environment-variables.md)
- [CLI 命令](reference/cli-commands.md)
- [uv 使用指南](reference/uv-guide.md)

### 📝 变更记录
- [CHANGELOG](changelog/CHANGELOG.md)

## 文档贡献

请参阅 [贡献指南](guides/developer/contributing.md) 了解如何贡献文档。

## 文档规范

- **文件命名**: 小写，连字符分隔（如 `getting-started.md`）
- **格式**: Markdown
- **版本控制**: 通过 Git 管理
- **更新频率**: 随代码变更同步更新
EOF
echo "   ✓ 创建 docs/README.md"

# scripts/README.md
cat > scripts/README.md << 'EOF'
# 项目脚本

本目录包含项目开发、测试、部署和维护所需的所有自动化脚本。

## 目录结构

```
scripts/
├── dev/           # 开发辅助脚本
├── test/          # 测试相关脚本
├── deploy/        # 部署脚本
├── maintenance/   # 维护脚本
├── tools/         # 工具脚本
├── database/      # 数据库管理
├── ci/            # CI/CD 脚本
└── utils/         # 通用工具函数
```

## 快速使用

### 开发环境

```bash
# 初始化开发环境
./scripts/dev/setup-env.sh

# 清理缓存
./scripts/dev/clean-cache.sh
```

### 测试

```bash
# 运行所有测试
./scripts/test/run-all-tests.sh

# 生成覆盖率报告
./scripts/test/run-all-tests.sh --coverage
```

### 工具

```bash
# 代码审查
./scripts/tools/code-review.sh <file>

# 检查文件组织
./scripts/tools/check-file-organization.sh

# 自动整理文件
./scripts/tools/organize-files.sh
```

## 脚本规范

所有脚本遵循以下规范：

1. **Shebang**: `#!/usr/bin/env bash` 或 `#!/usr/bin/env python3`
2. **权限**: 可执行脚本设置 `chmod +x`
3. **错误处理**: 使用 `set -euo pipefail`
4. **日志**: 提供清晰的输出和错误信息
5. **文档**: 脚本头部包含用法说明

## 添加新脚本

1. 确定脚本类别，放入对应子目录
2. 使用描述性命名（动词开头，小写，连字符分隔）
3. 添加脚本头部注释
4. 设置执行权限：`chmod +x script-name.sh`
5. 测试脚本功能
6. 更新本 README

## 故障排除

如脚本执行失败：

1. 检查权限：`ls -l scripts/path/to/script.sh`
2. 查看日志输出
3. 验证环境变量
4. 检查依赖工具是否安装

详见 [故障排除指南](../docs/guides/operations/troubleshooting.md)
EOF
echo "   ✓ 创建 scripts/README.md"

# 创建子目录 README
create_subdir_readme() {
    local dir=$1
    local title=$2
    local description=$3

    cat > "$dir/README.md" << EOF
# $title

$description

## 脚本列表

待添加...

## 使用说明

待添加...
EOF
}

create_subdir_readme "docs/api" "API 文档" "REST API、GraphQL 或 WebSocket 接口文档"
create_subdir_readme "docs/architecture" "架构设计文档" "系统架构、设计决策和技术选型文档"
create_subdir_readme "docs/guides" "使用指南" "分类存储不同受众的操作指南"
create_subdir_readme "docs/deployment" "部署文档" "所有环境的部署指南和配置"
create_subdir_readme "docs/integrations" "集成文档" "与外部系统、服务和工具的集成"
create_subdir_readme "docs/reference" "参考文档" "快速查询的参考资料"
create_subdir_readme "docs/changelog" "变更日志" "项目历史和版本变更"
create_subdir_readme "docs/archived" "归档文档" "过期但保留参考价值的文档"

echo "   ✓ 创建子目录 README 文件"

# 创建 ADR 模板
cat > docs/architecture/decisions/template.md << 'EOF'
# ADR-XXX: [简短标题]

## 状态

[提议 | 已接受 | 已废弃 | 已替代]

## 上下文

描述需要做出决策的背景和问题。

## 决策

我们决定...

## 后果

### 优点

- 优点 1
- 优点 2

### 缺点

- 缺点 1
- 缺点 2

### 风险

- 风险 1
- 风险 2

## 替代方案

我们考虑过但未采用的其他方案：

1. 方案 A - 原因...
2. 方案 B - 原因...

## 相关资源

- [相关文档链接]
- [参考资料]

---

**日期**: YYYY-MM-DD
**作者**: [姓名]
**审阅者**: [姓名列表]
EOF
echo "   ✓ 创建 ADR 模板"

# 创建 CHANGELOG 模板
cat > docs/changelog/CHANGELOG.md << 'EOF'
# 变更日志

本项目的所有重要变更都将记录在此文件中。

本格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- 文件归档系统

### 变更

### 废弃

### 移除

### 修复

### 安全

## [0.1.0] - 2025-10-27

### 新增
- 初始版本
EOF
echo "   ✓ 创建 CHANGELOG 模板"

# 创建 tests/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
echo "   ✓ 创建测试目录 __init__.py 文件"

# 创建 .temp/.gitkeep
cat > .temp/.gitkeep << 'EOF'
# 此目录用于临时文件
# 所有内容会被 .gitignore 忽略
EOF
echo "   ✓ 创建 .temp/.gitkeep"

# 显示目录树
echo ""
echo "======================================"
echo "  目录结构创建完成！"
echo "======================================"
echo ""
echo "docs/ 目录结构:"
tree -L 2 docs/ -I '__pycache__|*.pyc'
echo ""
echo "scripts/ 目录结构:"
tree -L 2 scripts/ -I '__pycache__|*.pyc'
echo ""
echo "tests/ 目录结构:"
tree -L 2 tests/ -I '__pycache__|*.pyc'
echo ""

echo "✅ 所有目录和索引文件创建完成！"
echo ""
echo "下一步："
echo "1. 查看 FILE_ORGANIZATION_SYSTEM.md 了解详细说明"
echo "2. 查看 IMPLEMENTATION_CHECKLIST.md 完成剩余实施步骤"
echo "3. 查看 QUICK_REFERENCE.md 作为快速参考"
echo "4. 运行 ./migrate-files.sh 迁移现有文件"
echo ""
