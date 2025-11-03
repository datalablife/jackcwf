# Coolify 域名和HTTPS配置指南

**应用信息**:
- 应用ID: mg8c40oowo80o08o0gsw0gwc
- 应用名: datalablife/jackcwf:main
- 当前状态: running:healthy

---

## 📋 配置任务

### 任务1: 添加主域名 www.jackcwf.com (强制HTTPS)

#### 步骤1: 进入应用设置

1. 访问 https://coolpanel.jackcwf.com
2. 登录到 Coolify 控制面板
3. 找到应用 **"datalablife/jackcwf:main"**
4. 点击应用进入详情页面

#### 步骤2: 配置域名

1. 在应用详情页面找到 **"Domains"** 或 **"Custom Domains"** 部分
2. 点击 **"Add Domain"** 或 **"+ Add"** 按钮
3. 在输入框中输入域名: **www.jackcwf.com**
4. 选择或创建SSL证书:
   - 选择 **"Let's Encrypt"** (免费自动证书)
   - 或者 **"Create New"** → 选择 Let's Encrypt
5. 启用 **"Redirect HTTP to HTTPS"** 或类似选项 (强制HTTPS)
6. 点击 **"Save"** 或 **"Create"** 保存配置

#### 步骤3: 验证SSL证书

- Coolify 会自动向 Let's Encrypt 请求证书
- 确保域名DNS已正确解析到Coolify主机IP
- 证书验证通常需要 **5-10 分钟**
- 证书生效后，应用会自动应用

#### 预期结果

✓ https://www.jackcwf.com → 访问应用 (自动跳转)
✓ http://www.jackcwf.com → 自动重定向到 HTTPS

---

### 任务2: 配置开发测试端口 www.jackcwf.com:3003

#### 方案A: 使用Coolify代理 (推荐，如支持)

1. 在应用详情页面的 **"Domains"** 部分
2. 点击 **"Add Domain"** 或 **"+ Add"** 按钮
3. 输入: **www.jackcwf.com:3003**
4. 配置:
   - 指向应用 (Coolify会自动代理到应用)
   - 启用HTTPS
   - 设置环境为开发或沙箱模式
5. 点击 **"Save"** 保存

#### 方案B: 使用防火墙规则 (备选方案)

如果Coolify不支持端口代理，可以:

1. **配置防火墙规则**
   ```bash
   # 允许 3003 端口
   sudo ufw allow 3003
   ```

2. **使用 Nginx 代理** (可选)
   - 配置 Nginx 将 3003 请求代理到应用的开发端口
   - 为 www.jackcwf.com:3003 配置 SSL 证书

3. **配置 Coolify**
   - 添加环境变量指定开发端口
   - 配置应用在该端口上运行

#### 预期结果

✓ https://www.jackcwf.com:3003 → 访问开发前端 (如配置成功)

---

### 任务3: 访问控制 (仅开发访问)

#### 选项A: IP白名单配置 (推荐)

1. 在应用设置中找到 **"Access Control"** 或 **"IP Whitelist"** 选项
2. 添加你的IP地址:
   - 获取你的IP: `curl https://ifconfig.me`
   - 输入IP地址到白名单
3. 启用白名单模式
4. 保存配置

**优点**: 快速、安全、无需额外凭证

#### 选项B: HTTP基本认证

1. 在应用环境变量中设置:
   ```bash
   AUTH_ENABLED=true
   AUTH_USER=dev
   AUTH_PASSWORD=your_secure_password
   ```

2. 在Reflex应用中实现认证检查

**优点**: 灵活、不依赖IP地址、适合多人开发

#### 选项C: 环境分离 (最安全)

1. 创建单独的开发应用实例
2. 仅在开发实例上暴露 3003 端口
3. 配置开发实例的IP白名单

---

## 🔧 命令行配置 (可选备选方案)

如果需要通过Coolify CLI配置，可以尝试:

```bash
# 更新应用域名配置
coolify app update mg8c40oowo80o08o0gsw0gwc \
  --fqdn www.jackcwf.com \
  --force-https true

# 列出应用详情确认配置
coolify app get mg8c40oowo80o08o0gsw0gwc

# 查看应用的所有域名配置
coolify app domains mg8c40oowo80o08o0gsw0gwc
```

**注意**: Coolify CLI 对域名和SSL的支持可能有限，推荐使用 Web UI 操作。

---

## ⚙️ 配置检查清单

### 前置条件 (必须完成)
- [ ] DNS 已解析: `www.jackcwf.com` 指向 Coolify 主机 IP
- [ ] DNS 生效已验证: `nslookup www.jackcwf.com` 返回正确IP
- [ ] Coolify 应用状态: `running:healthy`
- [ ] 应用可在本地访问: http://localhost:3000

### DNS 验证

```bash
# 验证 DNS 解析
nslookup www.jackcwf.com
# 应该显示:
# Name:   www.jackcwf.com
# Address: <Coolify主机IP>

# 或使用 dig 命令
dig www.jackcwf.com
# 应该在 ANSWER SECTION 显示解析结果

# 检查 DNS 传播状态 (可选)
# https://mxtoolbox.com/mxlookup.aspx (在线工具)
```

### 配置步骤
- [ ] 登录 Coolify 控制面板
- [ ] 进入应用 "datalablife/jackcwf:main" 详情页
- [ ] 在 Domains 部分添加 www.jackcwf.com
- [ ] 启用 Let's Encrypt 自动证书
- [ ] 配置强制 HTTPS 重定向
- [ ] 保存配置
- [ ] 等待证书生效 (5-10分钟)
- [ ] 添加开发端口 :3003 (如需要)
- [ ] 配置 IP 白名单或认证 (如需要)

