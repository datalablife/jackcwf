# Phase 4 - 文件上传功能任务列表

**生成日期**: 2025-11-08
**总任务数**: 32
**预计工期**: 3-4 天

---

## 📋 任务总览

| 阶段 | 任务数 | 状态 |
|------|--------|------|
| T044-T047: 后端数据库模型 | 4 | ⏳ 待实施 |
| T048-T051: 后端验证和解析服务 | 4 | ⏳ 待实施 |
| T052-T054: 后端 API 路由 | 3 | ⏳ 待实施 |
| T055-T057: 后端单元测试 | 3 | ⏳ 待实施 |
| T058-T060: 后端集成测试 | 3 | ⏳ 待实施 |
| T061-T065: 前端组件实现 | 5 | ⏳ 待实施 |
| T066-T067: 前端状态管理 | 2 | ⏳ 待实施 |
| T068-T069: 前端 API 客户端 | 2 | ⏳ 待实施 |
| T070-T072: 前端页面集成 | 3 | ⏳ 待实施 |
| T073-T075: 前端单元测试 | 3 | ⏳ 待实施 |
| T076-T078: 前端集成测试 | 3 | ⏳ 待实施 |

---

## 🗄️ 后端数据库模型 (T044-T047)

### T044: 创建 FileUpload ORM 模型
- **文件**: `backend/src/models/file_upload.py`
- **内容**:
  - FileUpload 类定义
  - 字段: id, name, type, size, status, error_message, created_at, updated_at
  - SQLAlchemy 关系配置
  - 类型注解和文档
- **验收**:
  - [ ] 模型类可正确导入
  - [ ] 所有字段都有正确的类型
  - [ ] 关系配置正确

### T045: 创建 FileMetadata ORM 模型
- **文件**: `backend/src/models/file_metadata.py`
- **内容**:
  - FileMetadata 类定义
  - 字段: id, file_upload_id, rows_count, columns_count, column_names, data_types, storage_path, created_at
  - 与 FileUpload 的一对一关系
  - JSON 列支持
  - 类型注解和文档
- **验收**:
  - [ ] 模型类可正确导入
  - [ ] 关系配置正确
  - [ ] JSON 字段支持

### T046: 创建数据库迁移 (FileUpload)
- **文件**: `backend/alembic/versions/xxx_add_file_uploads_table.py`
- **内容**:
  - CreateTable 操作
  - 所有列的定义
  - 主键和约束
- **验收**:
  - [ ] 迁移可正确执行
  - [ ] 表结构正确

### T047: 创建数据库迁移 (FileMetadata)
- **文件**: `backend/alembic/versions/xxx_add_file_metadata_table.py`
- **内容**:
  - CreateTable 操作
  - 所有列的定义
  - 外键关系
- **验收**:
  - [ ] 迁移可正确执行
  - [ ] 表结构正确

---

## 🔧 后端验证和解析服务 (T048-T051)

### T048: 创建文件验证服务
- **文件**: `backend/src/services/file_validation.py`
- **内容**:
  - FileValidationService 类
  - validate_file() - 检查大小和类型
  - validate_csv() - 验证 CSV 格式
  - validate_excel() - 验证 Excel 格式
  - 常量: MAX_FILE_SIZE, ALLOWED_TYPES
  - 异常类: FileValidationError
- **验收**:
  - [ ] 可导入使用
  - [ ] 验证逻辑正确
  - [ ] 错误消息清晰

### T049: 创建 CSV 解析服务
- **文件**: `backend/src/services/csv_parser.py`
- **内容**:
  - CSVParserService 类
  - parse_csv() - 解析 CSV 文件
  - get_column_names() - 获取列名
  - get_data_types() - 推断数据类型
  - get_preview() - 获取预览数据
  - get_row_count() - 获取行数
- **验收**:
  - [ ] 可导入使用
  - [ ] 正确解析 CSV 数据
  - [ ] 数据类型推断准确

### T050: 创建 Excel 解析服务
- **文件**: `backend/src/services/excel_parser.py`
- **内容**:
  - ExcelParserService 类
  - parse_excel() - 解析 Excel 文件
  - list_sheets() - 列出所有工作表
  - get_sheet_data() - 获取工作表数据
  - get_column_names() - 获取列名
  - get_data_types() - 推断数据类型
