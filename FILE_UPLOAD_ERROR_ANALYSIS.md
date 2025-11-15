# 🔴 文件上传 Network Error 分析与修复方案

**报告日期**: 2025-11-15
**问题**: 前端页面上传文件显示"❌ Network Error"
**状态**: 已诊断，解决方案准备就绪

---

## 📊 问题诊断

### 现象
1. 前端成功启动（http://localhost:3000）
2. 后端成功启动（http://localhost:8000）
3. 用户选择数据集文件并点击"开始上传"
4. 显示错误: **❌ Network Error**
5. 上传失败

### 诊断发现

#### 发现 1: 前端文件上传实现分析
**文件**: `frontend/src/pages/FileUploadDemo.tsx`

```typescript
// 现有实现 - 仅模拟上传，不调用真实 API
const handleFileUpload = async (file: File, dataSourceId: number) => {
  console.log('上传文件:', file.name, '数据源:', dataSourceId)

  setIsUploading(true)
  setUploadStatus('uploading')

  // ❌ 问题：这里只是模拟，没有调用真实的后端 API
  let progress = 0
  const interval = setInterval(() => {
    progress += Math.random() * 30
    if (progress >= 100) {
      // 模拟完成
    }
  }, 300)
}
```

**问题**: `handleFileUpload` 函数虽然存在，但**从未调用后端 API**，只是模拟上传进度

#### 发现 2: 前端有真实的 API 客户端
**文件**: `frontend/src/services/file.api.ts`

```typescript
// ✅ 真实的 API 函数存在！
export async function uploadFile(
  file: File,
  dataSourceId: number,
  onProgress?: UploadProgressCallback
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('data_source_id', String(dataSourceId))

  const response = await apiClient.post<UploadResponse>(
    '/api/file-uploads',  // ✅ 正确的后端端点
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        // 追踪上传进度
      },
    }
  )
  return response.data
}
```

**问题**: 这个函数存在但**未被 FileUploadDemo.tsx 调用**

#### 发现 3: 后端 API 端点存在且正确配置
**文件**: `backend/src/api/file_uploads.py`

```python
# ✅ 后端有对应的处理器
@router.post("/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    data_source_id: int = Form(...),
    session: AsyncSession = Depends(get_async_session)
):
    # 处理文件上传
```

**状态**: ✅ 端点已正确实现

#### 发现 4: CORS 配置正确
**文件**: `backend/src/main.py`

```python
# ✅ CORS 中间件已配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 路由已注册
app.include_router(file_uploads.router)  # 第 66 行
```

**状态**: ✅ CORS 和路由都正确配置

---

## 🎯 根本原因

**根本原因**: `FileUploadDemo.tsx` 中的 `handleFileUpload` 函数没有调用真实的后端 API

这导致两种可能的情况：

### 情景 1: 用户使用 FileUploadDemo 页面
- ❌ 前端代码只是**模拟**上传过程
- ✅ 后端 API 是**真实存在**的
- ❌ 两者之间**没有通信**

### 情景 2: 用户使用其他上传页面
- ⚠️  前端代码可能尝试调用真实 API
- ⚠️  由于其他配置问题导致 Network Error

---

## ✅ 解决方案

### 方案 1: 修复 FileUploadDemo.tsx（推荐）

**修改 FileUploadDemo.tsx 中的 handleFileUpload 函数**：

```typescript
import { uploadFile } from '../services/file.api'

const handleFileUpload = async (file: File, dataSourceId: number) => {
  console.log('上传文件:', file.name, '数据源:', dataSourceId)

  setIsUploading(true)
  setUploadStatus('uploading')
  setErrorMessage(null)

  try {
    // ✅ 调用真实的后端 API
    const result = await uploadFile(file, dataSourceId, (progress) => {
      setUploadProgress(progress.percentage)
    })

    // 上传成功
    setUploadProgress(100)
    setUploadStatus('completed')
    setCurrentFile({
      id: result.id,
      filename: result.filename,
      file_format: result.file_format,
      file_size: result.file_size,
      row_count: result.row_count,
      column_count: result.column_count,
      parse_status: result.parse_status,
      created_at: result.created_at,
      metadata: {
        rows_count: result.row_count || 0,
        columns_count: result.column_count || 0,
        column_names: [],
        data_types: [],
      },
    })
  } catch (error) {
    // 处理错误
    setUploadStatus('error')
    if (error instanceof Error) {
      setErrorMessage(error.message)
    } else {
      setErrorMessage('上传失败，请重试')
    }
  } finally {
    setIsUploading(false)
  }
}
```

