# -*- coding: utf-8 -*-
from ayon_server.addons import BaseServerAddon
from .version import __version__
from .settings import LocalConfigSettings, DEFAULT_VALUES


class LocalConfigServerAddon(BaseServerAddon):
    """Local Config server addon"""
    
    name = "local_config"
    version = __version__
    settings_model = LocalConfigSettings

    def initialize(self):
        """Initialize the server addon"""
        pass

    async def get_default_settings(self):
        """Get default settings for the addon"""
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)


__all__ = ["__version__", "LocalConfigSettings", "DEFAULT_VALUES", "LocalConfigServerAddon"]