# -*- coding: utf-8 -*-
import os
import traceback

from ayon_core.addon import AYONAddon, ITrayAddon
try:
    from qtpy import QtCore, QtGui, QtWidgets
except ImportError:
    from qtpy5 import QtCore, QtGui, QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.version import __version__


class LocalConfigMenuBuilder:
    def __init__(self, addon):
        self.addon = addon

    def update_menu_contents(self, menu):
        menu.clear()
        # Add "User Config" action
        action = QtWidgets.QAction("User Config", menu)
        action.triggered.connect(self.addon.show_config_window)
        menu.addAction(action)


class LocalConfigAddon(AYONAddon, ITrayAddon):
    """
    Local Config addon for AYON.

    This addon provides a way to manage user-specific configuration
    through a simple UI with settings defined on the server.
    """

    name = "local_config"
    label = "Local Config"
    version = __version__

    _config_window = None
    _menu_builder = None
    _tray_icon = None
    _menu = None

    def initialize(self, settings):
        """Initialization of addon."""
        # log.debug("Initializing Local Config addon")

        self.settings = settings.get("local_config", {})
        self._menu_builder = LocalConfigMenuBuilder(self)
        self.tray_icon = None
        self._menu = None

    def tray_init(self):
        # Called when tray is initialized
        if not self.tray_icon:
            self.tray_icon = QtWidgets.QSystemTrayIcon(self.get_icon())
            self.tray_icon.setToolTip(self.label)
            self.tray_icon.show()

    def tray_start(self):
        # Called when tray is started
        self._update_menu()

    def tray_exit(self):
        # Called when tray is exiting
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        if self._config_window:
            self._config_window.close()
            self._config_window = None

    def tray_menu(self, tray_menu):
        menu = QtWidgets.QMenu(self.label, tray_menu)
        menu.setProperty("submenu", "off")
        menu.setProperty("parentTrayMenu", tray_menu)
        tray_menu.addMenu(menu)
        self._menu = menu
        self._menu_builder.update_menu_contents(menu)
        # Connect aboutToShow for dynamic updates
        menu.aboutToShow.connect(lambda: self._menu_builder.update_menu_contents(menu))

    def _update_menu(self):
        if self._menu:
            self._menu_builder.update_menu_contents(self._menu)

    def get_icon(self):
        # Use a simple gear icon or similar for config
        return QtGui.QIcon()  # fallback - could add an icon file

    def get_launcher_action_paths(self):
        """Get paths to launcher action plugins"""
        # Get the addon root directory (where this file is located)
        addon_root = os.path.dirname(os.path.abspath(__file__))
        return [os.path.join(addon_root, "plugins", "actions")]

    def show_config_window(self):
        try:
            # Check if window exists and is valid (not closed)
            if self._config_window is None or not hasattr(self._config_window, 'isVisible'):
                from ayon_local_config.ui.config_window import LocalConfigWindow
                # Create window with complete UI
                self._config_window = LocalConfigWindow(self.settings)
                log.info("Created new Local Config window")
            else:
                log.info("Reusing existing Local Config window")
            
            # Show window
            self._config_window.show()
            log.info("Local Config window shown")
            
        except Exception as e:
            log.error(f"Failed to show Local Config window: {e}")
            log.error(traceback.format_exc())