# -*- coding: utf-8 -*-
from qtpy import QtCore

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class ResetWindowPositionsAction(LocalConfigCompatibleAction):
    """Action to reset QArgparse window positions"""

    # AYON action metadata
    name = "reset_window_positions"
    label = "Reset Window Positions"
    icon = None
    color = "#4a90e2"
    order = 60

    # Canonical AYON families approach
    families = ["local_config"]

    def execute_with_config(self, config_data):
        """Execute the window position reset action"""
        log.info("ResetWindowPositionsAction.execute_with_config called")
        try:
            settings = QtCore.QSettings(
                QtCore.QSettings.IniFormat,
                QtCore.QSettings.UserScope,
                "ayon_core.vendor.python.qargparse",
                "QArgparse",
            )
            log.info(f"Settings file: {settings.fileName()}")
            settings.clear()
            settings.sync()
            log.info("QArgparse UI geometry cleared.")
        except Exception as e:
            log.error(f"Error resetting window positions: {e}")
            raise

