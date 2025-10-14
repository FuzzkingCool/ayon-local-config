# -*- coding: utf-8 -*-
import os
import shutil
try:
    from qtpy import QtWidgets
except ImportError:
    from qtpy5 import QtWidgets

from ayon_local_config.plugin import LocalConfigCompatibleAction
from ayon_local_config.logger import log


class CleanLogsAction(LocalConfigCompatibleAction):
    """Example action plugin to clean log files"""
    
    # AYON action metadata
    name = "clean_logs"
    label = "Clean Log Files"
    icon = None
    color = "#ff6b35"
    order = 100
    
    # Canonical AYON families approach
    families = ["local_config"]
    
    def execute_with_config(self, config_data):
        """Execute the clean logs action"""
        try:
            # Check if we have a specific triggered setting value (e.g., from a path setting)
            sandbox_path = None
            if '_triggered_setting_value' in config_data:
                triggered_value = config_data['_triggered_setting_value']
                if triggered_value and os.path.exists(triggered_value):
                    sandbox_path = triggered_value
                    log.debug(f"Using triggered setting value for sandbox: {sandbox_path}")
            
            # Fallback to AYON_LOCAL_SANDBOX environment variable
            if not sandbox_path:
                sandbox_path = os.environ.get('AYON_LOCAL_SANDBOX')
                if sandbox_path:
                    log.debug(f"Using AYON_LOCAL_SANDBOX environment variable: {sandbox_path}")
            
            # Final fallback to default
            if not sandbox_path:
                sandbox_path = os.path.expanduser("~/.ayon")
                log.debug(f"Using default sandbox path: {sandbox_path}")
            
            logs_dir = os.path.join(sandbox_path, "logs")
            
            if not os.path.exists(logs_dir):
                QtWidgets.QMessageBox.information(
                    None,
                    "Clean Logs",
                    "No logs directory found."
                )
                return
            
            # Ask for confirmation
            reply = QtWidgets.QMessageBox.question(
                None,
                "Clean Logs",
                f"Are you sure you want to delete all log files in:\n{logs_dir}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                # Clean log files
                cleaned_count = 0
                for filename in os.listdir(logs_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(logs_dir, filename)
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            log.warning(f"Could not remove {file_path}: {e}")
                
                QtWidgets.QMessageBox.information(
                    None,
                    "Clean Logs",
                    f"Cleaned {cleaned_count} log files."
                )
                log.info(f"Cleaned {cleaned_count} log files")
            
        except Exception as e:
            log.error(f"Error in clean logs action: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Error cleaning logs: {str(e)}"
            )
