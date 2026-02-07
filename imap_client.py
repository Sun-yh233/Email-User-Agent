import imaplib
import ssl
from email import policy
from email.parser import BytesParser
from email.header import decode_header
from email.utils import parseaddr
from typing import List, Dict, Optional

from email_encoder import EmailEncoder, SecureMIMEBuilder


class IMAPClient:
    def __init__(self, imap_server: str, imap_port: int, username: str, password: str,
                 use_ssl: bool = True, mailbox: str = "INBOX"):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.mailbox = mailbox
        self.connection = None

    def connect(self) -> bool:
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.imap_server,
                    self.imap_port,
                    ssl_context=context
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.imap_server,
                    self.imap_port
                )
                self.connection.starttls()
            self.connection.login(self.username, self.password)
            self.connection.select(self.mailbox)
            return True
        except Exception as e:
            raise Exception(f"连接IMAP服务器失败: {str(e)}")

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None

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
        parser_policy = policy.default.clone(max_line_length=0)
        msg = BytesParser(policy=parser_policy).parsebytes(email_data)

        from_hdr = msg.get('From', '')
        from_name, from_addr = parseaddr(from_hdr)
        if from_name:
            from_name = self._decode_str(from_name)

        to_hdr = msg.get('To', '')
        to_name, to_addr = parseaddr(to_hdr)
        if to_name:
            to_name = self._decode_str(to_name)

        subject = msg.get('Subject', '')
        if subject:
            subject = self._decode_str(subject)

        date = msg.get('Date', '')
        is_secure = msg.get('X-Secure-Email') == 'true'

        body = ''
        verified = True
        msg_type = 'normal'
        attachments = []

        if decoder and decoder.use_secure and is_secure:
            parsed_content = SecureMIMEBuilder.parse_secure_email(msg, decoder)
            body = parsed_content.get('body', '')
            verified = parsed_content.get('verified', False)
            msg_type = parsed_content.get('msg_type', 'normal')
            attachments = parsed_content.get('attachments', [])
        else:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.is_multipart():
                        continue
                    content_type = part.get_content_type()
                    content_disposition = part.get_content_disposition()
                    filename = part.get_filename()

                    if content_disposition == 'attachment' or filename:
                        if filename:
                            decoded_parts = decode_header(filename)
                            decoded_filename = ''
                            for part_text, encoding in decoded_parts:
                                if isinstance(part_text, bytes):
                                    decoded_filename += part_text.decode(encoding or 'utf-8', errors='ignore')
                                else:
                                    decoded_filename += part_text
                            filename = decoded_filename
                        else:
                            filename = 'attachment'

                        payload = part.get_payload(decode=True)
                        attachments.append({
                            'filename': filename,
                            'data': payload,
                            'verified': True,
                            'secure': False,
                            'msg_type': 'normal'
                        })
                        continue

                    if content_type == 'text/plain' and not body:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
            else:
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
            'security_warning': None,
            'msg_type': msg_type,
            'attachments': attachments
        }

        if is_secure and not verified:
            result['security_warning'] = "安全警告: 此邮件验证失败，可能已被篡改或密钥错误"

        return result

    def list_emails(self, count: Optional[int] = None,
                    decoder: Optional[EmailEncoder] = None) -> List[Dict]:
        try:
            if not self.connection:
                self.connect()
            status, data = self.connection.search(None, 'ALL')
            if status != 'OK':
                raise Exception("IMAP搜索邮件失败")

            message_ids = data[0].split()
            total_count = len(message_ids)
            if count is None:
                count = total_count
            else:
                count = min(count, total_count)

            selected_ids = message_ids[-count:]
            emails = []
            for msg_id in reversed(selected_ids):
                try:
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    for item in msg_data:
                        if isinstance(item, tuple):
                            email_data = item[1]
                            email_info = self._parse_email(email_data, decoder)
                            email_info['index'] = msg_id.decode('utf-8', errors='ignore')
                            emails.append(email_info)
                            break
                except Exception as e:
                    print(f"解析邮件 {msg_id} 失败: {str(e)}")
                    continue
            return emails
        except Exception as e:
            raise Exception(f"获取邮件列表失败: {str(e)}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
