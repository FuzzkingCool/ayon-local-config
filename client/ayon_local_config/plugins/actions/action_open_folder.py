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


class OpenFolderAction(LocalConfigCompatibleAction):
    """Generic action to open folder in file explorer"""
    
    # AYON action metadata
    name = "open_folder"
    label = "Open Folder"
    icon = None
    color = "#4a90e2"
    order = 200
    
    # Canonical AYON families approach
    families = ["local_config"]
    
    def execute_with_config(self, config_data):
        """Execute the action with current config data"""
        try:
            # Get the path from the default value or triggered setting value
            folder_path = None
            
            # First, check if we have a specific triggered setting value
            if '_triggered_setting_value' in config_data:
                triggered_value = config_data['_triggered_setting_value']
                if triggered_value:
                    # Expand environment variables in the path
                    expanded_path = os.path.expandvars(triggered_value)
                    if os.path.exists(expanded_path):
                        folder_path = expanded_path
                        log.debug(f"Using triggered setting value for folder path: {folder_path}")
            
            # Fallback: Search through all groups for a path-type setting
            if not folder_path:
                for group_data in config_data.values():
                    if isinstance(group_data, dict):
                        for setting_key, setting_value in group_data.items():
                            # Check if this looks like a folder path
                            if setting_value:
                                # Expand environment variables in the path
                                expanded_path = os.path.expandvars(setting_value)
                                if os.path.exists(expanded_path):
                                    # Check if it's a directory or if the key suggests it's a folder
                                    if os.path.isdir(expanded_path) or "folder" in setting_key.lower() or "path" in setting_key.lower():
                                        folder_path = expanded_path
                                        log.debug(f"Found folder path in config: {folder_path}")
                                        break
                        if folder_path:
                            break
            
            if not folder_path:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Folder Path",
                    "No valid folder path found in configuration.\n"
                    "Please configure a folder path in your local settings."
                )
                return
            
            # Open the folder in the system file explorer
            self._open_folder(folder_path)
            
            QtWidgets.QMessageBox.information(
                None,
                "Folder Opened",
                f"Opened folder:\n{folder_path}"
            )
            
        except Exception as e:
            log.error(f"Error in open folder action: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Error opening folder: {str(e)}"
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
