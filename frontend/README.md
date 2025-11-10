# 数据文件管理系统 - 前端应用

一个功能强大的文件上传、预览和管理系统，使用现代前端技术栈构建。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [开发指南](#开发指南)
- [测试](#测试)
- [API 文档](#api-文档)
- [部署](#部署)

## ✨ 功能特性

### 核心功能

- **文件上传**
  - 支持多种文件格式（CSV, XLSX, XLS, JSON, JSONL）
  - 拖拽上传支持
  - 实时进度跟踪
  - 上传速度和剩余时间显示

- **文件预览**
  - 快速数据预览
  - 数据类型识别
  - Excel 多工作表支持
  - 分页浏览

- **文件管理**
  - 文件列表查看
  - 文件详情展示
  - 文件删除
  - 解析状态跟踪

### 用户界面特性

- 响应式设计（支持移动和桌面）
- 现代化的 UI 设计
- 流畅的动画和交互

## 🛠️ 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| React | 19.1.1 | UI 框架 |
| TypeScript | 5.9.3 | 类型安全 |
| React Router | 6.x | 路由管理 |
| Zustand | 5.0.8 | 状态管理 |
| Axios | 1.13.2 | HTTP 客户端 |
| Tailwind CSS | 3.4.18 | 样式系统 |
| Vite | 7.1.7 | 构建工具 |
| Vitest | 4.0.8 | 单元测试 |

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/         # React 组件
│   │   ├── file-upload/   # 文件上传相关组件
│   │   ├── file-preview/  # 文件预览相关组件
│   │   ├── navigation/    # 导航组件
│   │   ├── layout/        # 布局组件
│   │   └── common/        # 通用组件
│   ├── pages/             # 页面组件
│   │   ├── HomePage.tsx
│   │   ├── FileUploadPage.tsx
│   │   ├── FilePreviewPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── services/          # API 服务
│   ├── stores/            # Zustand 状态存储
│   ├── types/             # TypeScript 类型定义
│   ├── App.tsx            # 主应用入口
│   ├── router.tsx         # 路由配置
│   ├── main.tsx           # 应用启动文件
│   └── index.css          # 全局样式
├── tests/
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── e2e/              # 端到端测试（可选）
├── package.json           # 项目依赖
├── tsconfig.json          # TypeScript 配置
├── vite.config.ts         # Vite 配置
└── README.md              # 本文件
```

## 🚀 快速开始

### 前提条件

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:5173 启动。

### 构建生产版本

```bash
npm run build
```

生产文件将输出到 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 👨‍💻 开发指南

### 创建新组件

1. 在 `src/components` 下创建组件文件
2. 在相应的 `index.ts` 中导出组件
3. 在页面中导入和使用

### 创建新的 API 服务

1. 在 `src/services` 下创建 API 文件
2. 在页面中导入和使用

### 创建新的状态存储

使用 Zustand 创建状态管理：

```typescript
import { create } from 'zustand'

export const useMyStore = create((set) => ({
  // 状态和操作
}))
```

## 🧪 测试

### 运行测试

```bash
npm test
```

### 测试覆盖率

```bash
npm test -- --coverage
```

## 🌐 路由配置

| 路由 | 组件 | 说明 |
|------|------|------|
| `/` | HomePage | 首页 |
| `/upload` | FileUploadPage | 文件上传 |
| `/preview/:fileId` | FilePreviewPage | 文件预览 |
| `/*` | NotFoundPage | 404 页面 |

## 📦 环境变量

创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

## 🚢 部署

### 构建

```bash
npm run build
```

### Docker 部署

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📖 额外资源

- [React 文档](https://react.dev)
- [React Router 文档](https://reactrouter.com)
- [Zustand 文档](https://github.com/pmndrs/zustand)
- [Tailwind CSS 文档](https://tailwindcss.com)
- [Vite 文档](https://vitejs.dev)

---

**版本**: 1.0.0
**最后更新**: 2025-11-10

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
