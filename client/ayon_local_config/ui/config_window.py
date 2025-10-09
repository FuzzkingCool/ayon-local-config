 # -*- coding: utf-8 -*-
import os
from typing import Dict, Any

try:
    from qtpy import QtCore, QtGui, QtWidgets
except ImportError:
    from qtpy5 import QtCore, QtGui, QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.storage import LocalConfigStorage
from ayon_local_config.plugin import execute_action_by_name
from ayon_local_config.style import load_stylesheet, get_objected_colors


class SwitchWidget(QtWidgets.QWidget):
    """Custom toggle switch widget that looks like modern UI switches"""
    
    toggled = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._animation = None
        self.setFixedSize(28, 12)  # Smaller switch dimensions (2:1 ratio)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.toggled.emit(checked)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Switch dimensions
        width = self.width()
        height = self.height()
        radius = height // 2
        
        # Background colors
        if self._checked:
            bg_color = QtGui.QColor(86, 160, 111)  # Green when on
        else:
            bg_color = QtGui.QColor(60, 60, 60)   # Dark grey when off
        
        # Draw background
        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawRoundedRect(0, 0, width, height, radius, radius)
        
        # Draw thumb (white circle) - bigger relative to the smaller switch
        thumb_size = height - 2  # Much bigger thumb, only 2px margin
        thumb_margin = 1
        
        if self._checked:
            # Thumb on the right
            thumb_x = width - thumb_size - thumb_margin
        else:
            # Thumb on the left
            thumb_x = thumb_margin
        
        thumb_y = thumb_margin
        
        painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawEllipse(thumb_x, thumb_y, thumb_size, thumb_size)


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
        if not getattr(self, "_loading", False):
            self.valueChanged.emit(text)
    
    def _browse_path(self):
        # Open file/folder dialog based on path_type configuration
        current_path = self.line_edit.text() or os.path.expanduser("~")
        
        path_type = self.setting_config.get('path_type', 'folder')
        
        if path_type == 'folder':
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, 
                f"Select {self.setting_config.get('label', 'Folder')}", 
                current_path
            )
        elif path_type == 'file':
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 
                f"Select {self.setting_config.get('label', 'File')}", 
                current_path,
                "All Files (*.*)"
            )
        else:
            # Fallback: try to determine from label
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
        
        self.switch = SwitchWidget()
        self.switch.setToolTip(self.setting_config.get('tooltip', ''))
        
        # Set initial value
        if self.current_value is not None:
            self.switch.setChecked(bool(self.current_value))
        else:
            default_val = self.setting_config.get('default_boolean', False)
            self.switch.setChecked(default_val)
        
        self.switch.toggled.connect(self._on_toggled)
        layout.addWidget(self.switch)
        layout.addStretch()  # Push switch to the left
    
    def _on_toggled(self, checked):
        self.current_value = checked
        if not getattr(self, "_loading", False):
            self.valueChanged.emit(checked)
    
    def get_value(self):
        return self.switch.isChecked()
    
    def set_value(self, value):
        self.switch.setChecked(bool(value) if value is not None else False)


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
        if not getattr(self, "_loading", False):
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

class SpinBoxSettingWidget(SettingWidget):
    """Widget for spin box settings"""
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.spin_box = QtWidgets.QSpinBox()
        self.spin_box.setToolTip(self.setting_config.get('tooltip', ''))
        
        # Set initial value
        if self.current_value is not None:
            self.spin_box.setValue(int(self.current_value))
        else:
            default_val = self.setting_config.get('default_spin_box', 0)
            self.spin_box.setValue(default_val)
        
        self.spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin_box)
    
    def _on_value_changed(self, value):
        self.current_value = value
        if not getattr(self, "_loading", False):
            self.valueChanged.emit(value)
    
    def get_value(self):
        return self.spin_box.value()
    
    def set_value(self, value):
        self.spin_box.setValue(int(value) if value is not None else 0)


