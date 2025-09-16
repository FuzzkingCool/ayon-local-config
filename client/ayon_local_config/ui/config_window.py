# -*- coding: utf-8 -*-
import os
import traceback
from typing import Dict, Any

try:
    from qtpy import QtCore, QtGui, QtWidgets
except ImportError:
    from qtpy5 import QtCore, QtGui, QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.storage import LocalConfigStorage
from ayon_local_config.plugin import execute_action_by_name


class SettingWidget(QtWidgets.QWidget):
    """Base widget for individual settings"""
    
    valueChanged = QtCore.Signal(object)  # Emits the new value
    
    def __init__(self, setting_config: Dict[str, Any], current_value: Any = None, parent=None):
        super().__init__(parent)
        self.setting_config = setting_config
        self.current_value = current_value
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for this setting - implemented by subclasses"""
        raise NotImplementedError
    
    def get_value(self):
        """Get the current value - implemented by subclasses"""
        raise NotImplementedError
    
    def set_value(self, value):
        """Set the current value - implemented by subclasses"""
        raise NotImplementedError


class StringSettingWidget(SettingWidget):
    """Widget for string/text settings"""
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText(self.setting_config.get('tooltip', ''))
        
        # Set initial value
        if self.current_value is not None:
            self.line_edit.setText(str(self.current_value))
        else:
            default_val = self.setting_config.get('default_string', '')
            self.line_edit.setText(default_val)
        
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)
        
        # Add browse button if this is a path setting
        if self.setting_config.get('is_path', False):
            self.browse_button = QtWidgets.QPushButton("Browse...")
            self.browse_button.clicked.connect(self._browse_path)
            layout.addWidget(self.browse_button)
    
    def _on_text_changed(self, text):
        self.current_value = text
        self.valueChanged.emit(text)
    
    def _browse_path(self):
        # Open file/folder dialog based on context
        current_path = self.line_edit.text() or os.path.expanduser("~")
        
        # Try to determine if this should be a file or folder dialog
        if "folder" in self.setting_config.get('label', '').lower() or "dir" in self.setting_config.get('label', '').lower():
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, 
                f"Select {self.setting_config.get('label', 'Folder')}", 
                current_path
            )
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                f"Select {self.setting_config.get('label', 'File')}", 
                current_path,
                "All Files (*.*)"
            )
        
        if path:
            self.line_edit.setText(path)
    
    def get_value(self):
        return self.line_edit.text()
    
    def set_value(self, value):
        self.line_edit.setText(str(value) if value is not None else '')


class BooleanSettingWidget(SettingWidget):
    """Widget for boolean settings"""
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setToolTip(self.setting_config.get('tooltip', ''))
        
        # Set initial value
        if self.current_value is not None:
            self.checkbox.setChecked(bool(self.current_value))
        else:
            default_val = self.setting_config.get('default_boolean', False)
            self.checkbox.setChecked(default_val)
        
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)
        layout.addStretch()  # Push checkbox to the left
    
    def _on_toggled(self, checked):
        self.current_value = checked
        self.valueChanged.emit(checked)
    
    def get_value(self):
        return self.checkbox.isChecked()
    
    def set_value(self, value):
        self.checkbox.setChecked(bool(value) if value is not None else False)


class EnumSettingWidget(SettingWidget):
    """Widget for enum/dropdown settings"""
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setToolTip(self.setting_config.get('tooltip', ''))
        
        # Add enum options
        options = self.setting_config.get('enum_options', [])
        for option in options:
            self.combo_box.addItem(option)
        
        # Set initial value
        if self.current_value is not None:
            index = self.combo_box.findText(str(self.current_value))
            if index >= 0:
                self.combo_box.setCurrentIndex(index)
        else:
            default_val = self.setting_config.get('default_enum', '')
            index = self.combo_box.findText(default_val)
            if index >= 0:
                self.combo_box.setCurrentIndex(index)
        
        self.combo_box.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self.combo_box)
    
    def _on_selection_changed(self, text):
        self.current_value = text
        self.valueChanged.emit(text)
    
    def get_value(self):
        return self.combo_box.currentText()
    
    def set_value(self, value):
        index = self.combo_box.findText(str(value) if value is not None else '')
        if index >= 0:
            self.combo_box.setCurrentIndex(index)


class ButtonSettingWidget(SettingWidget):
    """Widget for button/action settings"""
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QtWidgets.QPushButton(self.setting_config.get('label', 'Execute'))
        self.button.setToolTip(self.setting_config.get('tooltip', ''))
        self.button.clicked.connect(self._execute_action)
        
        layout.addWidget(self.button)
        layout.addStretch()  # Push button to the left
    
    def _execute_action(self):
        action_name = self.setting_config.get('button_action', '')
        if action_name:
            # Get current config data from parent
            config_data = {}
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'get_current_config'):
                    config_data = parent_widget.get_current_config()
                    break
                parent_widget = parent_widget.parent()
            
            success = execute_action_by_name(action_name, config_data)
            if not success:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Action Failed",
                    f"Failed to execute action: {action_name}"
                )
    
    def get_value(self):
        return None  # Buttons don't have values
    
    def set_value(self, value):
        pass  # Buttons don't have values


class ConfigGroupWidget(QtWidgets.QWidget):
    """Widget for a configuration group with all its settings"""
    
    def __init__(self, group_config: Dict[str, Any], storage: LocalConfigStorage, parent=None):
        super().__init__(parent)
        self.group_config = group_config
        self.storage = storage
        self.group_id = self._generate_group_id()
        self.setting_widgets = {}
        self.setup_ui()
        self.load_values()
    
    def _generate_group_id(self):
        """Generate a unique ID for this group based on title"""
        title = self.group_config.get('title', 'group')
        return title.lower().replace(' ', '_').replace('-', '_')
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Group description
        description = self.group_config.get('description', '')
        if description:
            desc_label = QtWidgets.QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666666; font-style: italic; margin-bottom: 10px;")
            layout.addWidget(desc_label)
        
        # Settings form
        form_layout = QtWidgets.QFormLayout()
        
        settings = self.group_config.get('settings', [])
        for i, setting in enumerate(settings):
            setting_id = f"setting_{i}"
            label_text = setting.get('label', f'Setting {i+1}')
            
            # Create appropriate widget based on type
            setting_type = setting.get('type', 'string')
            if setting_type == 'string':
                widget = StringSettingWidget(setting)
            elif setting_type == 'boolean':
                widget = BooleanSettingWidget(setting)
            elif setting_type == 'enum':
                widget = EnumSettingWidget(setting)
            elif setting_type == 'button':
                widget = ButtonSettingWidget(setting)
            else:
                widget = StringSettingWidget(setting)  # Fallback
            
            # Connect value change signal
            if hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(lambda value, sid=setting_id: self._on_setting_changed(sid, value))
            
            self.setting_widgets[setting_id] = widget
            
            # Add to form
            label = QtWidgets.QLabel(label_text)
            tooltip = setting.get('tooltip', '')
            if tooltip:
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)
            
            form_layout.addRow(label, widget)
        
        layout.addLayout(form_layout)
        
        # Restore defaults button
        layout.addStretch()
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        self.restore_button = QtWidgets.QPushButton("Restore Defaults")
        self.restore_button.clicked.connect(self._restore_defaults)
        button_layout.addWidget(self.restore_button)
        
        layout.addLayout(button_layout)
    
    def _on_setting_changed(self, setting_id: str, value):
        """Handle setting value change"""
        try:
            self.storage.set_setting_value(self.group_id, setting_id, value)
            log.debug(f"Saved setting {self.group_id}.{setting_id} = {value}")
        except Exception as e:
            log.error(f"Failed to save setting {setting_id}: {e}")
    
    def load_values(self):
        """Load values from storage"""
        group_config = self.storage.get_group_config(self.group_id)
        
        for setting_id, widget in self.setting_widgets.items():
            if setting_id in group_config:
                widget.set_value(group_config[setting_id])
    
    def _restore_defaults(self):
        """Restore all settings to their default values"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Restore Defaults",
            f"Are you sure you want to restore all settings in '{self.group_config.get('title', 'this group')}' to their default values?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Get default values
            defaults = {}
            settings = self.group_config.get('settings', [])
            for i, setting in enumerate(settings):
                setting_id = f"setting_{i}"
                setting_type = setting.get('type', 'string')
                
                if setting_type == 'string':
                    defaults[setting_id] = setting.get('default_string', '')
                elif setting_type == 'boolean':
                    defaults[setting_id] = setting.get('default_boolean', False)
                elif setting_type == 'enum':
                    defaults[setting_id] = setting.get('default_enum', '')
                # Buttons don't have default values
            
            # Save and apply defaults
            self.storage.reset_group_to_defaults(self.group_id, defaults)
            self.load_values()
            
            QtWidgets.QMessageBox.information(
                self,
                "Defaults Restored",
                "All settings have been restored to their default values."
            )
    
    def get_current_config(self):
        """Get current configuration values for this group"""
        config = {}
        for setting_id, widget in self.setting_widgets.items():
            if hasattr(widget, 'get_value'):
                config[setting_id] = widget.get_value()
        return config


class LocalConfigWindow(QtWidgets.QWidget):
    """Main window for local configuration"""
    
    def __init__(self, settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.settings = settings
        self.storage = LocalConfigStorage()
        self.setWindowTitle("Local Configuration")
        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Add tabs for each enabled group
        groups = self.settings.get('groups', [])
        for group in groups:
            if group.get('enabled', True):
                title = group.get('title', 'Untitled Group')
                
                # Create group widget
                group_widget = ConfigGroupWidget(group, self.storage)
                
                # Add as tab
                self.tab_widget.addTab(group_widget, title)
        
        layout.addWidget(self.tab_widget)
        
        # Add close button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Apply styling
        self.apply_styling()
    
    def apply_styling(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #555555;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #555555;
            }
            QComboBox::down-arrow {
                image: none;
                border: 1px solid #aaaaaa;
                width: 0px;
                height: 0px;
                border-top: 4px solid #aaaaaa;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                selection-background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event"""
        log.info("Local Config window closed")
        event.accept()
