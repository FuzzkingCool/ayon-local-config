# -*- coding: utf-8 -*-
import os

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class SetUnityProjectAction(LocalConfigCompatibleAction):
    """Action to set the AYON_UNITY_PROJECT_PATH environment variable"""

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
        log.debug(
            f"SetUnityProjectAction.execute_with_config called with config_data keys: {list(config_data.keys())}"
        )
        try:
            # Get the Unity project path and auto-open setting from config data
            user_settings = config_data.get("user_settings", {})
            unity_project_path = user_settings.get("unity_project_path")
            auto_open_unity_raw = user_settings.get("auto_open_unity_project", "false")
            
            # Normalize boolean value - handle both string and boolean types
            if isinstance(auto_open_unity_raw, bool):
                auto_open_unity = auto_open_unity_raw
            elif isinstance(auto_open_unity_raw, str):
                auto_open_unity = auto_open_unity_raw.lower() in ("true", "1", "yes", "on")
            else:
                auto_open_unity = bool(auto_open_unity_raw)

            # Handle Unity project path if provided
            if unity_project_path:
                # Expand user home directory and normalize the path
                unity_project_path = os.path.expanduser(unity_project_path)
                unity_project_path = os.path.normpath(unity_project_path)

                # Check if the path exists
                if not os.path.exists(unity_project_path):
                    QtWidgets.QMessageBox.warning(
                        None,
                        "Path Not Found",
                        f"The Unity project path does not exist:\n{unity_project_path}\n\n"
                        "Please check the path and try again.",
                    )
                    return

                # Register the Unity project path
                self.register_environment_variable(
                    "AYON_UNITY_PROJECT_PATH",
                    unity_project_path,
                    "AYON Unity Project Path - automatically set by Local Config addon",
                )
                log.debug(f"Registered AYON_UNITY_PROJECT_PATH with registry: {unity_project_path}")

                # Register auto-open setting based on toggle (only if project path exists)
                # Always register the environment variable, just with different values
                auto_open_value = "true" if auto_open_unity else "false"
                self.register_environment_variable(
                    "AYON_UNITY_AUTO_OPEN_PROJECT",
                    auto_open_value,
                    "AYON Unity Auto Open Project - automatically set by Local Config addon",
                )
                log.debug(f"Registered AYON_UNITY_AUTO_OPEN_PROJECT with registry: {auto_open_value}")
            else:
                # No Unity project path set, unregister both variables
                self.unregister_environment_variable("AYON_UNITY_PROJECT_PATH")
                self.unregister_environment_variable("AYON_UNITY_AUTO_OPEN_PROJECT")
                log.debug("Unregistered AYON_UNITY_PROJECT_PATH from registry")
                log.debug("Unregistered AYON_UNITY_AUTO_OPEN_PROJECT from registry")

            return True

        except Exception as e:
            log.error(f"Failed to manage Unity project environment variable: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Failed to manage Unity project environment variable:\n{str(e)}",
            )
            return False

