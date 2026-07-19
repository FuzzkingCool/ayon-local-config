# -*- coding: utf-8 -*-
import json
import os
import shutil
from typing import Any, Dict, List, Optional

from ayon_local_config.logger import log
from ayon_local_config.project_context import (
    get_user_accessible_project_names,
    resolve_tray_project_name,
)


def _stable_localconfig_paths():
    """Profile-local Local Config paths (never under AYON_LOCAL_SANDBOX)."""
    config_dir = os.path.join(os.path.expanduser("~"), ".ayon", "settings")
    return config_dir, os.path.join(config_dir, "localconfig.json")


def _session_config_dir() -> str:
    return os.environ.get(
        "AYON_LOCAL_CONFIG_DIR",
        os.path.join(os.path.expanduser("~"), ".ayon", "settings"),
    )


def _session_file_path() -> str:
    """Return the last_workfile_session.json path.

    Reads ``AYON_LOCAL_CONFIG_DIR`` when set (injected at tray init), falling
    back to the stable profile directory so the path is always deterministic.
    """
    return os.path.join(_session_config_dir(), "last_workfile_session.json")


def read_last_workfile_session() -> Optional[Dict[str, Any]]:
    """Return the last workfile session dict, or None if absent/unreadable."""
    path = _session_file_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def format_resume_work_tooltip(session: Optional[Dict[str, Any]]) -> str:
    """Build tray tooltip text from a last-workfile session record."""
    if not session:
        return ""

    context_parts = [
        part
        for part in (
            session.get("project_name") or "",
            (session.get("folder_path") or "").strip("/"),
            session.get("task_name") or "",
        )
        if part
    ]
    workfile_path = session.get("workfile_path") or ""
    filename = os.path.basename(workfile_path) if workfile_path else ""

    lines = []
    if context_parts:
        lines.append(" / ".join(context_parts))
    if filename:
        lines.append(filename)
    return "\n".join(lines)


RECENT_WORKFILE_COUNT_DEFAULT = 5


def recent_workfile_count() -> int:
    """Return max recent workfile entries (default 5, env override)."""
    raw = os.environ.get("AYON_RECENT_FILES_COUNT", "").strip()
    if not raw:
        return RECENT_WORKFILE_COUNT_DEFAULT
    try:
        count = int(raw)
    except ValueError:
        log.warning(
            "Invalid AYON_RECENT_FILES_COUNT=%r; using default %d",
            raw,
            RECENT_WORKFILE_COUNT_DEFAULT,
        )
        return RECENT_WORKFILE_COUNT_DEFAULT
    return max(1, count)


def _recent_workfile_sessions_path() -> str:
    return os.path.join(_session_config_dir(), "recent_workfile_sessions.json")


def _normalize_workfile_path(workfile_path: str) -> str:
    return os.path.normcase(os.path.normpath(workfile_path))


def read_recent_workfile_sessions() -> List[Dict[str, Any]]:
    """Return recent workfile session dicts, most recent first."""
    path = _recent_workfile_sessions_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError, TypeError):
        return []

    if not isinstance(data, list):
        return []

    sessions = [entry for entry in data if isinstance(entry, dict)]
    return sessions[: recent_workfile_count()]


def touch_recent_workfile_session(session: Optional[Dict[str, Any]]) -> bool:
    """Prepend a session to recent workfiles, deduping by workfile path."""
    if not session:
        return False

    workfile_path = session.get("workfile_path") or ""
    if not workfile_path:
        return False

    normalized_path = _normalize_workfile_path(workfile_path)
    stored_session = dict(session)
    stored_session["workfile_path"] = workfile_path

    sessions = read_recent_workfile_sessions()
    sessions = [
        entry
        for entry in sessions
        if _normalize_workfile_path(entry.get("workfile_path") or "")
        != normalized_path
    ]
    sessions.insert(0, stored_session)
    sessions = sessions[: recent_workfile_count()]

    config_dir = _session_config_dir()
    path = _recent_workfile_sessions_path()
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(sessions, handle, indent=2)
        log.debug("Updated recent workfile sessions at %s", path)
        return True
    except OSError as exc:
        log.warning("Could not write recent workfile sessions to %s: %s", path, exc)
        return False


