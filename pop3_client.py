import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from typing import List, Dict, Optional
import ssl
from email_encoder import EmailEncoder, SecureMIMEBuilder

class POP3Client:
    
    def __init__(self, pop3_server: str, pop3_port: int, username: str, password: str, use_ssl: bool = True):
        self.pop3_server = pop3_server
        self.pop3_port = pop3_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.connection = None
    
    def connect(self) -> bool:
        try:
            if self.use_ssl:
                # 使用SSL连接
                context = ssl.create_default_context()
                self.connection = poplib.POP3_SSL(
                    self.pop3_server,
                    self.pop3_port,
                    timeout=30,
                    context=context
                )
            else:
                # 使用普通连接
                self.connection = poplib.POP3(
                    self.pop3_server,
                    self.pop3_port,
                    timeout=30
                )
            # 登录认证
            self.connection.user(self.username)
            self.connection.pass_(self.password)
            return True
        except Exception as e:
            raise Exception(f"连接POP3服务器失败: {str(e)}")
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            self.connection = None
    
    def get_email_count(self) -> int:
        try:
            if not self.connection: self.connect()
            # stat()返回邮件数量和邮箱大小
            count, size = self.connection.stat()
            return count
        except Exception as e:
            raise Exception(f"获取邮件数量失败: {str(e)}")
    
    def _decode_str(self, s: str) -> str:
        value, charset = decode_header(s)[0]
        if charset:
            try:
                value = value.decode(charset)
            except:
                value = value.decode('utf-8', errors='ignore')
        elif isinstance(value, bytes):
            value = value.decode('utf-8', errors='ignore')
        return value
    
    def _parse_email(self, email_data: bytes, decoder: Optional[EmailEncoder] = None) -> Dict:
        """
        解析邮件（支持安全解密）
        
        Args:
            email_data: 邮件原始数据
            decoder: 邮件解码器（用于安全通信）
        
        Returns:
            解析后的邮件信息字典
        """
        # 解析邮件
        msg = Parser().parsestr(email_data.decode('utf-8', errors='ignore'))
        
        # 解析发件人
        from_hdr = msg.get('From', '')
        from_name, from_addr = parseaddr(from_hdr)
        if from_name:
            from_name = self._decode_str(from_name)
        
        # 解析收件人
        to_hdr = msg.get('To', '')
        to_name, to_addr = parseaddr(to_hdr)
        if to_name:
            to_name = self._decode_str(to_name)
        
        # 解析主题
        subject = msg.get('Subject', '')
        if subject:
            subject = self._decode_str(subject)
        
        # 解析日期
        date = msg.get('Date', '')
        
        # 检查是否是安全邮件
        is_secure = msg.get('X-Secure-Email') == 'true'
        
        # 获取邮件正文
        body = ''
        verified = True
        
        if decoder and decoder.use_secure and is_secure:
            # 使用安全MIME解析器
            parsed_content = SecureMIMEBuilder.parse_secure_email(msg, decoder)
            body = parsed_content['body']
            verified = parsed_content['verified']
        else:
            # 标准解析
            if msg.is_multipart():
                # 多部分邮件
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except:
                            pass
            else:
                # 单部分邮件
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = msg.get_payload()
        
        result = {
            'from': f"{from_name} <{from_addr}>" if from_name else from_addr,
            'to': f"{to_name} <{to_addr}>" if to_name else to_addr,
            'subject': subject,
            'date': date,
            'body': body,
            'is_secure': is_secure,
            'verified': verified,
            'security_warning': None  # 存储安全警告信息
        }
        
        # 如果验证失败，添加安全警告
        if is_secure and not verified:
            result['security_warning'] = "⚠️ 安全警告: 此邮件验证失败，可能已被篡改或密钥错误"
        
        return result
    
    def list_emails(self, count: Optional[int] = None, decoder: Optional[EmailEncoder] = None) -> List[Dict]:
        """
        列出邮件（支持安全解密）
        
        Args:
            count: 要获取的邮件数量
            decoder: 邮件解码器（用于安全通信）
        
        Returns:
            邮件列表
        """
        try:
            if not self.connection:
                self.connect()
            # 获取邮件总数
            total_count = self.get_email_count()
            if count is None:
                count = total_count
            else:
                count = min(count, total_count)
            emails = []
            # 从最新的邮件开始获取
            for i in range(total_count, total_count - count, -1):
                try:
                    # 获取邮件内容
                    resp, lines, octets = self.connection.retr(i)
                    # 合并邮件内容
                    email_data = b'\r\n'.join(lines)
                    # 解析邮件
                    email_info = self._parse_email(email_data, decoder)
                    email_info['index'] = i
                    emails.append(email_info)
                except Exception as e:
                    print(f"解析邮件 {i} 失败: {str(e)}")
                    continue
            return emails
        except Exception as e:
            raise Exception(f"获取邮件列表失败: {str(e)}")
    
    def delete_email(self, index: int) -> bool:
        try:
            if not self.connection:
                self.connect()
            self.connection.dele(index)
            return True
        except Exception as e:
            raise Exception(f"删除邮件失败: {str(e)}")

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()