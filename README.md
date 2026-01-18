# Email User Agent (邮件用户代理)

一个支持SMTP发送和POP3接收功能的跨平台邮件客户端，具有安全通信功能。

## 功能特性

- ✉️ **邮件发送**: 支持SMTP协议发送邮件
- 📬 **邮件接收**: 支持POP3协议接收邮件
- 🔐 **安全通信**: 基于共享密钥的端到端加密
- 🔄 **一次一密**: 每封邮件使用不同的编码表
- ✅ **消息认证**: HMAC-SHA256防篡改
- 🛡️ **防重放攻击**: 序列号机制防止重放和重复
- 📝 **MIME支持**: 完整的MIME邮件格式支持
- 🔧 **多服务器支持**: 兼容多种邮件服务器（QQ、163、Sina等）
- 🖥️ **跨平台**: 支持Windows和Linux系统
- 🎨 **图形界面**: 提供友好的GUI界面

## 系统要求

- Python 3.6+
- tkinter (通常包含在Python标准库中)

## 安装与运行

### 从源代码运行

1. 克隆仓库:
```bash
git clone https://github.com/Sun-yh233/Email-User-Agent.git
cd Email-User-Agent
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 运行程序:
```bash
python main.py
```

### 使用可执行文件

下载对应平台的可执行文件：
- Windows: `EmailClient-Windows.exe`
- Linux: `EmailClient-Linux`

直接双击运行（Windows）或在终端运行（Linux）。

## 使用说明

### 配置邮箱账号

1. 启动程序后，点击"设置"菜单
2. 输入您的邮箱信息：
   - 邮箱地址
   - SMTP服务器地址
   - SMTP端口（通常为25、465或587）
   - POP3服务器地址
   - POP3端口（通常为110或995）
   - 授权码或密码

### 发送邮件

1. 点击"发送邮件"标签
2. 填写收件人地址、主题和正文
3. 点击"发送"按钮

### 接收邮件

1. 点击"接收邮件"标签
2. 点击"接收邮件"按钮
3. 邮件列表将显示收到的邮件
4. 点击邮件查看详细内容
5. 安全邮件会显示验证状态（✓ 已加密并验证 / ⚠️ 验证失败）

## 安全通信

### 配置安全邮件

1. 与通信对方约定一个共享密钥（建议16字符以上）
2. 打开"设置" -> "高级设置"
3. 勾选"启用自定义Base64编码"
4. 输入共享密钥
5. 保存设置

### 安全特性

- **一次一密**: 每封邮件使用不同的编码表，即使一封被破解也不影响其他邮件
- **消息认证**: 使用HMAC-SHA256验证邮件完整性，防止篡改
- **防重放**: 序列号机制自动检测重复邮件
- **健壮性**: 支持邮件丢失、重复、乱序情况下的正常解密
- **透明加密**: 对用户透明，发送和接收与普通邮件无异

详细说明请参考 [SECURITY_REPORT.md](SECURITY_REPORT.md)

## 构建可执行文件

### Windows

```bash
pyinstaller --onefile --windowed --name EmailClient-Windows main.py
```

### Linux

```bash
pyinstaller --onefile --windowed --name EmailClient-Linux main.py
```

## 项目结构

```
Email-User-Agent/
├── main.py                 # 主程序入口
├── smtp_client.py         # SMTP客户端实现（支持安全MIME）
├── pop3_client.py         # POP3客户端实现（支持安全解密）
├── email_encoder.py       # 安全邮件编码器（一次一密+HMAC）
├── gui.py                 # GUI界面实现
├── config_manager.py      # 配置管理（包括序列号持久化）
├── requirements.txt       # 依赖列表
├── README.md             # 使用说明
└── SECURITY_REPORT.md    # 安全实现详细报告
```

## 技术实现

- **SMTP协议**: 使用Python标准库`smtplib`实现
- **POP3协议**: 使用Python标准库`poplib`实现
- **GUI界面**: 使用`tkinter`实现跨平台图形界面
- **安全加密**: 
  - HMAC-SHA256密钥派生和消息认证
  - 基于序列号的一次一密编码表
  - 完整的MIME格式支持
  - 预留HTML和附件加密接口

## 安全实现

本项目实现了完整的端到端加密邮件系统：

### 核心技术
- **密钥派生**: HMAC-SHA256从共享密钥派生每封邮件的密钥
- **一次一密**: 每封邮件使用独立的Base64编码表
- **消息认证**: HMAC-SHA256保证邮件完整性
- **序列号机制**: 防止重放、重复和支持乱序

### 算法来源
- **HMAC-SHA256**: Python标准库`hashlib`和`hmac`
- **Base64**: Python标准库`base64`
- **随机洗牌**: Python标准库`random`

### 安全保证
- ✅ 防窃听: 内容使用自定义编码表加密
- ✅ 防篡改: HMAC-SHA256消息认证码
- ✅ 防重放: 序列号检测机制
- ✅ 健壮性: 支持丢失、重复、乱序

详细的安全分析和实现说明请参考 [SECURITY_REPORT.md](SECURITY_REPORT.md)

## 预留接口

本项目为未来扩展预留了接口：

- **HTML内容加密**: `SecureMIMEBuilder`已支持HTML参数
- **附件加密**: 预留attachments参数和加密接口
- **密钥轮换**: 支持更新共享密钥
- **算法升级**: 模块化设计便于替换加密算法

## 兼容性说明

本客户端遵循标准的SMTP和POP3协议，能够与其他标准实现的客户端互操作。特别是：
- 支持标准的认证机制（LOGIN、PLAIN）
- 支持SSL/TLS加密连接
- 遵循RFC 5321 (SMTP) 和 RFC 1939 (POP3)

## 许可证

MIT License

## 作者

Sun-yh233

## 参考资料

- RFC 5321: Simple Mail Transfer Protocol
- RFC 1939: Post Office Protocol - Version 3
- RFC 2045-2049: MIME (Multipurpose Internet Mail Extensions)
