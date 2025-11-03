# 📚 文档索引和快速导航

本项目包含完整的开发文档。本文件帮助您快速找到所需信息。

---

## 🚀 快速开始

**新来的开发者?** 按这个顺序阅读:

1. **[README.md](./README.md)** (5 分钟)
   - 项目概览
   - 技术栈
   - 快速启动步骤

2. **[DEVELOPMENT_ENVIRONMENT_SUMMARY.md](./DEVELOPMENT_ENVIRONMENT_SUMMARY.md)** (10 分钟)
   - 环境配置完整总结
   - 工作流程
   - 常用命令表

3. **[REFLEX_WITH_UV.md](./REFLEX_WITH_UV.md)** (当需要启动开发服务器时)
   - Reflex 框架详解
   - uv 集成方法
   - 全部启动命令

4. **[REFLEX_TROUBLESHOOTING.md](./REFLEX_TROUBLESHOOTING.md)** (遇到问题时)
   - 常见问题和解决方案
   - 性能优化建议

---

## 📖 按主题分类的文档

### 核心项目文档

| 文档 | 大小 | 用途 | 优先级 |
|------|------|------|--------|
| **README.md** | 6.4 KB | 项目概览和快速开始 | ⭐⭐⭐ 必读 |
| **DEVELOPMENT_ENVIRONMENT_SUMMARY.md** | 8.1 KB | 完整环境配置总结 | ⭐⭐⭐ 必读 |
| **CLAUDE.md** | 12.5 KB | Claude Code 项目规则 (包含 Coolify CLI) | ⭐⭐ 参考 |

### Reflex 框架相关

| 文档 | 大小 | 内容 | 适用场景 |
|------|------|------|---------|
| **REFLEX_WITH_UV.md** | 9.8 KB | Reflex + uv 集成完全指南 | 框架开发 |
| **REFLEX_TROUBLESHOOTING.md** | 5.2 KB | 故障排除和问题诊断 | 遇到问题 |

### PostgreSQL 数据库相关

| 文档 | 大小 | 内容 | 适用场景 |
|------|------|------|---------|
| **POSTGRESQL_QUICK_START.md** | 3.4 KB | 1 分钟快速参考 | 快速查询 |
| **POSTGRESQL_CONNECTION.md** | 7.6 KB | 详细连接指南 (6 种方式) | 深入了解 |

### 包管理相关

| 文档 | 大小 | 内容 | 适用场景 |
|------|------|------|---------|
| **UV_GUIDE.md** | 7.6 KB | uv 包管理器完全指南 | 依赖管理 |

### 脚本和工具

| 文件 | 类型 | 用途 |
|------|------|------|
| **test_postgres_connection.py** | Python | 数据库连接测试 |
| **coolify_postgres_manage.sh** | Bash | PostgreSQL 管理脚本 |

---

## 🎯 按使用场景查找文档

### 场景 1: 第一次启动项目

```
1. README.md (了解项目)
   ↓
2. DEVELOPMENT_ENVIRONMENT_SUMMARY.md (查看快速开始)
   ↓
3. uv run reflex run (启动服务器)
   ↓
4. 打开 http://localhost:3000
```

### 场景 2: 启动开发服务器时遇到问题

```
1. REFLEX_TROUBLESHOOTING.md (问题 1: Worker 重启循环)
   ↓
2. 执行建议的清理命令
   ↓
3. 重新启动
```

### 场景 3: 需要处理数据库

```
1. POSTGRESQL_QUICK_START.md (快速参考)
   ↓
2. python test_postgres_connection.py (测试连接)
   ↓
3. POSTGRESQL_CONNECTION.md (需要更多信息)
```

### 场景 4: 添加新的依赖包

```
1. UV_GUIDE.md (查看如何使用 uv)
   ↓
2. uv add package_name
   ↓
3. git add pyproject.toml uv.lock
   ↓
4. git commit -m "Add package description"
```

### 场景 5: 使用 Coolify CLI 管理应用

```
1. CLAUDE.md (Coolify CLI 管理规则 - 第 160-321 行)
   ↓
2. coolify context list (查看已配置的上下文)
   ↓
3. coolify app list (列出应用)
```

---

## 🔍 按关键词快速查找

### 虚拟环境和依赖
- **uv 是什么?** → README.md (第 10-27 行)
- **如何添加依赖?** → UV_GUIDE.md (第 12-16 行)
- **如何更新所有依赖?** → UV_GUIDE.md (第 15 行)
- **pyproject.toml 是什么?** → DEVELOPMENT_ENVIRONMENT_SUMMARY.md (虚拟环境部分)

### Reflex 框架
- **如何启动应用?** → README.md (第 59-71 行)
- **Reflex 命令有哪些?** → REFLEX_WITH_UV.md (命令参考)
- **前后端分离启动** → REFLEX_WITH_UV.md 或 REFLEX_TROUBLESHOOTING.md (方案 C)
- **端口规范** → CLAUDE.md (第 578-608 行) 或 DEVELOPMENT_ENVIRONMENT_SUMMARY.md

### 数据库
- **PostgreSQL 连接字符串** → POSTGRESQL_CONNECTION.md (第 1-50 行)
- **测试数据库连接** → test_postgres_connection.py
- **6 种连接方式** → POSTGRESQL_CONNECTION.md (第 51-200 行)
- **数据库管理** → coolify_postgres_manage.sh

