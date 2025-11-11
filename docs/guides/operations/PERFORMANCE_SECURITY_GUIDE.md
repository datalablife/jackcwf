# 性能和安全审计指南

**文档版本**: 1.0
**创建日期**: 2025-11-10
**Phase**: Phase 5 - T082

---

## 📋 目录

1. [快速开始](#快速开始)
2. [性能测试](#性能测试)
3. [安全审计](#安全审计)
4. [基准和目标](#基准和目标)
5. [报告和分析](#报告和分析)
6. [改进建议](#改进建议)

---

## 快速开始

### 执行完整审计

```bash
# 使脚本可执行
chmod +x performance-security-test.sh

# 运行完整审计（性能 + 安全）
./performance-security-test.sh

# 运行仅性能测试
./performance-security-test.sh --perf-only

# 运行仅安全审计
./performance-security-test.sh --sec-only

# 详细模式（显示所有细节）
./performance-security-test.sh -v
```

### 前置条件

确保以下服务已运行：

```bash
# 终端 1: 启动后端
cd backend && ./start-backend.sh dev

# 终端 2: 启动前端
cd frontend && npm run dev

# 终端 3: 运行审计脚本
./performance-security-test.sh
```

---

## 性能测试

### 1. API 响应时间测试

**目标**: 验证 API 的响应时间是否满足基准

**测试内容**:
- ✅ 健康检查端点响应时间
- ✅ 10 次请求的平均/最小/最大值
- ✅ 与 500ms 基准对比

**基准要求**:
```
平均响应时间 < 500ms ✅
最大响应时间 < 1000ms ⚠️
最小响应时间 > 50ms
```

**示例输出**:
```
API 性能测试完成:
  平均响应时间: 0.1234s
  最小响应时间: 0.0987s
  最大响应时间: 0.1567s
✅ API 性能满足基准要求
```

### 2. 前端应用响应时间

**目标**: 确保首页加载快速

**测试内容**:
- ✅ 前端首页完整加载时间
- ✅ HTML 解析和呈现时间
- ✅ 资源加载情况

**基准要求**:
```
首页加载时间 < 3s ✅
白屏时间 < 1s ✅
可交互时间 < 2s ⚠️
```

### 3. 构建大小分析

**目标**: 监控前端构建包大小

**关键指标**:
```
总构建大小: < 1MB
JavaScript: < 400KB (gzip)
CSS: < 50KB (gzip)
```

**检查命令**:
```bash
# 分析构建大小
du -sh frontend/dist
du -sh frontend/dist/assets/*

# 查看压缩后大小
gzip -c frontend/dist/assets/index-*.js | wc -c
```

### 4. 并发用户模拟

**目标**: 验证系统在并发请求下的表现

**测试方式**:
- ✅ 同时发送 5 个并发请求
- ✅ 计算成功率
- ✅ 监测响应时间变化

**基准要求**:
```
并发成功率 = 100%
响应时间增长 < 20%
```

### 5. 数据库性能

**目标**: 确保数据库查询足够快

**测试内容**:
- ✅ 连接时间
- ✅ 简单查询时间
- ✅ 复杂查询时间

**基准要求**:
```
连接时间 < 100ms
简单查询 < 50ms
复杂查询 < 500ms
```

### 性能优化建议

#### 1. API 优化

```python
# ❌ 不好：N+1 查询
def get_files():
    files = File.query.all()
    for file in files:
        file.metadata = get_metadata(file.id)  # 多次查询

# ✅ 好：批量加载
def get_files():
    files = db.session.query(File).options(
        joinedload(File.metadata)
    ).all()
```

#### 2. 缓存策略

```python
# 实施 Redis 缓存
from functools import lru_cache

@cache.cached(timeout=300)  # 5 分钟缓存
def get_file_list():
    return File.query.all()
```

#### 3. 数据库索引

```sql
-- 添加关键列的索引
CREATE INDEX idx_file_created_at ON files(created_at DESC);
CREATE INDEX idx_datasource_id ON files(data_source_id);
```

#### 4. 前端优化

```typescript
// 代码分割
const FilePreview = React.lazy(() =>
  import('./pages/FilePreviewPage')
);

// 虚拟化长列表
<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={35}
>
  {renderItem}
</FixedSizeList>

// 记忆化组件
const MemoComponent = React.memo(Component);
```

---

## 安全审计

### 1. HTTPS/TLS 检查

**目标**: 确保所有通信都加密

**检查内容**:
```bash
# 检查 HTTPS 证书
openssl s_client -connect localhost:443 -tls1_2

# 验证证书有效期
openssl x509 -enddate -noout -in /path/to/cert.pem

# 检查 TLS 版本
curl -I --tlsv1.2 https://your-domain.com
```

**基准要求**:
- ✅ TLS 1.2+ 必须使用
- ✅ SSL 3.0 和 TLS 1.0 禁用
- ✅ 证书有效期 > 30 天

### 2. 安全响应头

**目标**: 实施防御性安全头

**关键头部**:

```nginx
# Nginx 配置示例
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

**验证方法**:
```bash
curl -I https://your-domain.com | grep -E "X-|Content-Security|Strict-Transport"
```

### 3. 依赖漏洞扫描

**前端依赖检查**:
```bash
# npm audit
npm audit --prefix frontend

# npm audit 修复
npm audit fix --prefix frontend

# 详细报告
npm audit --prefix frontend --json > audit-report.json
```

**后端依赖检查**:
```bash
# Poetry 依赖列表
poetry show

# Safety 安全检查（需要安装）
pip install safety
safety check

# 或使用 Dependabot（GitHub）
# 自动检查和提交 PR
```

### 4. 敏感信息检查

**目标**: 防止敏感信息泄露

**检查项目**:
```bash
# 查找潜在的敏感信息
grep -r "API_KEY\|SECRET\|PASSWORD\|TOKEN" . \
  --include="*.js" \
  --include="*.ts" \
  --include="*.py" \
  --exclude-dir=node_modules \
  --exclude-dir=.venv

# 检查 .env 文件是否提交
git log --all --full-history -- ".env"

# 检查敏感路径
find . -name "*.pem" -o -name "*.key" -o -name "*.cert"
```

**防护措施**:
```bash
# 添加 .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "*.pem" >> .gitignore
echo "*.key" >> .gitignore

# 扫描历史记录中的敏感信息
git-secrets --install
git-secrets --register-aws
```

### 5. 输入验证

**目标**: 防止 XSS、SQL 注入等攻击

**前端验证**:
```typescript
// 表单验证
const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// 输入清理
const sanitizeInput = (input: string) => {
  return DOMPurify.sanitize(input)
}

// 文件上传限制
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ALLOWED_TYPES = ['text/csv', 'application/vnd.ms-excel']
```

**后端验证**:
```python
from pydantic import BaseModel, validator, EmailStr

class FileUploadRequest(BaseModel):
    filename: str
    file_format: str
    file_size: int
    data_source_id: int

    @validator('filename')
    def filename_not_empty(cls, v):
        if not v or len(v) > 255:
            raise ValueError('Invalid filename')
        return v

    @validator('file_format')
    def format_valid(cls, v):
        allowed_formats = ['csv', 'xlsx', 'json']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of {allowed_formats}')
        return v
```

### 6. 认证和授权

**实现 JWT/Bearer Token**:

```typescript
// 前端：请求拦截器
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 前端：响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

```python
# 后端：验证 Token
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"user_id": user_id}
```

### 7. 错误处理

**目标**: 避免在错误消息中泄露敏感信息

```typescript
// ❌ 不好：泄露敏感信息
catch (error) {
  console.error(error)  // 可能显示文件路径、SQL 等
  return res.status(500).json({ error: error.message })
}

// ✅ 好：通用错误消息
catch (error) {
  logger.error('Detailed error info', { error })  // 只记录日志
  return res.status(500).json({ error: 'Internal server error' })
}
```

### 8. CORS 配置

**目标**: 限制跨域请求

```python
# FastAPI CORS 配置
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 生产环境
# allow_origins=["https://your-domain.com"]
```

### 9. 日志和监控

**目标**: 记录安全相关事件

```python
import logging

logger = logging.getLogger(__name__)

# 记录认证事件
logger.info(f"User login attempt: {username}")
logger.warning(f"Failed login: {username}")

# 记录敏感操作
logger.info(f"File deleted: {file_id} by user {user_id}")
logger.warning(f"Unauthorized access attempt: {endpoint}")

# 性能监控
import time
start = time.time()
# ... 操作 ...
duration = time.time() - start
logger.info(f"Operation took {duration:.2f}s")
```

### 10. 数据库安全

**目标**: 防止 SQL 注入

```python
# ❌ 不好：字符串拼接
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 好：参数化查询
from sqlalchemy import text

query = text("SELECT * FROM users WHERE id = :id")
result = session.execute(query, {"id": user_id})

# ✅ 好：使用 ORM
user = session.query(User).filter(User.id == user_id).first()
```

---

## 基准和目标

### 性能基准

| 指标 | 目标 | 当前 |
|------|------|------|
| API 平均响应时间 | < 500ms | ? |
| 首页加载时间 | < 3s | ? |
| 数据库查询 | < 50ms | ? |
| JS 包大小 | < 400KB | ? |
| CSS 包大小 | < 50KB | ? |

### 安全基准

| 项目 | 要求 | 状态 |
|------|------|------|
| HTTPS | 必须 | ⏳ |
| 安全头 | 5/5 | ⏳ |
| 依赖漏洞 | 0 个 | ✅ |
| 敏感信息 | 0 个 | ✅ |
| 输入验证 | 100% | ✅ |
| 错误处理 | 完整 | ✅ |
| 日志记录 | 已实现 | ⏳ |

---

## 报告和分析

### 生成的报告

审计脚本会生成以下报告：

```
test-results/
└── performance-security-report-20251110_093000.md
```

### 报告内容

- ✅ 执行摘要
- ✅ 性能评估结果
- ✅ 安全评估结果
- ✅ 合规性检查
- ✅ 建议和改进
- ✅ 下一步行动

### 查看报告

```bash
# 查看报告
cat test-results/performance-security-report-*.md

# 或使用编辑器
code test-results/performance-security-report-*.md
```

---

## 改进建议

### 立即行动（优先级高）

1. **配置安全头**
   ```nginx
   # Nginx 配置
   add_header X-Content-Type-Options "nosniff";
   add_header X-Frame-Options "SAMEORIGIN";
   ```

2. **修复依赖漏洞**
   ```bash
   npm audit fix
   poetry update
   ```

3. **启用 HTTPS**
   ```bash
   # 使用 Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   ```

### 短期行动（优先级中）

1. **实施日志聚合**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - 或 Splunk

2. **配置监控告警**
   - Prometheus + Grafana
   - 性能告警阈值

3. **增强访问控制**
   - 实施 RBAC
   - API 速率限制

### 长期行动（优先级低）

1. **定期渗透测试**
   - 每季度一次
   - 外部安全公司

2. **员工安全培训**
   - OWASP 培训
   - 安全编码实践

3. **灾难恢复计划**
   - 备份策略
   - 恢复过程

---

## 工具和资源

### 性能工具

- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **WebPageTest**: https://www.webpagetest.org/
- **Artillery**: https://artillery.io/ (负载测试)
- **Apache JMeter**: https://jmeter.apache.org/

### 安全工具

- **OWASP ZAP**: https://www.zaproxy.org/
- **Burp Suite**: https://portswigger.net/burp
- **npm audit**: 内置
- **safety**: https://github.com/pyupio/safety
- **git-secrets**: https://github.com/awslabs/git-secrets

### 参考标准

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE Top 25**: https://cwe.mitre.org/top25/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework

---

## 常见问题

### Q: 如何解释性能报告？

A: 查看以下关键指标：
- API 平均响应时间应 < 500ms
- 首页加载应 < 3s
- 并发成功率应 = 100%

### Q: 安全审计应该多久运行一次？

A: 建议：
- 每个 Pull Request 运行一次
- 每周运行完整审计
- 发布前强制通过

### Q: 如何改进性能？

A: 参考上面的"改进建议"章节。主要方向：
- 数据库优化（索引、查询）
- 缓存策略
- CDN 集成
- 代码分割

---

**最后更新**: 2025-11-10
**维护者**: Claude Code
**状态**: ✅ 完成