class DividerSettingWidget(SettingWidget):
    """Widget for visual dividers/separators"""
    
    def setup_ui(self):
        orientation = self.setting_config.get('divider_orientation', 'horizontal')
        label_text = self.setting_config.get('label', '')
        
        if orientation == 'vertical':
            # Vertical divider - simple 2px line with padding
            layout = QtWidgets.QHBoxLayout(self)
            layout.setContentsMargins(12, 8, 12, 8)  # Adequate padding
            layout.setSpacing(0)  # No spacing
            
            # Create vertical line - simple 2px line
            self.divider = QtWidgets.QFrame()
            self.divider.setFixedWidth(2)  # Simple 2px line
            self.divider.setFixedHeight(200)  # Fixed height for speed
            # Styling is handled by CSS in style.css
            
            # No labels for vertical dividers - just the line
            layout.addWidget(self.divider)
        else:
            # Horizontal divider - expanding line with left-aligned label
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(6)

            self.divider = QtWidgets.QFrame()
            self.divider.setMinimumHeight(2)
            self.divider.setMaximumHeight(2)
            self.divider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self.divider.show()

            if label_text:
                label_layout = QtWidgets.QHBoxLayout()
                label_layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                label = QtWidgets.QLabel(label_text)
                label.setMinimumHeight(20)
                label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                label_layout.addWidget(label)
                label_layout.addWidget(self.divider, 1)
                layout.addLayout(label_layout)
            else:
                layout.addWidget(self.divider)
    
    def get_value(self):
        return None  # Dividers don't have values
    
    def set_value(self, value):
        pass  # Dividers don't have values


