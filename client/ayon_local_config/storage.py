# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any

from ayon_local_config.logger import log


class LocalConfigStorage:
    """Handles loading and saving of local configuration data"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".ayon", "settings")
        self.config_file = os.path.join(self.config_dir, "localconfig.json")
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure the config directory exists"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                log.debug(f"Created config directory: {self.config_dir}")
        except Exception as e:
            log.error(f"Failed to create config directory: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                log.debug(f"Loaded config from: {self.config_file}")
                return config
            else:
                log.debug("Config file does not exist, returning empty config")
                return {}
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log.debug(f"Saved config to: {self.config_file}")
            return True
        except Exception as e:
            log.error(f"Failed to save config: {e}")
            return False
    
    def get_setting_value(self, group_id: str, setting_id: str, default_value: Any = None) -> Any:
        """Get a specific setting value"""
        config = self.load_config()
        return config.get(group_id, {}).get(setting_id, default_value)
    
    def set_setting_value(self, group_id: str, setting_id: str, value: Any) -> bool:
        """Set a specific setting value"""
        config = self.load_config()
        if group_id not in config:
            config[group_id] = {}
        config[group_id][setting_id] = value
        return self.save_config(config)
    
    def get_group_config(self, group_id: str) -> Dict[str, Any]:
        """Get all settings for a specific group"""
        config = self.load_config()
        return config.get(group_id, {})
    
    def set_group_config(self, group_id: str, group_config: Dict[str, Any]) -> bool:
        """Set all settings for a specific group"""
        config = self.load_config()
        config[group_id] = group_config
        return self.save_config(config)
    
    def reset_group_to_defaults(self, group_id: str, default_values: Dict[str, Any]) -> bool:
        """Reset a group to default values"""
        return self.set_group_config(group_id, default_values)
    
    def backup_config(self) -> str:
        """Create a backup of the current config and return backup path"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_file}.backup_{timestamp}"
            
            if os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, backup_path)
                log.info(f"Created config backup: {backup_path}")
                return backup_path
            return ""
        except Exception as e:
            log.error(f"Failed to create config backup: {e}")
            return ""
