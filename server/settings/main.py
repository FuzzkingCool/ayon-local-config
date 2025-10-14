# -*- coding: utf-8 -*-
from typing import List
from ayon_server.settings import BaseSettingsModel, SettingsField
from pydantic import validator


def _get_available_action_choices():
    """Get available action choices dynamically from AYON action discovery"""
    try:
        # Import the client-side function to get action names
        # This will be resolved at runtime when the settings are loaded
        from ayon_local_config.plugin import get_available_action_names
        
        action_names = get_available_action_names()
        return [{"value": name, "label": name} for name in action_names]
    except Exception:
        # Fallback to empty list if dynamic discovery fails
        return []


class ActionChoiceModel(BaseSettingsModel):
    """Model for action button choices"""
    label: str = SettingsField(title="Action Label")
    action_id: str = SettingsField(title="Action ID")


class LocalConfigSettingModel(BaseSettingsModel):
    """Model for individual local config settings
    
    This model defines the structure for individual settings within a configuration group.
    Each setting can be one of several types, each with specific use cases and behaviors.
    
    Setting Types and Use Cases:
    
    1. STRING (Text Field):
       - Use for: Text input, file paths, directory paths, configuration values
       - Features: Optional path browser, placeholder text, validation
       - Examples: Project names, file paths, API keys, custom text values
       - Path Mode: Enable for file/folder selection with browse button
       
    2. BOOLEAN (Checkbox):
       - Use for: Toggle switches, enable/disable options, feature flags
       - Features: Modern switch styling, immediate feedback
       - Examples: Auto-save, debug mode, notifications, feature toggles
       - Values: "true"/"false", "1"/"0", "yes"/"no" (case insensitive)
       
    3. ENUM (Dropdown):
       - Use for: Predefined choices, categories, modes, quality settings
       - Features: Single selection from predefined options
       - Examples: Quality presets, themes, modes, categories
       - Options: One per line in enum_options field
       
    4. BUTTON (Action Button):
       - Use for: Executing actions, triggering workflows, opening dialogs
       - Features: Custom actions with data parameters, immediate execution
       - Examples: Clean logs, open folders, set environment variables
       - Actions: Defined in action_name field, data in action_data field
       
    5. SPINBOX (Numeric Input):
       - Use for: Numeric values with specific ranges, counts, sizes
       - Features: Min/max range configuration, auto-width calculation
       - Examples: Thread counts, cache sizes, timeouts, numeric limits
       - Range: Configure with "min-max" format (e.g., "1-100", "400-1000")
       
    6. DIVIDER (Visual Separator):
       - Use for: Organizing sections, creating visual breaks, column layouts
       - Features: Horizontal/vertical orientation, optional labels
       - Examples: Section headers, column separators, visual organization
       - Orientation: "horizontal" for section breaks, "vertical" for columns
    """
    _layout = "expanded"
    
    type: str = SettingsField(
        title="Setting Type",
        description="Choose the widget type for this setting. Each type has specific use cases and behaviors.",
        enum_resolver=lambda: [
            {"value": "string", "label": "Text Field - For text input, paths, and custom values"}, 
            {"value": "boolean", "label": "Checkbox - For toggle switches and enable/disable options"}, 
            {"value": "enum", "label": "Dropdown - For predefined choices and categories"}, 
            {"value": "button", "label": "Action Button - For executing actions and workflows"},
            {"value": "spinbox", "label": "Spin Box - For numeric values with specific ranges"},
            {"value": "divider", "label": "Divider - For visual organization and section breaks"}
        ]
    )
    label: str = SettingsField(
        title="Label",
        description="Display name for this setting. For dividers, this becomes the section header text."
    )
    tooltip: str = SettingsField(
        "", 
        title="Tooltip",
        description="Help text shown when hovering over the setting. Use this to explain what the setting does and how to use it."
    )
    
    # Default value field (works for all types)
    default_value: str = SettingsField(
        "", 
        title="Default Value",
        description="Initial value for this setting. For booleans, use 'true'/'false'. For spinboxes, use numeric values. For strings, use any text."
    )
    
    # String-specific fields
    is_path: bool = SettingsField(
        False, 
        title="Is Path",
        description="Enable this to add a 'Browse...' button for file/folder selection. Only applies to string type settings.",
        conditional_visibility={"type": "string"}
    )
    path_type: str = SettingsField(
        "folder", 
        title="Path Type",
        description="Choose whether to browse for files or folders when the Browse button is clicked.",
        enum_resolver=lambda: [
            {"value": "file", "label": "File - Opens file selection dialog"},
            {"value": "folder", "label": "Folder - Opens folder selection dialog"}
        ],
        conditional_visibility={"type": "string", "is_path": True}
    )
    
    # Enum-specific fields
    enum_options: List[str] = SettingsField(
        default_factory=list, 
        title="Enum Options (one per line)",
        description="List of options for dropdown selection. Enter one option per line. These will appear in the dropdown menu.",
        conditional_visibility={"type": "enum"}
    )
    
    # Action field for all UI elements (buttons trigger on click, others on value change)
    action_name: str = SettingsField(
        "", 
        title="Action Class Name",
        description="Name of the action class to execute. For buttons, executes on click. For other types, executes when value changes. Leave empty for no action.",
        conditional_visibility={"type": {"not": "divider"}}
    )
    
    # Action data field for button action parameters
    action_data: str = SettingsField(
        "", 
        title="Action Data",
        description="Data/parameters to pass to the action. Can be JSON string, plain text, or file paths. Used by button actions to provide context or parameters.",
        conditional_visibility={"type": "button"}
    )
    
    # Spinbox-specific fields
    spinbox_range: str = SettingsField(
        "", 
        title="Spinbox Min/Max Range",
        description="Enter range as 'min-max' (e.g., '0-100', '400-1000'). The spinbox width will automatically adjust based on the maximum value. Leave empty for default range (0-9999).",
        conditional_visibility={"type": "spinbox"}
    )
    
    
    # Divider-specific fields
    divider_orientation: str = SettingsField(
        "horizontal", 
        title="Divider Orientation",
        description="Choose divider orientation. Horizontal creates section breaks with labels. Vertical creates column separators for multi-column layouts.",
        enum_resolver=lambda: [
            {"value": "horizontal", "label": "Horizontal - Creates section breaks with optional labels"},
            {"value": "vertical", "label": "Vertical - Creates column separators for multi-column layouts"}
        ],
        conditional_visibility={"type": "divider"}
    )
    
    @validator("enum_options", pre=True)
    def validate_enum_options(cls, v):
        if isinstance(v, str):
            return [opt.strip() for opt in v.split('\n') if opt.strip()]
        return v or []