- **验收**:
  - [ ] 支持 .xlsx 和 .xls
  - [ ] 正确列出工作表
  - [ ] 正确解析数据

### T051: 创建文件管理服务
- **文件**: `backend/src/services/file_upload_service.py`
- **内容**:
  - FileUploadService 类
  - save_upload() - 保存上传文件
  - get_file() - 获取文件信息
  - list_files() - 列表查询
  - delete_file() - 删除文件
  - get_preview() - 获取文件预览
  - 与数据库交互
- **验收**:
  - [ ] 可正确保存文件
  - [ ] CRUD 操作完整

---

## 🌐 后端 API 路由 (T052-T054)

### T052: 创建文件上传 API 路由
- **文件**: `backend/src/api/file_uploads.py`
- **内容**:
  - POST /api/file-uploads - 上传文件
  - GET /api/file-uploads - 列表查询
  - GET /api/file-uploads/{id} - 获取详情
  - DELETE /api/file-uploads/{id} - 删除文件
  - Pydantic 模型
  - 错误处理
- **验收**:
  - [ ] 所有端点实现完整
  - [ ] 错误处理正确
  - [ ] API 文档完整

### T053: 创建文件预览 API 路由
- **文件**: `backend/src/api/file_preview.py`
- **内容**:
  - GET /api/file-uploads/{id}/preview - 获取预览数据
  - GET /api/file-uploads/{id}/sheets - 获取 Excel 工作表列表
  - GET /api/file-uploads/{id}/metadata - 获取文件元数据
  - 返回预览数据、列名、数据类型
- **验收**:
  - [ ] 端点实现完整
  - [ ] 预览数据正确

### T054: 集成 API 路由到主应用
- **文件**: `backend/src/main.py`
- **内容**:
  - 导入文件上传路由
  - 导入文件预览路由
  - 注册路由到 FastAPI 应用
  - 更新 API 文档
- **验收**:
  - [ ] 路由正确注册
  - [ ] 应用可正常启动

---

## 🧪 后端单元测试 (T055-T057)

### T055: 文件验证服务单元测试
- **文件**: `backend/tests/unit/test_file_validation.py`
- **内容**:
  - 测试有效文件验证
  - 测试无效文件类型
  - 测试文件大小限制
  - 测试 CSV/Excel 格式验证
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 95%

### T056: CSV/Excel 解析服务单元测试
- **文件**: `backend/tests/unit/test_csv_excel_parsers.py`
- **内容**:
  - CSV 解析测试
  - Excel 解析测试
  - 数据类型推断测试
  - 错误处理测试
- **验收**:
  - [ ] 至少 15 个测试
  - [ ] 测试通过率 >= 95%

### T057: 文件管理服务单元测试
- **文件**: `backend/tests/unit/test_file_upload_service.py`
- **内容**:
  - CRUD 操作测试
  - 文件保存测试
  - 预览生成测试
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 95%

---

## 🔗 后端集成测试 (T058-T060)

### T058: 文件上传 API 集成测试
- **文件**: `backend/tests/integration/test_file_upload_api.py`
- **内容**:
  - 测试 POST /api/file-uploads
  - 测试 GET /api/file-uploads
  - 测试 DELETE /api/file-uploads/{id}
  - 测试错误情况
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 95%

### T059: 文件预览 API 集成测试
- **文件**: `backend/tests/integration/test_file_preview_api.py`
- **内容**:
  - 测试文件预览端点
  - 测试 Excel 工作表列表
  - 测试文件元数据
- **验收**:
  - [ ] 至少 8 个测试
  - [ ] 测试通过率 >= 95%

### T060: 数据库模型集成测试
- **文件**: `backend/tests/integration/test_file_models.py`
- **内容**:
  - 测试模型创建
  - 测试关系
  - 测试数据持久化
- **验收**:
  - [ ] 至少 8 个测试
  - [ ] 测试通过率 >= 95%

---

## 🎨 前端组件实现 (T061-T065)

### T061: 创建文件上传表单组件
- **文件**: `frontend/src/components/file-upload/FileUploadForm.tsx`
- **内容**:
  - 文件输入表单
  - 表单验证
  - 上传按钮
  - 错误提示
  - 关于上传的文件类型和大小限制信息
- **验收**:
  - [ ] 组件可正确渲染
  - [ ] 表单验证正确
  - [ ] 样式美观

