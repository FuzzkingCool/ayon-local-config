# -*- coding: utf-8 -*-
# discipline: new-module local-config action for full AYON Qt settings reset
from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction
from ayon_local_config.qt_settings_reset import clear_all_ayon_pipeline_qt_settings

_RESET_SUMMARY = (
    "This resets saved Qt UI state for AYON and MDHR pipeline tools:\n"
    "- Tool window positions and splitter layouts (Launcher, Publisher, Loader, …)\n"
    "- Loader view mode and grid density\n"
    "- Color picker user swatches\n"
    "- QArgparse option dialog geometry\n"
    "- Harmony Scale/Crop dialog section state\n"
    "- Harmony Quick Render marker table sizing\n\n"
    "Host application settings outside these scopes are not changed.\n"
    "Restart open tools for changes to take full effect."
)


class ResetQtSettingsAction(LocalConfigCompatibleAction):
    """Reset all known AYON / MDHR pipeline Qt UI settings."""

    name = "reset_qt_settings"
    label = "Reset All Qt UI Settings"
    icon = None
    color = "#4a90e2"
    order = 61

    families = ["local_config"]

    def execute_with_config(self, config_data):
        log.debug("ResetQtSettingsAction.execute_with_config called")
        try:
            reply = QtWidgets.QMessageBox.question(
                None,
                "Reset Qt UI Settings",
                _RESET_SUMMARY,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                log.debug("Reset Qt UI settings cancelled by user")
                return

            cleared_paths = clear_all_ayon_pipeline_qt_settings()
            QtWidgets.QMessageBox.information(
                None,
                "Reset Qt UI Settings",
                (
                    f"Cleared {len(cleared_paths)} Qt settings store(s).\n"
                    "Restart open AYON tools to apply."
                ),
            )
            log.debug("Cleared Qt settings stores: %s", cleared_paths)
        except Exception as exc:
            log.error("Error resetting Qt UI settings: %s", exc)
            raise
