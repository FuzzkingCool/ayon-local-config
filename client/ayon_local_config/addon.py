# -*- coding: utf-8 -*-
import os
import queue
import threading
import traceback

from ayon_core.addon import AYONAddon, ITrayAddon
from ayon_core.style import AYON_COLOR
from ayon_core.tools.tray.launch_progress import (
    clear_launch_progress_queue,
    report_launch_progress,
    set_launch_progress_queue,
)
from ayon_core.tools.tray.ui.tray_menu_icons import (
    apply_tray_menu_icon,
    apply_tray_menu_tooltip,
    create_tray_icon_action,
    install_tray_menu_tooltips,
)
from ayon_core.tools.utils.lib import get_qta_icon_by_name_and_color
from qtpy import QtGui, QtWidgets

from ayon_local_config.environment_registry import (
    initialize_environment_registry,
)
from ayon_local_config.logger import log
from ayon_local_config.storage import (
    LocalConfigStorage,
    _stable_localconfig_paths,
    format_recent_work_menu_label,
    format_resume_work_tooltip,
    read_last_workfile_session,
    read_recent_workfile_sessions,
    touch_recent_workfile_session,
)
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
    _resume_action = None
    _recent_menu = None
    _environment_registry = None

    def get_global_environments(self):
        """Expose the local config directory so PreLaunchHooks can find it.

        ``AYON_LOCAL_CONFIG_DIR`` is consumed by
        ``RecordLastWorkfileSession`` in ayon-core to write the session
        record without a hard dependency on this addon.
        """
        config_dir, _ = _stable_localconfig_paths()
        return {"AYON_LOCAL_CONFIG_DIR": config_dir}

    def initialize(self, settings):
        """Initialization of addon."""
        # log.debug("Initializing Local Config addon")

        self.settings = settings.get("local_config", {})
        self.tray_icon = None
        self._action = None

        # Check if addon is enabled
        if not self.settings.get("enabled", False):
            log.debug("Local Config addon is disabled")
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
                    log.debug("Restored environment variables on addon initialization")
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
                log.debug("Restored environment variables on tray initialization")
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
                log.debug("Initializing AYON sandbox environment variable from settings")
                execute_action_by_name("SetAyonSandboxPathAction", config_data)

            if "set_default_local_render_path" in user_settings:
                log.debug(
                    "Initializing local render path environment variable from settings"
                )
            else:
                log.debug(
                    "No local render path in settings; registering OS Pictures default"
                )
            execute_action_by_name("SetRenderPathAction", config_data)

            # Execute Unity project action if Unity project path is set
            if "unity_project_path" in user_settings:
                log.debug(
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

        self._resume_action = create_tray_icon_action(tray_menu, "Resume Work")
        apply_tray_menu_icon(
            self._resume_action,
            get_qta_icon_by_name_and_color("paint-brush", AYON_COLOR),
        )
        self._resume_action.triggered.connect(self._trigger_resume_work)
        install_tray_menu_tooltips(tray_menu)
        tray_menu.addAction(self._resume_action)

        self._recent_menu = QtWidgets.QMenu("Recent Work", tray_menu)
        apply_tray_menu_icon(
            self._recent_menu.menuAction(),
            get_qta_icon_by_name_and_color("clock", AYON_COLOR),
        )
        tray_menu.addMenu(self._recent_menu)

        tray_menu.aboutToShow.connect(self._refresh_tray_work_actions)
        self._refresh_tray_work_actions()
        tray_menu.addSeparator()

        menu_item_name = self.settings.get("menu_item_name", "User Config")
        self._action = QtWidgets.QAction(menu_item_name, tray_menu)
        self._action.triggered.connect(self.show_config_window)
        tray_menu.addAction(self._action)

    def _refresh_tray_work_actions(self):
        last_session = read_last_workfile_session()
        if last_session and last_session.get("workfile_path"):
            touch_recent_workfile_session(last_session)

        enabled = last_session is not None
        self._resume_action.setEnabled(enabled)
        tooltip = format_resume_work_tooltip(last_session) if enabled else ""
        apply_tray_menu_tooltip(self._resume_action, tooltip)

        self._recent_menu.clear()
        recent_sessions = read_recent_workfile_sessions()
        if not recent_sessions:
            placeholder = self._recent_menu.addAction("(No recent workfiles)")
            placeholder.setEnabled(False)
            return

        for session in recent_sessions:
            label = format_recent_work_menu_label(session)
            action = create_tray_icon_action(self._recent_menu, label)
            apply_tray_menu_tooltip(
                action,
                format_resume_work_tooltip(session),
            )
            action.triggered.connect(
                lambda checked=False, entry=session: self._trigger_recent_work(entry)
            )
            self._recent_menu.addAction(action)

    def _trigger_resume_work(self):
        try:
            self._do_resume_work()
        except Exception:
            log.error("Resume Work failed", exc_info=True)

    def _trigger_recent_work(self, session):
        try:
            touch_recent_workfile_session(session)
            self._launch_workfile_session(session, title="Recent Work")
        except Exception:
            log.error("Recent Work failed", exc_info=True)

    def _resolve_resume_app_name(self, session, apps_addon):
        app_name = session.get("app_name")
        if app_name:
            return app_name

        host_name = session.get("host_name")
        if not host_name:
            return None

        apps_manager = apps_addon.get_applications_manager()
        app = apps_manager.find_latest_available_variant_for_group(host_name)
        if app is None:
            return None
        return app.full_name

    def _do_resume_work(self):
        session = read_last_workfile_session()
        if not session:
            log.debug("Resume Work: no session file found, aborting")
            return

        touch_recent_workfile_session(session)
        self._launch_workfile_session(session, title="Resume Work")

    def _launch_workfile_session(self, session, *, title):
        apps_addon = self.manager.get_enabled_addon("applications")
        if apps_addon is None:
            self.show_tray_message(
                title, "Applications addon is unavailable."
            )
            return

        app_name = self._resolve_resume_app_name(session, apps_addon)
        if not app_name:
            self.show_tray_message(
                title,
                "Could not resolve application from saved session.",
            )
            return

        app_label = app_name
        log.debug("%s: launching %s", title, app_label)

        progress_queue = queue.Queue()
        set_launch_progress_queue(progress_queue)
        report_launch_progress(10, f"Launching {app_label}...")

        from ayon_core.tools.tray.ui.progress_dialog import (
            CandyStripeProgressBar,
            WorkfileProgressDialog,
        )

        dialog = WorkfileProgressDialog(
            parent=None,
            title=title,
            bar_only=False,
            initial_message=f"Launching {app_label}...",
            progress_bar_class=CandyStripeProgressBar,
        )
        dialog.start_polling(progress_queue)
        dialog.show()

        def _launch():
            try:
                apps_addon.launch_application(
                    app_name=app_name,
                    project_name=session["project_name"],
                    folder_path=session["folder_path"],
                    task_name=session["task_name"],
                    workfile_path=session.get("workfile_path") or None,
                )
                progress_queue.put((100, "Launched"))
            except Exception:
                log.error("%s launch failed", title, exc_info=True)
                progress_queue.put((-1, "Launch failed"))
            finally:
                clear_launch_progress_queue()

        threading.Thread(target=_launch, daemon=True).start()

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
            from ayon_local_config.project_context import (
                get_user_accessible_project_names,
                pick_accessible_project_name,
                resolve_tray_project_name,
            )
            from ayon_local_config.settings_loader import load_server_settings
            from ayon_local_config.ui.config_window import LocalConfigWindow

            project_name = resolve_tray_project_name()
            accessible_name = pick_accessible_project_name(
                project_name,
                get_user_accessible_project_names(),
            )
            if accessible_name:
                project_name = accessible_name

            server_settings = load_server_settings(project_name)

            if self._config_window is None or not hasattr(
                self._config_window, "isVisible"
            ):
                self._config_window = LocalConfigWindow(
                    server_settings,
                    project_name=project_name,
                )
                log.debug("Created new Local Config window")
            else:
                self._config_window.refresh_for_project(
                    project_name,
                    server_settings,
                )
                log.debug("Refreshed existing Local Config window")

            self._config_window.show()
            log.debug("Local Config window shown")

        except Exception as e:
            log.error(f"Failed to show Local Config window: {e}")
            log.error(traceback.format_exc())
