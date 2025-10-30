# Reflex Coolify 部署 - 文档索引

> **快速开始**: 如果你只是想快速部署，直接阅读 [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md)（5 分钟）

---

## 文档分类导航

### 🚀 快速开始（新手必读）

**从这里开始 →** [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md) (5.7 KB)
- 5 分钟快速部署指南
- 最小化步骤
- 立即可执行的命令
- 检查清单

**适用场景**:
- ✓ 第一次部署到 Coolify
- ✓ 遇到部署失败，需要快速修复
- ✓ 时间紧迫，需要立即解决问题

---

### 📋 详细配置（完整步骤）

#### [COOLIFY_CONFIG.md](./COOLIFY_CONFIG.md) (9.6 KB)
Coolify 面板配置的完整指南

**内容**:
- Coolify UI 每个设置的详细说明
- 环境变量配置步骤
- 健康检查配置（关键）
- 端口映射和资源限制
- 截图和示例

**适用场景**:
- ✓ 第一次使用 Coolify
- ✓ 需要理解每个配置项的作用
- ✓ 遇到配置问题需要详细参考

**关键章节**:
- 步骤 4: 健康检查配置（最重要！）
- 步骤 2: 环境变量配置
- 步骤 5: 资源限制配置

---

### 🔍 问题诊断（技术深入）

#### [DEPLOYMENT_DIAGNOSIS.md](./DEPLOYMENT_DIAGNOSIS.md) (11 KB)
深入的技术诊断和问题分析

**内容**:
- 根本原因分析
- 技术细节说明
- Reflex 启动流程解析
- Nixpacks 配置详解
- 解决方案对比

**适用场景**:
- ✓ 想了解问题的技术细节
- ✓ 快速修复后仍有问题
- ✓ 需要自定义配置或优化
- ✓ 学习 Reflex/Coolify/Nixpacks

**关键章节**:
- 关键问题分析 → 了解为什么失败
- Reflex 启动流程 → 理解时间需求
- 解决方案 → 三种修复方案

#### [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) (11 KB)
执行摘要和完整总结

**内容**:
- 问题和解决方案总结
- 已创建文件清单
- 部署检查清单
- 预期结果和日志
- 故障排除快速参考

**适用场景**:
- ✓ 需要向团队汇报
- ✓ 记录解决过程
- ✓ 作为参考文档
- ✓ 复盘和学习

---

### 🧪 测试和验证

#### [scripts/test/test-docker-build.sh](./scripts/test/test-docker-build.sh)
本地 Dockerfile 构建测试脚本

**用途**:
- 在本地测试 Docker 构建
- 验证应用可以正常启动
- 检查端口和健康状态
- 查看资源使用

**使用方法**:
```bash
./scripts/test/test-docker-build.sh
```

**测试内容**:
- Docker 镜像构建
- 容器启动（60 秒监控）
- 前端端点测试 (port 3001)
- 后端端点测试 (port 8001)
- 资源使用统计

#### [scripts/test/test-nixpacks-build.sh](./scripts/test/test-nixpacks-build.sh)
本地 Nixpacks 构建测试脚本

**用途**:
- 模拟 Coolify 的 Nixpacks 构建
- 验证 nixpacks.toml 配置
- 测试构建和启动流程
- 复现 Coolify 环境

**前置要求**:
```bash
# 安装 Nixpacks
curl -sSL https://nixpacks.com/install.sh | bash
```

**使用方法**:
```bash
./scripts/test/test-nixpacks-build.sh
```

**测试内容**:
- Nixpacks 构建计划
- 完整构建流程
- 容器启动和监控
- 端点测试 (port 3002, 8002)
- 镜像大小和资源

---

### ⚙️ 配置文件

#### [nixpacks.toml](./nixpacks.toml) (1.1 KB)
Nixpacks 构建配置文件

