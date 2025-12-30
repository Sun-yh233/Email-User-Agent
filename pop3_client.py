import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from typing import List, Dict, Optional
import ssl

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
            if not self.connection:
                self.connect()
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
    
    def _parse_email(self, email_data: bytes, decoder_func=None) -> Dict:
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
        
        # 获取邮件正文
        body = ''
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
        
        # 应用解码函数（如果提供）
        # 这是为未来的Base64解码定制预留的接口
        if decoder_func and body:
            try:
                body = decoder_func(body)
            except:
                pass  # 如果解码失败，保留原文
        
        return {
            'from': f"{from_name} <{from_addr}>" if from_name else from_addr,
            'to': f"{to_name} <{to_addr}>" if to_name else to_addr,
            'subject': subject,
            'date': date,
            'body': body
        }
    
    def list_emails(self, count: Optional[int] = None, decoder_func=None) -> List[Dict]:
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
                    email_info = self._parse_email(email_data, decoder_func)
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
        """上下文管理器支持"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.disconnect()