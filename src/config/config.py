"""
配置管理模块
"""
import json
import os
from typing import Dict, Any


class Config:
    """配置类"""
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "network": {
                "default_port": 8001,
                "bootstrap_nodes": [],
                "discovery_port": 8080
            },
            "blockchain": {
                "difficulty": 2,
                "max_block_size": 1024,
                "consensus_type": "vdf_pow"
            },
            "security": {
                "enable_encryption": True,
                "key_size": 2048,
                "enable_replay_protection": True,
                "max_timestamp_drift": 300
            },
            "nat_traversal": {
                "enable_ngrok": True,
                "stun_servers": [
                    "stun.l.google.com:19302",
                    "stun1.l.google.com:19302"
                ],
                "upnp_enabled": True
            },
            "messages": {
                "max_message_size": 10240,  # 10KB
                "enable_offline_cache": True,
                "cache_duration": 86400  # 24小时
            },
            "dht": {
                "enabled": False,
                "bootstrap_nodes": [],
                "routing_table_size": 128,
                "bucket_size": 16
            },
            "vdf": {
                "enabled": True,
                "difficulty": 10000,
                "challenge_prefix": "vdf_challenge"
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置，如果配置文件不存在则使用默认配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并用户配置和默认配置
                return self.merge_config(self.default_config, user_config)
            except Exception as e:
                print(f"[!] 配置文件加载失败，使用默认配置: {e}")
                return self.default_config
        else:
            # 如果配置文件不存在，创建一个
            self.save_config(self.default_config)
            return self.default_config

    def merge_config(self, default: Dict, user: Dict) -> Dict:
        """合并默认配置和用户配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置到文件"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[!] 配置文件保存失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config_ref = self.config
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        config_ref[keys[-1]] = value


def get_config() -> Config:
    """获取全局配置实例"""
    return Config()