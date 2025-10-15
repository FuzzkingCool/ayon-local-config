# -*- coding: utf-8 -*-
from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class SetProjectEnvironmentVariableAction(LocalConfigCompatibleAction):
    """Action to configure project-specific environment variables using AYON Tools"""

    # AYON action metadata
    name = "set_project_env_var"
    label = "Configure Project Environment Variables"
    icon = None
    color = "#4a90e2"
    order = 60

    # Canonical AYON families approach
    families = ["local_config"]

    def execute_with_config(self, config_data):
        """Execute the project environment variable configuration action"""
        try:
            # Get the environment variable name and value from config data
            user_settings = config_data.get("user_settings", {})
            var_name = user_settings.get("variable_name")
            var_value = user_settings.get("variable_value")

            if not var_name:
                log.warning("No environment variable name found in configuration")
                return

            if var_value is None:
                log.warning("No environment variable value found in configuration")
                return

            # Get current project name
            project_name = self._get_current_project_name()
            if not project_name:
                log.warning("No active AYON project found")
                return

            # Show information about AYON Tools approach
            self._show_ayon_tools_info(var_name, var_value, project_name)

        except Exception as e:
            log.error(f"Error in set project environment variable action: {e}")

    def _show_ayon_tools_info(self, var_name, var_value, project_name):
        """Show information about using AYON Tools for project environment variables"""
        message = f"""
            Project Environment Variable Configuration

            Variable: {var_name} = {var_value}
            Project: {project_name}

            To set this as a project-specific environment variable that automatically applies when the project is loaded:

            1. Go to AYON Settings → Tools
            2. Create or edit a tool (e.g., "Local Config Project Vars")
            3. Add environment variable:
            {var_name} = {var_value}
            4. Set project filter to: {project_name}
            5. Save the tool configuration

            This will automatically apply the environment variable when the project is loaded in the AYON Launcher.

            For more information, see the AYON documentation on Tools Environment Variables.
        """

        QtWidgets.QMessageBox.information(
            None, "Project Environment Variable Configuration", message
        )


    def _get_current_project_name(self):
        """Get the current AYON project name"""
        try:
            from ayon_core.pipeline import get_current_project_name

            return get_current_project_name()
        except Exception as e:
            log.warning(f"Failed to get current project name: {e}")
            return None