class LocalConfigGroupModel(BaseSettingsModel):
    """Model for individual local config tab groups
    
    Each group represents a tab in the Local Config window. Groups organize related settings
    into logical sections for better user experience and organization.
    
    Use Cases:
    - Organize settings by functionality (e.g., "Performance", "UI", "Paths")
    - Group related settings together (e.g., all path settings in one tab)
    - Create workflow-specific configurations (e.g., "Rendering", "Animation")
    - Separate user preferences from system settings
    
    Best Practices:
    - Use descriptive names that clearly indicate the group's purpose
    - Keep related settings together in the same group
    - Use dividers within groups to create subsections
    - Provide helpful descriptions to guide users
    """
    _isGroup: bool = True
    
    enabled: bool = SettingsField(
        default=True, 
        title="Enabled",
        description="Enable or disable this configuration group. Disabled groups won't appear in the Local Config window."
    )
    name: str = SettingsField(
        default="", 
        title="Name",
        description="Display name for this configuration group. This appears as the tab title in the Local Config window."
    )
    description: str = SettingsField(
        default="",
        title="Description", 
        description="Optional description text shown at the top of this group's tab. Use this to explain what settings are in this group and how to use them.",
        widget="textarea"
    )
    settings: List[LocalConfigSettingModel] = SettingsField(
        default_factory=list,
        title="Settings",
        description="List of individual settings within this group. Each setting can be a different type (string, boolean, enum, button, spinbox, or divider)."
    )


