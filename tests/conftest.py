"""Test harness for ayon-local-config without loading the tray addon."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

CLIENT_ROOT = Path(__file__).resolve().parents[1] / "client"
PACKAGE_ROOT = CLIENT_ROOT / "ayon_local_config"

if str(CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(CLIENT_ROOT))

if "ayon_local_config" not in sys.modules:
    package = types.ModuleType("ayon_local_config")
    package.__path__ = [str(PACKAGE_ROOT)]
    sys.modules["ayon_local_config"] = package

importlib.import_module("ayon_local_config.logger")

project_context_stub = types.ModuleType("ayon_local_config.project_context")
project_context_stub.resolve_tray_project_name = lambda: "default"
project_context_stub.get_user_accessible_project_names = lambda: []
sys.modules["ayon_local_config.project_context"] = project_context_stub

importlib.import_module("ayon_local_config.storage")
