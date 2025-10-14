# -*- coding: utf-8 -*-
import os
from pathlib import Path

try:
    from qtpy import QtWidgets
except ImportError:
    from qtpy5 import QtWidgets

from ayon_local_config.plugin import LocalConfigCompatibleAction
from ayon_local_config.logger import log


class SetUnityProjectAction(LocalConfigCompatibleAction):
    """Action to set the AYON_UNITY_PROJECT environment variable"""
    
    # AYON action metadata
    name = "set_unity_project"
    label = "Set Unity Project"
    icon = None
    color = "#4a90e2"
    order = 50
    
    # Canonical AYON families approach
    families = ["local_config"]
    
    def execute_with_config(self, config_data):
        """Execute the Unity project path setting action"""
        try:
            # Check if "Auto Open Unity Project" is enabled
            auto_open_unity = self._get_auto_open_unity_setting(config_data)
            
            if auto_open_unity:
                # Get the Unity project path from config data
                unity_project_path = self._get_unity_project_path(config_data)
                
                if not unity_project_path:
                    QtWidgets.QMessageBox.warning(
                        None,
                        "No Unity Project Path",
                        "No Unity Project Path found in configuration.\n"
                        "Please set the Unity Project Path in your local settings."
                    )
                    return
                
                # Normalize the path
                unity_project_path = os.path.normpath(unity_project_path)
                
                # Check if the path exists
                if not os.path.exists(unity_project_path):
                    QtWidgets.QMessageBox.warning(
                        None,
                        "Path Not Found",
                        f"The Unity project path does not exist:\n{unity_project_path}\n\n"
                        "Please check the path and try again."
                    )
                    return
                
                # Register the environment variable with the registry
                success = self.register_environment_variable(
                    'AYON_UNITY_PROJECT', 
                    unity_project_path,
                    "AYON Unity Project Path - automatically set by Local Config addon"
                )
                
                if success:
                    log.info(f"Registered AYON_UNITY_PROJECT with registry: {unity_project_path}")
                    
                    QtWidgets.QMessageBox.information(
                        None,
                        "Unity Project Registered",
                        f"Successfully registered AYON_UNITY_PROJECT to:\n{unity_project_path}\n\n"
                        "This environment variable will be automatically restored when the addon loads."
                    )
                else:
                    # Fallback to direct environment variable setting
                    os.environ["AYON_UNITY_PROJECT"] = unity_project_path
                    log.info(f"Set AYON_UNITY_PROJECT directly: {unity_project_path}")
                    
                    QtWidgets.QMessageBox.information(
                        None,
                        "Unity Project Set",
                        f"Successfully set AYON_UNITY_PROJECT to:\n{unity_project_path}"
                    )
            else:
                # Unregister the environment variable from the registry
                success = self.unregister_environment_variable('AYON_UNITY_PROJECT')
                
                if success:
                    log.info("Unregistered AYON_UNITY_PROJECT from registry")
                    
                    QtWidgets.QMessageBox.information(
                        None,
                        "Unity Project Unregistered",
                        "Successfully unregistered AYON_UNITY_PROJECT environment variable.\n"
                        "This variable will no longer be automatically restored."
                    )
                else:
                    # Fallback to direct environment variable removal
                    if "AYON_UNITY_PROJECT" in os.environ:
                        del os.environ["AYON_UNITY_PROJECT"]
                        log.info("Unset AYON_UNITY_PROJECT environment variable")
                        
                        QtWidgets.QMessageBox.information(
                            None,
                            "Unity Project Unset",
                            "Successfully unset AYON_UNITY_PROJECT environment variable"
                        )
                    else:
                        log.info("AYON_UNITY_PROJECT was not set")
                        QtWidgets.QMessageBox.information(
                            None,
                            "Unity Project Unset",
                            "AYON_UNITY_PROJECT environment variable was not set"
                        )
            
            return True
            
        except Exception as e:
            log.error(f"Failed to manage Unity project environment variable: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Failed to manage Unity project environment variable:\n{str(e)}"
            )
            return False
    
    def _get_unity_project_path(self, config_data):
        """Get the Unity project path from config data"""
        # Look for Unity project path in the config data
        # This could be in various places depending on how the config is structured
        
        # First, try to find it in the ayon_local_sandbox group
        ayon_sandbox_config = config_data.get('ayon_local_sandbox', {})
        if ayon_sandbox_config:
            # Look for Unity project path setting
            for setting_id, value in ayon_sandbox_config.items():
                if 'unity' in setting_id.lower() and 'project' in setting_id.lower():
                    return value
        
        # Also check if there's a direct Unity project path in the config
        unity_project_path = config_data.get('unity_project_path')
        if unity_project_path:
            return unity_project_path
        
        # Check for any setting that might contain the Unity project path
        for group_name, group_config in config_data.items():
            if isinstance(group_config, dict):
                for setting_id, value in group_config.items():
                    if isinstance(value, str) and 'unity' in setting_id.lower() and 'project' in setting_id.lower():
                        return value
        
        return None
    
    def _get_auto_open_unity_setting(self, config_data):
        """Get the 'Auto Open Unity Project' setting from config data"""
        # Look for the auto open Unity setting in the config data
        # This could be in various places depending on how the config is structured
        
        # First, try to find it in the ayon_local_sandbox group
        ayon_sandbox_config = config_data.get('ayon_local_sandbox', {})
        if ayon_sandbox_config:
            # Look for auto open Unity project setting
            for setting_id, value in ayon_sandbox_config.items():
                if 'auto' in setting_id.lower() and 'open' in setting_id.lower() and 'unity' in setting_id.lower():
                    return bool(value)
        
        # Also check if there's a direct auto open Unity setting in the config
        auto_open_unity = config_data.get('auto_open_unity_project')
        if auto_open_unity is not None:
            return bool(auto_open_unity)
        
        # Check for any setting that might contain the auto open Unity setting
        for group_name, group_config in config_data.items():
            if isinstance(group_config, dict):
                for setting_id, value in group_config.items():
                    if isinstance(value, bool) and 'auto' in setting_id.lower() and 'open' in setting_id.lower() and 'unity' in setting_id.lower():
                        return value
        
        # Default to False if not found
        return False
