# Email User Agent (邮件用户代理)

一个支持SMTP发送和POP3接收功能的跨平台邮件客户端。

## 功能特性

- ✉️ **邮件发送**: 支持SMTP协议发送邮件
- 📬 **邮件接收**: 支持POP3协议接收邮件
- 🔧 **多服务器支持**: 兼容多种邮件服务器（QQ、163、Sina等）
- 🖥️ **跨平台**: 支持Windows和Linux系统
- 🎨 **图形界面**: 提供友好的GUI界面
- 🔐 **安全预留**: 为未来的Base64编码定制和安全通信预留接口

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

### 常见邮箱服务器配置

#### QQ邮箱
- SMTP服务器: smtp.qq.com
- SMTP端口: 465 (SSL) 或 587 (TLS)
- POP3服务器: pop.qq.com
- POP3端口: 995 (SSL)

#### 163邮箱
- SMTP服务器: smtp.163.com
- SMTP端口: 465 (SSL) 或 25
- POP3服务器: pop.163.com
- POP3端口: 995 (SSL) 或 110

#### Sina邮箱
- SMTP服务器: smtp.sina.com
- SMTP端口: 465 (SSL) 或 25
- POP3服务器: pop.sina.com
- POP3端口: 995 (SSL) 或 110

### 发送邮件

1. 点击"发送邮件"标签
2. 填写收件人地址、主题和正文
3. 点击"发送"按钮

### 接收邮件

1. 点击"接收邮件"标签
2. 点击"接收邮件"按钮
3. 邮件列表将显示收到的邮件
4. 点击邮件查看详细内容

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
├── smtp_client.py         # SMTP客户端实现
├── pop3_client.py         # POP3客户端实现
├── email_encoder.py       # Base64编码接口（预留）
├── gui.py                 # GUI界面实现
├── config_manager.py      # 配置管理
├── requirements.txt       # 依赖列表
├── README.md             # 使用说明
├── MANUAL.md             # 详细用户手册
└── docs/
    └── REPORT.md         # 项目报告
```

## 技术实现

- **SMTP协议**: 使用Python标准库`smtplib`实现
- **POP3协议**: 使用Python标准库`poplib`实现
- **GUI界面**: 使用`tkinter`实现跨平台图形界面
- **编码扩展**: 预留`email_encoder.py`接口用于未来的Base64编码定制

## 安全通信预留接口

本项目为未来的安全通信功能预留了接口，包括：
- Base64编码表的自动协商机制
- 一次一变的编码表更新机制
- 与其他客户端兼容的编码/解码接口

详见`email_encoder.py`中的接口定义。

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