def format_recent_work_menu_label(session: Dict[str, Any]) -> str:
    """Build a short tray submenu label for a recent workfile session."""
    workfile_path = session.get("workfile_path") or ""
    filename = (
        os.path.basename(workfile_path) if workfile_path else "Unknown workfile"
    )
    project_name = session.get("project_name") or ""
    if project_name:
        return f"{project_name} / {filename}"
    return filename


def _projects_effectively_empty(config: Dict[str, Any]) -> bool:
    """True if projects is missing or every project entry is an empty dict."""
    projects = config.get("projects")
    if not projects:
        return True
    return all(not p for p in projects.values())


def _sandbox_path_for_legacy_migration() -> Optional[str]:
    """Sandbox root for legacy file lookup: env first, then stable JSON registry."""
    raw = os.environ.get("AYON_LOCAL_SANDBOX")
    if raw:
        return os.path.normpath(os.path.expanduser(raw))

    _, stable_file = _stable_localconfig_paths()
    if not os.path.isfile(stable_file):
        return None
    try:
        with open(stable_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, TypeError):
        return None

    env_block = data.get("environment_variables") or {}
    val = env_block.get("AYON_LOCAL_SANDBOX")
    if isinstance(val, dict) and "value" in val:
        val = val["value"]
    if not val:
        return None
    return os.path.normpath(os.path.expanduser(str(val)))