### T062: 创建拖拽上传组件
- **文件**: `frontend/src/components/file-upload/FileDropZone.tsx`
- **内容**:
  - 拖拽上传区域
  - 文件预览
  - 拖拽反馈
  - 样式处理
- **验收**:
  - [ ] 拖拽功能正常
  - [ ] 样式美观

### T063: 创建上传进度条组件
- **文件**: `frontend/src/components/file-upload/UploadProgress.tsx`
- **内容**:
  - 进度显示
  - 上传速度
  - 剩余时间
  - 暂停/恢复功能 (可选)
- **验收**:
  - [ ] 进度显示正确
  - [ ] 样式清晰

### T064: 创建文件预览组件
- **文件**: `frontend/src/components/file-preview/FilePreview.tsx`
- **内容**:
  - 文件信息展示
  - 列名显示
  - 数据类型显示
  - 行数统计
  - 关联 PreviewTable 组件
- **验收**:
  - [ ] 组件可正确渲染
  - [ ] 显示信息完整

### T065: 创建预览表格组件
- **文件**: `frontend/src/components/file-preview/PreviewTable.tsx`
- **内容**:
  - 表格布局
  - 数据展示
  - 滚动支持
  - 分页 (可选)
- **验收**:
  - [ ] 表格显示正确
  - [ ] 数据完整

---

## 📦 前端状态管理 (T066-T067)

### T066: 创建文件上传状态存储
- **文件**: `frontend/src/stores/useFileUploadStore.ts`
- **内容**:
  - Zustand store 定义
  - uploadFile() 方法
  - getFiles() 方法
  - deleteFile() 方法
  - 状态: files, isLoading, error
- **验收**:
  - [ ] store 可正确导入
  - [ ] 方法正确实现

### T067: 创建文件预览状态存储
- **文件**: `frontend/src/stores/useFilePreviewStore.ts`
- **内容**:
  - 预览数据状态管理
  - 工作表列表管理
  - 元数据管理
- **验收**:
  - [ ] store 可正确导入
  - [ ] 状态管理正确

---

## 🔌 前端 API 客户端 (T068-T069)

### T068: 创建文件上传 API 客户端
- **文件**: `frontend/src/services/file.api.ts`
- **内容**:
  - uploadFile() - 上传文件
  - getFiles() - 获取文件列表
  - deleteFile() - 删除文件
  - Axios 配置
  - TypeScript 类型定义
- **验收**:
  - [ ] 所有方法实现完整
  - [ ] TypeScript 类型正确

### T069: 创建文件预览 API 客户端
- **文件**: `frontend/src/services/file-preview.api.ts`
- **内容**:
  - getPreview() - 获取预览数据
  - getSheets() - 获取 Excel 工作表列表
  - getMetadata() - 获取文件元数据
  - 类型定义
- **验收**:
  - [ ] 方法实现完整
  - [ ] 类型正确

---

## 📄 前端页面集成 (T070-T072)

### T070: 创建文件上传页面
- **文件**: `frontend/src/pages/FileUploadPage.tsx`
- **内容**:
  - 页面布局
  - 集成 FileUploadForm 和 FileDropZone
  - 集成 UploadProgress
  - 页面标题和说明
- **验收**:
  - [ ] 页面可正确渲染
  - [ ] 功能完整

### T071: 创建文件管理页面
- **文件**: `frontend/src/pages/FileManagementPage.tsx`
- **内容**:
  - 文件列表显示
  - 文件操作 (删除、重新上传)
  - 集成数据源列表
- **验收**:
  - [ ] 页面可正确渲染
  - [ ] 列表功能完整

### T072: 集成到 DataSourceSetup
- **文件**: `frontend/src/pages/DataSourceSetup.tsx`
- **内容**:
  - 添加文件上传选项卡
  - 集成 FileUploadPage
  - 集成 FileManagementPage
- **验收**:
  - [ ] 选项卡显示正确
  - [ ] 导航功能正常

---

## 🧪 前端单元测试 (T073-T075)

### T073: 文件上传组件单元测试
- **文件**: `frontend/tests/unit/file-upload.test.tsx`
- **内容**:
  - FileUploadForm 测试
  - FileDropZone 测试
  - UploadProgress 测试
- **验收**:
  - [ ] 至少 15 个测试
  - [ ] 测试通过率 >= 90%

