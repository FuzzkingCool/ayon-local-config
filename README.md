# AYON Local Config Addon

A simple AYON addon that allows users to manage local configuration settings through an intuitive interface.

## Features

- **Server-defined settings**: Configure setting groups and individual settings through AYON server settings
- **Multiple setting types**: Support for text fields, checkboxes, dropdowns, and action buttons
- **Path browser**: Text fields can be marked as file/folder paths with browse buttons
- **Action integration**: Buttons can execute custom action plugins
- **Local storage**: Settings are saved to `~/.ayon/settings/localconfig.json`
- **Tabbed interface**: Each settings group appears as a separate tab
- **Restore defaults**: Each group has a "Restore Defaults" button

## Setting Types

### String Settings
- Regular text input
- Optional "Is Path" flag adds a browse button for file/folder selection
- Default value support

### Boolean Settings  
- Checkbox input
- Default value support

### Enum Settings
- Dropdown selection
- Configurable options list
- Default selection support

### Button Settings
- Execute action plugins
- Link to compatible action plugins through action ID

## Server Configuration

Configure setting groups in the AYON server settings under "Local Config":

1. **Groups**: Create configuration groups with titles and descriptions
2. **Settings**: Add individual settings to each group with:
   - Type (string, boolean, enum, button)
   - Label and tooltip
   - Default values
   - Type-specific options (enum choices, path flag, action ID)

## Usage

1. Access through AYON tray menu: "User Config"
2. Configure settings in the tabbed interface
3. Settings are automatically saved to local JSON file
4. Use "Restore Defaults" to reset group settings

## Action Integration

The addon uses AYON-core's canonical action system with the `families` approach.

### Using AYON Actions
Any AYON launcher action can be made compatible by:
- Adding `"local_config"` to the action's `families` list
- Optionally implementing `execute_with_config(config_data)` method (falls back to standard `execute()`)
- The action will be automatically discovered using AYON-core's `discover_launcher_actions()`

### Creating Action Plugins
Create custom action plugins by:

1. Inheriting from `LocalConfigCompatibleAction` (which extends `LauncherAction`)
2. Setting proper AYON action metadata:
   - `name` (unique identifier)
   - `label`, `icon`, `color`, `order` (optional)
   - `families = ["local_config"]` (canonical AYON approach)
3. Implementing the `execute_with_config(config_data)` method
4. Placing in `plugins/actions/` directory

**Configuration**: In server settings, use the action's **class name** (e.g. "CleanLogsAction") in the button_action field.

Example action plugins included:
- **CleanLogsAction**: Clean AYON log files
- **OpenProjectFolderAction**: Open configured project folder in file explorer

### Discovery Process
The addon discovers actions using:
- Standard AYON-core `discover_launcher_actions()` for all actions
- Filters by `families` containing `"local_config"` (canonical AYON approach)

## Installation

1. Place the addon in your AYON addons directory
2. Configure setting groups in server settings
3. Restart AYON launcher
4. Access via tray menu "User Config"