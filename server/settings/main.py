# -*- coding: utf-8 -*-
from typing import Type, List
from ayon_server.settings import BaseSettingsModel, SettingsField
from pydantic import validator


class ActionChoiceModel(BaseSettingsModel):
    """Model for action button choices"""
    label: str = SettingsField(title="Action Label")
    action_id: str = SettingsField(title="Action ID")


class LocalConfigSettingModel(BaseSettingsModel):
    """Model for individual local config settings"""
    _layout = "expanded"
    
    type: str = SettingsField(
        title="Setting Type",
        enum_resolver=lambda: [
            {"value": "string", "label": "Text Field"}, 
            {"value": "boolean", "label": "Checkbox"}, 
            {"value": "enum", "label": "Dropdown"}, 
            {"value": "button", "label": "Action Button"}
        ]
    )
    label: str = SettingsField(title="Label")
    tooltip: str = SettingsField("", title="Tooltip")
    
    # String-specific fields
    default_string: str = SettingsField("", title="Default Value")
    is_path: bool = SettingsField(False, title="Is File/Folder Path")
    
    # Boolean-specific fields  
    default_boolean: bool = SettingsField(False, title="Default Value")
    
    # Enum-specific fields
    enum_options: List[str] = SettingsField(default_factory=list, title="Enum Options (one per line)")
    default_enum: str = SettingsField("", title="Default Selection")
    
    # Button-specific fields
    button_action: str = SettingsField("", title="Action Name (e.g. CleanLogsAction)")
    
    @validator("enum_options", pre=True)
    def validate_enum_options(cls, v):
        if isinstance(v, str):
            return [opt.strip() for opt in v.split('\n') if opt.strip()]
        return v or []


class LocalConfigGroupModel(BaseSettingsModel):
    """Model for local config groups"""
    _layout = "expanded"
    
    enabled: bool = SettingsField(True, title="Enabled")
    title: str = SettingsField(title="Group Title")
    description: str = SettingsField(
        "",
        title="Description", 
        widget="textarea"
    )
    settings: List[LocalConfigSettingModel] = SettingsField(
        default_factory=list,
        title="Settings"
    )


class LocalConfigSettings(BaseSettingsModel):
    """Local Config addon settings"""
    _layout = "expanded"
    
    groups: List[LocalConfigGroupModel] = SettingsField(
        default_factory=list,
        title="Configuration Groups"
    )


DEFAULT_VALUES = {
    "groups": [
        {
            "enabled": True,
            "title": "Example Configuration",
            "description": "This is an example configuration group. You can add your own groups and settings here.",
            "settings": [
                {
                    "type": "string",
                    "label": "Project Path",
                    "tooltip": "Path to your project directory",
                    "default_string": "",
                    "is_path": True,
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "boolean", 
                    "label": "Auto Save",
                    "tooltip": "Automatically save changes",
                    "default_string": "",
                    "is_path": False,
                    "default_boolean": True,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "button",
                    "label": "Clean Logs",
                    "tooltip": "Clean all AYON log files",
                    "default_string": "",
                    "is_path": False,
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "CleanLogsAction"
                }
            ]
        }
    ]
}