# Phase 4 - 文件上传功能规范

**日期**: 2025-11-08
**阶段**: Phase 4 - 文件处理与上传
**预计工期**: 3-4 天
**优先级**: High

---

## 📋 功能概述

Phase 4 实现用户文件上传、处理和预览功能，支持 CSV、Excel 等格式的数据源。

### 核心功能
1. **文件上传**：支持单/多文件上传
2. **文件验证**：检查文件类型、大小、格式
3. **文件预览**：显示上传文件内容预览
4. **数据解析**：解析 CSV/Excel 数据
5. **文件管理**：列表、删除、重新上传

---

## 🎯 用户故事

### US1: 上传 CSV 文件作为数据源
**作为**: 数据分析师
**我想**: 上传本地 CSV 文件作为数据源
**以便**: 使用 Text2SQL 查询上传的数据

**验收条件**:
- ✅ 能够选择和上传 CSV 文件
- ✅ 显示上传进度
- ✅ 验证文件格式和大小
- ✅ 保存文件到服务器
- ✅ 在数据源列表中显示上传的文件

### US2: 预览上传文件内容
**作为**: 数据分析师
**我想**: 在创建查询前预览上传文件的内容
**以便**: 确保上传了正确的文件

**验收条件**:
- ✅ 显示文件的前 N 行数据
- ✅ 显示列名称和数据类型
- ✅ 显示行数统计
- ✅ 支持滚动查看更多数据

### US3: 解析 Excel 文件
**作为**: 数据分析师
**我想**: 上传 Excel 文件并选择特定工作表
**以便**: 使用 Excel 中的数据

**验收条件**:
- ✅ 支持 .xlsx 和 .xls 格式
- ✅ 列出所有可用的工作表
- ✅ 选择特定工作表进行导入
- ✅ 验证工作表数据

### US4: 管理上传的文件
**作为**: 数据分析师
**我想**: 查看、重新上传或删除已上传的文件
**以便**: 保持数据源的整洁

**验收条件**:
- ✅ 显示上传文件列表
- ✅ 显示文件大小和上传时间
- ✅ 删除不需要的文件
- ✅ 重新上传相同文件覆盖旧版本

---

## 🏗️ 技术架构

### 后端架构

#### 新增服务
```
backend/src/services/
├── file_upload.py          # 文件上传服务
├── file_validation.py      # 文件验证服务
├── csv_parser.py           # CSV 解析服务
└── excel_parser.py         # Excel 解析服务
```

#### 新增 ORM 模型
```
backend/src/models/
├── file_upload.py          # 文件上传模型
└── file_metadata.py        # 文件元数据模型
```

#### 新增 API 路由
```
backend/src/api/
├── file_uploads.py         # 文件上传 REST API
└── file_preview.py         # 文件预览 API
```

### 前端架构

#### 新增组件
```
frontend/src/components/
├── file-upload/
│   ├── FileUploadForm.tsx       # 文件上传表单
│   ├── FileDropZone.tsx         # 拖拽上传区域
│   └── UploadProgress.tsx       # 上传进度条
├── file-preview/
│   ├── FilePreview.tsx          # 文件预览组件
│   └── PreviewTable.tsx         # 数据表格预览
└── file-management/
    ├── FileList.tsx             # 文件列表
    └── FileActions.tsx          # 文件操作
```

#### 新增存储
```
frontend/src/stores/
├── useFileUploadStore.ts    # 文件上传状态管理
└── useFilePreviewStore.ts   # 文件预览状态管理
```

#### 新增 API 服务
```
frontend/src/services/
└── file.api.ts             # 文件上传 API 客户端
```

---

## 📊 数据模型

### FileUpload 表
```sql
CREATE TABLE file_uploads (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50),                    -- csv, xlsx, xls
  size INTEGER NOT NULL,
  status VARCHAR(20),                  -- pending, processing, completed, failed
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(255),

  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);
```

### FileMetadata 表
```sql
CREATE TABLE file_metadata (
  id SERIAL PRIMARY KEY,
  file_upload_id INTEGER NOT NULL UNIQUE,
  rows_count INTEGER,
  columns_count INTEGER,
  column_names TEXT[],                 -- JSON array of column names
  data_types TEXT[],                   -- JSON array of data types
  storage_path VARCHAR(500),           -- S3 或本地路径
  created_at TIMESTAMP DEFAULT NOW(),

  FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id) ON DELETE CASCADE
);
```

---

## 🔄 实施流程

### 第一天：后端实施
1. 创建 FileUpload 和 FileMetadata ORM 模型
2. 创建文件验证服务 (文件类型、大小检查)
3. 创建 CSV 解析服务
4. 创建 Excel 解析服务
5. 创建文件上传 REST API
6. 创建文件预览 API
7. 编写后端单元和集成测试

### 第二天：前端实施
1. 创建文件上传表单组件
2. 创建拖拽上传区域
3. 创建上传进度条组件
4. 创建文件预览组件
5. 创建文件列表管理组件
6. 实现 Zustand 状态管理
7. 实现 API 客户端

### 第三天：集成和优化
1. 集成前后端
2. 创建前端集成测试
3. 性能优化
4. 错误处理和边界情况
5. 文档编写

### 第四天：部署和验收
1. 部署到 Coolify
2. 进行 E2E 测试
3. 性能基准测试
4. 用户验收测试
5. 完成报告

---

## 🧪 测试策略

### 后端测试
- 文件上传 API 测试 (成功、失败、验证错误)
- 文件验证测试 (类型、大小、格式)
- CSV 解析测试 (正常、错误格式、大文件)
- Excel 解析测试 (单工作表、多工作表)
- 文件预览 API 测试

### 前端测试
- 文件上传表单测试
- 拖拽上传测试
- 文件预览渲染测试
- 文件列表管理测试
- 状态管理测试

---

## 🔐 安全要求

- ✅ 文件大小限制 (最大 100MB)
- ✅ 文件类型白名单 (仅允许 CSV, XLSX, XLS)
- ✅ 病毒扫描 (可选，使用第三方服务)
- ✅ 文件隔离存储 (用户可见的只有自己的文件)
- ✅ 访问控制 (用户只能访问自己上传的文件)

---

## 📈 性能要求

- ✅ 单文件上传时间 < 5 秒 (对于 10MB 文件)
- ✅ 文件预览加载时间 < 2 秒
- ✅ 支持并发上传 (最多 5 个)
- ✅ 内存使用 < 500MB

---

## 📝 验收标准

### 功能完成
- [ ] 所有 REST API 端点已实现
- [ ] 所有 React 组件已实现
- [ ] 文件上传流程完整可用
- [ ] 文件预览功能正常
- [ ] 文件管理功能完整

### 测试覆盖
- [ ] 后端单元测试通过率 >= 95%
- [ ] 后端集成测试通过率 >= 95%
- [ ] 前端组件测试通过率 >= 90%
- [ ] 前端集成测试通过率 >= 90%
- [ ] 手工测试全部通过

### 文档完成
- [ ] API 文档完整
- [ ] 组件文档完整
- [ ] 部署指南完整

---

**阶段状态**: 📋 规范完成
**下一步**: 生成详细任务列表和实施计划