class LocalConfigSettings(BaseSettingsModel):
    """Local Config addon settings
    
    This is the main settings model for the Local Config addon. It controls the overall
    behavior and appearance of the Local Config window and its configuration groups.
    
    The Local Config addon provides a flexible, user-friendly interface for managing
    project-specific and user-specific settings. It supports multiple widget types,
    custom actions, and organized tab-based layouts.
    
    Key Features:
    - Multiple widget types: strings, booleans, enums, buttons, spinboxes, dividers
    - Project-specific settings with automatic switching
    - Custom actions that can be triggered by settings or buttons
    - Flexible tab-based organization
    - Modern UI with AYON styling
    - Persistent storage with automatic saving
    """
    
    enabled: bool = SettingsField(
        default=True,
        title="Enabled",
        description="Enable or disable the Local Config addon. When disabled, the tray menu item won't appear and the configuration window won't be accessible."
    )
    
    menu_item_name: str = SettingsField(
        default="User Config",
        title="Tray Menu Item Name",
        description="Name of the tray menu item that opens the Local Config window. This appears in the AYON tray menu when the addon is enabled."
    )
    
    show_project_selector: bool = SettingsField(
        default=True,
        title="Show Project Selector",
        description="Show a dropdown at the top of the Local Config window to select which project's settings to manage. When disabled, settings are managed for the current project only."
    )
    
    tab_groups: List[LocalConfigGroupModel] = SettingsField(
        default_factory=list,
        title="Tab Groups",
        description="Configuration groups that appear as tabs in the Local Config window. Each group can contain multiple settings of different types, organized for specific use cases or workflows."
    )


