# -*- coding: utf-8 -*-

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class SetEnvironmentVariableAction(LocalConfigCompatibleAction):
    """Action to set environment variables where action_data specifies the env var name and the widget value is used"""

    # AYON action metadata
    name = "set_project_env_var"
    label = "Configure Project Environment Variables"
    icon = None
    color = "#4a90e2"
    order = 60

    # Canonical AYON families approach
    families = ["local_config"]

    def execute_with_config(self, config_data, action_data=""):
        """Execute the project environment variable configuration action


        Args:

            config_data: Configuration data containing user_settings with widget values

            action_data: Environment variable name to set (e.g., "AYON_HARMONY_MAX_RENDER_THREADS")
        """

        try:
            if not action_data:
                log.warning(
                    "No action_data provided - action_data should contain the environment variable name"
                )

                return False

            # action_data contains the environment variable name
            var_name = action_data.strip()

            # Get the value from _triggered_setting_value (set by the UI when action is triggered)
            var_value = config_data.get("_triggered_setting_value")

            if var_value is None:
                log.warning(f"No value found for environment variable '{var_name}'")

                return False

            # Convert value to string if it isn't already
            var_value_str = str(var_value)

            # Register the environment variable
            self.register_environment_variable(
                var_name,
                var_value_str,
                "Project environment variable - automatically set by Local Config addon",
            )

            log.debug(
                f"Registered environment variable '{var_name}' = '{var_value_str}'"
            )

            return True

        except Exception as e:
            log.error(f"Error in set project environment variable action: {e}")

            return False
