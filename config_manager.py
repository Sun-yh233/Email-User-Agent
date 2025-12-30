import json
import os
from typing import Dict, Optional, List


class ConfigManager:
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
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
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def add_account(self, account: Dict) -> bool:
        # 检查必需字段
        required_fields = ['name', 'email', 'smtp_server', 'smtp_port', 'pop3_server', 'pop3_port', 'password']
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
        if account_name is None:
            account_name = self.config['current_account']
        
        if account_name is None:
            return None
        
        for account in self.config['accounts']:
            if account['name'] == account_name:
                return account
        
        return None
    
    def list_accounts(self) -> List[str]:
        return [account['name'] for account in self.config['accounts']]
    
    def set_current_account(self, account_name: str) -> bool:
        for account in self.config['accounts']:
            if account['name'] == account_name:
                self.config['current_account'] = account_name
                return self.save_config()
        
        print(f"账号 '{account_name}' 不存在")
        return False
    
    def get_current_account(self) -> Optional[Dict]:
        return self.get_account()
    
    def update_account(self, account_name: str, updates: Dict) -> bool:
        for account in self.config['accounts']:
            if account['name'] == account_name:
                account.update(updates)
                return self.save_config()
        
        print(f"账号 '{account_name}' 不存在")
        return False
    
    def get_setting(self, key: str, default=None):
        return self.config['settings'].get(key, default)
    
    def set_setting(self, key: str, value) -> bool:
        self.config['settings'][key] = value
        return self.save_config()