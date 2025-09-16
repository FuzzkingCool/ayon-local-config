# -*- coding: utf-8 -*-
import os
import inspect
from typing import List, Dict, Any

from ayon_core.pipeline.actions import discover_launcher_actions
from ayon_core.pipeline import LauncherAction

from ayon_local_config.logger import log


class LocalConfigCompatibleAction(LauncherAction):
    """Base class for Local Config compatible action plugins"""
    
    # AYON Action required attributes
    name = "local_config_action"
    label = "Local Config Action"
    icon = None
    color = None
    order = 0
    
    # Mark as local config compatible
    local_config_compatible = True
    
    def execute_with_config(self, config_data: Dict[str, Any]):
        """
        Execute the action with current config data
        
        Args:
            config_data (dict): Current configuration values from local config
        """
        raise NotImplementedError("Local Config actions must implement execute_with_config method")
    
    def is_compatible(self, session):
        """Check if this action is compatible with current session - always true for local config"""
        return True
    
    def process(self, session, **kwargs):
        """Standard AYON action process method - not used for local config actions"""
        return True


def discover_localconfig_compatible_actions() -> List[LauncherAction]:
    """Discover all AYON launcher actions that are compatible with Local Config"""
    compatible_actions = []
    
    try:
        # Use AYON-core's standard launcher action discovery
        # This will now include our actions since we registered the path
        all_actions = discover_launcher_actions()
        
        for action_class in all_actions:
            # Check if action has "local_config" in families (canonical AYON approach)
            if _is_action_compatible_with_local_config(action_class):
                compatible_actions.append(action_class)
                log.debug(f"Found local config compatible action: {action_class.__name__}")
                            
    except Exception as e:
        log.warning(f"Error discovering compatible actions: {e}")
    
    return compatible_actions


def _is_action_compatible_with_local_config(action_class) -> bool:
    """Check if an action is compatible with local config using canonical AYON families"""
    try:
        # Check if action has "local_config" in families (canonical AYON approach)
        if hasattr(action_class, 'families'):
            families = action_class.families
            if isinstance(families, (list, tuple)) and "local_config" in families:
                return True
        
        # Check if it's our own LocalConfigCompatibleAction subclass
        if issubclass(action_class, LocalConfigCompatibleAction):
            return True
            
    except Exception as e:
        log.debug(f"Error checking action compatibility for {action_class.__name__}: {e}")
    
    return False






def get_available_action_names() -> List[str]:
    """Get list of available action names for server settings configuration"""
    action_names = []
    
    try:
        compatible_actions = discover_localconfig_compatible_actions()
        for action_class in compatible_actions:
            # Use class name as the action identifier
            action_names.append(action_class.__name__)
            
    except Exception as e:
        log.warning(f"Error getting action names: {e}")
    
    return action_names


def find_action_by_name(action_name: str) -> LauncherAction:
    """Find an action class by its name"""
    try:
        compatible_actions = discover_localconfig_compatible_actions()
        for action_class in compatible_actions:
            if action_class.__name__ == action_name:
                return action_class
                
    except Exception as e:
        log.warning(f"Error finding action {action_name}: {e}")
    
    return None


def execute_action_by_name(action_name: str, config_data: Dict[str, Any]) -> bool:
    """Execute an action by name with current config data"""
    try:
        action_class = find_action_by_name(action_name)
        if action_class:
            # Create instance and execute
            action_instance = action_class()
            
            # Use execute_with_config if available, otherwise fall back to execute
            if hasattr(action_instance, 'execute_with_config'):
                action_instance.execute_with_config(config_data)
            elif hasattr(action_instance, 'execute'):
                # Legacy support - try to pass config_data if the method accepts it
                import inspect
                sig = inspect.signature(action_instance.execute)
                if len(sig.parameters) > 0:
                    action_instance.execute(config_data)
                else:
                    action_instance.execute()
            else:
                log.error(f"Action {action_name} has no execute method")
                return False
                
            log.info(f"Successfully executed action: {action_name}")
            return True
        else:
            log.warning(f"Action not found: {action_name}")
            return False
            
    except Exception as e:
        log.error(f"Error executing action {action_name}: {e}")
        return False


def list_available_actions():
    """Utility function to list all available actions for debugging"""
    try:
        print("=== Available Local Config Compatible Actions ===")
        compatible_actions = discover_localconfig_compatible_actions()
        
        if not compatible_actions:
            print("No compatible actions found.")
            return
        
        for i, action_class in enumerate(compatible_actions, 1):
            print(f"{i}. {action_class.__name__}")
            if hasattr(action_class, 'label'):
                print(f"   Label: {action_class.label}")
            if hasattr(action_class, 'description'):
                print(f"   Description: {action_class.description}")
            if hasattr(action_class, 'identifier'):
                print(f"   Identifier: {action_class.identifier}")
            print()
            
    except Exception as e:
        print(f"Error listing actions: {e}")


# For debugging - uncomment to test action discovery
# if __name__ == "__main__":
#     list_available_actions()
