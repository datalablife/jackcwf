# Coolify 部署文档完整索引

**更新日期**: 2025-10-30
**文档总数**: 12 个完整指南
**适用版本**: Reflex 0.8.16+, Coolify 4.0.0+

---

## 🎯 快速导航 (CI/CD Agents)

### 我需要...

#### 立即解决部署问题
1. **[QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md)** - 5分钟快速修复指南
   - 常见错误和快速解决方案
   - 快速检查清单

2. **[COOLIFY_FIX_REPORT.md](./COOLIFY_FIX_REPORT.md)** - 完整的错误诊断报告
   - 7个部署错误的详细分析
   - 根本原因和修复方案

#### 理解标准部署流程
1. **[START_HERE.md](./START_HERE.md)** - 新手入门指南
   - 项目概览
   - 部署流程概述

2. **[COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md)** - 标准部署规范
   - 生产环境标准流程
   - 检查清单和自动化脚本
   - CI/CD 代理任务模板

#### 学习最佳实践
1. **[REFLEX_COOLIFY_BEST_PRACTICES.md](./REFLEX_COOLIFY_BEST_PRACTICES.md)** - 最佳实践指南
   - 应用配置标准
   - 性能优化建议
   - 安全配置指南

#### 配置健康检查
1. **[COOLIFY_CONFIG.md](./COOLIFY_CONFIG.md)** - 配置详解
   - 健康检查配置（最关键！）
   - 环境变量设置
   - Web UI 操作步骤

#### 诊断和故障排除
1. **[DEPLOYMENT_DIAGNOSIS.md](./DEPLOYMENT_DIAGNOSIS.md)** - 诊断工具
   - 故障排除决策树
   - 日志分析方法

2. **[COOLIFY_GIT_INTEGRATION.md](./COOLIFY_GIT_INTEGRATION.md)** - Git 集成指南
   - GitHub 仓库配置
   - Coolify CLI 使用

---

## 📚 完整文档目录

### 核心报告（生产部署重点）

| 文档 | 大小 | 用途 | 优先级 |
|------|------|------|--------|
| **COOLIFY_FIX_REPORT.md** | 17KB | 完整的错误诊断和修复 | ⭐⭐⭐ |
| **COOLIFY_DEPLOYMENT_STANDARDS.md** | 21KB | 标准部署流程和规范 | ⭐⭐⭐ |
| **REFLEX_COOLIFY_BEST_PRACTICES.md** | 19KB | 最佳实践和优化 | ⭐⭐⭐ |
| **COOLIFY_CONFIG.md** | 9.6KB | 配置指南（含健康检查） | ⭐⭐⭐ |

### 快速参考指南

| 文档 | 大小 | 用途 | 优先级 |
|------|------|------|--------|
| **QUICK_FIX_GUIDE.md** | 5.7KB | 5分钟快速解决方案 | ⭐⭐⭐ |
| **START_HERE.md** | 7.4KB | 新手入门指南 | ⭐⭐ |
| **DEPLOYMENT_DIAGNOSIS.md** | 11KB | 故障诊断工具 | ⭐⭐ |

### 工作流程指南

| 文档 | 大小 | 用途 | 优先级 |
|------|------|------|--------|
| **QUICK_START.md** | 6.5KB | 10分钟快速启动 | ⭐⭐ |
| **COOLIFY_GIT_INTEGRATION.md** | 16KB | Git 和 CLI 配置 | ⭐⭐ |
| **DEPLOYMENT_INDEX.md** | 9.1KB | 旧版文档索引 | ⭐ |
| **ci-cd.md** | 17KB | GitHub Actions 指南 | ⭐ |

---

## 🔑 关键配置三件事

### 1️⃣ Reflex 环境参数
```bash
# ✅ 正确
--env prod

# ❌ 错误（Reflex 0.8.16 不支持）
--env production
```

