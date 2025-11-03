# 域名和HTTPS快速参考卡

**应用**: datalablife/jackcwf:main
**主机**: https://coolpanel.jackcwf.com
**应用ID**: mg8c40oowo80o08o0gsw0gwc

---

## ⚡ 3分钟快速检查清单

```
☐ 步骤1: DNS验证 (1分钟)
  command: nslookup www.jackcwf.com
  expected: 显示 Coolify 主机 IP 地址

☐ 步骤2: 登录Coolify (1分钟)
  url: https://coolpanel.jackcwf.com
  navigate: 找到应用 "datalablife/jackcwf:main"

☐ 步骤3: 添加域名 (1分钟)
  action: Domains → Add Domain
  value: www.jackcwf.com
  ssl: Let's Encrypt
  redirect: HTTP to HTTPS (启用)
  save: 保存
```

---

## 🎯 Coolify Web UI 操作步骤

### 位置
```
Coolify Panel → Applications → datalablife/jackcwf:main → Domains
```

### 操作

#### 添加主域名
1. 点击 **Add Domain**
2. 输入: `www.jackcwf.com`
3. SSL证书: 选择 **Let's Encrypt**
4. 检查: ✓ Redirect HTTP to HTTPS
5. 点击 **Save**

#### 添加开发端口 (可选)
1. 再次点击 **Add Domain**
2. 输入: `www.jackcwf.com:3003`
3. SSL证书: 选择 **Let's Encrypt**
4. 检查: ✓ Redirect HTTP to HTTPS
5. 点击 **Save**

---

## ⏱️ 预计时间表

| 步骤 | 时间 | 说明 |
|------|------|------|
| DNS验证 | 2 min | `nslookup` 命令 |
| 登录和导航 | 1 min | Coolify面板 |
| 添加域名 | 2 min | Web UI操作 |
| 等待证书生效 | 5-10 min | Let's Encrypt自动处理 |
| **总计** | **10-15 min** | 包括证书生效 |

---

## ✅ 验证域名配置

```bash
# 1. DNS解析
nslookup www.jackcwf.com
# 预期: 返回 Coolify 主机 IP

# 2. HTTPS访问
curl -I https://www.jackcwf.com
# 预期: HTTP/2 200 或 301 (重定向)

# 3. HTTP重定向
curl -I http://www.jackcwf.com
# 预期: HTTP/1.1 301 → 重定向到 HTTPS

# 4. 检查证书
openssl s_client -connect www.jackcwf.com:443
# 预期: 显示 Let's Encrypt 证书信息
```

---

## 🆘 快速故障排除

### DNS 未解析
```bash
# 验证DNS设置
dig www.jackcwf.com
nslookup www.jackcwf.com

# 如果显示"NXDOMAIN"或无结果:
# 1. 检查域名注册商的DNS设置
# 2. 确认A记录指向 Coolify 主机IP
# 3. 等待DNS传播 (15-60分钟)
```

### 证书错误
```bash
# 如果显示证书错误:
# 1. 确保DNS已正确解析
# 2. 等待Let's Encrypt证书生效 (5-10分钟)
# 3. 清除浏览器缓存
# 4. 检查应用日志:
coolify app logs mg8c40oowo80o08o0gsw0gwc
```

### 端口3003无法访问
```bash
# 如果 :3003 无法访问:
# 方案1: 检查防火墙
sudo ufw status
sudo ufw allow 3003

# 方案2: 检查应用是否在该端口监听
netstat -tulpn | grep 3003
ss -tulpn | grep 3003

# 方案3: Coolify不支持该配置
# 联系Coolify支持或查看DOMAIN_HTTPS_CONFIGURATION.md 方案B
```

---

## 🔗 相关文档

- **详细配置**: `docs/deployment/DOMAIN_HTTPS_CONFIGURATION.md`
- **完整索引**: `docs/deployment/INDEX.md`
- **故障诊断**: `docs/deployment/DEPLOYMENT_DIAGNOSIS.md`
- **Coolify配置**: `docs/deployment/COOLIFY_CONFIG.md`

---

## 💡 常见问题速答

**Q: 多久能访问?**
A: DNS 生效后立即访问，通常 2-10 分钟。证书需要 5-10 分钟生效。

**Q: 开发端口 3003 需要配置什么?**
A: 同样配置域名即可，`www.jackcwf.com:3003`。Coolify 会自动代理或使用防火墙。

**Q: 如何限制访问?**
A: 使用 IP 白名单（推荐）或 HTTP 基本认证。详见 DOMAIN_HTTPS_CONFIGURATION.md。

**Q: 能用其他域名吗?**
A: 可以，操作步骤相同。确保DNS配置正确即可。

**Q: SSL 证书自动续期吗?**
A: 是的，Let's Encrypt 证书由 Coolify 自动管理和续期。

---

**最后更新**: 2025-10-30
**应用状态**: ✓ running:healthy
**部署环境**: Coolify 4.0.0+