class LocalConfigStorage:
    """Handles loading and saving of local configuration data.

    ``localconfig.json`` always lives under the user profile (``~/.ayon/settings``),
    not under ``AYON_LOCAL_SANDBOX``, so settings stay available when the sandbox
    volume is offline (e.g. removable SD).
    """

    def __init__(self, project_name: str = None):
        if project_name:
            self.project_name = project_name
        else:
            self.project_name = resolve_tray_project_name()
            if not self.project_name:
                self.project_name = "default"
                log.debug(
                    "No active AYON project, using 'default' for Local Config storage"
                )

        # Initialize config directory (stable profile path)
        self._update_config_paths()
        self._ensure_config_dir()
    
    def _update_config_paths(self):
        """Set config directory and file paths to the stable profile location."""
        self.config_dir, self.config_file = _stable_localconfig_paths()

    def _maybe_migrate_legacy_sandbox_localconfig(self) -> None:
        """One-time style migration from old <sandbox>/settings/localconfig.json.

        Older versions stored ``localconfig.json`` under ``AYON_LOCAL_SANDBOX``.
        If the profile copy is missing or has no project data, copy or merge
        from the legacy sandbox file when that path exists and is readable.
        """
        sandbox_path = _sandbox_path_for_legacy_migration()
        if not sandbox_path:
            return
        legacy_file = os.path.join(sandbox_path, "settings", "localconfig.json")
        stable_dir, stable_file = _stable_localconfig_paths()

        try:
            if os.path.normcase(os.path.abspath(legacy_file)) == os.path.normcase(
                os.path.abspath(stable_file)
            ):
                return
        except OSError:
            return

        if not os.path.isfile(legacy_file):
            return

        os.makedirs(stable_dir, exist_ok=True)

        if os.path.isfile(stable_file) and os.path.getsize(stable_file) == 0:
            try:
                os.remove(stable_file)
            except OSError as exc:
                log.warning("Could not remove empty localconfig at %s: %s", stable_file, exc)

        if not os.path.isfile(stable_file):
            try:
                shutil.copy2(legacy_file, stable_file)
                log.info(
                    "Migrated localconfig.json from sandbox to profile (%s -> %s)",
                    legacy_file,
                    stable_file,
                )
            except OSError as exc:
                log.warning("Legacy localconfig copy failed: %s", exc)
            return

        try:
            with open(stable_file, "r", encoding="utf-8") as f:
                stable_cfg = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            log.debug("Skipping legacy merge; could not read stable config: %s", exc)
            return

        if not _projects_effectively_empty(stable_cfg):
            return

        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                legacy_cfg = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            log.debug("Skipping legacy merge; could not read legacy config: %s", exc)
            return

        if _projects_effectively_empty(legacy_cfg):
            return

        stable_cfg["projects"] = dict(legacy_cfg.get("projects") or {})

        leg_env = legacy_cfg.get("environment_variables") or {}
        stab_env = stable_cfg.get("environment_variables") or {}
        if not stab_env and leg_env:
            stable_cfg["environment_variables"] = dict(leg_env)
        elif stab_env and leg_env:
            merged_env = dict(stab_env)
            for key, val in leg_env.items():
                merged_env.setdefault(key, val)
            stable_cfg["environment_variables"] = merged_env

        if stable_cfg.get("last_selected_project") is None:
            lsp = legacy_cfg.get("last_selected_project")
            if lsp is not None:
                stable_cfg["last_selected_project"] = lsp

        try:
            with open(stable_file, "w", encoding="utf-8") as f:
                json.dump(stable_cfg, f, indent=2, ensure_ascii=False)
            log.info(
                "Merged project settings from legacy sandbox localconfig (%s)",
                legacy_file,
            )
        except OSError as exc:
            log.warning("Failed to write merged localconfig: %s", exc)

    def _ensure_config_dir(self):
        """Ensure the config directory exists"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
                log.debug(f"Created config directory: {self.config_dir}")
        except Exception as e:
            log.error(f"Failed to create config directory: {e}")
            # Try to create parent directories if they don't exist
            try:
                parent_dir = os.path.dirname(self.config_dir)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                    log.debug(f"Created parent directory: {parent_dir}")
                # Try to create config directory again
                os.makedirs(self.config_dir, exist_ok=True)
                log.debug(f"Created config directory after creating parent: {self.config_dir}")
            except Exception as e2:
                log.error(f"Failed to create config directory even after creating parent: {e2}")
                raise

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            self._update_config_paths()
            self._ensure_config_dir()
            self._maybe_migrate_legacy_sandbox_localconfig()

            if os.path.exists(self.config_file):
                # Check if file is empty or corrupted
                if os.path.getsize(self.config_file) == 0:
                    log.debug("Config file is empty, initializing with default structure")
                    return self._initialize_default_config()
                
                with open(self.config_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        log.debug("Config file is empty, initializing with default structure")
                        return self._initialize_default_config()
                    
                    config = json.loads(content)
                    log.debug(f"Loaded config from: {self.config_file}")
                    return config
            else:
                log.debug("Config file does not exist, initializing with default structure")
                return self._initialize_default_config()
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON config: {e}")
            log.debug("Initializing with default config structure")
            return self._initialize_default_config()
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return self._initialize_default_config()
    
    def _initialize_default_config(self) -> Dict[str, Any]:
        """Initialize with default config structure"""
        default_config = {
            "projects": {},
            "environment_variables": {},  # Global environment variables
            "last_selected_project": None  # Remember last selected project
            # Note: Project-specific environment variables are handled by AYON Tools Environment Variables
        }
        # Save the default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        try:
            self._update_config_paths()
            
            # Ensure directory exists before saving
            self._ensure_config_dir()
            
            log.debug(f"Saving config to: {self.config_file}")
            log.debug(f"Config data: {json.dumps(config, indent=2)}")
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log.debug(f"Successfully saved config to: {self.config_file}")
            return True
        except Exception as e:
            log.error(f"Failed to save config: {e}")
            return False

    def get_setting_value(
        self, group_id: str, setting_id: str, default_value: Any = None
    ) -> Any:
        """Get a specific setting value for the current project"""
        config = self.load_config()
        project_config = config.get("projects", {}).get(self.project_name, {})
        return project_config.get(group_id, {}).get(setting_id, default_value)

    def set_setting_value(self, group_id: str, setting_id: str, value: Any, setting_type: str = None) -> bool:
        """Set a specific setting value for the current project
        
        Args:
            group_id: The group identifier
            setting_id: The setting identifier
            value: The value to set
            setting_type: The widget type (boolean, spinbox, string, etc.)
        """
        log.debug(f"Setting value: project={self.project_name}, group={group_id}, setting={setting_id}, value={value}, type={setting_type}")
        
        # Normalize boolean values to lowercase strings for consistency
        # Only apply boolean normalization for boolean widget types
        if setting_type == "boolean":
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, str) and value.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                # Convert string boolean representations to lowercase
                if value.lower() in ("true", "1", "yes", "on"):
                    value = "true"
                else:
                    value = "false"
        elif isinstance(value, bool):
            # For non-boolean widgets that somehow got a bool value, convert to string
            value = str(value).lower()
        
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        if self.project_name not in config["projects"]:
            config["projects"][self.project_name] = {}
        if group_id not in config["projects"][self.project_name]:
            config["projects"][self.project_name][group_id] = {}
        config["projects"][self.project_name][group_id][setting_id] = value
        
        log.debug(f"Updated config structure: {json.dumps(config, indent=2)}")
        return self.save_config(config)

    def get_group_config(self, group_id: str) -> Dict[str, Any]:
        """Get all settings for a specific group in the current project"""
        config = self.load_config()
        project_config = config.get("projects", {}).get(self.project_name, {})
        return project_config.get(group_id, {})

    def set_group_config(self, group_id: str, group_config: Dict[str, Any]) -> bool:
        """Set all settings for a specific group in the current project"""
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        if self.project_name not in config["projects"]:
            config["projects"][self.project_name] = {}
        config["projects"][self.project_name][group_id] = group_config
        return self.save_config(config)

    def reset_group_to_defaults(
        self, group_id: str, default_values: Dict[str, Any]
    ) -> bool:
        """Reset a group to default values for the current project"""
        return self.set_group_config(group_id, default_values)

    def get_available_projects(self) -> List[str]:
        """Get projects the signed-in user may select in Local Config."""
        try:
            accessible_projects = get_user_accessible_project_names()
            if accessible_projects:
                log.debug(
                    "Found %d user-accessible projects: %s",
                    len(accessible_projects),
                    accessible_projects,
                )
                return accessible_projects

            log.warning(
                "No user-accessible projects resolved; project selector will be empty."
            )
            return []

        except Exception as e:
            log.warning(f"Failed to get user-accessible projects: {e}")
            return []

    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get all configuration for a specific project"""
        config = self.load_config()
        return config.get("projects", {}).get(project_name, {})

    def set_project_config(
        self, project_name: str, project_config: Dict[str, Any]
    ) -> bool:
        """Set all configuration for a specific project"""
        config = self.load_config()
        if "projects" not in config:
            config["projects"] = {}
        config["projects"][project_name] = project_config
        return self.save_config(config)

    def delete_project(self, project_name: str) -> bool:
        """Delete a project and all its settings"""
        config = self.load_config()
        if "projects" in config and project_name in config["projects"]:
            del config["projects"][project_name]
            return self.save_config(config)
        return True  # Project didn't exist, so it's already "deleted"

    def backup_config(self) -> str:
        """Create a backup of the current config and return backup path"""
        try:
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_file}.backup_{timestamp}"

            if os.path.exists(self.config_file):
                import shutil

                shutil.copy2(self.config_file, backup_path)
                log.debug(f"Created config backup: {backup_path}")
                return backup_path
            return ""
        except Exception as e:
            log.error(f"Failed to create config backup: {e}")
            return ""
    
    def get_last_selected_project(self) -> str:
        """Get the last selected project"""
        config = self.load_config()
        return config.get("last_selected_project")
    
    def set_last_selected_project(self, project_name: str) -> bool:
        """Set the last selected project"""
        config = self.load_config()
        config["last_selected_project"] = project_name
        return self.save_config(config)
    
    # Note: Project-specific environment variables are now handled by AYON Tools Environment Variables
    # This provides better integration with AYON's project loading system