**关键配置**:
```toml
[phases.setup]
nixPkgs = ["python312", "nodejs_20", "curl", "git"]

[phases.build]
# 前端编译 - 关键步骤
python -m reflex export --frontend-only

[variables]
# 环境变量
PYTHONUNBUFFERED = "1"
REFLEX_ENV = "production"
```

**作用**:
- 定义系统依赖
- 配置构建步骤
- 设置环境变量
- 指定启动命令

#### [start.sh](./start.sh) (1.8 KB)
应用启动脚本（增强版）

**功能**:
- 显示环境信息
- 验证 Reflex 安装
- 检查前端编译产物
- 提供详细日志
- 错误检测

**使用场景**:
- 需要更详细的启动日志
- 调试启动问题
- 验证环境配置

#### [Dockerfile](./Dockerfile) (1.6 KB)
Docker 构建文件（备用方案）

**用途**:
- 当 Nixpacks 有问题时使用
- 完全控制构建流程
- 本地测试

**使用方法**:
在 Coolify 中选择 "Dockerfile" build pack

---

### 📚 项目文档

#### [README.md](./README.md) (8.6 KB)
项目主文档

**内容**:
- 项目概述和技术栈
- 快速开始指南
- 开发工作流
- **新增**: Coolify 部署章节
- 资源链接

**更新内容**:
- ✅ 添加了 Coolify 部署章节
- ✅ 部署文档索引表
- ✅ 本地测试指南
- ✅ 故障排除快速参考

#### [CLAUDE.md](./CLAUDE.md) (36 KB)
Claude Code 项目规则和指南

**内容**:
- 项目架构设计
- 开发工作流程
- MCP 服务器配置
- Coolify CLI 管理规则
- **新增**: Reflex 部署规范

---

## 推荐阅读路径

### 路径 1: 快速部署（最快）

```
1. QUICK_FIX_GUIDE.md      (5 分钟阅读 + 5 分钟执行)
   ↓
2. 执行部署步骤
   ↓
3. 验证成功
```

**时间**: 10-15 分钟
**适合**: 紧急修复，快速上线

---

### 路径 2: 理解后部署（推荐）

```
1. DEPLOYMENT_SUMMARY.md   (10 分钟 - 了解全貌)
   ↓
2. QUICK_FIX_GUIDE.md      (5 分钟 - 执行步骤)
   ↓
3. COOLIFY_CONFIG.md       (15 分钟 - 详细配置)
   ↓
4. 本地测试（可选）
   ↓
5. 执行部署
```

**时间**: 30-40 分钟
**适合**: 第一次部署，希望理解原理

---

### 路径 3: 深入学习（完整）

```
1. DEPLOYMENT_SUMMARY.md       (10 分钟)
   ↓
2. DEPLOYMENT_DIAGNOSIS.md     (20 分钟)
   ↓
3. COOLIFY_CONFIG.md           (15 分钟)
   ↓
4. 本地测试
   - test-docker-build.sh
   - test-nixpacks-build.sh
   ↓
5. 阅读配置文件
   - nixpacks.toml
   - start.sh
   - Dockerfile
   ↓
6. 执行部署并监控
```

**时间**: 1-2 小时
**适合**: 技术深入学习，自定义优化

---

## 故障排除路径

### 问题: 容器立即退出

```
1. 查看 DEPLOYMENT_DIAGNOSIS.md
   → "为什么容器日志为空？" 章节
   ↓
2. 检查 Coolify 应用日志
   coolify app logs mg8c40oowo80o08o0gsw0gwc
   ↓
3. 查看 DEPLOYMENT_SUMMARY.md
   → "故障排除快速参考" 表格
   ↓
4. 运行本地测试
   ./scripts/test/test-nixpacks-build.sh
```

### 问题: 健康检查失败

```
1. 查看 QUICK_FIX_GUIDE.md
   → "问题：健康检查还是失败" 章节
   ↓
2. 确认 COOLIFY_CONFIG.md
   → "步骤 4: 健康检查配置"
   ↓
3. 验证 Initial Delay = 60 秒
```

### 问题: 前端 404

