import base64
import random
import json
import hashlib
import hmac
from typing import Optional, Dict, Tuple, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


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
    
    def __init__(self, shared_secret: Optional[str] = None, ua_identity: Optional[str] = None):
        """
        初始化编码器
        
        Args:
            shared_secret: 共享密钥（可选，不提供则使用标准Base64）
            ua_identity: UA身份标识（用于收件中心模式）
        """
        self.shared_secret = shared_secret
        self.use_secure = shared_secret is not None and len(shared_secret) > 0
        self.ua_identity = ua_identity or ""
        
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

    def _map_base64_with_table(self, b64_text: str, encoding_table: str) -> str:
        """
        仅对Base64字符串进行字符表映射，不再次进行Base64编码
        """
        result = []
        for char in b64_text:
            if char in self.STANDARD_BASE64_CHARS:
                index = self.STANDARD_BASE64_CHARS.index(char)
                result.append(encoding_table[index])
            else:
                result.append(char)
        return ''.join(result)

    def _unmap_base64_with_table(self, mapped_text: str, encoding_table: str) -> str:
        """
        将映射后的Base64字符串还原为标准Base64字符表
        """
        result = []
        for char in mapped_text:
            if char in encoding_table:
                index = encoding_table.index(char)
                result.append(self.STANDARD_BASE64_CHARS[index])
            else:
                result.append(char)
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
        
        # 计算HMAC（包括序列号、UA身份和编码后的内容）
        hmac_data = f"{sequence}:{self.ua_identity}:{encoded_content}"
        message_hmac = self._compute_hmac(hmac_data, hmac_key)
        
        return {
            'sequence': sequence,
            'content': encoded_content,
            'content_type': content_type,
            'hmac': message_hmac,
            'ua_identity': self.ua_identity,
            'secure': True,
            'version': '1.0'  # 协议版本
        }
    
    def encode_attachment(self, file_data: bytes, filename: str) -> Dict:
        """
        编码安全附件
        
        Args:
            file_data: 附件二进制数据
            filename: 附件文件名
        
        Returns:
            包含编码附件和元数据的字典
        """
        if not self.use_secure:
            # 不使用安全编码，直接返回原数据
            return {
                'data': file_data,
                'filename': filename,
                'secure': False
            }
        
        # 递增序列号
        self.sent_sequence += 1
        sequence = self.sent_sequence
        
        # 派生本次消息的密钥
        message_key = self._derive_key(sequence, "attachment")
        hmac_key = self._derive_key(sequence, "hmac")
        
        # 生成编码表
        encoding_table = self._generate_encoding_table(message_key)
        
        # 先用标准Base64编码附件
        b64_data = base64.b64encode(file_data).decode('ascii')

        # 然后使用自定义编码表重新映射（不再次Base64编码）
        encoded_data = self._map_base64_with_table(b64_data, encoding_table)
        
        # 计算HMAC
        hmac_data = f"{sequence}:{self.ua_identity}:{filename}:{encoded_data}"
        attachment_hmac = self._compute_hmac(hmac_data, hmac_key)
        
        return {
            'sequence': sequence,
            'data': encoded_data,
            'filename': filename,
            'hmac': attachment_hmac,
            'ua_identity': self.ua_identity,
            'secure': True,
            'version': '1.0'
        }
    
    def decode_secure_message(self, message_data: Dict) -> Tuple[str, bool, str]:
        """
        解码安全邮件内容
        
        Args:
            message_data: 编码的消息数据
        
        Returns:
            (解码后的内容, 验证是否成功, 消息类型)
            消息类型: 'paired' - 配对UA, 'other_ua' - 其他UA, 'normal' - 普通邮件
        """
        if not message_data.get('secure', False):
            # 非安全消息，直接返回
            return message_data.get('content', ''), True, 'normal'
        
        if not self.use_secure:
            return "[错误: 需要配置共享密钥才能解密此邮件]", False, 'other_ua'
        
        try:
            sequence = message_data['sequence']
            encoded_content = message_data['content']
            received_hmac = message_data['hmac']
            sender_ua_identity = message_data.get('ua_identity', '')
            
            # 检查UA身份（收件中心模式）
            msg_type = 'paired' if sender_ua_identity == self.ua_identity else 'other_ua'
            
            # 如果是其他UA的消息，直接返回错误，不尝试解密
            if msg_type == 'other_ua':
                return "[来自其他UA: 无法解密，请使用配对的UA查看]", False, msg_type
            
            # 检查序列号（检测重放攻击和重复）
            if sequence in self.received_sequences:
                return f"[警告: 检测到重复消息 (序列号: {sequence})]", False, msg_type
            
            # 派生密钥
            message_key = self._derive_key(sequence, "message")
            hmac_key = self._derive_key(sequence, "hmac")
            
            # 验证HMAC
            hmac_data = f"{sequence}:{sender_ua_identity}:{encoded_content}"
            expected_hmac = self._compute_hmac(hmac_data, hmac_key)
            
            if not hmac.compare_digest(received_hmac, expected_hmac):
                return "[错误: 消息认证失败，可能已被篡改]", False, msg_type
            
            # 生成解码表
            encoding_table = self._generate_encoding_table(message_key)
            
            # 解码内容
            decoded_content = self._decode_with_table(encoded_content, encoding_table)
            
            # 记录已接收的序列号
            self.received_sequences.add(sequence)
            
            return decoded_content, True, msg_type
            
        except Exception as e:
            msg_type = 'other_ua' if message_data.get('ua_identity', '') != self.ua_identity else 'paired'
            return f"[错误: 解码失败 - {str(e)}]", False, msg_type
    
    def decode_attachment(self, attachment_data: Dict) -> Tuple[Optional[bytes], bool, str]:
        """
        解码安全附件
        
        Args:
            attachment_data: 编码的附件数据
        
        Returns:
            (解码后的数据, 验证是否成功, 消息类型)
        """
        if not attachment_data.get('secure', False):
            # 非安全附件，直接返回
            return attachment_data.get('data'), True, 'normal'
        
        if not self.use_secure:
            return None, False, 'other_ua'
        
        try:
            sequence = attachment_data['sequence']
            encoded_data = attachment_data['data']
            filename = attachment_data['filename']
            received_hmac = attachment_data['hmac']
            sender_ua_identity = attachment_data.get('ua_identity', '')
            
            # 检查UA身份
            msg_type = 'paired' if sender_ua_identity == self.ua_identity else 'other_ua'
            
            # 如果是其他UA的附件，直接返回错误，不尝试解密
            if msg_type == 'other_ua':
                return None, False, msg_type
            
            # 检查序列号
            if sequence in self.received_sequences:
                return None, False, msg_type
            
            # 派生密钥
            message_key = self._derive_key(sequence, "attachment")
            hmac_key = self._derive_key(sequence, "hmac")
            
            # 验证HMAC
            hmac_data = f"{sequence}:{sender_ua_identity}:{filename}:{encoded_data}"
            expected_hmac = self._compute_hmac(hmac_data, hmac_key)
            
            if not hmac.compare_digest(received_hmac, expected_hmac):
                return None, False, msg_type
            
            # 生成解码表
            encoding_table = self._generate_encoding_table(message_key)
            
            # 解码数据（先反向映射，再Base64解码）
            standard_b64 = self._unmap_base64_with_table(encoded_data, encoding_table)
            decoded_data = base64.b64decode(standard_b64.encode('ascii'))
            
            # 记录已接收的序列号
            self.received_sequences.add(sequence)
            
            return decoded_data, True, msg_type
            
        except Exception as e:
            msg_type = 'other_ua' if attachment_data.get('ua_identity', '') != self.ua_identity else 'paired'
            return None, False, msg_type
    
    def get_next_sequence(self) -> int:
        """获取下一个序列号（不递增）"""
        return self.sent_sequence + 1
    
    def reset_sequence(self, sequence: int = 0):
        """重置发送序列号"""
        self.sent_sequence = sequence
    
    def clear_received_sequences(self, keep_recent: Optional[int] = None):
        """
        清除已接收序列号记录
        
        Args:
            keep_recent: 如果指定，仅保留最近N个序列号（用于防止内存无限增长）
        """
        if keep_recent is None:
            self.received_sequences.clear()
        else:
            if len(self.received_sequences) > keep_recent:
                # 保留最大的N个序列号
                sorted_seqs = sorted(self.received_sequences, reverse=True)
                self.received_sequences = set(sorted_seqs[:keep_recent])
    
    def to_dict(self) -> Dict:
        """导出配置为字典"""
        return {
            'use_secure': self.use_secure,
            'shared_secret': self.shared_secret,
            'ua_identity': self.ua_identity,
            'sent_sequence': self.sent_sequence
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'EmailEncoder':
        """从字典加载配置"""
        encoder = cls(config.get('shared_secret'), config.get('ua_identity', ''))
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
            msg_root['X-UA-Identity'] = encoder.ua_identity
        
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
                'ua_identity': encoded_data['ua_identity'],
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
                    'ua_identity': encoded_html_data['ua_identity'],
                    'version': encoded_html_data['version'],
                    'secure': True  # 标记为安全内容
                }
                html_content = json.dumps(html_payload, ensure_ascii=False)
                html_part = MIMEText(html_content, 'html', 'utf-8')
                html_part.add_header('X-Content-Secure', 'true')
            else:
                html_part = MIMEText(html_body, 'html', 'utf-8')
            msg_alternative.attach(html_part)
        
        # 附件支持
        if attachments:
            for attachment in attachments:
                filename = attachment.get('filename', 'attachment')
                file_data = attachment.get('data')
                
                if not file_data:
                    continue
                
                # 判断是否不应该加密（多媒体文件、PDF等）
                # 这些文件保持原样可以让邮件服务器正确识别附件类型
                should_not_encrypt = False
                file_ext = os.path.splitext(filename)[1].lower()
                # 图片、音频、视频、PDF等文件不加密
                unencrypted_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                                    '.mp3', '.wav', '.ogg', '.mp4', '.avi', '.mov', 
                                    '.mkv', '.flv', '.wmv', '.pdf']
                
                if file_ext in unencrypted_exts:
                    should_not_encrypt = True
                
                # 对于应该保持原样的文件（多媒体、PDF等），不加密
                # 对于其他文件（文本文件等），进行加密
                if should_not_encrypt or not encoder.use_secure:
                    # 不加密，直接添加
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file_data)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg_root.attach(part)
                else:
                    # 加密附件
                    encoded_attachment = encoder.encode_attachment(file_data, filename)
                    
                    # 将加密的附件数据打包为JSON
                    secure_payload = {
                        'sequence': encoded_attachment['sequence'],
                        'data': encoded_attachment['data'],
                        'filename': encoded_attachment['filename'],
                        'hmac': encoded_attachment['hmac'],
                        'ua_identity': encoded_attachment['ua_identity'],
                        'version': encoded_attachment['version'],
                        'secure': True
                    }
                    
                    attachment_json = json.dumps(secure_payload, ensure_ascii=False).encode('utf-8')
                    part = MIMEBase('application', 'x-secure-attachment')
                    part.set_payload(attachment_json)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}.secure"')
                    part.add_header('X-Original-Filename', filename)
                    part.add_header('X-Content-Secure', 'true')
                    msg_root.attach(part)
        
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
            'verified': True,
            'msg_type': 'normal'  # 'paired', 'other_ua', 'normal'
        }
        
        # 检查是否是安全邮件
        is_secure = msg.get('X-Secure-Email') == 'true'
        sender_ua_identity = msg.get('X-UA-Identity', '')
        
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
                            decoded_body, verified, msg_type = encoder.decode_secure_message(secure_data)
                            result['body'] = decoded_body
                            result['verified'] = result['verified'] and verified
                            result['msg_type'] = msg_type
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
                            decoded_html, verified, msg_type = encoder.decode_secure_message(secure_data)
                            result['html'] = decoded_html
                            result['verified'] = result['verified'] and verified
                        else:
                            result['html'] = payload
                    except:
                        pass
                
                # 处理附件
                elif content_type == 'application/x-secure-attachment':
                    # 加密的附件
                    try:
                        payload = part.get_payload(decode=True)
                        secure_data = json.loads(payload.decode('utf-8', errors='ignore'))
                        original_filename = part.get('X-Original-Filename', secure_data.get('filename', 'attachment'))
                        
                        decoded_data, verified, msg_type = encoder.decode_attachment(secure_data)
                        
                        if decoded_data:
                            result['attachments'].append({
                                'filename': original_filename,
                                'data': decoded_data,
                                'verified': verified,
                                'secure': True,
                                'msg_type': msg_type
                            })
                            result['verified'] = result['verified'] and verified
                        else:
                            result['attachments'].append({
                                'filename': original_filename,
                                'data': None,
                                'verified': False,
                                'secure': True,
                                'msg_type': msg_type,
                                'error': '无法解密附件'
                            })
                            result['verified'] = False
                    except Exception as e:
                        result['attachments'].append({
                            'filename': 'unknown',
                            'data': None,
                            'verified': False,
                            'secure': True,
                            'error': f'解析失败: {str(e)}'
                        })
                        result['verified'] = False
                
                elif content_type.startswith('application/') or content_type.startswith('image/') or content_type.startswith('audio/') or content_type.startswith('video/'):
                    # 普通附件（未加密的多媒体文件等）
                    try:
                        filename = part.get_filename()
                        if filename:
                            # 解码文件名
                            from email.header import decode_header
                            decoded_parts = decode_header(filename)
                            filename = ''
                            for part_text, encoding in decoded_parts:
                                if isinstance(part_text, bytes):
                                    filename += part_text.decode(encoding or 'utf-8', errors='ignore')
                                else:
                                    filename += part_text
                            
                            payload = part.get_payload(decode=True)
                            result['attachments'].append({
                                'filename': filename,
                                'data': payload,
                                'verified': True,
                                'secure': False,
                                'msg_type': 'normal'
                            })
                    except:
                        pass
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                if is_secure:
                    try:
                        secure_data = json.loads(payload)
                        decoded_body, verified, msg_type = encoder.decode_secure_message(secure_data)
                        result['body'] = decoded_body
                        result['verified'] = verified
                        result['msg_type'] = msg_type
                    except:
                        result['body'] = payload
                else:
                    result['body'] = payload
            except:
                result['body'] = msg.get_payload()
        
        return result


# 便捷函数

def create_encoder(shared_secret: Optional[str] = None, ua_identity: Optional[str] = None) -> EmailEncoder:
    """
    创建邮件编码器
    
    Args:
        shared_secret: 共享密钥（可选）
        ua_identity: UA身份标识（可选）
    
    Returns:
        EmailEncoder实例
    """
    return EmailEncoder(shared_secret, ua_identity)
