# -*- coding: utf-8 -*-
"""Client-side path resolution for Local Config (Qt standard locations)."""

from __future__ import annotations

import os
from pathlib import Path

from qtpy.QtCore import QStandardPaths

DEFAULT_RENDER_SUBFOLDER = "Renders"
_LEGACY_PICTURES_PREFIXES = ("~/Pictures", "~\\Pictures")


def get_os_pictures_dir() -> Path:
    """Return the OS Pictures folder (OneDrive redirect, XDG, etc.)."""
    location = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
    if not location:
        raise RuntimeError("QStandardPaths.PicturesLocation returned empty")
    return Path(location)


def resolve_local_render_path(config_value: str | None) -> str:
    """Absolute render folder for ``AYON_LOCAL_RENDER_PATH`` registration."""
    raw = (config_value or "").strip()
    if not raw:
        return str(get_os_pictures_dir() / DEFAULT_RENDER_SUBFOLDER)

    normalized = raw.replace("\\", "/")
    lower = normalized.lower()
    for prefix in _LEGACY_PICTURES_PREFIXES:
        prefix_norm = prefix.replace("\\", "/")
        prefix_lower = prefix_norm.lower()
        if lower == prefix_lower or lower.startswith(prefix_lower + "/"):
            suffix = normalized[len(prefix_norm) :].lstrip("/\\")
            base = get_os_pictures_dir()
            return str(base / suffix) if suffix else str(base)

    return os.path.normpath(os.path.expanduser(raw))
