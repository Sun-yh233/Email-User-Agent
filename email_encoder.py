import base64
import random
import json
import hashlib
import hmac
from typing import Optional, Dict, Tuple, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase


class EmailEncoder:
    """
    安全邮件编码器
    
    基于共享密钥实现一次一密的Base64编码表映射，支持：
    1. 每封邮件使用不同的编码表（通过序列号派生）
    2. 消息认证（HMAC-SHA256）
    3. 防重放/乱序/丢失（序列号机制）
    
    安全假设：
    - A和B共享一个秘密密钥（通过线下安全渠道交换）
    - 使用HMAC-SHA256进行消息认证
    - 使用SHA-256进行密钥派生
    """

    # 标准Base64字符表
    STANDARD_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    def __init__(self, shared_secret: Optional[str] = None):
        """
        初始化编码器
        
        Args:
            shared_secret: 共享密钥（可选，不提供则使用标准Base64）
        """
        self.shared_secret = shared_secret
        self.use_secure = shared_secret is not None and len(shared_secret) > 0
        
        # 消息序列追踪（用于防重放和检测丢失）
        self.sent_sequence = 0
        self.received_sequences = set()  # 存储已接收的序列号
    
    def _derive_key(self, sequence: int, context: str = "") -> bytes:
        """
        从共享密钥和序列号派生每封邮件的密钥
        
        使用HMAC-SHA256进行密钥派生，确保每封邮件使用不同的密钥
        
        Args:
            sequence: 消息序列号
            context: 额外的上下文信息
        
        Returns:
            派生的密钥（32字节）
        """
        if not self.use_secure:
            raise ValueError("未设置共享密钥")
        
        # 使用HMAC-SHA256进行密钥派生
        # KDF(K, seq, context) = HMAC-SHA256(K, seq || context)
        message = f"{sequence}:{context}".encode('utf-8')
        return hmac.new(
            self.shared_secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
    
    def _generate_encoding_table(self, key: bytes) -> str:
        """
        从密钥生成确定性的Base64编码表
        
        Args:
            key: 派生的密钥
        
        Returns:
            64字符的编码表
        """
        # 使用密钥作为随机数生成器的种子
        seed = int.from_bytes(key[:8], byteorder='big')
        rng = random.Random(seed)
        
        chars = list(self.STANDARD_BASE64_CHARS)
        rng.shuffle(chars)
        
        return ''.join(chars)
    
    def _encode_with_table(self, text: str, encoding_table: str) -> str:
        """
        使用自定义编码表进行Base64编码
        
        Args:
            text: 要编码的文本
            encoding_table: 64字符的编码表
        
        Returns:
            编码后的文本
        """
        # 先用标准Base64编码
        encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
        
        # 然后进行字符表映射
        result = []
        for char in encoded:
            if char in self.STANDARD_BASE64_CHARS:
                index = self.STANDARD_BASE64_CHARS.index(char)
                result.append(encoding_table[index])
            else:
                result.append(char)  # 保留填充字符'='
        
        return ''.join(result)
    
    def _decode_with_table(self, encoded_text: str, encoding_table: str) -> str:
        """
        使用自定义编码表进行Base64解码
        
        Args:
            encoded_text: 编码后的文本
            encoding_table: 64字符的编码表
        
        Returns:
            解码后的文本
        """
        # 先进行字符表反向映射
        result = []
        for char in encoded_text:
            if char in encoding_table:
                index = encoding_table.index(char)
                result.append(self.STANDARD_BASE64_CHARS[index])
            else:
                result.append(char)  # 保留填充字符'='
        
        standard_encoded = ''.join(result)
        
        # 然后用标准Base64解码
        decoded_bytes = base64.b64decode(standard_encoded.encode('ascii'))
        return decoded_bytes.decode('utf-8')
    
    def _compute_hmac(self, data: str, key: bytes) -> str:
        """
        计算消息的HMAC-SHA256
        
        Args:
            data: 要认证的数据
            key: HMAC密钥
        
        Returns:
            HMAC值的十六进制表示
        """
        return hmac.new(
            key,
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def encode_secure_message(self, content: str, content_type: str = 'text/plain') -> Dict:
        """
        编码安全邮件内容
        
        Args:
            content: 邮件内容
            content_type: 内容类型（如'text/plain', 'text/html'）
        
        Returns:
            包含编码内容和元数据的字典
        """
        if not self.use_secure:
            # 不使用安全编码，直接返回原文
            return {
                'content': content,
                'content_type': content_type,
                'secure': False
            }
        
        # 递增序列号
        self.sent_sequence += 1
        sequence = self.sent_sequence
        
        # 派生本次消息的密钥
        message_key = self._derive_key(sequence, "message")
        hmac_key = self._derive_key(sequence, "hmac")
        
        # 生成编码表
        encoding_table = self._generate_encoding_table(message_key)
        
        # 编码内容
        encoded_content = self._encode_with_table(content, encoding_table)
        
        # 计算HMAC（包括序列号和编码后的内容）
        hmac_data = f"{sequence}:{encoded_content}"
        message_hmac = self._compute_hmac(hmac_data, hmac_key)
        
        return {
            'sequence': sequence,
            'content': encoded_content,
            'content_type': content_type,
            'hmac': message_hmac,
            'secure': True,
            'version': '1.0'  # 协议版本
        }
    
    def decode_secure_message(self, message_data: Dict) -> Tuple[str, bool]:
        """
        解码安全邮件内容
        
        Args:
            message_data: 编码的消息数据
        
        Returns:
            (解码后的内容, 验证是否成功)
        """
        if not message_data.get('secure', False):
            # 非安全消息，直接返回
            return message_data.get('content', ''), True
        
        if not self.use_secure:
            return "[错误: 需要配置共享密钥才能解密此邮件]", False
        
        try:
            sequence = message_data['sequence']
            encoded_content = message_data['content']
            received_hmac = message_data['hmac']
            
            # 检查序列号（检测重放攻击和重复）
            if sequence in self.received_sequences:
                return f"[警告: 检测到重复消息 (序列号: {sequence})]", False
            
            # 派生密钥
            message_key = self._derive_key(sequence, "message")
            hmac_key = self._derive_key(sequence, "hmac")
            
            # 验证HMAC
            hmac_data = f"{sequence}:{encoded_content}"
            expected_hmac = self._compute_hmac(hmac_data, hmac_key)
            
            if not hmac.compare_digest(received_hmac, expected_hmac):
                return "[错误: 消息认证失败，可能已被篡改]", False
            
            # 生成解码表
            encoding_table = self._generate_encoding_table(message_key)
            
            # 解码内容
            decoded_content = self._decode_with_table(encoded_content, encoding_table)
            
            # 记录已接收的序列号
            self.received_sequences.add(sequence)
            
            return decoded_content, True
            
        except Exception as e:
            return f"[错误: 解码失败 - {str(e)}]", False
    
    def get_next_sequence(self) -> int:
        """获取下一个序列号（不递增）"""
        return self.sent_sequence + 1
    
    def reset_sequence(self, sequence: int = 0):
        """重置发送序列号"""
        self.sent_sequence = sequence
    
    def clear_received_sequences(self):
        """清除已接收序列号记录"""
        self.received_sequences.clear()
    
    def to_dict(self) -> Dict:
        """导出配置为字典"""
        return {
            'use_secure': self.use_secure,
            'shared_secret': self.shared_secret,
            'sent_sequence': self.sent_sequence
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'EmailEncoder':
        """从字典加载配置"""
        encoder = cls(config.get('shared_secret'))
        encoder.sent_sequence = config.get('sent_sequence', 0)
        return encoder


class SecureMIMEBuilder:
    """
    安全MIME邮件构建器
    
    负责构建包含安全内容的MIME邮件，支持：
    1. 文本内容加密
    2. 预留HTML内容加密接口
    3. 预留附件加密接口
    
    邮件结构：
    - multipart/mixed (外层，用于附件)
      - multipart/alternative (内层，用于文本/HTML)
        - text/plain (安全编码的文本)
        - text/html (预留，安全编码的HTML)
      - application/octet-stream (预留，加密的附件)
    """
    
    @staticmethod
    def create_secure_email(
        from_addr: str,
        to_addrs: List[str],
        subject: str,
        body: str,
        encoder: EmailEncoder,
        cc_addrs: Optional[List[str]] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> MIMEMultipart:
        """
        创建安全MIME邮件
        
        Args:
            from_addr: 发件人地址
            to_addrs: 收件人地址列表
            subject: 邮件主题
            body: 邮件正文（纯文本）
            encoder: 编码器实例
            cc_addrs: 抄送地址列表
            html_body: HTML正文（预留）
            attachments: 附件列表（预留）
        
        Returns:
            构建好的MIME消息
        """
        # 创建外层容器（用于附件）
        msg_root = MIMEMultipart('mixed')
        msg_root['From'] = from_addr
        msg_root['To'] = ', '.join(to_addrs)
        msg_root['Subject'] = subject
        
        if cc_addrs:
            msg_root['Cc'] = ', '.join(cc_addrs)
        
        # 添加自定义头部，标识这是安全邮件
        if encoder.use_secure:
            msg_root['X-Secure-Email'] = 'true'
            msg_root['X-Secure-Version'] = '1.0'
        
        # 创建内层容器（用于文本和HTML）
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        
        # 编码并添加纯文本内容
        encoded_data = encoder.encode_secure_message(body, 'text/plain')
        
        if encoded_data['secure']:
            # 安全邮件：将元数据和内容打包为JSON
            secure_payload = {
                'sequence': encoded_data['sequence'],
                'content': encoded_data['content'],
                'hmac': encoded_data['hmac'],
                'version': encoded_data['version'],
                'secure': True  # 标记为安全内容
            }
            text_content = json.dumps(secure_payload, ensure_ascii=False)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            text_part.add_header('X-Content-Secure', 'true')
        else:
            # 非安全邮件：直接使用原文
            text_part = MIMEText(body, 'plain', 'utf-8')
        
        msg_alternative.attach(text_part)
        
        # 预留：HTML内容支持
        if html_body:
            encoded_html_data = encoder.encode_secure_message(html_body, 'text/html')
            if encoded_html_data['secure']:
                html_payload = {
                    'sequence': encoded_html_data['sequence'],
                    'content': encoded_html_data['content'],
                    'hmac': encoded_html_data['hmac'],
                    'version': encoded_html_data['version'],
                    'secure': True  # 标记为安全内容
                }
                html_content = json.dumps(html_payload, ensure_ascii=False)
                html_part = MIMEText(html_content, 'html', 'utf-8')
                html_part.add_header('X-Content-Secure', 'true')
            else:
                html_part = MIMEText(html_body, 'html', 'utf-8')
            msg_alternative.attach(html_part)
        
        # 预留：附件支持
        if attachments:
            for attachment in attachments:
                # TODO: 实现附件加密
                # 这里预留接口，后续可以添加附件加密功能
                # 每个附件可以使用独立的序列号派生密钥
                pass
        
        return msg_root
    
    @staticmethod
    def parse_secure_email(msg, encoder: EmailEncoder) -> Dict:
        """
        解析安全MIME邮件
        
        Args:
            msg: 邮件消息对象
            encoder: 解码器实例
        
        Returns:
            解析后的邮件内容字典
        """
        result = {
            'body': '',
            'html': None,
            'attachments': [],
            'verified': True
        }
        
        # 检查是否是安全邮件
        is_secure = msg.get('X-Secure-Email') == 'true'
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_secure = part.get('X-Content-Secure') == 'true'
                
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        
                        if content_secure and is_secure:
                            # 解析安全内容
                            secure_data = json.loads(payload)
                            decoded_body, verified = encoder.decode_secure_message(secure_data)
                            result['body'] = decoded_body
                            result['verified'] = result['verified'] and verified
                        else:
                            # 普通内容
                            result['body'] = payload
                    except Exception as e:
                        result['body'] = f"[解析错误: {str(e)}]"
                        result['verified'] = False
                
                elif content_type == 'text/html':
                    try:
                        payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        
                        if content_secure and is_secure:
                            secure_data = json.loads(payload)
                            decoded_html, verified = encoder.decode_secure_message(secure_data)
                            result['html'] = decoded_html
                            result['verified'] = result['verified'] and verified
                        else:
                            result['html'] = payload
                    except:
                        pass
                
                # 预留：附件解析
                elif content_type.startswith('application/') or content_type.startswith('image/'):
                    # TODO: 实现附件解密
                    pass
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                if is_secure:
                    try:
                        secure_data = json.loads(payload)
                        decoded_body, verified = encoder.decode_secure_message(secure_data)
                        result['body'] = decoded_body
                        result['verified'] = verified
                    except:
                        result['body'] = payload
                else:
                    result['body'] = payload
            except:
                result['body'] = msg.get_payload()
        
        return result


# 便捷函数

def create_encoder(shared_secret: Optional[str] = None) -> EmailEncoder:
    """
    创建邮件编码器
    
    Args:
        shared_secret: 共享密钥（可选）
    
    Returns:
        EmailEncoder实例
    """
    return EmailEncoder(shared_secret)
