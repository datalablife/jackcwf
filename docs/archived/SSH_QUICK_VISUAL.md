# GitHub SSH Key - 快速可视化指南

## 🎯 GitHub SSH Key 在哪里？

### 网页位置

```
https://github.com/settings/keys
```

### 逐步导航

```
1. 打开 GitHub 网站
   https://github.com

2. 点击右上角头像
   │
   ├─ Your repositories
   ├─ Your projects
   ├─ Your stars
   ├─ Your gists
   ├─ Settings ← 点这里！
   ├─ Sign out
   └─ ...

3. 左侧菜单 - Access
   │
   ├─ SSH and GPG keys ← 点这里！
   ├─ Emails
   ├─ Notifications
   ├─ Billing and plans
   └─ ...

4. 页面上方
   ├─ Authenticate with a passkey
   ├─ SSH keys ← 在这里添加
   ├─ GPG keys
   ├─ Deploy keys
   └─ ...

5. 点击绿色按钮
   "New SSH key" ← 添加新 Key
```

---

## 🚀 快速 3 步使用 SSH 推送

### 第 1 步：生成 SSH Key

```bash
# 在终端运行（替换你的邮箱）
ssh-keygen -t ed25519 -C "your_email@github.com"

# 提示时全部按 Enter（3 次回车）
```

### 第 2 步：复制公钥到 GitHub

```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 输出类似：
# ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKx... your_email@github.com

# 1. 复制整个内容（从 ssh-ed25519 到 @gmail.com）
# 2. 打开 https://github.com/settings/keys
# 3. 点击 "New SSH key"
# 4. Title: "My Computer" 或 "WSL"
# 5. Key: 粘贴公钥内容
# 6. 点击 "Add SSH key"
```

### 第 3 步：推送代码

```bash
# 在项目目录运行
cd /mnt/d/工作区/云开发/working

# 改成 SSH URL（如果还没改）
git remote set-url origin git@github.com:datalablife/jackcwf.git

# 推送
git push -u origin main

# 完成！✅
```

---

## 📍 GitHub SSH Key 页面长这样

```
Settings
├─ Account
├─ Access
│  ├─ SSH and GPG keys          ← 你在这里！
│  ├─ Emails
│  ├─ Authentication
│  └─ Sessions
├─ Code, planning, and automation
└─ ...

┌─────────────────────────────────────┐
│ SSH and GPG keys                    │
├─────────────────────────────────────┤
│                                     │
│ Authenticate with a passkey         │
│ ┌─────────────────────────────────┐ │
│ │  No passkeys configured         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ SSH keys                            │
│ ┌─────────────────────────────────┐ │
│ │  New SSH key  [+ 按钮]          │ │
│ ├─────────────────────────────────┤ │
│ │  Key 1: My WSL Machine          │ │
│ │  Added on Jan 15, 2024          │ │
│ │  Last used: Jan 20, 2024        │ │
│ │  [Delete]                       │ │
│ │                                 │ │
│ │  Key 2: Windows Laptop          │ │
│ │  Added on Dec 10, 2023          │ │
│ │  Never used                     │ │
│ │  [Delete]                       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ GPG keys                            │
│ ┌─────────────────────────────────┐ │
│ │  [+ New GPG key]                │ │
│ │  (No keys configured)           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Deploy keys                         │
│ ┌─────────────────────────────────┐ │
│ │  (No deploy keys configured)    │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔑 "New SSH key" 表单

```
┌──────────────────────────────────────────────────┐
│ Add a new SSH key                                │
├──────────────────────────────────────────────────┤
│                                                  │
│ Title *                                          │
│ ┌────────────────────────────────────────────┐  │
│ │ My WSL Machine                             │  │ ← 填一个描述名称
│ └────────────────────────────────────────────┘  │
│ Provide a descriptive label for the new key     │
│                                                  │
│ Key type *                                       │
│ ● Authentication Key                           │ ← 保持选中
│ ○ Signing Key                                  │
│                                                  │
│ Key *                                            │
│ ┌────────────────────────────────────────────┐  │
│ │ ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...   │  │
│ │ ...IKx8/p4GDXxnW6tYqvBa8c...               │  │ ← 粘贴公钥
│ │ your_email@github.com                      │  │
│ │                                             │  │
│ │                                             │  │
│ └────────────────────────────────────────────┘  │
│ Paste a public SSH key                          │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Add SSH key] 按钮（绿色）                   │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## ✅ 完整流程图