### T074: 文件预览组件单元测试
- **文件**: `frontend/tests/unit/file-preview.test.tsx`
- **内容**:
  - FilePreview 测试
  - PreviewTable 测试
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 90%

### T075: 文件状态存储单元测试
- **文件**: `frontend/tests/unit/file-stores.test.ts`
- **内容**:
  - useFileUploadStore 测试
  - useFilePreviewStore 测试
- **验收**:
  - [ ] 至少 15 个测试
  - [ ] 测试通过率 >= 90%

---

## 🔗 前端集成测试 (T076-T078)

### T076: 文件上传流程集成测试
- **文件**: `frontend/tests/integration/file-upload-flow.test.tsx`
- **内容**:
  - 完整的上传流程测试
  - 错误处理测试
  - 进度显示测试
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 90%

### T077: 文件预览集成测试
- **文件**: `frontend/tests/integration/file-preview-flow.test.tsx`
- **内容**:
  - 预览加载测试
  - 工作表选择测试
  - 数据展示测试
- **验收**:
  - [ ] 至少 10 个测试
  - [ ] 测试通过率 >= 90%

### T078: 文件管理集成测试
- **文件**: `frontend/tests/integration/file-management.test.tsx`
- **内容**:
  - 文件列表测试
  - 删除操作测试
  - 重新上传测试
- **验收**:
  - [ ] 至少 8 个测试
  - [ ] 测试通过率 >= 90%

---

## 📋 执行计划

### 第 1 天: 后端数据库和基础服务
- [ ] T044: 创建 FileUpload 模型
- [ ] T045: 创建 FileMetadata 模型
- [ ] T046: 数据库迁移 (FileUpload)
- [ ] T047: 数据库迁移 (FileMetadata)
- [ ] T048: 文件验证服务
- [ ] T049: CSV 解析服务
- [ ] T050: Excel 解析服务

### 第 2 天: 后端 API 和测试
- [ ] T051: 文件管理服务
- [ ] T052: 文件上传 API
- [ ] T053: 文件预览 API
- [ ] T054: 集成 API 路由
- [ ] T055: 验证服务单元测试
- [ ] T056: 解析服务单元测试

### 第 3 天: 前端实现
- [ ] T057: 文件管理服务单元测试
- [ ] T058: 文件上传 API 集成测试
- [ ] T059: 文件预览 API 集成测试
- [ ] T060: 数据库模型集成测试
- [ ] T061: 文件上传表单
- [ ] T062: 拖拽上传组件
- [ ] T063: 上传进度条

### 第 4 天: 前端集成和测试
- [ ] T064: 文件预览组件
- [ ] T065: 预览表格组件
- [ ] T066: 文件上传状态存储
- [ ] T067: 文件预览状态存储
- [ ] T068: 文件上传 API 客户端
- [ ] T069: 文件预览 API 客户端
- [ ] T070: 文件上传页面
- [ ] T071: 文件管理页面
- [ ] T072: DataSourceSetup 集成

### 第 5 天: 测试和完成
- [ ] T073: 文件上传组件单元测试
- [ ] T074: 文件预览组件单元测试
- [ ] T075: 文件状态存储单元测试
- [ ] T076: 文件上传流程集成测试
- [ ] T077: 文件预览集成测试
- [ ] T078: 文件管理集成测试
- [ ] 文档编写和完成报告

---

## 🔗 任务依赖

```
T044-T047 (数据库模型)
    ↓
T048-T051 (服务实现)
    ↓
T052-T054 (API 路由)
    ├─→ T055-T057 (后端单元测试) [并行]
    └─→ T058-T060 (后端集成测试) [依赖 T052-T054]

T061-T065 (前端组件) [不依赖后端]
T066-T067 (前端状态管理) [依赖 T061-T065]
T068-T069 (API 客户端) [依赖 T054]
T070-T072 (页面集成) [依赖 T061-T069]

T073-T075 (前端单元测试) [依赖 T061-T069]
T076-T078 (前端集成测试) [依赖 T070-T072]
```

---

**总体完成度**: 0% (待实施)
**预计总工时**: 40-48 小时
**建议团队**: 2-3 人 (后端 1-2 人，前端 1-2 人)

---

*生成于 2025-11-08*
*Next Phase: Phase 4 Implementation*
