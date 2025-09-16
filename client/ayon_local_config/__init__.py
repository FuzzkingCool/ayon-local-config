# -*- coding: utf-8 -*-
import os

from .addon import LocalConfigAddon
from .version import __version__
from .logger import log

LOCALCONFIG_ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))

__all__ = (
    "__version__",
    "log", 
    "LOCALCONFIG_ADDON_ROOT",
    "LocalConfigAddon",
)