### 2️⃣ 健康检查初始延迟
```toml
# ✅ 正确（给 Reflex 编译时间）
start_period=120s

# ❌ 错误（太短，总是超时）
start_period=40s
```

### 3️⃣ 系统包配置
```toml
# ✅ 正确（包含 Bun 所需的 unzip）
nixPkgs = ["python312", "nodejs_20", "curl", "git", "unzip"]

# ❌ 错误（缺少 unzip）
nixPkgs = ["python312", "nodejs_20", "curl", "git"]
```

---

## 🚀 常见场景快速路径

### 场景 1：首次部署 Reflex 应用到 Coolify
1. 阅读 [START_HERE.md](./START_HERE.md) (3 min)
2. 查阅 [COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md) 的前置条件部分 (5 min)
3. 按照标准流程操作 (15-20 min)
4. 遇到问题→查看 [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md)

### 场景 2：部署失败，需要快速修复
1. 查看 [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md) (3 min)
2. 如果没找到，查看 [COOLIFY_FIX_REPORT.md](./COOLIFY_FIX_REPORT.md) 第一部分 (10 min)
3. 根据错误类型找到对应的修复方案

### 场景 3：健康检查持续超时
1. 直接查看 [COOLIFY_CONFIG.md](./COOLIFY_CONFIG.md) 健康检查部分 (5 min)
2. 参考 [COOLIFY_FIX_REPORT.md](./COOLIFY_FIX_REPORT.md) - 错误 2 的详细解释 (5 min)
3. 将 `start-period` 改为 120s

### 场景 4：想优化部署性能
1. 查看 [REFLEX_COOLIFY_BEST_PRACTICES.md](./REFLEX_COOLIFY_BEST_PRACTICES.md) 性能优化部分
2. 查看 [COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md) 中的自动化脚本

### 场景 5：设置自动化部署
1. 查看 [COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md) 的自动部署配置
2. 查看 [COOLIFY_GIT_INTEGRATION.md](./COOLIFY_GIT_INTEGRATION.md) 的 GitHub 集成部分
3. 参考 [COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md) 中的 Bash 脚本

---

## 📊 部署错误参考表

根据你遇到的错误，快速查找对应的解决方案：

| 错误 | 文档位置 | 快速修复 |
|------|---------|---------|
| `app.compile()` 不存在 | COOLIFY_FIX_REPORT.md 错误1 | 修复 __main__.py |
| 健康检查超时 | COOLIFY_FIX_REPORT.md 错误2 | start-period 改为 120s |
| Nixpacks 配置失败 | COOLIFY_FIX_REPORT.md 错误3 | 创建 nixpacks.toml |
| 模块导入失败 | COOLIFY_FIX_REPORT.md 错误4-5 | 检查导入路径 |
| `unzip` 缺失 | COOLIFY_FIX_REPORT.md 错误6 | 添加到 nixPkgs |
| `--env production` 无效 | COOLIFY_FIX_REPORT.md 错误7 | 改为 `--env prod` |

---

## 🔗 文档间引用关系

```
START_HERE.md (入门)
    ↓
QUICK_FIX_GUIDE.md (快速解决)
    ↓
COOLIFY_DEPLOYMENT_STANDARDS.md (标准流程)
    ├→ COOLIFY_CONFIG.md (配置详解)
    ├→ REFLEX_COOLIFY_BEST_PRACTICES.md (最佳实践)
    └→ COOLIFY_FIX_REPORT.md (深入分析)
         ↓
    DEPLOYMENT_DIAGNOSIS.md (故障诊断)

COOLIFY_GIT_INTEGRATION.md (Git 和 CLI)
    ↓
ci-cd.md (GitHub Actions)
```

---

## 📋 CI/CD 代理快速参考

### 部署前检查 (5 min)
```
1. 代码已提交到 GitHub main ✓
2. 所有单元测试通过 ✓
3. Dockerfile --env 使用 prod ✓
4. nixpacks.toml 包含 unzip ✓
5. __main__.py 格式正确 ✓

查看: COOLIFY_DEPLOYMENT_STANDARDS.md 部分 I
```

