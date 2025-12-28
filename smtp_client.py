"""
SMTP客户端实现
使用Python标准库smtplib实现SMTP协议的邮件发送功能

参考: RFC 5321 - Simple Mail Transfer Protocol
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
import ssl


class SMTPClient:
    """SMTP客户端，支持发送邮件"""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 username: str, password: str, use_ssl: bool = True):
        """
        初始化SMTP客户端
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 用户名（邮箱地址）
            password: 密码或授权码
            use_ssl: 是否使用SSL/TLS加密
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.connection = None
    
    def connect(self) -> bool:
        """
        连接到SMTP服务器
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
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
        """断开与SMTP服务器的连接"""
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            self.connection = None
    
    def send_email(self, to_addrs: List[str], subject: str, 
                   body: str, cc_addrs: Optional[List[str]] = None,
                   bcc_addrs: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None,
                   encoder_func=None) -> bool:
        """
        发送邮件
        
        Args:
            to_addrs: 收件人列表
            subject: 邮件主题
            body: 邮件正文
            cc_addrs: 抄送列表
            bcc_addrs: 密送列表
            attachments: 附件文件路径列表
            encoder_func: 编码函数（用于未来的Base64编码定制），接收原文返回编码后的文本
        
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = subject
            
            if cc_addrs:
                msg['Cc'] = ', '.join(cc_addrs)
            
            # 应用编码函数（如果提供）
            # 这是为未来的Base64编码定制预留的接口
            encoded_body = body
            if encoder_func:
                encoded_body = encoder_func(body)
            
            # 添加邮件正文
            msg.attach(MIMEText(encoded_body, 'plain', 'utf-8'))
            
            # 添加附件（如果有）
            if attachments:
                for filepath in attachments:
                    try:
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {filepath.split("/")[-1]}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        raise Exception(f"添加附件失败 {filepath}: {str(e)}")
            
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
        """上下文管理器支持"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.disconnect()


def get_smtp_config(provider: str) -> Dict:
    """
    获取常见邮件服务商的SMTP配置
    
    Args:
        provider: 服务商名称 (qq, 163, sina, gmail等)
    
    Returns:
        Dict: 包含服务器地址和端口的配置字典
    """
    configs = {
        'qq': {
            'server': 'smtp.qq.com',
            'port': 465,
            'use_ssl': True
        },
        '163': {
            'server': 'smtp.163.com',
            'port': 465,
            'use_ssl': True
        },
        'sina': {
            'server': 'smtp.sina.com',
            'port': 465,
            'use_ssl': True
        },
        'gmail': {
            'server': 'smtp.gmail.com',
            'port': 465,
            'use_ssl': True
        },
        '126': {
            'server': 'smtp.126.com',
            'port': 465,
            'use_ssl': True
        },
        'yeah': {
            'server': 'smtp.yeah.net',
            'port': 465,
            'use_ssl': True
        }
    }
    
    return configs.get(provider.lower(), {
        'server': '',
        'port': 465,
        'use_ssl': True
    })
