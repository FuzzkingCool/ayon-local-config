# -*- coding: utf-8 -*-
import os

try:
    from qtpy import QtWidgets
except ImportError:
    from qtpy5 import QtWidgets

from ayon_local_config.plugin import LocalConfigCompatibleAction
from ayon_local_config.logger import log


class SetProjectEnvironmentVariableAction(LocalConfigCompatibleAction):
    """Action to configure project-specific environment variables using AYON Tools"""
    
    # AYON action metadata
    name = "set_project_env_var"
    label = "Configure Project Environment Variables"
    icon = None
    color = "#4a90e2"
    order = 60
    
    # Canonical AYON families approach
    families = ["local_config"]
    
    def execute_with_config(self, config_data):
        """Execute the project environment variable configuration action"""
        try:
            # Get the environment variable name and value from config data
            var_name = self._get_variable_name(config_data)
            var_value = self._get_variable_value(config_data)
            
            if not var_name:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Variable Name",
                    "No environment variable name found in configuration.\n"
                    "Please set the variable name in your local settings."
                )
                return
            
            if var_value is None:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Variable Value",
                    "No environment variable value found in configuration.\n"
                    "Please set the variable value in your local settings."
                )
                return
            
            # Get current project name
            project_name = self._get_current_project_name()
            if not project_name:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Active Project",
                    "No active AYON project found.\n"
                    "Please ensure you have a project loaded."
                )
                return
            
            # Show information about AYON Tools approach
            self._show_ayon_tools_info(var_name, var_value, project_name)
            
        except Exception as e:
            log.error(f"Error in set project environment variable action: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Error configuring project environment variable: {str(e)}"
            )
    
    def _show_ayon_tools_info(self, var_name, var_value, project_name):
        """Show information about using AYON Tools for project environment variables"""
        message = f"""
Project Environment Variable Configuration

Variable: {var_name} = {var_value}
Project: {project_name}

To set this as a project-specific environment variable that automatically applies when the project is loaded:

1. Go to AYON Settings → Tools
2. Create or edit a tool (e.g., "Local Config Project Vars")
3. Add environment variable:
   {var_name} = {var_value}
4. Set project filter to: {project_name}
5. Save the tool configuration

This will automatically apply the environment variable when the project is loaded in the AYON Launcher.

For more information, see the AYON documentation on Tools Environment Variables.
        """
        
        QtWidgets.QMessageBox.information(
            None,
            "Project Environment Variable Configuration",
            message
        )
    
    def _get_variable_name(self, config_data):
        """Get the environment variable name from config data"""
        # Look for variable name in config data
        for group_data in config_data.values():
            if isinstance(group_data, dict):
                for setting_key, setting_value in group_data.items():
                    if "variable_name" in setting_key.lower() and setting_value:
                        return setting_value
        
        # Fallback: look for any setting that might contain the variable name
        for group_data in config_data.values():
            if isinstance(group_data, dict):
                for setting_key, setting_value in group_data.items():
                    if isinstance(setting_value, str) and setting_value.isupper() and "_" in setting_value:
                        # This looks like an environment variable name
                        return setting_value
        
        return None
    
    def _get_variable_value(self, config_data):
        """Get the environment variable value from config data"""
        # Look for variable value in config data
        for group_data in config_data.values():
            if isinstance(group_data, dict):
                for setting_key, setting_value in group_data.items():
                    if "variable_value" in setting_key.lower() and setting_value:
                        return setting_value
        
        # Fallback: look for any setting that might contain the variable value
        for group_data in config_data.values():
            if isinstance(group_data, dict):
                for setting_key, setting_value in group_data.items():
                    if isinstance(setting_value, str) and setting_value and "variable_name" not in setting_key.lower():
                        # This might be the variable value
                        return setting_value
        
        return None
    
    def _get_current_project_name(self):
        """Get the current AYON project name"""
        try:
            from ayon_core.pipeline import get_current_project_name
            return get_current_project_name()
        except Exception as e:
            log.warning(f"Failed to get current project name: {e}")
            return None
    
