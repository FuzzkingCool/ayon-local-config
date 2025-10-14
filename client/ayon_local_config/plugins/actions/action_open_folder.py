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
    
    def execute_with_config(self, config_data, action_data=""):
        """Execute the action with current config data"""
        try:
            # Debug: Log the parameters
            log.debug(f"Action data: {action_data}")
            log.debug(f"Config data keys: {list(config_data.keys())}")
            
            # Get the path from the action_data or config_data
            folder_path = None
            
            # First, check if we have action_data  
            if action_data:
                log.debug(f"Using action_data for folder path: {action_data}")
                # Expand environment variables and user home directory
                expanded_path = os.path.expanduser(os.path.expandvars(action_data))
                log.debug(f"Expanded path: {expanded_path}")
                log.debug(f"Path exists: {os.path.exists(expanded_path)}")
                if os.path.exists(expanded_path):
                    folder_path = expanded_path
                    log.debug(f"Using action_data for folder path: {folder_path}")
                else:
                    log.debug(f"Expanded path does not exist: {expanded_path}")
                    # Try to create the directory if it doesn't exist
                    try:
                        os.makedirs(expanded_path, exist_ok=True)
                        if os.path.exists(expanded_path):
                            folder_path = expanded_path
                            log.debug(f"Created directory and using path: {folder_path}")
                    except Exception as e:
                        log.debug(f"Failed to create directory {expanded_path}: {e}")
            
            
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
        
        if system == "Windows": # Windows
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