### 方案 2: 检查网络请求（调试用）

如果错误仍然存在，检查以下几点：

1. **检查 API 基础 URL**
   ```typescript
   // file.api.ts 第 11 行
   const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
   ```

   - ✅ 默认值 `http://localhost:8000` 正确
   - ⚠️ 如果在 `.env.local` 中定义了 `VITE_API_URL`，需要验证值

2. **检查 Axios 配置**
   ```typescript
   const apiClient: AxiosInstance = axios.create({
     baseURL: API_BASE_URL,
     timeout: 60000,  // 60 秒超时 - 足够
     headers: {
       'Content-Type': 'multipart/form-data',  // ✅ 正确
     },
   })
   ```

3. **检查后端是否正确接收请求**
   - 查看后端日志是否看到请求到达
   - 检查文件上传目录是否可写
   - 确认 `UPLOAD_DIR` 配置正确

---

## 🔍 技术细节分析

### API 调用链

```
┌─ 前端 (localhost:3000) ─┐
│                         │
│ 1. onClick "开始上传"    │
│ 2. handleFileUpload()   │ ← ❌ 当前：仅模拟
│    ↓ ← ✅ 应该：调用 uploadFile()
│ 3. uploadFile()         │
│    ├─ FormData 包装文件 │
│    └─ POST /api/file-uploads
│
└─────────────────────────┘
        ↓ (Network)
┌─ 后端 (localhost:8000) ┐
│                        │
│ POST /api/file-uploads │ ← ✅ 端点存在
│ ├─ CORS 检查 ✅         │
│ ├─ 验证文件 ✅          │
│ ├─ 保存文件 ✅          │
│ └─ 返回 JSON 响应 ✅     │
│
└────────────────────────┘
```

### CORS 流程（已正确配置）

```
前端请求:
  OPTIONS /api/file-uploads (预检请求)
  │
  ├─ Origin: http://localhost:3000
  ├─ Access-Control-Request-Method: POST
  └─ Access-Control-Request-Headers: content-type

后端响应:
  ✅ Access-Control-Allow-Origin: http://localhost:3000
  ✅ Access-Control-Allow-Methods: *
  ✅ Access-Control-Allow-Headers: *

前端发送:
  POST /api/file-uploads
  (实际上传)
```

---

## 📝 修复步骤

### 步骤 1: 修改 FileUploadDemo.tsx

位置: `frontend/src/pages/FileUploadDemo.tsx`

```diff
 import { useState } from 'react'
 import {
   FileUploadForm,
   FileDropZone,
   UploadProgress,
 } from '../components/file-upload'
 import { FilePreview, PreviewTable } from '../components/file-preview'
 import type { FileMetadata } from '../components/file-preview/FilePreview'
+import { uploadFile } from '../services/file.api'

 export function FileUploadDemo() {
   // ... 其他状态定义 ...

   // 修改 handleFileUpload 函数
-  const handleFileUpload = async (file: File, dataSourceId: number) => {
-    // 旧代码：只是模拟
+  const handleFileUpload = async (file: File, dataSourceId: number) => {
+    console.log('上传文件:', file.name, '数据源:', dataSourceId)
+
+    setIsUploading(true)
+    setUploadStatus('uploading')
+    setErrorMessage(null)
+
+    try {
+      const result = await uploadFile(file, dataSourceId, (progress) => {
+        setUploadProgress(progress.percentage)
+      })
+
+      setUploadProgress(100)
+      setUploadStatus('completed')
+      setCurrentFile({
+        id: result.id,
+        filename: result.filename,
+        file_format: result.file_format,
+        file_size: result.file_size,
+        row_count: result.row_count,
+        column_count: result.column_count,
+        parse_status: result.parse_status,
+        created_at: result.created_at,
+        metadata: {
+          rows_count: result.row_count || 0,
+          columns_count: result.column_count || 0,
+          column_names: [],
+          data_types: [],
+        },
+      })
+    } catch (error) {
+      setUploadStatus('error')
+      if (error instanceof Error) {
+        setErrorMessage(error.message)
+      } else {
+        setErrorMessage('上传失败: 网络错误或服务器问题')
+      }
+      console.error('上传错误:', error)
+    } finally {
+      setIsUploading(false)
+    }
   }
```

