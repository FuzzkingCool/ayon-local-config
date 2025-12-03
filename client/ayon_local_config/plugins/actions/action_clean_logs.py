# -*- coding: utf-8 -*-
import os

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


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
            # Get sandbox path from config or environment
            user_settings = config_data.get("user_settings", {})
            sandbox_path = (
                config_data.get("_triggered_setting_value")
                or user_settings.get("ayon_sandbox_folder")
                or os.environ.get("AYON_LOCAL_SANDBOX")
                or os.path.expanduser("~/.ayon")
            )

            logs_dir = os.path.join(sandbox_path, "logs").replace("\\", "/")

            if not os.path.exists(logs_dir):
                log.debug("No logs directory found")
                return

            # Ask for confirmation
            reply = QtWidgets.QMessageBox.question(
                None,
                "Clean Logs",
                f"Are you sure you want to delete all log files in:\n{logs_dir}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if reply == QtWidgets.QMessageBox.Yes:
                # Clean log files
                cleaned_count = 0
                for filename in os.listdir(logs_dir):
                    if filename.endswith(".log"):
                        file_path = os.path.join(logs_dir, filename)
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            log.warning(f"Could not remove {file_path}: {e}")

                QtWidgets.QMessageBox.information(
                    None, "Clean Logs", f"Cleaned {cleaned_count} log files."
                )
                log.debug(f"Cleaned {cleaned_count} log files")

        except Exception as e:
            log.error(f"Error in clean logs action: {e}")
