import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import List, Optional, Dict
import ssl
from email_encoder import EmailEncoder, SecureMIMEBuilder

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

    def send_email(self, to_addrs: List[str], subject: str, body: str, 
                   cc_addrs: Optional[List[str]] = None, 
                   bcc_addrs: Optional[List[str]] = None, 
                   encoder: Optional[EmailEncoder] = None,
                   html_body: Optional[str] = None,
                   attachments: Optional[List[Dict]] = None) -> bool:
        """
        发送邮件（支持安全加密）
        
        Args:
            to_addrs: 收件人地址列表
            subject: 邮件主题
            body: 邮件正文
            cc_addrs: 抄送地址列表
            bcc_addrs: 密送地址列表
            encoder: 邮件编码器（用于安全通信）
            html_body: HTML正文（预留）
            attachments: 附件列表（字典包含'filename'和'data'）
        
        Returns:
            是否发送成功
        """
        try:
            # 如果提供了编码器且启用了安全模式，使用安全MIME构建器
            if encoder and encoder.use_secure:
                msg = SecureMIMEBuilder.create_secure_email(
                    from_addr=self.username,
                    to_addrs=to_addrs,
                    subject=subject,
                    body=body,
                    encoder=encoder,
                    cc_addrs=cc_addrs,
                    html_body=html_body,
                    attachments=attachments
                )
            else:
                # 否则使用标准MIME格式
                msg = MIMEMultipart()
                msg['From'] = self.username
                msg['To'] = ', '.join(to_addrs)
                msg['Subject'] = subject
                if cc_addrs:
                    msg['Cc'] = ', '.join(cc_addrs)
                
                # 添加邮件正文
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 预留：HTML正文支持
                if html_body:
                    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
                # 添加附件
                if attachments:
                    from email import encoders
                    for attachment in attachments:
                        filename = attachment.get('filename', 'attachment')
                        file_data = attachment.get('data')
                        if file_data:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file_data)
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            msg.attach(part)
            
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