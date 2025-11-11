# Memori 与 Claude API 集成文档

本目录包含 Memori 内存管理系统与 Anthropic Claude API 集成的完整文档。

## 📚 文档结构

### 🚀 快速开始
**[MEMORI_QUICKSTART.md](./MEMORI_QUICKSTART.md)** - 5分钟快速开始指南
- 环境设置步骤
- 核心概念速览
- 常见任务示例
- API 端点速查表
- 环境变量参考
- 调试技巧
- 常见问题

**建议对象**: 新用户、快速上手

---

### 📖 完整集成指南
**[MEMORI_INTEGRATION_GUIDE.md](./MEMORI_INTEGRATION_GUIDE.md)** - 详细的集成参考（1200+ 行）

#### 内容包括：
- **架构概览** - 系统设计和组件交互
- **安装配置** - 依赖安装和环境配置
- **核心模块说明** - 四个主要模块的详细说明
  - MemoriConfig - 配置管理
  - MemoryManager - 内存管理器
  - ClaudeIntegrationService - Claude 集成
  - Memory API - RESTful 端点
- **API 端点详解** - 8 个完整端点的请求/响应示例
- **使用场景** - 4 个实际应用场景
- **记忆类型和重要性评分指南**
- **性能优化建议**
- **监控和调试**
- **故障排除** - 常见问题和解决方案
- **最佳实践** - 生产级建议
- **后续开发计划**

**建议对象**: 开发者、架构师、运维人员

---

### ✅ 实现总结和检查清单
**[MEMORI_IMPLEMENTATION_SUMMARY.md](./MEMORI_IMPLEMENTATION_SUMMARY.md)** - 项目实现概览（700+ 行）

#### 内容包括：
- **项目概述** - 总体完成情况
- **实现完成情况** - 模块、数据库、API、文档清单
- **架构亮点** - 关键设计特性
- **关键特性** - 功能总结
- **使用示例** - 代码片段
- **文件结构** - 项目文件组织
- **集成点** - 与 FastAPI 的集成方式
- **部署检查清单** - 开发/测试/生产环节
- **性能指标** - 推荐配置
- **监控 KPI** - 关键指标
- **下一步建议** - 短中长期规划
- **技术债务和限制** - 已知问题
- **支持和维护** - 日常维护任务

**建议对象**: 项目经理、运维人员、质量保证

---

## 🗂️ 相关代码文件

### 后端实现
- `backend/src/memory/config.py` - Memori 配置管理
- `backend/src/memory/manager.py` - 内存管理器
- `backend/src/services/claude_integration.py` - Claude 集成服务
- `backend/src/api/memory.py` - 内存管理 API 端点
- `backend/src/main.py` - 应用启动（已集成）

### 数据库
- `backend/migrations/versions/002_add_memori_memory_tables.py` - 数据库迁移脚本
- `backend/.env.example` - 环境变量示例（已更新）
- `backend/pyproject.toml` - 项目依赖（已更新）

### 测试和示例
- `backend/tests/test_memory_integration.py` - 集成测试
- `backend/examples/memori_integration_example.py` - 可运行示例（6 个场景）

---

## 🎯 快速导航

### 对于不同角色

#### 👤 新开发者
推荐阅读顺序：
1. [MEMORI_QUICKSTART.md](./MEMORI_QUICKSTART.md) - 了解基础
2. [backend/examples/memori_integration_example.py](../../backend/examples/memori_integration_example.py) - 看代码示例
3. [MEMORI_INTEGRATION_GUIDE.md](./MEMORI_INTEGRATION_GUIDE.md) - 深入学习