### 标准部署流程 (20 min)
```
1. 验证前置条件 (5 min)
2. 推送到 GitHub (2 min)
3. 触发 Coolify 部署 (3 min)
4. 等待初始化 (120s)
5. 验证部署成功 (5 min)

查看: COOLIFY_DEPLOYMENT_STANDARDS.md 部分 E
```

### 故障排除流程
```
1. 收集错误日志
2. 查看错误参考表（本文档）
3. 查找对应的解决方案
4. 执行修复
5. 重新部署

查看: QUICK_FIX_GUIDE.md 或 DEPLOYMENT_DIAGNOSIS.md
```

---

## 🎓 文档学习路径

### 路径 1：快速上手 (30 min)
1. START_HERE.md (7 min)
2. QUICK_FIX_GUIDE.md (5 min)
3. COOLIFY_DEPLOYMENT_STANDARDS.md - 前置条件部分 (8 min)
4. COOLIFY_CONFIG.md - 健康检查部分 (5 min)

### 路径 2：深入理解 (1.5 hours)
1. 完整阅读 COOLIFY_DEPLOYMENT_STANDARDS.md (25 min)
2. 完整阅读 REFLEX_COOLIFY_BEST_PRACTICES.md (20 min)
3. 完整阅读 COOLIFY_FIX_REPORT.md (20 min)
4. 查阅 COOLIFY_CONFIG.md (15 min)

### 路径 3：精通部署 (2.5 hours)
1. 所有核心文档 (见路径2)
2. COOLIFY_GIT_INTEGRATION.md (15 min)
3. DEPLOYMENT_DIAGNOSIS.md (10 min)
4. 实践操作和测试 (30 min)

---

## 🔒 重要安全信息

- **API Token**: 包含特殊字符，用单引号包裹：`'2|TZO...'`
- **敏感信息**: 使用环境变量存储，不要硬编码
- **Health Check**: 必须设置 120s 初始延迟
- **生产环境**: 始终使用 `--env prod`

详见: REFLEX_COOLIFY_BEST_PRACTICES.md 安全部分

---

## 📞 获取帮助

### 问题排查步骤
1. **快速查找**: 使用本索引页的"按错误查找"表
2. **快速解决**: 查看 QUICK_FIX_GUIDE.md
3. **深入分析**: 查看 COOLIFY_FIX_REPORT.md
4. **诊断工具**: 使用 DEPLOYMENT_DIAGNOSIS.md

### 常见问题速查
- **"健康检查失败"** → COOLIFY_CONFIG.md 或 COOLIFY_FIX_REPORT.md 错误2
- **"构建错误"** → COOLIFY_FIX_REPORT.md 按错误类型查找
- **"如何自动部署"** → COOLIFY_DEPLOYMENT_STANDARDS.md 部分E2
- **"如何优化性能"** → REFLEX_COOLIFY_BEST_PRACTICES.md

---

## 📈 文档统计

| 指标 | 值 |
|------|-----|
| **总文档数** | 12 个 |
| **总字数** | ~100,000+ 字 |
| **总大小** | 172 KB |
| **覆盖的错误** | 7 个 |
| **包含脚本** | 3 个 (Bash) |
| **检查清单** | 10+ 个 |
| **代码示例** | 50+ 个 |

---

## 🎯 下一步

1. **首次使用**: 阅读 [START_HERE.md](./START_HERE.md)
2. **遇到问题**: 查看 [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md)
3. **深入学习**: 选择相应的学习路径
4. **自动化部署**: 使用 [COOLIFY_DEPLOYMENT_STANDARDS.md](./COOLIFY_DEPLOYMENT_STANDARDS.md) 中的脚本

---

**维护者**: Claude Code AI Assistant
**最后更新**: 2025-10-30
**部署状态**: ✅ 生产环境成功部署

🚀 祝你部署顺利！
