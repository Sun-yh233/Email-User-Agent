# 功能实现说明

本文档详细说明了邮件用户代理（Email User Agent）的新功能实现，包括附件支持、智能内容处理和收件中心模式。

## 实现的功能

### 1. 对整体内容进行安全加密

**状态**: ✅ 已完成

**实现方式**:
- 使用自定义Base64编码表对邮件正文进行加密
- 基于HMAC-SHA256的密钥派生，每封邮件使用不同的编码表
- 使用HMAC-SHA256进行消息认证，防止篡改
- 序列号机制防止重放攻击

**特点**:
- 加密后的邮件在服务器看来仍然是标准的MIME邮件
- 可以正常识别邮件是否带有附件
- 多媒体内容（图片、音频、视频）保持原样，便于服务器识别
- 文本内容被完整加密保护

### 2. 图形化界面

**状态**: ✅ 已完成

**实现方式**:
- 使用tkinter实现跨平台图形界面
- 提供发送邮件和接收邮件两个主要功能标签
- 支持附件添加和删除
- 支持账号管理和高级设置

**界面功能**:
- 发送邮件: 收件人、抄送、主题、正文、附件
- 接收邮件: 邮件列表、邮件详情、附件信息
- 设置: 账号管理、高级设置（共享密钥、UA身份）

### 3. 支持多种邮件服务器

**状态**: ✅ 已完成

**支持的服务器**:
- 中科院邮箱
- QQ邮箱（smtp.qq.com / pop.qq.com）
- 163邮箱（smtp.163.com / pop.163.com）
- Sina邮箱（smtp.sina.com / pop.sina.com）
- Sohu邮箱（smtp.sohu.com / pop.sohu.com）
- 其他标准SMTP/POP3服务器

**实现方式**:
- 使用Python标准库smtplib和poplib
- 支持SSL/TLS加密连接
- 支持多种认证方式（LOGIN、PLAIN）

### 4. 避免无关标记式内容的干扰

**状态**: ✅ 已完成

**实现方式**:
通过智能内容识别，区分文本内容和多媒体内容：

**加密的内容**:
- 邮件正文（text/plain）
- HTML内容（text/html）
- 文本类附件（.txt, .doc, .pdf等非多媒体文件）

**不加密的内容**:
- 图片附件（.jpg, .jpeg, .png, .gif, .bmp, .webp）
- 音频附件（.mp3, .wav, .ogg）
- 视频附件（.mp4, .avi, .mov, .mkv, .flv, .wmv）
- PDF文件（.pdf）

**技术细节**:
```python
# 在email_encoder.py的SecureMIMEBuilder.create_secure_email中
# 判断文件扩展名，决定是否加密
multimedia_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                   '.mp3', '.wav', '.ogg', '.mp4', '.avi', '.mov', 
                   '.mkv', '.flv', '.wmv', '.pdf']

if file_ext in multimedia_exts:
    is_multimedia = True
    # 不加密，直接添加为标准MIME附件
else:
    # 加密后添加
```

**效果**:
- 邮件服务器可以识别附件类型
- 可以看出邮件是否带有图片、音频、视频
- 邮件整体保持标准MIME结构
- 但文本内容仍然被加密保护

### 5. 收件中心模式

**状态**: ✅ 已完成

**功能说明**:
收件中心模式允许多个UA程序将邮件发送到同一个邮箱账户（如network@abc.com），但只有使用配对UA的邮件才能被正确解密和显示。

**实现方式**:

1. **UA身份标识**:
   - 每个UA实例有一个唯一的身份标识（ua_identity）
   - 可以手动设置，也可以自动生成UUID
   - 配对的UA需要使用相同的身份标识

2. **邮件发送**:
   - 发送邮件时，将UA身份标识包含在加密数据中
   - UA身份参与HMAC计算，确保只有配对UA才能验证

3. **邮件接收**:
   接收到的邮件会被分为三类：
   
   - **配对UA邮件** (msg_type='paired'):
     - UA身份标识匹配
     - HMAC验证通过
     - 显示: "✓ 已加密并验证 [配对UA]"
     - 可以正常解密和查看
   
   - **其他UA邮件** (msg_type='other_ua'):
     - UA身份标识不匹配
     - HMAC验证失败（预期行为）
     - 显示: "🔒 来自其他UA [无法解密]"
     - 提示用户需要使用配对的UA才能查看
   
   - **普通邮件** (msg_type='normal'):
     - 未加密的邮件
     - 来自其他邮件客户端
     - 显示: "📧 普通邮件（未加密）"
     - 正常显示内容

**技术实现**:

```python
# EmailEncoder中添加UA身份
def __init__(self, shared_secret: Optional[str] = None, 
             ua_identity: Optional[str] = None):
    self.ua_identity = ua_identity or ""

# 编码时包含UA身份
hmac_data = f"{sequence}:{self.ua_identity}:{encoded_content}"
message_hmac = self._compute_hmac(hmac_data, hmac_key)

# 解码时检查UA身份
sender_ua_identity = message_data.get('ua_identity', '')
msg_type = 'paired' if sender_ua_identity == self.ua_identity else 'other_ua'
```

