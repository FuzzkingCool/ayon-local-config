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
            # Get logs directory
            logs_dir = os.path.join(os.path.expanduser("~"), ".ayon", "logs")
            
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
