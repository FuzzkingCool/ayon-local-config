# -*- coding: utf-8 -*-
import os

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class SetRenderPathAction(LocalConfigCompatibleAction):
    """Action to set the AYON_LOCAL_RENDER_PATH environment variable"""

    # AYON action metadata
    name = "set_local_render_path"
    label = "Set Local Render Path"
    icon = None
    color = "#4a90e2"
    order = 50

    # Canonical AYON families approach
    families = ["local_config"]

    def execute_with_config(self, config_data):
        """Execute the local render path management action"""
        log.info(
            f"SetRenderPathAction.execute_with_config called with config_data keys: {list(config_data.keys())}"
        )
        try:
            # Get the local render path from config data
            user_settings = config_data.get("user_settings", {})
            local_render_path = user_settings.get("set_default_localrender_path")

            if not local_render_path:
                log.warning("No Local Render Path found in configuration")
                return

            # Expand user home directory and normalize the path
            local_render_path = os.path.expanduser(local_render_path)
            local_render_path = os.path.normpath(local_render_path)

            # Check if the path exists
            if not os.path.exists(local_render_path):
                QtWidgets.QMessageBox.warning(
                    None,
                    "Path Not Found",
                    f"The local render path does not exist:\n{local_render_path}\n\n"
                    "Please check the path and try again.",
                )
                return

            # Register environment variable with the registry
            self.register_environment_variable(
                "AYON_LOCAL_RENDER_PATH",
                local_render_path,
                "AYON Local Render Path - automatically set by Local Config addon",
            )

            log.info(f"Registered AYON_LOCAL_RENDER_PATH with registry: {local_render_path}")

            return True

        except Exception as e:
            log.error(f"Failed to manage local render path environment variable: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Failed to manage local render path environment variable:\n{str(e)}",
            )
            return False

