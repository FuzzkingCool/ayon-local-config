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
            {"value": "button", "label": "Action Button"},
            {"value": "spinbox", "label": "Spin Box"},
            {"value": "divider", "label": "Divider"}
        ]
    )
    label: str = SettingsField(title="Label")
    tooltip: str = SettingsField("", title="Tooltip")
    
    # String-specific fields
    default_string: str = SettingsField(
        "", 
        title="Default Value",
        conditional_visibility={"type": "string"}
    )
    is_path: bool = SettingsField(
        False, 
        title="Is Path",
        conditional_visibility={"type": "string"}
    )
    path_type: str = SettingsField(
        "folder", 
        title="Path Type",
        enum_resolver=lambda: [
            {"value": "file", "label": "File"},
            {"value": "folder", "label": "Folder"}
        ],
        conditional_visibility={"type": "string", "is_path": True}
    )
    
    # Boolean-specific fields  
    default_boolean: bool = SettingsField(
        False, 
        title="Default Value",
        conditional_visibility={"type": "boolean"}
    )
    
    # Enum-specific fields
    enum_options: List[str] = SettingsField(
        default_factory=list, 
        title="Enum Options (one per line)",
        conditional_visibility={"type": "enum"}
    )
    default_enum: str = SettingsField(
        "", 
        title="Default Selection",
        conditional_visibility={"type": "enum"}
    )
    
    # Button-specific fields
    button_action: str = SettingsField(
        "", 
        title="Action Name (e.g. CleanLogsAction)",
        conditional_visibility={"type": "button"}
    )
    
    # SpinBox-specific fields
    default_spin_box: int = SettingsField(
        0, 
        title="Default Value",
        conditional_visibility={"type": "spinbox"}
    )
    
    # Divider-specific fields
    divider_orientation: str = SettingsField(
        "horizontal", 
        title="Orientation",
        enum_resolver=lambda: [
            {"value": "horizontal", "label": "Horizontal"},
            {"value": "vertical", "label": "Vertical"}
        ],
        conditional_visibility={"type": "divider"}
    )
    
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
            "title": "Data Type Examples",
            "description": "Comprehensive examples of all available data types in the Local Config addon.",
            "settings": [
                {
                    "type": "divider",
                    "label": "String Fields",
                    "tooltip": "Examples of text input fields",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "string",
                    "label": "Project Name",
                    "tooltip": "Enter the name of your project",
                    "default_string": "My Awesome Project",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "string",
                    "label": "Project Path",
                    "tooltip": "Path to your project directory",
                    "default_string": "C:/Projects/MyProject",
                    "is_path": True,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "string",
                    "label": "Config File",
                    "tooltip": "Path to configuration file",
                    "default_string": "C:/Projects/MyProject/config.json",
                    "is_path": True,
                    "path_type": "file",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "divider",
                    "label": "Boolean Fields",
                    "tooltip": "Examples of checkbox fields",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "boolean",
                    "label": "Auto Save",
                    "tooltip": "Automatically save changes",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": True,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "boolean",
                    "label": "Enable Debug",
                    "tooltip": "Enable debug logging",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "boolean",
                    "label": "Use GPU Acceleration",
                    "tooltip": "Enable GPU acceleration for rendering",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": True,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "divider",
                    "label": "Enum Fields",
                    "tooltip": "Examples of dropdown selection fields",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "enum",
                    "label": "Render Quality",
                    "tooltip": "Select the rendering quality preset",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": ["Low", "Medium", "High", "Ultra"],
                    "default_enum": "Medium",
                    "button_action": ""
                },
                {
                    "type": "enum",
                    "label": "Color Space",
                    "tooltip": "Choose the color space for your project",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": ["sRGB", "Rec. 709", "DCI-P3", "Rec. 2020", "ACES"],
                    "default_enum": "sRGB",
                    "button_action": ""
                },
                {
                    "type": "enum",
                    "label": "File Format",
                    "tooltip": "Select the output file format",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": ["PNG", "JPEG", "EXR", "TIFF", "HDR"],
                    "default_enum": "PNG",
                    "button_action": ""
                },
                {
                    "type": "divider",
                    "label": "Spin Box Fields",
                    "tooltip": "Examples of numeric input fields",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "spinbox",
                    "label": "Max Threads",
                    "tooltip": "Maximum number of threads to use",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "default_spin_box": 8
                },
                {
                    "type": "spinbox",
                    "label": "Cache Size (MB)",
                    "tooltip": "Size of the cache in megabytes",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "default_spin_box": 1024
                },
                {
                    "type": "spinbox",
                    "label": "Timeout (seconds)",
                    "tooltip": "Operation timeout in seconds",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "default_spin_box": 30
                },
                {
                    "type": "divider",
                    "label": "Action Buttons",
                    "tooltip": "Examples of action button fields",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "button",
                    "label": "Clean Logs",
                    "tooltip": "Clean all AYON log files",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "CleanLogsAction"
                },
                {
                    "type": "button",
                    "label": "Reset Settings",
                    "tooltip": "Reset all settings to default values",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "ResetSettingsAction"
                },
                {
                    "type": "button",
                    "label": "Export Config",
                    "tooltip": "Export current configuration to file",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "ExportConfigAction"
                },
                {
                    "type": "divider",
                    "label": "Layout Examples",
                    "tooltip": "Examples of different divider orientations",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "divider",
                    "label": "Vertical Divider",
                    "tooltip": "This is a vertical divider example",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "vertical"
                },
                {
                    "type": "divider",
                    "label": "Second Column Settings",
                    "tooltip": "Settings that appear in the second column",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "string",
                    "label": "Output Directory",
                    "tooltip": "Directory for output files",
                    "default_string": "C:/Output/Renders",
                    "is_path": True,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "boolean",
                    "label": "Enable Notifications",
                    "tooltip": "Show desktop notifications",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": True,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": ""
                },
                {
                    "type": "enum",
                    "label": "Theme",
                    "tooltip": "Select the application theme",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": ["Dark", "Light", "Auto"],
                    "default_enum": "Dark",
                    "button_action": ""
                },
                {
                    "type": "spinbox",
                    "label": "Refresh Rate (Hz)",
                    "tooltip": "Display refresh rate",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "",
                    "default_spin_box": 60
                },
                {
                    "type": "button",
                    "label": "Test Connection",
                    "tooltip": "Test network connection",
                    "default_string": "",
                    "is_path": False,
                    "path_type": "folder",
                    "default_boolean": False,
                    "enum_options": [],
                    "default_enum": "",
                    "button_action": "TestConnectionAction"
                }
            ]
        }
    ]
}