# 构建与测试说明

## 验证测试结果

本项目已通过以下验证测试:

### 1. 代码语法检查 ✓
所有Python模块编译通过，无语法错误：
- main.py
- smtp_client.py
- pop3_client.py
- email_encoder.py
- config_manager.py
- gui.py

### 2. 模块导入测试 ✓
所有核心模块可以正常导入：
- SMTP客户端模块
- POP3客户端模块
- 邮件编码器模块
- 配置管理器模块

### 3. Base64编码功能测试 ✓
测试项目：
- 标准Base64编码/解码
- 自定义Base64编码表
- 共享密钥协商
- 编码表兼容性

所有测试通过，验证了：
- 编码后的文本与原文不同
- 解码后可以还原原文
- 相同密钥的编码器互相兼容
- 支持中文编码

### 4. 配置管理测试 ✓
测试项目：
- 账号添加
- 账号列表
- 账号检索
- 当前账号管理
- 服务商自动识别
- 设置管理

所有测试通过，验证了配置系统正常工作。

### 5. SMTP/POP3客户端测试 ✓
测试项目：
- 服务器配置获取（QQ、163、Sina、Gmail）
- SMTP客户端初始化
- POP3客户端初始化
- 接口完整性

所有测试通过，验证了客户端接口正确。

### 6. GUI模块结构测试 ✓
验证项目：
- GUI模块可以导入
- 关键类定义完整
  - EmailClientGUI
  - AccountManagerWindow
  - AdvancedSettingsWindow
- 运行函数可用

注意：GUI的完整测试需要在有图形界面的环境中进行。

## 构建可执行文件

### Linux平台

```bash
# 安装构建工具
pip install pyinstaller

# 确保tkinter已安装
# Ubuntu/Debian:
sudo apt-get install python3-tk

# CentOS/RHEL:
sudo yum install python3-tkinter

# 运行构建脚本
./build_linux.sh

# 或手动构建
pyinstaller --onefile --windowed --name EmailClient-Linux main.py

# 运行可执行文件
chmod +x dist/EmailClient-Linux
./dist/EmailClient-Linux
```

### Windows平台

```cmd
REM 安装构建工具
pip install pyinstaller

REM 运行构建脚本
build_windows.bat

REM 或手动构建
pyinstaller --onefile --windowed --name EmailClient-Windows main.py

REM 运行可执行文件
dist\EmailClient-Windows.exe
```

## 运行要求

### 系统要求
- Python 3.6或更高版本
- tkinter (通常包含在Python标准发行版中)

### 依赖库
除了PyInstaller（仅用于构建），不需要安装任何第三方库。
所有核心功能都使用Python标准库实现。

## 功能验证清单

- [x] SMTP协议实现（RFC 5321）
- [x] POP3协议实现（RFC 1939）
- [x] SSL/TLS加密支持
- [x] 多邮件服务器支持
- [x] 图形用户界面（tkinter）
- [x] 账号管理功能
- [x] Base64编码定制接口
- [x] 编码表协商机制
- [x] 一次一变支持
- [x] 跨平台兼容性
- [x] 完整的中文文档

## 项目文件清单

### 核心代码
- main.py - 主程序入口
- smtp_client.py - SMTP客户端实现
- pop3_client.py - POP3客户端实现
- email_encoder.py - Base64编码器
- config_manager.py - 配置管理器
- gui.py - 图形用户界面

### 文档
- README.md - 项目介绍和快速开始
- MANUAL.md - 详细用户手册
- docs/REPORT.md - 项目报告
- docs/BUILD_TEST.md - 本文件

### 构建脚本
- build_linux.sh - Linux构建脚本
- build_windows.bat - Windows构建脚本
- requirements.txt - 依赖列表

### 配置
- .gitignore - Git忽略文件
- LICENSE - MIT许可证

## 使用示例

### 从源代码运行

```bash
# 克隆仓库
git clone https://github.com/Sun-yh233/Email-User-Agent.git
cd Email-User-Agent

# 直接运行
python main.py
```

### 配置邮箱账号

1. 启动程序后，点击"设置" -> "账号管理"
2. 点击"添加"按钮
3. 填写账号信息或使用"自动识别服务器"功能
4. 保存配置

### 发送邮件

1. 切换到"发送邮件"标签
2. 填写收件人、主题、正文
3. 点击"发送"按钮

### 接收邮件

1. 切换到"接收邮件"标签
2. 点击"接收邮件"按钮
3. 点击邮件列表查看详情

## 注意事项

1. **授权码**: 大多数邮箱服务商（如QQ、163）需要使用授权码而不是登录密码
2. **SSL/TLS**: 建议始终启用SSL/TLS加密
3. **防火墙**: 确保防火墙允许SMTP(465/587)和POP3(995/110)端口
4. **服务开启**: 在邮箱设置中开启SMTP和POP3服务

## 常见问题

### 问题1: 无法连接到服务器
- 检查网络连接
- 确认服务器地址和端口正确
- 检查防火墙设置

### 问题2: 认证失败
- 确认使用的是授权码而不是登录密码
- 在邮箱设置中开启SMTP/POP3服务
- 检查账号和密码是否正确

### 问题3: tkinter导入错误（Linux）
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter

# Fedora
sudo dnf install python3-tkinter
```

## 技术支持

- GitHub仓库: https://github.com/Sun-yh233/Email-User-Agent
- 问题反馈: 在GitHub上提交Issue

---

**版本**: 1.0  
**测试日期**: 2025-12-28  
**测试状态**: 通过 ✓