```
1. 查看 DEPLOYMENT_DIAGNOSIS.md
   → "问题 3: 前端编译产物缺失"
   ↓
2. 检查构建日志
   → 确认 "reflex export" 步骤
   ↓
3. 验证 nixpacks.toml
   → [phases.build] 部分
```

---

## 文件大小和阅读时间

| 文档 | 大小 | 阅读时间 | 优先级 |
|------|------|---------|--------|
| **QUICK_FIX_GUIDE.md** | 5.7 KB | 5 分钟 | ⭐⭐⭐⭐⭐ |
| **COOLIFY_CONFIG.md** | 9.6 KB | 15 分钟 | ⭐⭐⭐⭐ |
| **DEPLOYMENT_DIAGNOSIS.md** | 11 KB | 20 分钟 | ⭐⭐⭐ |
| **DEPLOYMENT_SUMMARY.md** | 11 KB | 10 分钟 | ⭐⭐⭐⭐ |
| **README.md** | 8.6 KB | 10 分钟 | ⭐⭐⭐ |
| **nixpacks.toml** | 1.1 KB | 2 分钟 | ⭐⭐⭐⭐⭐ |
| **start.sh** | 1.8 KB | 3 分钟 | ⭐⭐ |

**总阅读时间**:
- 快速路径: 10-15 分钟
- 推荐路径: 30-40 分钟
- 完整路径: 1-2 小时

---

## 快速查找

### 我想知道...

| 问题 | 文档 | 章节 |
|------|------|------|
| **如何快速修复部署失败？** | QUICK_FIX_GUIDE.md | TL;DR 章节 |
| **为什么容器会立即退出？** | DEPLOYMENT_DIAGNOSIS.md | 关键问题分析 → 1 |
| **如何配置健康检查？** | COOLIFY_CONFIG.md | 步骤 4 |
| **如何添加环境变量？** | COOLIFY_CONFIG.md | 步骤 2 |
| **Reflex 启动需要多久？** | DEPLOYMENT_DIAGNOSIS.md | Reflex 应用启动流程 |
| **如何本地测试构建？** | README.md | 本地测试部署 |
| **nixpacks.toml 怎么写？** | DEPLOYMENT_DIAGNOSIS.md | 问题 A |
| **部署成功的标志？** | DEPLOYMENT_SUMMARY.md | 成功指标 |

---

## 检查清单

### 部署前

- [ ] 阅读 QUICK_FIX_GUIDE.md
- [ ] 更新 nixpacks.toml（已完成）
- [ ] 提交代码到 Git
- [ ] 本地测试（可选）

### Coolify 配置

- [ ] 按照 COOLIFY_CONFIG.md 配置所有设置
- [ ] 特别注意健康检查 Initial Delay = 60 秒
- [ ] 验证环境变量
- [ ] 检查端口映射

### 部署后

- [ ] 查看构建日志
- [ ] 查看应用日志
- [ ] 验证应用状态 = `running:healthy`
- [ ] 测试前端和后端

---

## 支持和帮助

### 如果遇到问题

1. **查看故障排除路径**（本文档上方）
2. **阅读相关技术文档**（根据问题类型）
3. **运行本地测试**（复现问题）
4. **收集日志信息**（Coolify 应用日志）

### 相关资源

- [Reflex 官方文档](https://reflex.dev/docs)
- [Coolify 文档](https://coolify.io/docs)
- [Nixpacks 文档](https://nixpacks.com/)
- [uv 文档](https://docs.astral.sh/uv/)

---

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2025-10-30 | 创建所有部署文档和测试脚本 |
| 2025-10-30 | 修复 nixpacks.toml 配置 |
| 2025-10-30 | 添加启动脚本和健康检查配置 |
| 2025-10-30 | 创建本索引文档 |

---

**准备好了吗？从 [QUICK_FIX_GUIDE.md](./QUICK_FIX_GUIDE.md) 开始！**

祝你部署顺利！🚀