### 步骤 2: 验证后端配置

检查 `.env` 文件中的上传配置：

```env
# .env
UPLOAD_DIR=./tmp/uploads
MAX_FILE_SIZE=536870912  # 500MB
```

### 步骤 3: 测试 API 端点（手动测试）

```bash
# 测试后端是否响应
curl http://localhost:8000/health

# 测试 CORS
curl -X OPTIONS http://localhost:8000/api/file-uploads \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# 测试文件上传（使用 curl）
curl -X POST http://localhost:8000/api/file-uploads \
  -F "file=@/path/to/test.csv" \
  -F "data_source_id=1"
```

---

## 🎯 潜在的其他错误原因

如果修改后仍然出现 Network Error，检查以下几点：

| 检查项 | 症状 | 解决方案 |
|--------|------|--------|
| **CORS 错误** | 浏览器控制台: "Cross-Origin Request Blocked" | 检查后端 CORS 配置（已验证 ✅） |
| **超时** | 请求超过 60 秒 | 增加 `timeout` 值或检查文件大小 |
| **文件太大** | 上传大文件失败 | 检查 `MAX_FILE_SIZE` 配置 |
| **权限错误** | 后端写入 UPLOAD_DIR 失败 | 确认目录存在且可写 |
| **数据源 ID 无效** | dataSourceId 不存在 | 确认数据源 ID 有效 |
| **API 路由问题** | 404 Not Found | 检查后端路由注册（已验证 ✅） |

---

## ✅ 验证清单

在修复后，验证以下内容：

- [ ] `FileUploadDemo.tsx` 中导入了 `uploadFile` 函数
- [ ] `handleFileUpload` 调用了 `uploadFile()` 而不是模拟
- [ ] 错误处理在 try-catch 中正确实现
- [ ] 上传进度通过 `onProgress` 回调更新
- [ ] 成功响应正确解析并更新 UI
- [ ] 后端日志显示请求被接收
- [ ] 文件被保存到 `UPLOAD_DIR` 目录

---

## 📊 修复前后对比

### 修复前
```
用户上传 → 前端模拟 → 假进度条 ❌ 后端未调用
          ↓
        显示"完成"（实际上没上传到服务器）
```

### 修复后
```
用户上传 → 调用 uploadFile() → FormData 准备 → POST 请求
          ↓                                    ↓
        显示实时进度 ← onUploadProgress        后端处理
                                              ↓
                                            验证 & 保存
                                              ↓
                                        返回文件元数据
                                              ↓
                                        显示预览
```

---

## 💾 相关文件

- **前端上传组件**: `frontend/src/components/file-upload/FileUploadForm.tsx`
- **前端演示页面**: `frontend/src/pages/FileUploadDemo.tsx` ← **需要修复**
- **前端 API 服务**: `frontend/src/services/file.api.ts` ✅
- **后端 API 处理**: `backend/src/api/file_uploads.py` ✅
- **后端主应用**: `backend/src/main.py` ✅

---

**报告完成时间**: 2025-11-15
**建议行动**: 立即应用方案 1 的修复
**预期结果**: 文件成功上传到后端，显示预览
