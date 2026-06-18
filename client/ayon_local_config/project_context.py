"""Resolve the active AYON project for tray-local-config surfaces."""

from __future__ import annotations

import os
from typing import List, Optional, Set

from ayon_core.pipeline import get_current_project_name
from ayon_core.tools.tray.bundle_filter import read_persisted_tray_filter_project

from ayon_local_config.logger import log

DEFAULT_PROJECT_NAME = "default"


def _user_is_project_privileged(user_data: dict) -> bool:
    return bool(
        user_data.get("isManager")
        or user_data.get("isAdmin")
        or user_data.get("isService")
    )


def _query_active_standard_project_names() -> Set[str]:
    """Return active, non-library project names from the AYON server."""
    try:
        import ayon_api
    except ImportError:
        log.debug("AYON API not available for project discovery.")
        return set()

    try:
        api = ayon_api.get_server_api_connection()
        if not api or not api.is_server_available:
            log.debug("AYON server not available for project discovery.")
            return set()
    except Exception:
        log.debug("Failed to connect to AYON server for project discovery.", exc_info=True)
        return set()

    try:
        return {
            project["name"]
            for project in ayon_api.get_projects(
                active=True,
                fields=["name", "active", "library"],
            )
            if project.get("active", True) and not project.get("library", False)
        }
    except Exception:
        log.debug("Failed to query active projects from AYON server.", exc_info=True)
        return set()


def get_user_accessible_project_names() -> List[str]:
    """Return project names the signed-in user may select in Local Config.

    Managers/admins/services receive all active standard projects. Other users
    receive only projects with a non-empty ``accessGroups`` assignment,
    intersected with active standard projects when the server is reachable.
    """
    try:
        import ayon_api
    except ImportError:
        log.debug("AYON API not available; no accessible projects resolved.")
        return []

    try:
        user = ayon_api.get_user()
    except Exception:
        log.debug("Failed to load AYON user for project filtering.", exc_info=True)
        return []

    user_data = user.get("data") or {}
    active_names = _query_active_standard_project_names()

    if _user_is_project_privileged(user_data):
        projects = sorted(active_names)
        log.info(
            "Local Config project selector: %d accessible projects (privileged user).",
            len(projects),
        )
        return projects

    access_groups = user_data.get("accessGroups") or {}
    if not isinstance(access_groups, dict):
        return []

    if active_names:
        active_by_lower = {name.lower(): name for name in active_names}
        projects = []
        for project_name, groups in access_groups.items():
            if not project_name or not groups:
                continue
            canonical = active_by_lower.get(str(project_name).lower())
            if canonical:
                projects.append(canonical)
    else:
        projects = [
            str(project_name)
            for project_name, groups in access_groups.items()
            if project_name and groups
        ]

    projects = sorted(set(projects))
    log.info(
        "Local Config project selector: %d accessible projects for user.",
        len(projects),
    )
    return projects


def pick_accessible_project_name(
    project_name: str,
    accessible_projects: List[str],
) -> Optional[str]:
    """Return canonical accessible name matching ``project_name``, if any."""
    if not project_name or not accessible_projects:
        return None
    if project_name in accessible_projects:
        return project_name

    by_lower = {name.lower(): name for name in accessible_projects}
    return by_lower.get(project_name.lower())


def read_last_selected_project_name() -> Optional[str]:
    """Return last project selected in the Local Config UI, if any."""
    from ayon_local_config.storage import LocalConfigStorage

    try:
        storage = LocalConfigStorage(project_name=DEFAULT_PROJECT_NAME)
        return storage.get_last_selected_project()
    except Exception:
        log.debug(
            "Failed to read last selected Local Config project.",
            exc_info=True,
        )
        return None


def resolve_tray_project_name() -> str:
    """Pick the project whose server schema and local values should load.

    Priority:
        1. ``AYON_PROJECT_NAME`` env
        2. Persisted tray filter project (launcher / bundle relaunch)
        3. Current pipeline context project
        4. Last Local Config UI selection
        5. ``default`` fallback
    """
    project_name = os.getenv("AYON_PROJECT_NAME")
    if project_name:
        return project_name

    project_name = read_persisted_tray_filter_project()
    if project_name:
        return project_name

    try:
        project_name = get_current_project_name()
        if project_name:
            return project_name
    except Exception:
        log.debug(
            "Failed to resolve project from pipeline context.",
            exc_info=True,
        )

    project_name = read_last_selected_project_name()
    if project_name:
        return project_name

    log.debug(
        "No tray project resolved; using %r for Local Config.",
        DEFAULT_PROJECT_NAME,
    )
    return DEFAULT_PROJECT_NAME
