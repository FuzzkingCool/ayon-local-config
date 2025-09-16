# -*- coding: utf-8 -*-
import os
import subprocess
import platform

try:
    from qtpy import QtWidgets
except ImportError:
    from qtpy5 import QtWidgets

from ayon_local_config.plugin import LocalConfigCompatibleAction
from ayon_local_config.logger import log


class OpenProjectFolderAction(LocalConfigCompatibleAction):
    """Example action to open project folder in file explorer"""
    
    # AYON action metadata
    name = "open_project_folder"
    label = "Open Project Folder"
    icon = None
    color = "#4a90e2"
    order = 200
    
    # Canonical AYON families approach
    families = ["local_config"]
    
    def execute_with_config(self, config_data):
        """Execute the action with current config data"""
        try:
            # Look for a project path setting in the config data
            project_path = None
            
            # Search through all groups for a path-type setting
            for group_data in config_data.values():
                if isinstance(group_data, dict):
                    for setting_key, setting_value in group_data.items():
                        # Check if this looks like a project path
                        if ("project" in setting_key.lower() or 
                            "path" in setting_key.lower()) and setting_value:
                            if os.path.exists(setting_value):
                                project_path = setting_value
                                break
                    if project_path:
                        break
            
            if not project_path:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Project Path",
                    "No valid project path found in configuration.\n"
                    "Please configure a project path in your local settings."
                )
                return
            
            # Open the folder in the system file explorer
            self._open_folder(project_path)
            
            QtWidgets.QMessageBox.information(
                None,
                "Folder Opened",
                f"Opened project folder:\n{project_path}"
            )
            
        except Exception as e:
            log.error(f"Error in open project folder action: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Error opening project folder: {str(e)}"
            )
    
    def _open_folder(self, path):
        """Open folder in system file explorer"""
        system = platform.system()
        
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