```
┌─────────────────────────────────────────────────────────┐
│ 第 1 步：生成 SSH Key                                  │
│ ssh-keygen -t ed25519 -C "email@github.com"           │
│ ↓                                                       │
│ 生成文件：                                            │
│ - ~/.ssh/id_ed25519     （私钥 - 保密）               │
│ - ~/.ssh/id_ed25519.pub （公钥 - 可分享）             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 第 2 步：复制公钥                                       │
│ cat ~/.ssh/id_ed25519.pub                              │
│ ↓                                                       │
│ 复制整个输出内容（以 ssh-ed25519 开头）               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 第 3 步：添加到 GitHub                                 │
│ 1. 打开 https://github.com/settings/keys               │
│ 2. 点击 "New SSH key"                                  │
│ 3. Title: "My Computer"                                │
│ 4. Key: 粘贴公钥                                       │
│ 5. 点击 "Add SSH key"                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 第 4 步：配置 Git 使用 SSH                             │
│ git remote set-url origin \                            │
│   git@github.com:datalablife/jackcwf.git              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 第 5 步：推送代码                                       │
│ git push -u origin main                                │
│ ↓                                                       │
│ ✅ 成功！代码已推送到 GitHub                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 在手机上看 GitHub SSH Key 设置

如果你用手机：

```
1. 打开 GitHub App 或网页
2. 点击左下角头像
3. 向下滑动找 "Settings"
4. 点 "SSH and GPG keys"
5. 点 "New SSH key"
6. 填写和添加
```

---

## 🚨 SSH Key 安全提示

### ✅ 可以做的

- ✅ 分享 **公钥**（id_ed25519.pub）
- ✅ 在 GitHub 粘贴公钥
- ✅ 多台电脑都可以有不同的 SSH Key
- ✅ 给每个 Key 取个名字便于识别

### ❌ 不能做的

- ❌ 分享 **私钥**（id_ed25519）
- ❌ 把私钥上传到 GitHub
- ❌ 把私钥发送给别人
- ❌ 把私钥复制到其他电脑
- ❌ 在代码里提交私钥

---

## 🔧 如果出错了

### 错误 1：Permission denied (publickey)

```bash
# 原因：SSH Key 没有添加到 GitHub

# 解决：
1. 检查 GitHub settings/keys 是否有你的 SSH Key
2. 检查 Key 内容是否完整
3. 重新复制和添加（通常是复制不完整）
```

### 错误 2：Could not resolve hostname

```bash
# 原因：网络问题

# 解决：
1. 检查网络连接
2. 尝试 ping github.com
3. 如果在 WSL，可能需要配置 DNS
4. 改用 HTTPS 临时推送
```

---

## 🎯 总结

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `ssh-keygen -t ed25519 -C "email@github.com"` | 生成 SSH Key |
| 2 | `cat ~/.ssh/id_ed25519.pub` | 显示公钥 |
| 3 | 访问 https://github.com/settings/keys | GitHub 设置页面 |
| 4 | 点 "New SSH key" 并粘贴 | 添加公钥到 GitHub |
| 5 | `git remote set-url origin git@github.com:datalablife/jackcwf.git` | 改成 SSH URL |
| 6 | `git push -u origin main` | 推送代码 |

---

## 📚 相关文件

- **SSH_SETUP_GUIDE.md** - 完整详细指南
- **PUSH_TO_GITHUB.md** - 其他推送方法
- **QUICK_COMMANDS.txt** - 命令参考

---

**就这么简单！🎉**

