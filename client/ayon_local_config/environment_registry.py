# -*- coding: utf-8 -*-
import os
from typing import Dict, Any, List, Optional, Callable

from ayon_local_config.logger import log
from ayon_local_config.storage import LocalConfigStorage


class EnvironmentVariableRegistry:
    """
    Registry for managing environment variables that need to persist across addon loads.
    
    This registry allows actions to register environment variables that should be
    automatically set when the addon loads, providing persistence across sessions.
    """
    
    def __init__(self, storage: LocalConfigStorage = None):
        """
        Initialize the environment variable registry.
        
        Args:
            storage: LocalConfigStorage instance for persistence. If None, creates a new one.
        """
        self.storage = storage or LocalConfigStorage()
        self._registered_vars: Dict[str, str] = {}
        self._action_callbacks: Dict[str, List[Callable]] = {}
        self._load_registered_variables()
    
    def _load_registered_variables(self):
        """Load previously registered environment variables from storage"""
        try:
            config = self.storage.load_config()
            env_vars = config.get('environment_variables', {})
            
            # Migrate from complex format to simple key-value format
            self._registered_vars = self._migrate_environment_variables(env_vars)
            
            log.debug(f"Loaded {len(self._registered_vars)} registered environment variables")
        except Exception as e:
            log.error(f"Failed to load registered environment variables: {e}")
            self._registered_vars = {}
    
    def _migrate_environment_variables(self, env_vars: Dict[str, Any]) -> Dict[str, str]:
        """
        Migrate environment variables from complex format to simple key-value format.
        
        Args:
            env_vars: Environment variables from storage (may be complex or simple format)
            
        Returns:
            Dict with simple key-value pairs
        """
        migrated_vars = {}
        
        for var_name, var_data in env_vars.items():
            if isinstance(var_data, dict):
                # Complex format - extract the value
                if 'value' in var_data:
                    migrated_vars[var_name] = var_data['value']
                    log.debug(f"Migrated complex environment variable {var_name}")
                else:
                    # Fallback - use the entire dict as string (shouldn't happen)
                    migrated_vars[var_name] = str(var_data)
                    log.warning(f"Unexpected environment variable format for {var_name}")
            else:
                # Already simple format
                migrated_vars[var_name] = var_data
                log.debug(f"Environment variable {var_name} already in simple format")
        
        # Save migrated format if we found complex data
        if any(isinstance(var_data, dict) for var_data in env_vars.values()):
            log.info(f"Migrated {len(migrated_vars)} environment variables to simple format")
            self._save_migrated_variables(migrated_vars)
        
        return migrated_vars
    
    def _save_migrated_variables(self, migrated_vars: Dict[str, str]):
        """Save migrated environment variables to storage"""
        try:
            config = self.storage.load_config()
            config['environment_variables'] = migrated_vars
            self.storage.save_config(config)
            log.info("Saved migrated environment variables to simple format")
        except Exception as e:
            log.error(f"Failed to save migrated environment variables: {e}")
    
    def _save_registered_variables(self):
        """Save registered environment variables to storage"""
        try:
            config = self.storage.load_config()
            config['environment_variables'] = self._registered_vars
            self.storage.save_config(config)
            log.debug(f"Saved {len(self._registered_vars)} registered environment variables")
        except Exception as e:
            log.error(f"Failed to save registered environment variables: {e}")
    
    def register_environment_variable(
        self, 
        var_name: str, 
        value: str, 
        action_name: str = None,
        description: str = "",
        persistent: bool = True
    ) -> bool:
        """
        Register an environment variable for automatic setting on addon load.
        
        Args:
            var_name: Name of the environment variable
            value: Value to set for the environment variable
            action_name: Name of the action that registered this variable (optional)
            description: Optional description of the variable (optional)
            persistent: Whether this variable should persist across sessions
            
        Returns:
            bool: True if registration was successful
        """
        try:
            # Simple key-value storage - only store the value
            self._registered_vars[var_name] = value
            
            # Set the environment variable immediately
            os.environ[var_name] = value
            
            # Save to storage if persistent
            if persistent:
                self._save_registered_variables()
            
            log.info(f"Registered environment variable {var_name} = {value}")
            return True
            
        except Exception as e:
            log.error(f"Failed to register environment variable {var_name}: {e}")
            return False
    
    def unregister_environment_variable(self, var_name: str, action_name: str = None) -> bool:
        """
        Unregister an environment variable.
        
        Args:
            var_name: Name of the environment variable to unregister
            action_name: Optional action name for validation (ignored in simple storage)
            
        Returns:
            bool: True if unregistration was successful
        """
        try:
            if var_name not in self._registered_vars:
                log.warning(f"Environment variable {var_name} not found in registry")
                return False
            
            # Remove from environment
            if var_name in os.environ:
                del os.environ[var_name]
            
            # Remove from registry
            del self._registered_vars[var_name]
            
            # Save changes
            self._save_registered_variables()
            
            log.info(f"Unregistered environment variable {var_name}")
            return True
            
        except Exception as e:
            log.error(f"Failed to unregister environment variable {var_name}: {e}")
            return False
    
    def update_environment_variable(self, var_name: str, new_value: str, action_name: str = None) -> bool:
        """
        Update the value of a registered environment variable.
        
        Args:
            var_name: Name of the environment variable
            new_value: New value to set
            action_name: Optional action name for validation (ignored in simple storage)
            
        Returns:
            bool: True if update was successful
        """
        try:
            if var_name not in self._registered_vars:
                log.warning(f"Environment variable {var_name} not found in registry")
                return False
            
            # Update the value (simple key-value storage)
            self._registered_vars[var_name] = new_value
            
            # Set the environment variable
            os.environ[var_name] = new_value
            
            # Save changes
            self._save_registered_variables()
            
            log.info(f"Updated environment variable {var_name} to: {new_value}")
            return True
            
        except Exception as e:
            log.error(f"Failed to update environment variable {var_name}: {e}")
            return False
    
    def restore_environment_variables(self):
        """
        Restore all registered environment variables from storage.
        This should be called when the addon loads.
        
        Note: Project-specific environment variables are now handled by AYON Tools Environment Variables.
        This provides better integration with AYON's project loading system.
        """
        try:
            restored_count = 0
            
            # Restore global environment variables
            for var_name, value in self._registered_vars.items():
                os.environ[var_name] = value
                restored_count += 1
                log.debug(f"Restored global environment variable {var_name} = {value}")
            
            log.info(f"Restored {restored_count} environment variables on addon load")
            
        except Exception as e:
            log.error(f"Failed to restore environment variables: {e}")
    
    def get_registered_variables(self) -> Dict[str, str]:
        """
        Get all registered environment variables.
        
        Returns:
            Dict containing all registered variables as key-value pairs
        """
        return self._registered_vars.copy()
    
    def get_variable_value(self, var_name: str) -> Optional[str]:
        """
        Get the value of a specific registered variable.
        
        Args:
            var_name: Name of the environment variable
            
        Returns:
            Variable value or None if not found
        """
        return self._registered_vars.get(var_name)
    
    def is_variable_registered(self, var_name: str) -> bool:
        """
        Check if a variable is registered.
        
        Args:
            var_name: Name of the environment variable
            
        Returns:
            bool: True if variable is registered
        """
        return var_name in self._registered_vars
    
    def clear_all_variables(self, action_name: str = None):
        """
        Clear all registered environment variables.
        
        Args:
            action_name: Optional action name (ignored in simple storage)
        """
        try:
            # Clear all variables (simple storage doesn't track action names)
            for var_name in self._registered_vars.keys():
                if var_name in os.environ:
                    del os.environ[var_name]
            
            self._registered_vars.clear()
            log.info("Cleared all registered environment variables")
            
            self._save_registered_variables()
            
        except Exception as e:
            log.error(f"Failed to clear environment variables: {e}")
    
    def register_action_callback(self, action_name: str, callback: Callable):
        """
        Register a callback to be called when environment variables are restored.
        
        Args:
            action_name: Name of the action
            callback: Callback function to call
        """
        if action_name not in self._action_callbacks:
            self._action_callbacks[action_name] = []
        self._action_callbacks[action_name].append(callback)
        log.debug(f"Registered callback for action {action_name}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current environment variable registry state.
        
        Returns:
            Dict with summary information
        """
        return {
            'total_registered': len(self._registered_vars),
            'config_file_path': self.storage.config_file,
            'variables': list(self._registered_vars.keys())
        }


# Global registry instance
_global_registry: Optional[EnvironmentVariableRegistry] = None


def get_environment_registry() -> EnvironmentVariableRegistry:
    """
    Get the global environment variable registry instance.
    
    Returns:
        EnvironmentVariableRegistry: The global registry instance
    """
    global _global_registry
    if _global_registry is None:
        # If no registry is initialized, create one with default storage
        from ayon_local_config.storage import LocalConfigStorage
        storage = LocalConfigStorage()
        _global_registry = EnvironmentVariableRegistry(storage)
    return _global_registry


def initialize_environment_registry(storage: LocalConfigStorage = None) -> EnvironmentVariableRegistry:
    """
    Initialize the global environment variable registry.
    
    Args:
        storage: Optional storage instance to use
        
    Returns:
        EnvironmentVariableRegistry: The initialized registry
    """
    global _global_registry
    _global_registry = EnvironmentVariableRegistry(storage)
    return _global_registry


def restore_environment_variables():
    """
    Restore all registered environment variables.
    This is a convenience function for the global registry.
    """
    registry = get_environment_registry()
    registry.restore_environment_variables()