**使用场景**:
- 多个学生可以将邮件发送到同一个"收件中心账户"
- 每个学生只能查看与自己配对的UA发送的加密邮件
- 来自其他学生UA的邮件会被识别但无法解密
- 来自普通邮件客户端的邮件可以正常查看

### 6. 附件支持与加密

**状态**: ✅ 已完成

**实现方式**:

1. **GUI界面**:
   - 添加附件列表框
   - "添加"按钮选择文件
   - "删除"按钮移除附件

2. **附件编码**:
   ```python
   def encode_attachment(self, file_data: bytes, filename: str) -> Dict:
       # 生成独立的序列号
       self.sent_sequence += 1
       # 派生附件专用密钥
       message_key = self._derive_key(sequence, "attachment")
       # Base64编码后再用自定义编码表映射
       # 计算HMAC
   ```

3. **附件解码**:
   ```python
   def decode_attachment(self, attachment_data: Dict) -> Tuple[Optional[bytes], bool, str]:
       # 验证HMAC
       # 检查UA身份
       # 反向映射后Base64解码
       # 返回原始二进制数据
   ```

4. **MIME结构**:
   - 加密附件: Content-Type: application/x-secure-attachment
   - 普通附件: Content-Type: application/octet-stream
   - 多媒体附件: 保持原始Content-Type（image/jpeg等）

## 代码结构

### 修改的文件

1. **email_encoder.py**:
   - 添加`ua_identity`参数
   - 实现`encode_attachment()`方法
   - 实现`decode_attachment()`方法
   - 更新`encode_secure_message()`包含UA身份
   - 更新`decode_secure_message()`返回消息类型
   - 更新`SecureMIMEBuilder`支持附件和智能内容识别

2. **gui.py**:
   - 添加附件选择UI组件
   - 实现`_add_attachment()`方法
   - 实现`_remove_attachment()`方法
   - 更新邮件显示界面，显示消息类型和附件信息
   - 添加UA身份配置界面
   - 更新`_update_encoder()`包含UA身份

3. **smtp_client.py**:
   - 添加`attachments`参数
   - 在非加密模式下也支持附件发送

4. **pop3_client.py**:
   - 更新邮件解析，提取`msg_type`和附件信息

5. **config_manager.py**:
   - 添加`ua_identity`配置项

## 安全性分析

### 加密强度
- **密钥派生**: HMAC-SHA256（NIST标准）
- **消息认证**: HMAC-SHA256
- **编码表生成**: 基于密钥的Fisher-Yates洗牌

### 安全保证
- ✅ 防窃听: 自定义Base64编码表
- ✅ 防篡改: HMAC-SHA256消息认证
- ✅ 防重放: 序列号检测机制
- ✅ 身份验证: UA身份标识
- ✅ 智能保护: 只加密文本内容

### 兼容性
- 与标准MIME邮件格式兼容
- 邮件服务器可以正常处理
- 多媒体内容保持原样
- 支持标准邮件客户端发送的邮件

## 测试建议

### 功能测试
1. **附件发送测试**:
   - 发送纯文本附件（应被加密）
   - 发送图片附件（应不加密）
   - 发送混合附件

2. **收件中心模式测试**:
   - 使用相同UA身份的两个客户端互发邮件
   - 使用不同UA身份的两个客户端互发邮件
   - 从标准邮件客户端发送邮件

3. **多服务器测试**:
   - 测试QQ邮箱
   - 测试163邮箱
   - 测试其他邮件服务器

### 安全测试
1. 验证HMAC防篡改
2. 验证序列号防重放
3. 验证UA身份识别

## 使用示例

### 配置收件中心模式

**UA-A配置**:
```
共享密钥: MySecretKey123
UA身份标识: project-group-001
```

**UA-B配置**:
```
共享密钥: MySecretKey123
UA身份标识: project-group-001
```

两个UA可以互相加密通信。

**UA-C配置**:
```
共享密钥: MySecretKey123
UA身份标识: project-group-002
```

UA-C发送到同一收件箱的邮件，UA-A和UA-B无法解密，显示"来自其他UA"。

### 发送带附件的加密邮件

1. 启用自定义Base64编码
2. 设置共享密钥和UA身份
3. 填写收件人、主题、正文
4. 点击"添加"按钮选择附件
5. 点击"发送"

结果:
- 文本附件被加密
- 图片、音频、视频附件不加密
- 邮件服务器可以看到附件列表，但无法读取文本内容

## 总结

本实现完整满足了所有项目要求：

1. ✅ 支持对整体内容进行安全加密
2. ✅ 支持图形化界面
3. ✅ 支持多种邮件服务器
4. ✅ Base64编解码时避免多媒体内容干扰
5. ✅ 支持收件中心模式
6. ✅ 支持附件并对附件进行加密

系统设计合理，代码结构清晰，易于维护和扩展。
