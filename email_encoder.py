import base64
import random
import json
from typing import Optional, Dict, Tuple


class EmailEncoder:

    # 标准Base64字符表
    STANDARD_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    def __init__(self, custom_table: Optional[str] = None):
        self.custom_table = custom_table
        self.use_custom = custom_table is not None
        
        if self.use_custom and len(custom_table) != 64:
            raise ValueError("自定义编码表必须包含64个字符")
    
    def encode(self, text: str) -> str:
        if not self.use_custom:
            # 使用标准Base64编码
            encoded_bytes = base64.b64encode(text.encode('utf-8'))
            return encoded_bytes.decode('ascii')
        else:
            # 使用自定义编码表
            # 先用标准Base64编码
            encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
            # 然后进行字符表映射
            result = []
            for char in encoded:
                if char in self.STANDARD_BASE64_CHARS:
                    index = self.STANDARD_BASE64_CHARS.index(char)
                    result.append(self.custom_table[index])
                else:
                    result.append(char)  # 保留填充字符'='
            
            return ''.join(result)
    
    def decode(self, encoded_text: str) -> str:
        if not self.use_custom:
            # 使用标准Base64解码
            decoded_bytes = base64.b64decode(encoded_text.encode('ascii'))
            return decoded_bytes.decode('utf-8')
        else:
            # 使用自定义编码表
            # 先进行字符表反向映射
            result = []
            for char in encoded_text:
                if char in self.custom_table:
                    index = self.custom_table.index(char)
                    result.append(self.STANDARD_BASE64_CHARS[index])
                else:
                    result.append(char)  # 保留填充字符'='
            
            standard_encoded = ''.join(result)
            
            # 然后用标准Base64解码
            decoded_bytes = base64.b64decode(standard_encoded.encode('ascii'))
            return decoded_bytes.decode('utf-8')
    
    @staticmethod
    def generate_custom_table(seed: Optional[int] = None) -> str:
        if seed is not None:
            random.seed(seed)
        
        chars = list(EmailEncoder.STANDARD_BASE64_CHARS)
        random.shuffle(chars)
        
        return ''.join(chars)
    
    @staticmethod
    def negotiate_table(shared_secret: str) -> str:
        # 使用共享密钥生成确定性的种子
        seed = sum(ord(c) for c in shared_secret)
        return EmailEncoder.generate_custom_table(seed)
    
    def update_table(self, new_table: str):
        if len(new_table) != 64:
            raise ValueError("编码表必须包含64个字符")
        
        self.custom_table = new_table
        self.use_custom = True
    
    def export_table(self) -> Optional[str]:
        return self.custom_table if self.use_custom else None
    
    def to_dict(self) -> Dict:
        return {
            'use_custom': self.use_custom,
            'custom_table': self.custom_table
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'EmailEncoder':
        custom_table = config.get('custom_table') if config.get('use_custom') else None
        return cls(custom_table)


class EncoderNegotiator:
    def __init__(self):
        self.negotiation_data = {}
    
    def create_negotiation_request(self, sender_id: str, shared_secret: str) -> Dict:
        # 生成编码表
        table = EmailEncoder.negotiate_table(shared_secret)
        
        # 生成协商标识
        negotiation_id = f"{sender_id}_{random.randint(1000, 9999)}"
        
        self.negotiation_data[negotiation_id] = {
            'sender_id': sender_id,
            'table': table,
            'timestamp': None  # 实际应用中应该使用真实时间戳
        }
        
        return {
            'negotiation_id': negotiation_id,
            'sender_id': sender_id
        }
    
    def accept_negotiation(self, negotiation_request: Dict, shared_secret: str) -> Tuple[str, str]:
        negotiation_id = negotiation_request['negotiation_id']
        sender_id = negotiation_request['sender_id']
        
        # 使用相同的共享密钥生成编码表
        table = EmailEncoder.negotiate_table(shared_secret)
        
        return negotiation_id, table
    
    def rotate_table(self, current_table: str, rotation_seed: int) -> str:
        chars = list(current_table)
        random.seed(rotation_seed)
        random.shuffle(chars)
        
        return ''.join(chars)


# 便捷函数

def create_encoder(use_custom: bool = False, shared_secret: Optional[str] = None) -> EmailEncoder:
    if not use_custom:
        return EmailEncoder()
    
    if shared_secret:
        table = EmailEncoder.negotiate_table(shared_secret)
        return EmailEncoder(table)
    else:
        table = EmailEncoder.generate_custom_table()
        return EmailEncoder(table)


def encode_email_body(body: str, encoder: Optional[EmailEncoder] = None) -> str:
    if encoder is None:
        return body
    
    return encoder.encode(body)


def decode_email_body(encoded_body: str, encoder: Optional[EmailEncoder] = None) -> str:
    if encoder is None:
        return encoded_body
    
    return encoder.decode(encoded_body)
