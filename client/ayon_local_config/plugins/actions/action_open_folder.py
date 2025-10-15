# -*- coding: utf-8 -*-
import os
import platform
import subprocess

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


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

            # Get the path from action_data
            if not action_data:
                log.warning("No folder path provided")
                return

            # Expand environment variables and user home directory
            folder_path = os.path.expanduser(os.path.expandvars(action_data))
            
            # Create directory if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)

            # Open the folder in the system file explorer
            self._open_folder(folder_path)

        except Exception as e:
            log.error(f"Error in open folder action: {e}")

    def _open_folder(self, path):
        """Open folder in system file explorer"""
        system = platform.system()

        if system == "Windows":  # Windows
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
