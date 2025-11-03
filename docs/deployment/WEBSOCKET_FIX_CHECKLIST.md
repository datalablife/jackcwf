# WebSocket 修复 - 快速操作清单

**应用状态**: ✅ running:healthy
**问题**: ⚠️ WebSocket 连接超时 (`wss://www.jackcwf.com/_event`)
**预计修复时间**: 5-10 分钟

---

## ✅ 快速清单 (按顺序执行)

### [ ] 步骤 1: 重新部署应用 (5 分钟)

```
1. 打开浏览器，访问:
   https://coolpanel.jackcwf.com

2. 登录到 Coolify 面板

3. 在左侧菜单或应用列表中找到应用:
   "datalablife/jackcwf:main"
   或
   UUID: mg8c40oowo80o08o0gsw0gwc

4. 点击应用进入详情页

5. 查找按钮:
   - 如果看到 "Redeploy" → 点击它
   - 如果看到 "Restart" → 点击它
   - 如果都没看到 → 找 "Actions" 或 "More" 菜单

6. 确认重新部署/重启

7. 等待应用重启 (大约 2-3 分钟)
   - 应该看到状态: running:healthy
```

### [ ] 步骤 2: 验证 WebSocket (2 分钟)

```
1. 访问应用:
   https://www.jackcwf.com

2. 打开浏览器开发工具:
   按 F12

3. 点击 "Network" 标签

4. 刷新页面 (Ctrl+R 或 Cmd+R)

5. 在请求列表中查找 "WS" 或 "_event"

6. 检查状态列：
   ✅ 如果显示 "101 Switching Protocols" → 成功!
   ❌ 如果显示 "Failed" 或红色 → 继续步骤 3
```

### [ ] 步骤 3: 测试登录 (1 分钟)

```
1. 关闭开发工具 (F12)

2. 尝试登录:
   - 输入用户名
   - 输入密码
   - 点击登录按钮

3. 检查结果:
   ✅ 成功登录 → 问题已解决!
   ❌ 仍然显示错误 → 执行步骤 4
```

### [ ] 步骤 4: 手动修复 (如步骤 3 失败)

如果上面的步骤都不能解决，需要手动修改 Traefik 配置。

**方案 B 的完整说明在**: `CURRENT_STATUS_AND_NEXT_STEPS.md` - 方案 B 部分

---

## 🔍 快速诊断命令

如果需要了解具体的错误原因，在服务器上执行：

```bash
# 查看应用日志
docker logs -n 50 mg8c40oowo80o08o0gsw0gwc-090124817222

# 查看 Traefik 日志（检查 WebSocket 相关）
docker logs -n 100 coolify-proxy | grep -i websocket

# 检查应用状态
coolify app get mg8c40oowo80o08o0gsw0gwc
```

---

## 📊 预期结果

### ✅ 修复成功的标志

1. **浏览器 Network 标签**:
   - 看到请求: `wss://www.jackcwf.com/_event`
   - 状态: `101 Switching Protocols`
   - 连接类型: `websocket`

2. **应用界面**:
   - 不再显示 "Cannot connect to server: timeout" 错误
   - 页面加载正常
   - 登录表单可以交互

3. **功能验证**:
   - 能输入用户名和密码
   - 能成功登录
   - 应用正常使用

### ❌ 仍有问题的标志

- 浏览器 Console 有红色错误信息
- Network 标签中 `_event` 请求显示 "Failed"
- 输入用户名密码后点击登录，页面没有反应

---

## 💬 问题快速查询

| 问题 | 可能原因 | 解决方案 |
|------|--------|--------|
| 重新部署后仍超时 | Traefik 未重新加载配置 | 执行 `docker restart coolify-proxy` |
| 看不到 `_event` 请求 | 应用根本没有连接 | 检查是否能正常访问 https://www.jackcwf.com |
| 请求显示 503 | 后端应用未运行 | 检查 `docker ps` 中应用状态 |
| 请求显示 502 | 反向代理配置错误 | 执行方案 B 手动修复 |

---

## 📚 详细文档

- **完整指南**: `CURRENT_STATUS_AND_NEXT_STEPS.md`
- **Traefik 配置**: `TRAEFIK_WEBSOCKET_FIX.md`
- **诊断工具**: `DEPLOYMENT_DIAGNOSIS.md`

---

**提示**: 大多数情况下，步骤 1-3 就能解决问题。如果不行，再参考详细文档执行方案 B。