#### 🏗️ 架构师
推荐阅读：
1. [MEMORI_INTEGRATION_GUIDE.md - 架构概览](./MEMORI_INTEGRATION_GUIDE.md#架构概览)
2. [MEMORI_IMPLEMENTATION_SUMMARY.md - 架构亮点](./MEMORI_IMPLEMENTATION_SUMMARY.md#架构亮点)
3. [MEMORI_INTEGRATION_GUIDE.md - 核心模块说明](./MEMORI_INTEGRATION_GUIDE.md#核心模块说明)

#### 🔧 运维人员
推荐阅读：
1. [MEMORI_QUICKSTART.md - 快速开始](./MEMORI_QUICKSTART.md#5-分钟快速开始)
2. [MEMORI_IMPLEMENTATION_SUMMARY.md - 部署清单](./MEMORI_IMPLEMENTATION_SUMMARY.md#部署检查清单)
3. [MEMORI_INTEGRATION_GUIDE.md - 监控和调试](./MEMORI_INTEGRATION_GUIDE.md#监控和调试)

#### 📊 项目经理
推荐阅读：
1. [MEMORI_IMPLEMENTATION_SUMMARY.md - 项目概述](./MEMORI_IMPLEMENTATION_SUMMARY.md#项目概述)
2. [MEMORI_IMPLEMENTATION_SUMMARY.md - 实现完成情况](./MEMORI_IMPLEMENTATION_SUMMARY.md#实现完成情况)
3. [MEMORI_IMPLEMENTATION_SUMMARY.md - 下一步建议](./MEMORI_IMPLEMENTATION_SUMMARY.md#下一步建议)

---

## 📋 快速参考

### API 端点速查

```
添加记忆      POST   /api/memory/add
搜索记忆      POST   /api/memory/search
搜索（GET）   GET    /api/memory/search?query=...
对话上下文    GET    /api/memory/context/{id}
系统统计      GET    /api/memory/stats
清理记忆      DELETE /api/memory/clear
Claude 消息   POST   /api/memory/claude/message
健康检查      GET    /api/memory/health
```

详见：[MEMORI_INTEGRATION_GUIDE.md - API 端点](./MEMORI_INTEGRATION_GUIDE.md#api-端点)

### 记忆类型

| 类型 | 用途 | 重要性 |
|------|------|--------|
| `short_term` | 当前会话临时信息 | 0.3-0.6 |
| `long_term` | 跨会话持久化信息 | 0.5-0.9 |
| `rule` | 系统约束和准则 | 0.7-1.0 |
| `entity` | 命名实体和引用 | 0.4-0.8 |

### 环境变量关键配置

```env
ANTHROPIC_API_KEY=sk-...           # Claude API 密钥（必需）
MEMORI_DB_TYPE=sqlite              # 开发用 SQLite
MEMORI_SQLITE_PATH=./memori.db     # 数据库文件路径
MEMORI_CONSCIOUS_INGEST=true       # 启用持久化上下文
MEMORI_AUTO_INGEST=true            # 启用动态上下文注入
```

详见：[MEMORI_QUICKSTART.md - 环境变量参考](./MEMORI_QUICKSTART.md#环境变量参考)

---

## 🚀 立即开始

### 1. 5 分钟快速开始
```bash
# 进入后端目录
cd backend

# 复制环境配置
cp .env.example .env

# 编辑 .env，设置 ANTHROPIC_API_KEY

# 安装依赖
poetry install

# 运行数据库迁移
alembic upgrade head

# 启动应用
python -m src.main
```

### 2. 测试 API
```bash
# 查看内存统计
curl http://localhost:8000/api/memory/stats
```

详见：[MEMORI_QUICKSTART.md - 5 分钟快速开始](./MEMORI_QUICKSTART.md#5-分钟快速开始)

---

## 📚 文档统计

| 文档 | 大小 | 内容 |
|------|------|------|
| MEMORI_QUICKSTART.md | ~8.5 KB | 快速参考指南 |
| MEMORI_INTEGRATION_GUIDE.md | ~18 KB | 完整集成指南 |
| MEMORI_IMPLEMENTATION_SUMMARY.md | ~11 KB | 实现总结 |
| **总计** | **~37.5 KB** | **3000+ 行文档** |

---

## ✅ 功能完成清单

### 后端集成
- ✅ Memori 配置管理模块
- ✅ 内存管理器（CRUD、搜索、统计）
- ✅ Claude API 集成服务
- ✅ 8 个 RESTful API 端点
- ✅ 数据库迁移脚本
- ✅ 集成测试
- ✅ 可运行示例

### 文档
- ✅ 快速开始指南
- ✅ 完整集成指南
- ✅ 实现总结
- ✅ 代码示例
- ✅ API 文档
- ✅ 故障排除指南

### 配置
- ✅ 依赖更新
- ✅ 环境变量配置
- ✅ 多数据库支持
- ✅ 性能参数配置

---

## 🔗 外部资源

- [Memori 官方仓库](https://github.com/GibsonAI/Memori)
- [Memori 文档](https://memori.readthedocs.io/)
- [Anthropic Claude 文档](https://docs.anthropic.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 📞 获取帮助

1. **快速问题** → 查看 [MEMORI_QUICKSTART.md](./MEMORI_QUICKSTART.md)
2. **实现细节** → 查看 [MEMORI_INTEGRATION_GUIDE.md](./MEMORI_INTEGRATION_GUIDE.md)
3. **部署问题** → 查看 [MEMORI_IMPLEMENTATION_SUMMARY.md](./MEMORI_IMPLEMENTATION_SUMMARY.md)
4. **代码示例** → 查看 [示例代码](../../backend/examples/memori_integration_example.py)
5. **运行测试** → 查看 [测试代码](../../backend/tests/test_memory_integration.py)

---

## 📝 主文档索引

**主索引文件**: [../../CLAUDE.md](../../CLAUDE.md)

CLAUDE.md 是项目根目录的主索引文件，包含：
- Memori 系统的完整导航
- 所有文档的链接
- API 快速参考
- 使用场景
- 部署清单
- 学习路径

---

**最后更新**: 2024-11-12
**状态**: 生产就绪 ✅
**版本**: 1.0.0