### 问题排除
- **Worker 重启循环** → REFLEX_TROUBLESHOOTING.md (问题 1)
- **端口占用 3000/8000** → REFLEX_TROUBLESHOOTING.md (问题 3)
- **编译失败** → REFLEX_TROUBLESHOOTING.md (问题 4)
- **数据库连接失败** → REFLEX_TROUBLESHOOTING.md (问题 5)

### Coolify
- **配置 Coolify CLI** → CLAUDE.md (第 160-180 行)
- **使用 Coolify CLI 命令** → CLAUDE.md (第 184-204 行)
- **查看应用日志** → coolify_postgres_manage.sh

---

## 📋 文档清单

### 必读文档 (项目成功的基础)
- [ ] README.md - 项目概览
- [ ] DEVELOPMENT_ENVIRONMENT_SUMMARY.md - 环境总结
- [ ] REFLEX_WITH_UV.md - 框架指南

### 参考文档 (需要时查阅)
- [ ] CLAUDE.md - 项目规则
- [ ] REFLEX_TROUBLESHOOTING.md - 问题排除
- [ ] POSTGRESQL_CONNECTION.md - 数据库详解
- [ ] UV_GUIDE.md - 包管理详解

### 快速参考 (常用速查)
- [ ] POSTGRESQL_QUICK_START.md - 数据库速查
- [ ] DOCUMENTATION_INDEX.md - 本文件

---

## 🛠️ 常用命令速查表

### 启动应用
```bash
uv run reflex run                    # 完整应用
uv run reflex run --backend-only     # 仅后端
uv run reflex run --frontend-only    # 仅前端
```

### 管理依赖
```bash
uv sync                              # 同步环境
uv add package_name                  # 添加依赖
uv pip list                          # 列出包
```

### 测试数据库
```bash
source .postgres_config && psql      # 连接数据库
python test_postgres_connection.py   # 连接测试
./coolify_postgres_manage.sh status  # 查看应用状态
```

### 问题排除
```bash
rm -rf .web && uv run reflex run     # 清除缓存后重启
pkill -f "reflex run" -9             # 杀死所有 Reflex 进程
lsof -i :3000 :8000                 # 查看端口占用
```

---

## 📞 获取帮助

### 如果您不确定...

| 问题 | 查看 |
|------|------|
| 项目是干什么的? | README.md |
| 如何启动项目? | DEVELOPMENT_ENVIRONMENT_SUMMARY.md |
| 环境配置有问题 | REFLEX_WITH_UV.md |
| 应用启动失败 | REFLEX_TROUBLESHOOTING.md |
| 数据库连接问题 | POSTGRESQL_CONNECTION.md |
| 如何管理依赖 | UV_GUIDE.md |
| 快速查找命令 | 本文档的"速查表"部分 |

---

## 📊 文档统计

| 类别 | 数量 | 总大小 |
|------|------|--------|
| 核心文档 | 3 | 26.9 KB |
| Reflex 文档 | 2 | 15.0 KB |
| 数据库文档 | 2 | 11.0 KB |
| 包管理文档 | 1 | 7.6 KB |
| 脚本工具 | 2 | - |
| **总计** | **10+** | **60.5 KB** |

---

## 📅 文档更新日期

| 文档 | 最后更新 | 版本 |
|------|---------|------|
| README.md | 2025-10-27 | 2.0 |
| DEVELOPMENT_ENVIRONMENT_SUMMARY.md | 2025-10-27 | 1.0 |
| REFLEX_TROUBLESHOOTING.md | 2025-10-27 | 1.0 |
| CLAUDE.md | 2025-10-27 | 3.0 |
| REFLEX_WITH_UV.md | 2025-10-27 | 2.0 |
| UV_GUIDE.md | 2025-10-27 | 1.0 |
| POSTGRESQL_CONNECTION.md | 2025-10-27 | 2.0 |
| POSTGRESQL_QUICK_START.md | 2025-10-27 | 1.0 |

---

## 💡 使用建议

1. **第一次使用**: 按"快速开始"部分的顺序读
2. **日常开发**: 使用"按场景查找文档"快速导航
3. **遇到问题**: 直接查阅相关的故障排除文档
4. **快速查询**: 使用"按关键词快速查找"部分
5. **收藏本页**: 定期参考本索引了解全局文档结构

---

## 🎓 学习路径

### 初学者 (2 小时)
```
1. README.md (15 分钟) - 了解项目
2. DEVELOPMENT_ENVIRONMENT_SUMMARY.md (30 分钟) - 理解环境
3. 实际操作 (1 小时 15 分钟) - 启动应用，尝试修改代码
```

### 中级开发者 (4 小时)
```
1. REFLEX_WITH_UV.md (1 小时) - 深入框架
2. POSTGRESQL_CONNECTION.md (1 小时) - 数据库集成
3. UV_GUIDE.md (1 小时) - 依赖管理
4. 实际开发 (1 小时) - 编写功能
```

### 高级开发者 (参考资料)
```
1. CLAUDE.md - 项目规则和工作流程
2. REFLEX_TROUBLESHOOTING.md - 性能优化
3. 外部文档 - Reflex/FastAPI/PostgreSQL 官方文档
```

---

## 📝 笔记

- 所有命令都假设您在项目根目录 (`/mnt/d/工作区/云开发/working`)
- 文件大小是近似值，实际可能略有不同
- 文档会定期更新以反映项目状态

---

**最后更新**: 2025-10-27
**维护者**: Jack
**项目状态**: 开发环境就绪 ✅
