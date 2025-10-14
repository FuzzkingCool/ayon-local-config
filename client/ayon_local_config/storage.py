# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any, List

from ayon_local_config.logger import log
from ayon_core.pipeline import get_current_project_name


class LocalConfigStorage:
    """Handles loading and saving of local configuration data"""

    def __init__(self, project_name: str = None):
        # Use AYON_LOCAL_SANDBOX environment variable, fallback to ~/.ayon
        sandbox_path = os.environ.get("AYON_LOCAL_SANDBOX")
        if sandbox_path:
            self.config_dir = os.path.join(sandbox_path, "settings")
        else:
            self.config_dir = os.path.join(os.path.expanduser("~"), ".ayon", "settings")

        self.config_file = os.path.join(self.config_dir, "localconfig.json")
        
        # Get project name with fallback for Local Config addon
        if project_name:
            self.project_name = project_name
        else:
            try:
                self.project_name = get_current_project_name()
                # If get_current_project_name returns None or empty, use a default
                if not self.project_name:
                    self.project_name = "default"
                    log.debug("No active AYON project, using 'default' for Local Config storage")
            except Exception as e:
                log.warning(f"Failed to get current project name: {e}, using 'default'")
                self.project_name = "default"
        
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
                # Check if file is empty or corrupted
                if os.path.getsize(self.config_file) == 0:
                    log.debug("Config file is empty, initializing with default structure")
                    return self._initialize_default_config()
                
                with open(self.config_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        log.debug("Config file is empty, initializing with default structure")
                        return self._initialize_default_config()
                    
                    config = json.loads(content)
                    log.debug(f"Loaded config from: {self.config_file}")
                    return config
            else:
                log.debug("Config file does not exist, initializing with default structure")
                return self._initialize_default_config()
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON config: {e}")
            log.info("Initializing with default config structure")
            return self._initialize_default_config()
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return self._initialize_default_config()
    
    def _initialize_default_config(self) -> Dict[str, Any]:
        """Initialize with default config structure"""
        default_config = {
            "projects": {},
            "environment_variables": {},  # Global environment variables
            "last_selected_project": None  # Remember last selected project
            # Note: Project-specific environment variables are handled by AYON Tools Environment Variables
        }
        # Save the default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        try:
            log.debug(f"Saving config to: {self.config_file}")
            log.debug(f"Config data: {json.dumps(config, indent=2)}")
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log.debug(f"Successfully saved config to: {self.config_file}")
            return True
        except Exception as e:
            log.error(f"Failed to save config: {e}")
            return False

    def get_setting_value(
        self, group_id: str, setting_id: str, default_value: Any = None
    ) -> Any:
        """Get a specific setting value for the current project"""
        config = self.load_config()
        project_config = config.get("projects", {}).get(self.project_name, {})
        return project_config.get(group_id, {}).get(setting_id, default_value)

    def set_setting_value(self, group_id: str, setting_id: str, value: Any) -> bool:
        """Set a specific setting value for the current project"""
        log.debug(f"Setting value: project={self.project_name}, group={group_id}, setting={setting_id}, value={value}")
        
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        if self.project_name not in config["projects"]:
            config["projects"][self.project_name] = {}
        if group_id not in config["projects"][self.project_name]:
            config["projects"][self.project_name][group_id] = {}
        config["projects"][self.project_name][group_id][setting_id] = value
        
        log.debug(f"Updated config structure: {json.dumps(config, indent=2)}")
        return self.save_config(config)

    def get_group_config(self, group_id: str) -> Dict[str, Any]:
        """Get all settings for a specific group in the current project"""
        config = self.load_config()
        project_config = config.get("projects", {}).get(self.project_name, {})
        return project_config.get(group_id, {})

    def set_group_config(self, group_id: str, group_config: Dict[str, Any]) -> bool:
        """Set all settings for a specific group in the current project"""
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        if self.project_name not in config["projects"]:
            config["projects"][self.project_name] = {}
        config["projects"][self.project_name][group_id] = group_config
        return self.save_config(config)

    def reset_group_to_defaults(
        self, group_id: str, default_values: Dict[str, Any]
    ) -> bool:
        """Reset a group to default values for the current project"""
        return self.set_group_config(group_id, default_values)

    def get_available_projects(self) -> List[str]:
        """Get list of all available projects from AYON server and local config"""
        try:
            # First try to get projects from AYON server
            ayon_projects = self._get_ayon_projects()
            
            # Get projects from local config
            config = self.load_config()
            local_projects = list(config.get("projects", {}).keys())
            
            # Combine and deduplicate
            all_projects = list(set(ayon_projects + local_projects))
            
            # Remove "default" from the list
            if "default" in all_projects:
                all_projects.remove("default")
            
            # Sort alphabetically
            all_projects.sort()
            
            log.debug(f"Found {len(all_projects)} available projects: {all_projects}")
            return all_projects
            
        except Exception as e:
            log.warning(f"Failed to get AYON projects, using local config only: {e}")
            # Fallback to local config only
            config = self.load_config()
            local_projects = list(config.get("projects", {}).keys())
            # Remove "default" from fallback list too
            if "default" in local_projects:
                local_projects.remove("default")
            return local_projects
    
    def _get_ayon_projects(self) -> List[str]:
        """Get projects from AYON server using the API"""
        try:
            # Import AYON API
            from ayon_api import get_server_api_connection
            
            # Get server connection
            api = get_server_api_connection()
            if not api or not api.is_server_available:
                log.debug("AYON server not available, skipping project discovery")
                return []
            
            # Get projects from server
            projects = api.get_projects()
            project_names = [project["name"] for project in projects]
            
            log.debug(f"Discovered {len(project_names)} projects from AYON server: {project_names}")
            return project_names
            
        except ImportError:
            log.debug("AYON API not available, skipping server project discovery")
            return []
        except Exception as e:
            log.warning(f"Failed to get projects from AYON server: {e}")
            return []

    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get all configuration for a specific project"""
        config = self.load_config()
        return config.get("projects", {}).get(project_name, {})

    def set_project_config(
        self, project_name: str, project_config: Dict[str, Any]
    ) -> bool:
        """Set all configuration for a specific project"""
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        config["projects"][project_name] = project_config
        return self.save_config(config)

    def delete_project(self, project_name: str) -> bool:
        """Delete a project and all its settings"""
        config = self.load_config()
        if "projects" in config and project_name in config["projects"]:
            del config["projects"][project_name]
            return self.save_config(config)
        return True  # Project didn't exist, so it's already "deleted"

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
    
    def get_last_selected_project(self) -> str:
        """Get the last selected project"""
        config = self.load_config()
        return config.get("last_selected_project")
    
    def set_last_selected_project(self, project_name: str) -> bool:
        """Set the last selected project"""
        config = self.load_config()
        config["last_selected_project"] = project_name
        return self.save_config(config)
    
    # Note: Project-specific environment variables are now handled by AYON Tools Environment Variables
    # This provides better integration with AYON's project loading system
