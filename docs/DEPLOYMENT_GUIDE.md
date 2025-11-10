# 部署指南

本文档详细说明如何将数据文件管理系统部署到各种环境。

## 📋 前置要求

### 系统要求
- Docker（用于容器化部署）
- Node.js 16+（用于本地部署）
- nginx（用于反向代理）
- Git（用于版本管理）

### 网络要求
- 互联网连接
- 开放必要的端口（80, 443）
- 足够的磁盘空间（至少 2GB）
- 足够的内存（至少 2GB）

## 🚀 本地部署

### 1. 前端部署

#### 安装依赖

```bash
cd frontend
npm install
```

#### 构建生产版本

```bash
npm run build
```

生产文件将在 `dist/` 目录中生成。

#### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动。

### 2. 后端部署

请参考后端项目的部署指南。

## 🐳 Docker 部署

### 1. 构建前端镜像

创建 `Dockerfile`：

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

创建 `nginx.conf`：

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # 配置单页应用路由
    location / {
        try_files $uri /index.html;
    }

    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 不缓存 HTML
    location ~* \.html?$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # 日志
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
}
```

### 2. 构建镜像

```bash
docker build -t data-management-system:latest .
```

### 3. 运行容器

```bash
docker run -d \
  --name data-management-frontend \
  -p 80:80 \
  -e VITE_API_URL=http://api.example.com \
  data-management-system:latest
```

### 4. Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    container_name: data-management-frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    container_name: data-management-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    container_name: data-management-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:

networks:
  default:
    driver: bridge
```

启动所有服务：

```bash
docker-compose up -d
```

## ☁️ Vercel 部署

### 1. 连接 GitHub

1. 访问 [Vercel](https://vercel.com)
2. 使用 GitHub 账号登录
3. 点击"Import Project"
4. 选择你的 GitHub 仓库

### 2. 配置构建设置

- **Framework Preset**: Next.js（或选择 Other）
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### 3. 环境变量

在 Vercel 仪表板中设置环境变量：

```
VITE_API_URL=https://api.example.com
```

### 4. 部署

点击"Deploy"按钮开始部署。

## 🔧 Nginx 配置

### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. 配置文件

编辑 `/etc/nginx/sites-available/default`：

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name example.com www.example.com;

    # 重定向 HTTP 到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 前端应用
    location / {
        root /var/www/frontend/dist;
        index index.html;
        try_files $uri /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # WebSocket 支持
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 日志
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
}
```

### 3. 启动 Nginx

```bash
# 检查配置
sudo nginx -t

# 启动服务
sudo systemctl start nginx

# 启用开机自启
sudo systemctl enable nginx

# 重新加载配置
sudo systemctl reload nginx
```

## 🔒 SSL/TLS 配置

### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --nginx -d example.com -d www.example.com

# 自动更新
sudo systemctl enable certbot.timer
```

## 📊 监控和日志

### 1. 应用日志

```bash
# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Docker 日志
docker logs -f data-management-frontend
```

### 2. 性能监控

使用工具如：
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- New Relic

## 🔄 CI/CD 流程

### GitHub Actions 示例

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci --prefix frontend

      - name: Build
        run: npm run build --prefix frontend

      - name: Deploy to Vercel
        uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## 🚨 故障排查

### 问题：403 Forbidden 错误

**解决方案**：
1. 检查 Nginx 配置中的 root 路径
2. 检查文件权限：`sudo chmod -R 755 /var/www/frontend/dist`
3. 检查 SELinux 设置（如果启用）

### 问题：API 连接失败

**解决方案**：
1. 检查 VITE_API_URL 环境变量
2. 检查后端服务状态
3. 检查防火墙和网络连接
4. 查看浏览器控制台错误

### 问题：构建失败

**解决方案**：
1. 检查 Node.js 版本：`node --version`
2. 清除 node_modules：`rm -rf node_modules && npm install`
3. 检查磁盘空间：`df -h`
4. 查看构建日志：`npm run build 2>&1 | tee build.log`

## 📈 性能优化

### 1. 启用压缩

在 Nginx 中：

```nginx
gzip on;
gzip_types text/plain text/css text/xml text/javascript
    application/x-javascript application/xml+rss
    application/javascript application/json;
gzip_min_length 1000;
gzip_comp_level 6;
```

### 2. CDN 配置

使用 Cloudflare 或其他 CDN 服务：
- 加快全球访问速度
- 提供 DDoS 保护
- 自动压缩和缓存

### 3. 数据库优化

- 添加索引
- 查询优化
- 连接池配置

## 🔐 安全最佳实践

### 1. 环境变量

不要在代码中硬编码敏感信息：

```bash
# 使用环境变量
export VITE_API_URL=https://api.example.com
npm run build
```

### 2. CORS 配置

在后端配置 CORS：

```python
# FastAPI 示例
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 安全头

在 Nginx 中添加安全头：

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## 📝 备份和恢复

### 1. 数据库备份

```bash
# PostgreSQL 备份
pg_dump dbname > backup.sql

# 恢复
psql dbname < backup.sql
```

### 2. 应用备份

```bash
# 备份应用文件
tar -czf backup-$(date +%Y%m%d).tar.gz /var/www/frontend/dist
```

---

**最后更新**: 2025-11-10
*本部署指南适用于生产环境配置*
