"""Load project-scoped Local Config server schema from AYON."""

from __future__ import annotations

from typing import Any

from ayon_core.settings import get_project_settings

from ayon_local_config.logger import log


def load_server_settings(project_name: str) -> dict[str, Any]:
    """Return merged ``local_config`` addon settings for ``project_name``."""
    project_settings = get_project_settings(project_name)
    local_config_settings = project_settings.get("local_config", {}) or {}

    tab_groups = local_config_settings.get("tab_groups") or []
    show_project_selector = local_config_settings.get("show_project_selector", True)
    log.info(
        "Local Config server schema project=%r show_project_selector=%s "
        "tab_groups=%s",
        project_name,
        show_project_selector,
        len(tab_groups),
    )
    return local_config_settings


def schema_fingerprint(settings: dict[str, Any]) -> str:
    """Stable key for comparing server schema shapes."""
    import json

    payload = {
        "show_project_selector": settings.get("show_project_selector", True),
        "tab_groups": settings.get("tab_groups", []),
        "menu_item_name": settings.get("menu_item_name", "User Config"),
    }
    return json.dumps(payload, sort_keys=True, default=str)
