# -*- coding: utf-8 -*-
import os
import traceback

from ayon_core.addon import AYONAddon, ITrayAddon
from qtpy import QtGui, QtWidgets

from ayon_local_config.environment_registry import (
    initialize_environment_registry,
)
from ayon_local_config.logger import log
from ayon_local_config.storage import LocalConfigStorage
from ayon_local_config.version import __version__


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
    _tray_icon = None
    _action = None
    _environment_registry = None

    def initialize(self, settings):
        """Initialization of addon."""
        # log.debug("Initializing Local Config addon")

        self.settings = settings.get("local_config", {})
        self.tray_icon = None
        self._action = None

        # Check if addon is enabled
        if not self.settings.get("enabled", False):
            log.info("Local Config addon is disabled")
            return

        # Initialize environment variable registry
        try:
            storage = LocalConfigStorage()
            self._environment_registry = initialize_environment_registry(storage)
            log.debug("Environment variable registry initialized")
            
            # Restore environment variables immediately after initialization
            if self._environment_registry:
                try:
                    self._environment_registry.restore_environment_variables()
                    log.info("Restored environment variables on addon initialization")
                except Exception as e:
                    log.error(f"Failed to restore environment variables: {e}")
        except Exception as e:
            log.error(f"Failed to initialize environment variable registry: {e}")
            self._environment_registry = None

    def tray_init(self):
        # Called when tray is initialized
        if not self.tray_icon:
            self.tray_icon = QtWidgets.QSystemTrayIcon(self.get_icon())
            self.tray_icon.setToolTip(self.label)
            self.tray_icon.show()

        # Restore environment variables when tray initializes
        if self._environment_registry:
            try:
                self._environment_registry.restore_environment_variables()
                log.info("Restored environment variables on tray initialization")
            except Exception as e:
                log.error(f"Failed to restore environment variables: {e}")

        # Initialize environment variables from settings if not already registered
        self._initialize_environment_variables_from_settings()

    def _initialize_environment_variables_from_settings(self):
        """Initialize environment variables from current settings"""
        try:
            from ayon_local_config.plugin import execute_action_by_name
            from ayon_local_config.storage import LocalConfigStorage

            # Get current config data
            storage = LocalConfigStorage()
            user_settings = storage.get_group_config("user_settings")
            
            # Wrap user_settings in proper config_data structure that actions expect
            config_data = {
                "user_settings": user_settings
            }

            # Execute sandbox path action if sandbox folder is set
            if "ayon_sandbox_folder" in user_settings:
                log.info("Initializing AYON sandbox environment variable from settings")
                execute_action_by_name("SetAyonSandboxPathAction", config_data)

            # Execute Unity project action if Unity project path is set
            if "unity_project_path" in user_settings:
                log.info(
                    "Initializing Unity project environment variable from settings"
                )
                execute_action_by_name("SetUnityProjectAction", config_data)

        except Exception as e:
            log.error(f"Failed to initialize environment variables from settings: {e}")

    def tray_start(self):
        # Called when tray is started
        pass

    def tray_exit(self):
        # Called when tray is exiting
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        if self._config_window:
            self._config_window.close()
            self._config_window = None
        self._action = None

    def tray_menu(self, tray_menu):
        # Check if addon is enabled
        if not self.settings.get("enabled", False):
            return

        # Get the menu item name from settings
        menu_item_name = self.settings.get("menu_item_name", "User Config")

        # Create a single action instead of a submenu
        self._action = QtWidgets.QAction(menu_item_name, tray_menu)
        self._action.triggered.connect(self.show_config_window)
        tray_menu.addAction(self._action)

    def get_icon(self):
        # Use a simple gear icon or similar for config
        return QtGui.QIcon()  # fallback - could add an icon file

    def get_launcher_action_paths(self):
        """Get paths to launcher action plugins"""
        # Get the addon root directory (where this file is located)
        addon_root = os.path.dirname(os.path.abspath(__file__))
        return [os.path.join(addon_root, "plugins", "actions")]

    def get_environment_registry(self):
        """Get the environment variable registry instance"""
        return self._environment_registry

    def show_config_window(self):
        try:
            # Check if window exists and is valid (not closed)
            if self._config_window is None or not hasattr(
                self._config_window, "isVisible"
            ):
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
