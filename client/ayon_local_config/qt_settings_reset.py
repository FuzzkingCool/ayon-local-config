# discipline: new-module canonical QSettings scopes for AYON pipeline UI reset
"""Clear known AYON / MDHR pipeline QSettings stores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qtpy import QtCore

from ayon_local_config.logger import log

_Format = Literal["native", "ini"]

# Sources:
# - ayon_core/tools/utils/window_state.py
# - ayon_core/tools/utils/color_widgets/simple_color_picker.py
# - ayon_core/vendor/python/qargparse.py (+ external qargparse package)
# - ayon_harmony/studio_tools/scale_crop_tool/constants.py
_AYON_PIPELINE_QT_SETTINGS_SCOPE_SPECS = (
    ("AYON", "ayon_core", "native"),
    ("ayon-core", "color_picker", "ini"),
    ("ayon_core.vendor.python.qargparse", "QArgparse", "ini"),
    ("qargparse", "QArgparse", "ini"),
    ("MDHR", "ScaleCrop", "native"),
)

HOST_APP_QT_SETTINGS_PREFIXES = ("quick_render/",)


@dataclass(frozen=True)
class QtSettingsScope:
    """One QSettings organization/application identity."""

    organization: str
    application: str
    storage_format: _Format = "native"

    def create_settings(self) -> QtCore.QSettings:
        if self.storage_format == "ini":
            return QtCore.QSettings(
                QtCore.QSettings.IniFormat,
                QtCore.QSettings.UserScope,
                self.organization,
                self.application,
            )
        return QtCore.QSettings(self.organization, self.application)


def clear_qt_settings_scope(scope: QtSettingsScope) -> str:
    """Clear one QSettings scope and return its storage path."""
    settings = scope.create_settings()
    path = settings.fileName()
    settings.clear()
    settings.sync()
    return path


def clear_host_app_qt_setting_prefixes(prefixes: tuple[str, ...]) -> str | None:
    """Remove host-app QSettings keys matching the given prefixes."""
    settings = QtCore.QSettings()
    if not settings.organizationName() and not settings.applicationName():
        log.debug("Skipping host-app QSettings: no org/app on QApplication")
        return None

    path = settings.fileName()
    for key in settings.allKeys():
        if any(key.startswith(prefix) for prefix in prefixes):
            settings.remove(key)
    settings.sync()
    return path


def clear_all_ayon_pipeline_qt_settings() -> list[str]:
    """Clear all known pipeline QSettings stores."""
    cleared: list[str] = []

    for organization, application, storage_format in _AYON_PIPELINE_QT_SETTINGS_SCOPE_SPECS:
        scope = QtSettingsScope(organization, application, storage_format)
        try:
            path = clear_qt_settings_scope(scope)
            cleared.append(path)
            log.debug(
                "Cleared QSettings %s/%s @ %s",
                scope.organization,
                scope.application,
                path,
            )
        except Exception as exc:
            log.warning(
                "Failed to clear QSettings %s/%s: %s",
                scope.organization,
                scope.application,
                exc,
            )

    try:
        host_path = clear_host_app_qt_setting_prefixes(HOST_APP_QT_SETTINGS_PREFIXES)
        if host_path:
            cleared.append(host_path)
            log.debug("Cleared host-app QSettings prefixes @ %s", host_path)
    except Exception as exc:
        log.warning("Failed to clear host-app QSettings prefixes: %s", exc)

    return cleared
