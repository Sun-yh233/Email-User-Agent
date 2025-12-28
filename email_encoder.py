"""
邮件编码器接口
为未来的Base64编码表自定义和一次一变机制预留接口

这个模块提供了用于邮件安全通信的编码/解码接口，支持：
1. 自定义Base64编码表
2. 编码表的自动协商机制
3. 一次一变的编码表更新机制
"""

import base64
import random
import json
from typing import Optional, Dict, Tuple


class EmailEncoder:
    """
    邮件编码器
    
    提供标准Base64编码和自定义编码表的支持
    为未来的安全通信功能预留扩展接口
    """
    
    # 标准Base64字符表
    STANDARD_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    def __init__(self, custom_table: Optional[str] = None):
        """
        初始化编码器
        
        Args:
            custom_table: 自定义的Base64字符表（64个字符）
        """
        self.custom_table = custom_table
        self.use_custom = custom_table is not None
        
        if self.use_custom and len(custom_table) != 64:
            raise ValueError("自定义编码表必须包含64个字符")
    
    def encode(self, text: str) -> str:
        """
        编码文本
        
        Args:
            text: 原始文本
        
        Returns:
            str: 编码后的文本
        """
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
        """
        解码文本
        
        Args:
            encoded_text: 编码后的文本
        
        Returns:
            str: 原始文本
        """
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
        """
        生成自定义Base64字符表
        
        Args:
            seed: 随机种子，用于生成可重复的字符表
        
        Returns:
            str: 64个字符的自定义编码表
        """
        if seed is not None:
            random.seed(seed)
        
        chars = list(EmailEncoder.STANDARD_BASE64_CHARS)
        random.shuffle(chars)
        
        return ''.join(chars)
    
    @staticmethod
    def negotiate_table(shared_secret: str) -> str:
        """
        基于共享密钥协商编码表
        
        这是一个简化的协商机制示例，实际应用中应该使用更安全的密钥交换协议
        
        Args:
            shared_secret: 共享密钥
        
        Returns:
            str: 协商得到的编码表
        """
        # 使用共享密钥生成确定性的种子
        seed = sum(ord(c) for c in shared_secret)
        return EmailEncoder.generate_custom_table(seed)
    
    def update_table(self, new_table: str):
        """
        更新编码表（支持一次一变机制）
        
        Args:
            new_table: 新的编码表
        """
        if len(new_table) != 64:
            raise ValueError("编码表必须包含64个字符")
        
        self.custom_table = new_table
        self.use_custom = True
    
    def export_table(self) -> Optional[str]:
        """
        导出当前编码表
        
        Returns:
            Optional[str]: 当前编码表，如果使用标准编码则返回None
        """
        return self.custom_table if self.use_custom else None
    
    def to_dict(self) -> Dict:
        """
        将编码器配置导出为字典
        
        Returns:
            Dict: 编码器配置
        """
        return {
            'use_custom': self.use_custom,
            'custom_table': self.custom_table
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'EmailEncoder':
        """
        从字典创建编码器
        
        Args:
            config: 编码器配置字典
        
        Returns:
            EmailEncoder: 编码器实例
        """
        custom_table = config.get('custom_table') if config.get('use_custom') else None
        return cls(custom_table)


class EncoderNegotiator:
    """
    编码表协商器
    
    用于在不同客户端之间协商和同步自定义编码表
    这是为未来的安全通信功能预留的接口
    """
    
    def __init__(self):
        self.negotiation_data = {}
    
    def create_negotiation_request(self, sender_id: str, 
                                   shared_secret: str) -> Dict:
        """
        创建协商请求
        
        Args:
            sender_id: 发送者ID
            shared_secret: 共享密钥
        
        Returns:
            Dict: 协商请求数据
        """
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
    
    def accept_negotiation(self, negotiation_request: Dict,
                          shared_secret: str) -> Tuple[str, str]:
        """
        接受协商请求
        
        Args:
            negotiation_request: 协商请求数据
            shared_secret: 共享密钥
        
        Returns:
            Tuple[str, str]: (协商ID, 编码表)
        """
        negotiation_id = negotiation_request['negotiation_id']
        sender_id = negotiation_request['sender_id']
        
        # 使用相同的共享密钥生成编码表
        table = EmailEncoder.negotiate_table(shared_secret)
        
        return negotiation_id, table
    
    def rotate_table(self, current_table: str, rotation_seed: int) -> str:
        """
        轮换编码表（一次一变机制）
        
        Args:
            current_table: 当前编码表
            rotation_seed: 轮换种子
        
        Returns:
            str: 新的编码表
        """
        chars = list(current_table)
        random.seed(rotation_seed)
        random.shuffle(chars)
        
        return ''.join(chars)


# 便捷函数

def create_encoder(use_custom: bool = False, 
                  shared_secret: Optional[str] = None) -> EmailEncoder:
    """
    创建邮件编码器
    
    Args:
        use_custom: 是否使用自定义编码表
        shared_secret: 共享密钥（用于协商编码表）
    
    Returns:
        EmailEncoder: 编码器实例
    """
    if not use_custom:
        return EmailEncoder()
    
    if shared_secret:
        table = EmailEncoder.negotiate_table(shared_secret)
        return EmailEncoder(table)
    else:
        table = EmailEncoder.generate_custom_table()
        return EmailEncoder(table)


def encode_email_body(body: str, encoder: Optional[EmailEncoder] = None) -> str:
    """
    编码邮件正文
    
    Args:
        body: 原始正文
        encoder: 编码器实例，如果为None则不编码
    
    Returns:
        str: 编码后的正文
    """
    if encoder is None:
        return body
    
    return encoder.encode(body)


def decode_email_body(encoded_body: str, encoder: Optional[EmailEncoder] = None) -> str:
    """
    解码邮件正文
    
    Args:
        encoded_body: 编码后的正文
        encoder: 编码器实例，如果为None则不解码
    
    Returns:
        str: 原始正文
    """
    if encoder is None:
        return encoded_body
    
    return encoder.decode(encoded_body)
