import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
#from email import encoders
from typing import List, Optional, Dict
import ssl

class SMTPClient:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_ssl: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.connection = None
    
    def connect(self) -> bool:
        try:
            if self.use_ssl:
                # 使用SSL连接
                context = ssl.create_default_context()
                self.connection = smtplib.SMTP_SSL(
                    self.smtp_server, 
                    self.smtp_port, 
                    context=context,
                    timeout=30
                )
            else:
                # 使用普通连接后STARTTLS
                self.connection = smtplib.SMTP(
                    self.smtp_server, 
                    self.smtp_port,
                    timeout=30
                )
                self.connection.starttls()
            # 登录认证
            self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            raise Exception(f"连接SMTP服务器失败: {str(e)}")
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            self.connection = None

    def send_email(self, to_addrs: List[str], subject: str, body: str, cc_addrs: Optional[List[str]] = None, bcc_addrs: Optional[List[str]] = None, encoder_func = None) -> bool:
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = subject
            if cc_addrs:
                msg['Cc'] = ', '.join(cc_addrs)
            # 这是为未来的Base64编码定制预留的接口
            encoded_body = body
            if encoder_func:
                encoded_body = encoder_func(body)

            # 添加邮件正文
            msg.attach(MIMEText(encoded_body, 'plain', 'utf-8'))
            # 准备收件人列表
            all_recipients = to_addrs.copy()
            if cc_addrs:
                all_recipients.extend(cc_addrs)
            if bcc_addrs:
                all_recipients.extend(bcc_addrs)
            # 发送邮件
            if not self.connection:
                self.connect()
            self.connection.sendmail(
                self.username,
                all_recipients,
                msg.as_string()
            )
            return True
        except Exception as e:
            raise Exception(f"发送邮件失败: {str(e)}")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()