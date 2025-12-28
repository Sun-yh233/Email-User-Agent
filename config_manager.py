"""
配置管理器
管理邮件账号配置和应用设置
"""

import json
import os
from typing import Dict, Optional, List


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            Dict: 配置字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {str(e)}")
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """
        获取默认配置
        
        Returns:
            Dict: 默认配置字典
        """
        return {
            'accounts': [],
            'current_account': None,
            'settings': {
                'auto_receive': False,
                'receive_interval': 300,  # 自动接收间隔（秒）
                'max_emails': 50,  # 每次接收的最大邮件数
                'use_custom_encoder': False,
                'shared_secret': ''
            }
        }
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存成功返回True
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def add_account(self, account: Dict) -> bool:
        """
        添加邮件账号
        
        Args:
            account: 账号信息字典，包含以下字段：
                - name: 账号名称
                - email: 邮箱地址
                - smtp_server: SMTP服务器
                - smtp_port: SMTP端口
                - pop3_server: POP3服务器
                - pop3_port: POP3端口
                - password: 密码/授权码
                - use_ssl: 是否使用SSL
        
        Returns:
            bool: 添加成功返回True
        """
        # 检查必需字段
        required_fields = ['name', 'email', 'smtp_server', 'smtp_port',
                          'pop3_server', 'pop3_port', 'password']
        
        for field in required_fields:
            if field not in account:
                print(f"缺少必需字段: {field}")
                return False
        
        # 检查是否已存在同名账号
        for existing_account in self.config['accounts']:
            if existing_account['name'] == account['name']:
                print(f"账号 '{account['name']}' 已存在")
                return False
        
        # 添加默认值
        if 'use_ssl' not in account:
            account['use_ssl'] = True
        
        self.config['accounts'].append(account)
        
        # 如果这是第一个账号，设为当前账号
        if len(self.config['accounts']) == 1:
            self.config['current_account'] = account['name']
        
        return self.save_config()
    
    def remove_account(self, account_name: str) -> bool:
        """
        删除邮件账号
        
        Args:
            account_name: 账号名称
        
        Returns:
            bool: 删除成功返回True
        """
        for i, account in enumerate(self.config['accounts']):
            if account['name'] == account_name:
                self.config['accounts'].pop(i)
                
                # 如果删除的是当前账号，清除当前账号设置
                if self.config['current_account'] == account_name:
                    if self.config['accounts']:
                        self.config['current_account'] = self.config['accounts'][0]['name']
                    else:
                        self.config['current_account'] = None
                
                return self.save_config()
        
        print(f"账号 '{account_name}' 不存在")
        return False
    
    def get_account(self, account_name: Optional[str] = None) -> Optional[Dict]:
        """
        获取账号信息
        
        Args:
            account_name: 账号名称，如果为None则返回当前账号
        
        Returns:
            Optional[Dict]: 账号信息，如果不存在返回None
        """
        if account_name is None:
            account_name = self.config['current_account']
        
        if account_name is None:
            return None
        
        for account in self.config['accounts']:
            if account['name'] == account_name:
                return account
        
        return None
    
    def list_accounts(self) -> List[str]:
        """
        获取所有账号名称列表
        
        Returns:
            List[str]: 账号名称列表
        """
        return [account['name'] for account in self.config['accounts']]
    
    def set_current_account(self, account_name: str) -> bool:
        """
        设置当前使用的账号
        
        Args:
            account_name: 账号名称
        
        Returns:
            bool: 设置成功返回True
        """
        for account in self.config['accounts']:
            if account['name'] == account_name:
                self.config['current_account'] = account_name
                return self.save_config()
        
        print(f"账号 '{account_name}' 不存在")
        return False
    
    def get_current_account(self) -> Optional[Dict]:
        """
        获取当前账号信息
        
        Returns:
            Optional[Dict]: 当前账号信息，如果没有设置返回None
        """
        return self.get_account()
    
    def update_account(self, account_name: str, updates: Dict) -> bool:
        """
        更新账号信息
        
        Args:
            account_name: 账号名称
            updates: 要更新的字段字典
        
        Returns:
            bool: 更新成功返回True
        """
        for account in self.config['accounts']:
            if account['name'] == account_name:
                account.update(updates)
                return self.save_config()
        
        print(f"账号 '{account_name}' 不存在")
        return False
    
    def get_setting(self, key: str, default=None):
        """
        获取设置项
        
        Args:
            key: 设置项键名
            default: 默认值
        
        Returns:
            设置项的值
        """
        return self.config['settings'].get(key, default)
    
    def set_setting(self, key: str, value) -> bool:
        """
        设置配置项
        
        Args:
            key: 设置项键名
            value: 设置项的值
        
        Returns:
            bool: 设置成功返回True
        """
        self.config['settings'][key] = value
        return self.save_config()
    
    def get_provider_from_email(self, email: str) -> str:
        """
        从邮箱地址识别服务商
        
        Args:
            email: 邮箱地址
        
        Returns:
            str: 服务商名称（qq, 163, sina等）
        """
        if '@' not in email:
            return 'unknown'
        
        domain = email.split('@')[1].lower()
        
        if 'qq.com' in domain:
            return 'qq'
        elif '163.com' in domain:
            return '163'
        elif '126.com' in domain:
            return '126'
        elif 'sina.com' in domain or 'sina.cn' in domain:
            return 'sina'
        elif 'gmail.com' in domain:
            return 'gmail'
        elif 'yeah.net' in domain:
            return 'yeah'
        else:
            return 'custom'
