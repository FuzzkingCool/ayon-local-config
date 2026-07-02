# -*- coding: utf-8 -*-
import os

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.path_utils import resolve_local_render_path
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
        log.debug(
            f"SetRenderPathAction.execute_with_config called with config_data keys: {list(config_data.keys())}"
        )
        try:
            user_settings = config_data.get("user_settings", {})
            config_value = user_settings.get("set_default_local_render_path")
            local_render_path = resolve_local_render_path(config_value)

            if not os.path.exists(local_render_path):
                log.warning(
                    "Local render path does not exist yet: %s",
                    local_render_path,
                )

            self.register_environment_variable(
                "AYON_LOCAL_RENDER_PATH",
                local_render_path,
                "AYON Local Render Path - automatically set by Local Config addon",
            )

            log.debug(
                "Registered AYON_LOCAL_RENDER_PATH with registry: %s",
                local_render_path,
            )

            return True

        except Exception as e:
            log.error(f"Failed to manage local render path environment variable: {e}")
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                f"Failed to manage local render path environment variable:\n{str(e)}",
            )
            return False