DEFAULT_VALUES = {
    "enabled": True,
    "menu_item_name": "User Config",
    "show_project_selector": True,
    "tab_groups": [
        {
            "enabled": True,
            "name": "AYON Local Sandbox",
            "description": "Configure the AYON local sandbox directory where logs, workfiles, and settings are stored.",
            "settings": [
                {
                    "type": "string",
                    "label": "AYON Local Sandbox Path",
                    "tooltip": "Path to the AYON local sandbox directory (defaults to ~/.ayon if AYON_LOCAL_SANDBOX is not set)",
                    "default_value": "~/.ayon",
                    "is_path": True,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "SetAyonSandboxPathAction"
                }
            ]
        },
        {
            "enabled": True,
            "name": "Data Type Examples",
            "description": "Examples demonstrating all available widget types and their capabilities.",
            "settings": [
                {
                    "type": "divider",
                    "label": "Text Input Fields",
                    "tooltip": "String widgets with different path configurations",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "string",
                    "label": "Project Name",
                    "tooltip": "STRING TYPE: Use for text input, names, or custom values. Set 'is_path' to true for file/folder browsing. Use 'action_name' to trigger actions on value change.",
                    "default_value": "My Project",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "string",
                    "label": "Project Directory",
                    "tooltip": "STRING WITH PATH: Enable 'is_path' for browse button. Set 'path_type' to 'folder' or 'file'. Browse button opens file/folder dialog.",
                    "default_value": "C:/Projects/MyProject",
                    "is_path": True,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "string",
                    "label": "Config File",
                    "tooltip": "STRING WITH FILE PATH: Set 'path_type' to 'file' for file selection dialog. Use for selecting specific files like configs, scripts, or documents.",
                    "default_value": "C:/Projects/MyProject/config.json",
                    "is_path": True,
                    "path_type": "file",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "divider",
                    "label": "Toggle Switches",
                    "tooltip": "Boolean widgets with modern switch styling",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "boolean",
                    "label": "Auto Save",
                    "tooltip": "BOOLEAN TYPE: Use for on/off switches. Set 'default_value' to 'true'/'false'. Triggers 'action_name' on toggle. Modern switch styling with immediate feedback.",
                    "default_value": "true",
                    "is_path": True,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "boolean",
                    "label": "Enable Debug",
                    "tooltip": "BOOLEAN EXAMPLE: Shows how boolean values work. Case insensitive: 'true'/'false', '1'/'0', 'yes'/'no' all work. Use for feature toggles and options.",
                    "default_value": "False",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "divider",
                    "label": "Dropdown Selections",
                    "tooltip": "Enum widgets with predefined options",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "enum",
                    "label": "Render Quality",
                    "tooltip": "ENUM TYPE: Use for predefined choices. Add options in 'enum_options' field (one per line). Set 'default_value' to one of the options. Triggers 'action_name' on selection change.",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": ["Low", "Medium", "High", "Ultra"],
                    "default_value": "Medium",
                    "action_name": ""
                },
                
                {
                    "type": "divider",
                    "label": "Numeric Input",
                    "tooltip": "Spin box widgets for numeric values",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "spinbox",
                    "label": "Max Threads",
                    "tooltip": "SPINBOX TYPE: Use for numeric values with ranges. Set 'spinbox_range' as 'min-max' (e.g., '1-32'). Width auto-adjusts to max value. Triggers 'action_name' on value change.",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "default_value": "8",
                    "action_name": "",
                    "spinbox_range": "1-32"
                },
                {
                    "type": "spinbox",
                    "label": "Cache Size (MB)",
                    "tooltip": "SPINBOX WITH RANGE: Shows range configuration '100-10000'. Widget width automatically adjusts based on maximum value digits. Use for counts, sizes, limits.",
                    "default_value": "1024",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "spinbox_range": "100-10000"
                },
                {
                    "type": "divider",
                    "label": "Action Buttons",
                    "tooltip": "Buttons that execute real actions",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "button",
                    "label": "Clean Logs",
                    "tooltip": "BUTTON TYPE: Use for executing actions. Set 'action_name' to action class name. Use 'action_data' for parameters. Executes immediately on click.",
                    "default_value": "",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "CleanLogsAction",
                    "action_data": ""
                },
               
                {
                    "type": "button",
                    "label": "Set AYON Sandbox",
                    "tooltip": "BUTTON WITH ACTION: Shows how buttons trigger actions. 'action_name' executes the action class. Use for workflows, dialogs, and system operations.",
                    "default_value": "",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "SetAyonSandboxPathAction",
                    "action_data": ""
                },
              
                {
                    "type": "divider",
                    "label": "Vertical Divider",
                    "tooltip": "DIVIDER TYPE: Use for visual organization. Set 'divider_orientation' to 'vertical' for column separators or 'horizontal' for section breaks. Labels become section headers.",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "vertical"
                },
                {
                    "type": "divider",
                    "label": "Second Column - String Fields",
                    "tooltip": "String widgets in the second column",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "string",
                    "label": "Output Directory",
                    "tooltip": "STRING IN SECOND COLUMN: Demonstrates multi-column layout. Path browsing works the same way. Use dividers to create column layouts.",
                    "default_value": "C:/Output/Renders",
                    "is_path": True,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "divider",
                    "label": "Second Column - Boolean Fields",
                    "tooltip": "Boolean widgets in the second column",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "boolean",
                    "label": "Enable Notifications",
                    "tooltip": "BOOLEAN IN SECOND COLUMN: Shows how switches work in multi-column layouts. All boolean features work the same way regardless of column position.",
                    "default_value": "true",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": ""
                },
                {
                    "type": "divider",
                    "label": "Second Column - Enum Fields",
                    "tooltip": "Enum widgets in the second column",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "enum",
                    "label": "Theme",
                    "tooltip": "ENUM IN SECOND COLUMN: Dropdowns work identically in any column. Options are defined in 'enum_options' field. Default value must match one of the options.",
                    "default_value": "Dark",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": ["Dark", "Light", "Auto"],
                    "action_name": ""
                },
                {
                    "type": "divider",
                    "label": "Second Column - Spinbox Fields",
                    "tooltip": "Spinbox widgets in the second column",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "spinbox",
                    "label": "Refresh Rate (Hz)",
                    "tooltip": "SPINBOX IN SECOND COLUMN: Shows range '30-240' with auto-width calculation. Width adjusts based on max value digits. Works identically in any column position.",
                    "default_value": "60",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "spinbox_range": "30-240"
                },
                {
                    "type": "divider",
                    "label": "Second Column - Buttons with data",
                    "tooltip": "Button widgets in the second column",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "",
                    "divider_orientation": "horizontal"
                },
                {
                    "type": "button",
                    "label": "Open Folder",
                    "tooltip": "BUTTON WITH DATA: Shows 'action_data' usage. Pass parameters to actions via 'action_data' field. Can be JSON, text, or file paths.",
                    "default_value": "",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "OpenFolderAction",
                    "action_data": "AYON_LOCAL_SANDBOX"
                },

                {
                    "type": "button",
                    "label": "Set Unity Project",
                    "tooltip": "BUTTON WITH PATH DATA: Demonstrates passing file paths as 'action_data'. Actions can use this data for file operations, environment variables, or system commands.",
                    "default_value": "",
                    "is_path": False,
                    "path_type": "folder",
                    "enum_options": [],
                    "action_name": "SetUnityProjectAction",
                    "action_data": "C:/Projects/MyProject"
                }
            ]
        }
    ]
}