### 验证配置
- [ ] 访问 https://www.jackcwf.com 成功
- [ ] HTTP 访问 http://www.jackcwf.com 自动跳转到 HTTPS
- [ ] HTTPS 证书有效 (浏览器地址栏无警告)
- [ ] 应用功能正常运行
- [ ] 开发端口 https://www.jackcwf.com:3003 可访问 (如已配置)
- [ ] 非授权 IP 无法访问 (如已配置 IP 白名单)

---

## 🆘 常见问题和解决方案

### Q1: DNS 解析失败

**问题症状**: 访问 www.jackcwf.com 显示 "DNS 查询失败" 或 "无法连接"

**解决步骤**:
1. 验证 DNS 已正确配置
   ```bash
   nslookup www.jackcwf.com
   ```
2. 如果返回空或错误，检查域名注册商的 DNS 设置
3. 确认 DNS 指向的IP是否为 Coolify 主机的正确IP
4. DNS 传播可能需要 15-60 分钟，请耐心等待

### Q2: SSL 证书验证失败

**问题症状**: 访问显示 "证书错误" 或 "不安全连接"

**原因和解决**:
- 原因: DNS 未正确解析或传播延迟
- 解决: 等待 DNS 传播完成 (5-10分钟)，然后重新尝试
- 如果问题持续: 检查 Coolify 日志 `coolify app logs mg8c40oowo80o08o0gsw0gwc`

### Q3: 域名已在其他应用使用

**问题症状**: 添加域名时显示 "域名已被使用" 错误

**原因和解决**:
- 原因: 该域名绑定到其他应用
- 解决:
  1. 从其他应用移除旧的域名绑定
  2. 在当前应用中重新添加域名

### Q4: 3003 端口访问失败

**问题症状**: https://www.jackcwf.com:3003 无法访问

**原因和解决**:
- 原因A: Coolify 不支持自定义端口代理
  - 解决: 使用方案B (防火墙+Nginx)

- 原因B: 防火墙未开放 3003 端口
  - 解决: 运行 `sudo ufw allow 3003`

- 原因C: 应用未在 3003 端口监听
  - 解决: 检查应用配置，确保应用在该端口运行

### Q5: HTTPS 强制重定向不工作

**问题症状**: http://www.jackcwf.com 仍然访问 HTTP 版本

**原因和解决**:
- 原因: Coolify 或 Nginx 配置未启用重定向
- 解决:
  1. 确保在 Coolify 中启用 "Redirect HTTP to HTTPS"
  2. 重新保存配置
  3. 清除浏览器缓存
  4. 如果问题持续，检查 Nginx 配置是否有冲突

### Q6: 浏览器显示"不是私密连接"警告

**问题症状**: 浏览器显示 SSL 证书警告

**原因和解决**:
- 原因: Let's Encrypt 证书尚未生效或验证失败
- 解决:
  1. 刷新页面 (F5)
  2. 清除浏览器缓存
  3. 等待几分钟让证书完全生效
  4. 如果 24 小时后仍有问题，检查 DNS 和防火墙配置

---

## 📊 预期配置结果

完成所有配置后，你应该看到以下结果:

| 访问方式 | 状态 | 说明 |
|---------|------|------|
| http://www.jackcwf.com | ✓ 重定向 | → https://www.jackcwf.com |
| https://www.jackcwf.com | ✓ 访问成功 | 显示应用首页 |
| https://www.jackcwf.com:3003 | ✓ 访问成功 | (如已配置) 显示开发版本 |
| 非白名单IP访问 | ✓ 拒绝 | (如已配置) 返回 403 或认证页面 |

---

## 📝 完整配置流程 (总结)

### 第一步: DNS 验证 (2 分钟)
```bash
# 验证域名已指向 Coolify
nslookup www.jackcwf.com
```

### 第二步: 配置主域名 (5 分钟)
1. 登录 https://coolpanel.jackcwf.com
2. 进入应用详情
3. 添加域名 www.jackcwf.com
4. 启用 Let's Encrypt
5. 启用 HTTPS 重定向
6. 保存

### 第三步: 等待证书生效 (5-10 分钟)
- Coolify 自动请求和配置证书
- 刷新浏览器查看结果

### 第四步: 验证配置 (3 分钟)
- 测试 https://www.jackcwf.com
- 测试 HTTP 重定向
- 检查证书有效期

### 第五步: 配置开发端口 (可选, 5 分钟)
- 添加 www.jackcwf.com:3003
- 选择方案A或B
- 配置访问控制

### 第六步: 配置访问控制 (可选, 5 分钟)
- 设置 IP 白名单，或
- 配置 HTTP 基本认证

---

## 🎯 下一步

**立即执行**:
1. 在本地验证 DNS: `nslookup www.jackcwf.com`
2. 登录 Coolify 控制面板
3. 按照配置步骤操作
4. 报告任何错误或问题

**如遇到问题**:
1. 查看上方 "常见问题" 部分
2. 检查 Coolify 应用日志
3. 验证 DNS 和防火墙配置
4. 参考 docs/deployment/COOLIFY_CONFIG.md 获取更多信息

---

**配置完成时间预计**: 20-30 分钟 (包括 DNS 传播和证书生效)

祝你配置顺利！🚀