class ConfigGroupWidget(QtWidgets.QWidget):
    """Widget for a configuration group with all its settings"""
    
    def __init__(self, group_config: Dict[str, Any], storage: LocalConfigStorage, parent=None):
        super().__init__(parent)
        
        self.group_config = group_config
        self.storage = storage
        self.group_id = self._generate_group_id()
        self.setting_widgets = {}
        self._loading = False # Flag to prevent valueChanged signals during programmatic loads
        
        # Set minimum size to prevent layout issues
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
    
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
            # Use AYON color system for description
            colors = get_objected_colors()
            text_color = colors['font-disabled'].name()
            desc_label.setStyleSheet(f"color: {text_color}; font-style: italic; margin-bottom: 10px;")
            layout.addWidget(desc_label)
        
        # Create main content layout
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(12)  # Add spacing between sections
        self.main_layout.setContentsMargins(8, 8, 8, 8)  # Add margins
        layout.addLayout(self.main_layout)
        
        # Process settings and create layout sections
        self._create_layout_sections()
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Restore defaults button
        # No buttons needed here - they're in the footer
    
    def _create_layout_sections(self):
        """Create layout sections based on vertical dividers"""
        settings = self.group_config.get('settings', [])
        
        # Start with first section
        current_section = QtWidgets.QVBoxLayout()
        current_section.setContentsMargins(6, 6, 6, 6)
        current_section.setSpacing(4)  # Compact spacing
        current_section.setAlignment(QtCore.Qt.AlignTop)  # Align content to top
        self.main_layout.addLayout(current_section)
        
        for i, setting in enumerate(settings):
            setting_id = f"setting_{i}"
            setting_type = setting.get('type', 'string')
            
            # Check if this is a vertical divider
            if setting_type == 'divider' and setting.get('divider_orientation', 'horizontal') == 'vertical':
                # Create the vertical divider widget
                widget = self._create_setting_widget(setting, setting_id)
                if widget:
                    self.setting_widgets[setting_id] = widget
                    # Add the vertical divider directly to the main layout (between columns)
                    self.main_layout.addWidget(widget)
                
                # Then start a new section for the next column
                current_section = QtWidgets.QVBoxLayout()
                current_section.setContentsMargins(8, 8, 8, 8)
                current_section.setSpacing(8)  # Increased spacing
                current_section.setAlignment(QtCore.Qt.AlignTop)  # Align content to top
                self.main_layout.addLayout(current_section)
                continue
            
            # Create the widget
            widget = self._create_setting_widget(setting, setting_id)
            if widget:
                self.setting_widgets[setting_id] = widget
                
                # Add to current section
                if setting_type == 'divider':
                    # Horizontal divider - add directly
                    current_section.addWidget(widget)
                else:
                    # Regular setting - add with label
                    label_text = setting.get('label', f'Setting {i+1}')
                    label = QtWidgets.QLabel(label_text)
                    tooltip = setting.get('tooltip', '')
                    if tooltip:
                        label.setToolTip(tooltip)
                        widget.setToolTip(tooltip)
                    
                    # Create form row with compact sizing
                    row_layout = QtWidgets.QHBoxLayout()
                    row_layout.setContentsMargins(0, 2, 0, 2)  # Compact vertical spacing
                    row_layout.setSpacing(6)  # Compact horizontal spacing
                    
                    # Set proper minimum sizes to prevent cutoff
                    label.setMinimumWidth(120)  # Compact label width
                    label.setMinimumHeight(26)  # Increased height to match CSS
                    label.setMaximumHeight(30)  # Prevent oversized labels
                    label.setAlignment(QtCore.Qt.AlignVCenter)  # Center align labels vertically
                    widget.setMinimumHeight(26)  # Match CSS height
                    widget.setMaximumHeight(30)  # Fixed height to prevent cutoff
                    widget.setMinimumWidth(160)  # Compact minimum width
                    
                    row_layout.addWidget(label)
                    row_layout.addWidget(widget)
                    current_section.addLayout(row_layout)
    
    def _create_setting_widget(self, setting, setting_id):
        """Create a setting widget based on type"""
        setting_type = setting.get('type', 'string')
        
        if setting_type == 'string':
            widget = StringSettingWidget(setting)
        elif setting_type == 'boolean':
            widget = BooleanSettingWidget(setting)
        elif setting_type == 'enum':
            widget = EnumSettingWidget(setting)
        elif setting_type == 'button':
            widget = ButtonSettingWidget(setting)
        elif setting_type == 'spinbox':
            widget = SpinBoxSettingWidget(setting)
        elif setting_type == 'divider':
            widget = DividerSettingWidget(setting)
        else:
            widget = StringSettingWidget(setting)  # Fallback
        
        # Connect value change signal
        if hasattr(widget, 'valueChanged'):
            widget.valueChanged.connect(lambda value, sid=setting_id: self._on_setting_changed(sid, value))
        
        return widget
    
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
        self._load_values_from_config_data(group_config)
    
    def load_values_from_config(self, config):
        """Load values from provided config data"""
        group_config = config.get(self.group_id, {})
        self._load_values_from_config_data(group_config)
    
    def _load_values_from_config_data(self, group_config):
        """Load values from group config data"""
        for setting_id, widget in self.setting_widgets.items():
            if setting_id in group_config:
                # Prevent signal emission while programmatically setting values
                setattr(widget, "_loading", True)
                try:
                    widget.set_value(group_config[setting_id])
                finally:
                    setattr(widget, "_loading", False)
    
    def get_current_config(self):
        """Get current configuration values from all widgets"""
        config = {}
        for setting_id, widget in self.setting_widgets.items():
            if hasattr(widget, 'get_value'):
                config[setting_id] = widget.get_value()
        return {self.group_id: config}
    
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
        
        # Set window properties immediately (canonical Qt approach)
        self.setWindowTitle("Local Configuration")
        self.setMinimumSize(800, 600)
        self.resize(900, 1031)
        self.move(830, 150)
        
        # Create minimal UI first - just a loading indicator
        self._create_minimal_ui()
        
        # Defer full UI building until after window is shown
        QtCore.QTimer.singleShot(100, self._build_full_ui)
    
    def _create_minimal_ui(self):
        """Create minimal UI with just a loading indicator"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a simple loading widget
        self.loading_widget = QtWidgets.QWidget()
        loading_layout = QtWidgets.QVBoxLayout(self.loading_widget)
        loading_layout.setContentsMargins(20, 20, 20, 20)
        loading_layout.setSpacing(10)
        
        # Loading label
        loading_label = QtWidgets.QLabel("Loading Local Configuration...")
        loading_label.setAlignment(QtCore.Qt.AlignCenter)
        loading_label.setObjectName("loading_label")
        loading_layout.addWidget(loading_label)
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setObjectName("progress_bar")
        loading_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.loading_widget)
        
        # Apply basic styling
        from ayon_local_config.style import load_stylesheet
        stylesheet = load_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def _build_full_ui(self):
        """Build the complete UI after window is shown"""
        # Hide loading widget
        self.loading_widget.hide()
        
        # Build the full UI
        self._build_ui()
        
        # Load values
        self._load_values_after_show()
    
    def _build_ui(self):
        """Build UI directly in this widget"""
        # Use the existing layout
        layout = self.layout()
        
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Add tabs for each enabled group
        groups = self.settings.get('groups', [])
        
        for group in groups:
            if group.get('enabled', True):
                title = group.get('title', 'Untitled Group')
                
                # Create group widget
                group_widget = ConfigGroupWidget(group, self.storage)
                
                # Add to tab widget
                self.tab_widget.addTab(group_widget, title)
        
        layout.addWidget(self.tab_widget)
        
        # Create footer with status bar and buttons
        footer_widget = QtWidgets.QWidget()
        footer_widget.setObjectName("footer_widget")
        footer_layout = QtWidgets.QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(8, 4, 8, 4)
        footer_layout.setSpacing(8)
        
        # Status bar (left side)
        self.status_bar = QtWidgets.QLabel("Initializing...")
        self.status_bar.setObjectName("status_bar")
        footer_layout.addWidget(self.status_bar)
        
        # Stretch to push buttons to the right
        footer_layout.addStretch()
        
        # Restore Defaults button
        restore_button = QtWidgets.QPushButton("Restore Defaults")
        restore_button.clicked.connect(self.restore_defaults)
        footer_layout.addWidget(restore_button)
        
        # Close button
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        footer_layout.addWidget(close_button)
        
        layout.addWidget(footer_widget)
        
        # Apply AYON styling
        from ayon_local_config.style import load_stylesheet
        stylesheet = load_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def _load_values_after_show(self):
        """Load values after window is shown to prevent layout interference"""
        if hasattr(self, 'status_bar'):
            self.status_bar.setText("Loading values...")
        
        # Load config once and pass to all widgets to avoid repeated file loading
        config = self.storage.load_config()
        
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, 'load_values_from_config'):
                tab_widget.load_values_from_config(config)
            elif hasattr(tab_widget, 'load_values'):
                tab_widget.load_values()
        
        if hasattr(self, 'status_bar'):
            self.status_bar.setText("Ready")
    
    def restore_defaults(self):
        """Restore all settings to their default values"""
        try:
            log.debug("Restoring default values...")
            self.status_bar.setText("Restoring defaults...")
            
            # Restore defaults for all groups
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, 'restore_defaults'):
                    tab_widget.restore_defaults()
            
            self.status_bar.setText("Defaults restored")
            log.debug("Default values restored successfully")
        except Exception as e:
            log.error(f"Failed to restore defaults: {e}")
            self.status_bar.setText("Error restoring defaults")
    
    def execute_action(self, action_name: str):
        """Execute a local config action"""
        try:
            from ayon_local_config.plugin import execute_action_by_name
            
            # Get current config data
            config_data = self.get_current_config()
            
            # Execute the action
            success = execute_action_by_name(action_name, config_data)
            
            if success:
                log.info(f"Successfully executed action: {action_name}")
                self.status_bar.setText(f"Executed {action_name}")
            else:
                log.warning(f"Failed to execute action: {action_name}")
                self.status_bar.setText(f"Failed to execute {action_name}")
                
        except Exception as e:
            log.error(f"Error executing action {action_name}: {e}")
            self.status_bar.setText(f"Error executing {action_name}")
    
    def get_current_config(self):
        """Get current configuration data from all groups"""
        config_data = {}
        
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, 'get_current_config'):
                group_config = tab_widget.get_current_config()
                config_data.update(group_config)
        
        return config_data
    
    def show(self):
        """Show the window"""
        # Use show() for non-modal display
        super().show()
        self.raise_()
        self.activateWindow()
    
    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event"""
        log.info("Local Config window closed")
        # Don't delete the window, just hide it
        self.hide()
        event.ignore()  # Don't actually close, just hide
