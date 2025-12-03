# -*- coding: utf-8 -*-
import os
from typing import Any, Dict

from qtpy import QtCore, QtGui, QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import execute_action_by_name
from ayon_local_config.storage import LocalConfigStorage
from ayon_local_config.style import get_objected_colors, load_stylesheet


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
            bg_color = QtGui.QColor(60, 60, 60)  # Dark grey when off

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

    def __init__(
        self, setting_config: Dict[str, Any], current_value: Any = None, parent=None
    ):
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
        # Set tooltip as placeholder text only if there's no default value
        default_val = self.setting_config.get("default_value", "")
        if not default_val:
            self.line_edit.setPlaceholderText(self.setting_config.get("tooltip", ""))

        # Set initial value
        if self.current_value is not None:
            self.line_edit.setText(str(self.current_value))
        else:
            default_val = self.setting_config.get("default_value", "")
            self.line_edit.setText(default_val)

        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)

        # Add browse button if this is a path setting
        if self.setting_config.get("is_path", False):
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

        path_type = self.setting_config.get("path_type", "folder")

        if path_type == "folder":
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                f"Select {self.setting_config.get('label', 'Folder')}",
                current_path,
            )
        elif path_type == "file":
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                f"Select {self.setting_config.get('label', 'File')}",
                current_path,
                "All Files (*.*)",
            )
        else:
            # Fallback: try to determine from label
            if (
                "folder" in self.setting_config.get("label", "").lower()
                or "dir" in self.setting_config.get("label", "").lower()
            ):
                path = QtWidgets.QFileDialog.getExistingDirectory(
                    self,
                    f"Select {self.setting_config.get('label', 'Folder')}",
                    current_path,
                )
            else:
                path, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self,
                    f"Select {self.setting_config.get('label', 'File')}",
                    current_path,
                    "All Files (*.*)",
                )

        if path:
            self.line_edit.setText(path)

    def get_value(self):
        return self.line_edit.text()

    def set_value(self, value):
        self.line_edit.setText(str(value) if value is not None else "")


class BooleanSettingWidget(SettingWidget):
    """Widget for boolean settings"""

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.switch = SwitchWidget()
        self.switch.setToolTip(self.setting_config.get("tooltip", ""))

        # Set initial value
        if self.current_value is not None:
            self.switch.setChecked(bool(self.current_value))
        else:
            default_val = self.setting_config.get("default_value", "")
            # Convert string to boolean - "true", "1", "yes" are truthy, everything else is falsy
            bool_val = default_val.lower() in ("true", "1", "yes", "on")
            self.switch.setChecked(bool_val)

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
        if value is None:
            self.switch.setChecked(False)
        elif isinstance(value, bool):
            self.switch.setChecked(value)
        elif isinstance(value, str):
            # Handle normalized string boolean values
            self.switch.setChecked(value.lower() in ("true", "1", "yes", "on"))
        else:
            self.switch.setChecked(bool(value))


class EnumSettingWidget(SettingWidget):
    """Widget for enum/dropdown settings"""

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setToolTip(self.setting_config.get("tooltip", ""))

        # Add enum options
        options = self.setting_config.get("enum_options", [])
        for option in options:
            self.combo_box.addItem(option)

        # Set initial value
        if self.current_value is not None:
            index = self.combo_box.findText(str(self.current_value))
            if index >= 0:
                self.combo_box.setCurrentIndex(index)
        else:
            default_val = self.setting_config.get("default_value", "")
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
        index = self.combo_box.findText(str(value) if value is not None else "")
        if index >= 0:
            self.combo_box.setCurrentIndex(index)


class ButtonSettingWidget(SettingWidget):
    """Widget for button/action settings"""

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QtWidgets.QPushButton(self.setting_config.get("label", "Execute"))
        self.button.setToolTip(self.setting_config.get("tooltip", ""))
        self.button.clicked.connect(self._execute_action)

        layout.addWidget(self.button)

    def _execute_action(self):
        action_name = self.setting_config.get("action_name", "")
        if action_name:
            # Get current config data from parent
            config_data = {}
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, "get_all_config_data"):
                    config_data = parent_widget.get_all_config_data()
                    break
                parent_widget = parent_widget.parent()

            # Get action data from setting config
            action_data = self.setting_config.get("action_data", "")

            success = execute_action_by_name(action_name, config_data, action_data)
            if not success:
                QtWidgets.QMessageBox.warning(
                    self, "Action Failed", f"Failed to execute action: {action_name}"
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
        self.spin_box.setToolTip(self.setting_config.get("tooltip", ""))

        # Parse and set range from spinbox_range configuration
        self._configure_range()

        # Set initial value
        if self.current_value is not None:
            self.spin_box.setValue(int(self.current_value))
        else:
            default_val = self.setting_config.get("default_value", "0")
            # Convert string to integer, default to 0 if invalid
            try:
                int_val = int(default_val)
            except (ValueError, TypeError):
                int_val = 0
            self.spin_box.setValue(int_val)

        # Calculate and set width based on max value digits
        self._set_optimal_width()

        self.spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin_box)

    def _configure_range(self):
        """Configure the spinbox range from the spinbox_range setting"""
        range_str = self.setting_config.get("spinbox_range", "")
        if range_str:
            try:
                # Parse range string like "400-1000"
                if "-" in range_str:
                    min_val, max_val = range_str.split("-", 1)
                    min_val = int(min_val.strip())
                    max_val = int(max_val.strip())
                    self.spin_box.setRange(min_val, max_val)
                else:
                    # Single value - use as max, 0 as min
                    max_val = int(range_str.strip())
                    self.spin_box.setRange(0, max_val)
            except (ValueError, TypeError):
                # Invalid range format, use default range
                self.spin_box.setRange(0, 9999)
        else:
            # No range specified, use default range
            self.spin_box.setRange(0, 9999)

    def _set_optimal_width(self):
        """Set the spinbox width based on the number of digits in the max value"""
        max_val = self.spin_box.maximum()
        # Calculate width based on number of digits
        digit_count = len(str(max_val))
        # Base width calculation: ~12px per digit + adequate padding for buttons
        base_width = (
            digit_count * 12 + 50
        )  # 50px for buttons and padding (increased from 24px)
        # Set minimum and maximum reasonable widths
        min_width = 80  # Increased minimum width to accommodate buttons
        max_width = 200
        optimal_width = max(min_width, min(base_width, max_width))

        self.spin_box.setFixedWidth(optimal_width)

    def _on_value_changed(self, value):
        self.current_value = value
        if not getattr(self, "_loading", False):
            self.valueChanged.emit(value)

    def get_value(self):
        return self.spin_box.value()

    def set_value(self, value):
        if value is None:
            self.spin_box.setValue(0)
        else:
            try:
                int_val = int(value)
                self.spin_box.setValue(int_val)
            except (ValueError, TypeError) as e:
                log.warning(f"Invalid value for spinbox: {value} (type: {type(value)}), defaulting to 0. Error: {e}")
                self.spin_box.setValue(0)


class DividerSettingWidget(SettingWidget):
    """Widget for visual dividers/separators"""

    def setup_ui(self):
        orientation = self.setting_config.get("divider_orientation", "horizontal")
        label_text = self.setting_config.get("label", "")

        if orientation == "vertical":
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
            layout.setContentsMargins(
                0, 16, 0, 8
            )  # Increased top margin for heading, reduced bottom
            layout.setSpacing(4)  # Reduced spacing for tighter layout

            self.divider = QtWidgets.QFrame()
            self.divider.setMinimumHeight(2)
            self.divider.setMaximumHeight(2)
            self.divider.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
            )
            self.divider.show()

            if label_text:
                label_layout = QtWidgets.QHBoxLayout()
                label_layout.setContentsMargins(
                    0, 0, 0, 0
                )  # No extra margins for left alignment
                label_layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                label = QtWidgets.QLabel(label_text)
                label.setMinimumHeight(24)  # Increased for 16px font
                label.setMaximumHeight(28)  # Increased for 16px font
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

    def __init__(
        self, group_config: Dict[str, Any], storage: LocalConfigStorage, parent=None
    ):
        super().__init__(parent)

        self.group_config = group_config
        self.storage = storage
        self.group_id = self._generate_group_id()
        self.setting_widgets = {}
        self._loading = (
            False  # Flag to prevent valueChanged signals during programmatic loads
        )

        # Minimum size will be calculated based on content

        self.setup_ui()

    def _generate_group_id(self):
        """Generate a unique ID for this group based on name"""
        name = self.group_config.get("name", "group")
        return name.lower().replace(" ", "_").replace("-", "_")

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Group description
        description = self.group_config.get("description", "")
        if description:
            desc_label = QtWidgets.QLabel(description)
            desc_label.setWordWrap(True)
            # Use AYON color system for description
            colors = get_objected_colors()
            text_color = colors["font-disabled"].name()
            desc_label.setStyleSheet(
                f"color: {text_color}; font-style: italic; margin-bottom: 10px;"
            )
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
        settings = self.group_config.get("settings", [])

        # Start with first section
        current_section = QtWidgets.QVBoxLayout()
        current_section.setContentsMargins(8, 8, 8, 8)  # Consistent margins
        current_section.setSpacing(8)  # Consistent spacing
        current_section.setAlignment(QtCore.Qt.AlignTop)  # Align content to top
        self.main_layout.addLayout(current_section)

        i = 0
        while i < len(settings):
            setting = settings[i]
            # Use a more meaningful setting_id based on the label
            setting_label = (
                setting.get("label", "").lower().replace(" ", "_").replace("-", "_")
            )
            if setting_label:
                setting_id = setting_label
            else:
                setting_id = f"setting_{i}"
            log.debug(
                f"Generated setting_id: {setting_id} from label: {setting.get('label', '')}"
            )
            setting_type = setting.get("type", "string")

            # Check if this is a vertical divider
            if (
                setting_type == "divider"
                and setting.get("divider_orientation", "horizontal") == "vertical"
            ):
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
                i += 1
                continue

            # Check if this is a button and if there are consecutive buttons
            if setting_type == "button":
                # Collect consecutive button settings
                button_settings = []
                button_widgets = []
                j = i

                while (
                    j < len(settings) and settings[j].get("type", "string") == "button"
                ):
                    button_setting = settings[j]
                    button_setting_id = f"setting_{j}"

                    # Create the button widget
                    widget = self._create_setting_widget(
                        button_setting, button_setting_id
                    )
                    if widget:
                        self.setting_widgets[button_setting_id] = widget
                        button_widgets.append(widget)
                        button_settings.append(button_setting)

                    j += 1

                # Create horizontal layout for consecutive buttons
                if len(button_widgets) > 1:
                    button_row_layout = QtWidgets.QHBoxLayout()
                    button_row_layout.setContentsMargins(
                        0, 4, 0, 4
                    )  # Consistent vertical spacing
                    button_row_layout.setSpacing(8)  # Consistent horizontal spacing

                    for widget in button_widgets:
                        button_row_layout.addWidget(widget)

                    # Add stretch to push buttons to the left
                    button_row_layout.addStretch()
                    current_section.addLayout(button_row_layout)
                else:
                    # Single button - add directly
                    current_section.addWidget(button_widgets[0])

                i = j  # Skip processed button settings
                continue

            # Create the widget for non-button settings
            widget = self._create_setting_widget(setting, setting_id)
            if widget:
                self.setting_widgets[setting_id] = widget

                # Add to current section
                if setting_type == "divider":
                    # Horizontal divider - add directly
                    current_section.addWidget(widget)
                else:
                    # Regular setting - add with label
                    label_text = setting.get("label", f"Setting {i + 1}")
                    label = QtWidgets.QLabel(label_text)
                    tooltip = setting.get("tooltip", "")
                    if tooltip:
                        label.setToolTip(tooltip)
                        widget.setToolTip(tooltip)

                    # Create form row with consistent sizing
                    row_layout = QtWidgets.QHBoxLayout()
                    row_layout.setContentsMargins(
                        0, 4, 0, 4
                    )  # Consistent vertical spacing
                    row_layout.setSpacing(8)  # Consistent horizontal spacing

                    # Set proper minimum sizes to prevent cutoff
                    label.setMinimumWidth(120)  # Compact label width
                    label.setMinimumHeight(26)  # Increased height to match CSS
                    label.setMaximumHeight(30)  # Prevent oversized labels
                    label.setAlignment(
                        QtCore.Qt.AlignVCenter
                    )  # Center align labels vertically
                    widget.setMinimumHeight(26)  # Match CSS height
                    widget.setMaximumHeight(30)  # Fixed height to prevent cutoff
                    widget.setMinimumWidth(160)  # Compact minimum width

                    row_layout.addWidget(label)
                    row_layout.addWidget(widget)
                    current_section.addLayout(row_layout)

            i += 1

    def _create_setting_widget(self, setting, setting_id):
        """Create a setting widget based on type"""
        setting_type = setting.get("type", "string")

        if setting_type == "string":
            widget = StringSettingWidget(setting)
        elif setting_type == "boolean":
            widget = BooleanSettingWidget(setting)
        elif setting_type == "enum":
            widget = EnumSettingWidget(setting)
        elif setting_type == "button":
            widget = ButtonSettingWidget(setting)
        elif setting_type == "spinbox":
            widget = SpinBoxSettingWidget(setting)
        elif setting_type == "divider":
            widget = DividerSettingWidget(setting)
        else:
            widget = StringSettingWidget(setting)  # Fallback

        # Connect value change signal
        if hasattr(widget, "valueChanged"):
            widget.valueChanged.connect(
                lambda value, sid=setting_id: self._on_setting_changed(sid, value)
            )

        return widget

    def _on_setting_changed(self, setting_id: str, value):
        """Handle setting value change"""
        try:
            # Get the widget type from the setting widget
            setting_widget = self.setting_widgets.get(setting_id)
            setting_type = None
            if setting_widget and hasattr(setting_widget, "setting_config"):
                setting_type = setting_widget.setting_config.get("type")
            
            self.storage.set_setting_value(self.group_id, setting_id, value, setting_type)
            log.debug(f"Saved setting {self.group_id}.{setting_id} = {value} (type: {setting_type})")

            # Check if this setting has an action to trigger
            setting_widget = self.setting_widgets.get(setting_id)
            if setting_widget and hasattr(setting_widget, "setting_config"):
                action_name = setting_widget.setting_config.get("action_name")
                # Get action data from setting config (same as buttons do)
                action_data = setting_widget.setting_config.get("action_data", "")
                log.debug(f"Setting {setting_id} has action_name: {action_name}, action_data: {action_data}")
                if action_name:
                    # Get the full project config data for the action
                    full_config = self.storage.load_config()
                    project_config = full_config.get("projects", {}).get(self.storage.project_name, {})
                    
                    # Try to get current UI values if we have access to tab_widget
                    current_ui_values = {}
                    if hasattr(self, 'tab_widget'):
                        try:
                            for i in range(self.tab_widget.count()):
                                tab_widget = self.tab_widget.widget(i)
                                if hasattr(tab_widget, "get_widget_values"):
                                    tab_values = tab_widget.get_widget_values()
                                    current_ui_values.update(tab_values)
                        except Exception as e:
                            log.debug(f"Could not get current UI values: {e}")
                    
                    # Merge saved config with current UI values
                    user_settings = project_config.get("user_settings", {}).copy()
                    user_settings.update(current_ui_values)
                    
                    # Pass the full project config with all nested structures
                    config_data = project_config.copy()
                    config_data["user_settings"] = user_settings
                    config_data["_triggered_setting_value"] = value

                    # Execute the action directly (same as buttons do)
                    from ayon_local_config.plugin import execute_action_by_name
                    execute_action_by_name(action_name, config_data, action_data)

        except Exception as e:
            log.error(f"Failed to save setting {setting_id}: {e}")

    def _trigger_action(self, action_name: str, value):
        """Trigger an action when a setting value changes"""
        log.debug(f"Triggering action: {action_name} with value: {value}")
        try:
            # Get the full project config data for the action
            full_config = self.storage.load_config()
            project_config = full_config.get("projects", {}).get(self.storage.project_name, {})
            
            # Try to get current UI values if we have access to tab_widget
            current_ui_values = {}
            if hasattr(self, 'tab_widget'):
                try:
                    for i in range(self.tab_widget.count()):
                        tab_widget = self.tab_widget.widget(i)
                        if hasattr(tab_widget, "get_widget_values"):
                            tab_values = tab_widget.get_widget_values()
                            current_ui_values.update(tab_values)
                except Exception as e:
                    log.debug(f"Could not get current UI values: {e}")
                    # Continue with just saved config
            
            # Merge saved config with current UI values (UI values take precedence)
            user_settings = project_config.get("user_settings", {}).copy()
            user_settings.update(current_ui_values)
            
            # Pass the full project config with all nested structures
            config_data = project_config.copy()
            config_data["user_settings"] = user_settings

            # Add the specific setting value to the config data
            config_data["_triggered_setting_value"] = value

            # Execute the action
            from ayon_local_config.plugin import execute_action_by_name

            success = execute_action_by_name(action_name, config_data, "")

            if success:
                log.debug(
                    f"Successfully triggered action {action_name} on value change with value: {value}"
                )
            else:
                log.warning(f"Failed to trigger action {action_name} on value change")

        except Exception as e:
            log.error(f"Error triggering action {action_name}: {e}")

    def load_values(self):
        """Load values from storage"""
        group_config = self.storage.get_group_config(self.group_id)
        self._load_values_from_config_data(group_config)

    def load_values_from_config(self, config):
        """Load values from provided config data"""
        # Get the project-specific config for the current project
        project_config = config.get("projects", {}).get(self.storage.project_name, {})
        group_config = project_config.get(self.group_id, {})
        self._load_values_from_config_data(group_config)

    def _load_values_from_config_data(self, group_config):
        """Load values from group config data"""
        log.debug(f"Loading values from config: {group_config}")
        log.debug(f"Available widgets: {list(self.setting_widgets.keys())}")

        for setting_id, widget in self.setting_widgets.items():
            if setting_id in group_config:
                # Prevent signal emission while programmatically setting values
                setattr(widget, "_loading", True)
                try:
                    widget.set_value(group_config[setting_id])
                    log.debug(f"Set {setting_id} to: {group_config[setting_id]}")
                finally:
                    setattr(widget, "_loading", False)
            else:
                # If no saved value, ensure widget shows default value and save it to config
                if hasattr(widget, "set_value") and hasattr(widget, "setting_config"):
                    default_val = widget.setting_config.get("default_value", "")
                    if default_val:
                        setattr(widget, "_loading", True)
                        try:
                            widget.set_value(default_val)
                            log.debug(f"Set {setting_id} to default: {default_val}")
                            
                            # Save the default value to the config file
                            setting_type = widget.setting_config.get("type") if hasattr(widget, "setting_config") else None
                            self.storage.set_setting_value(self.group_id, setting_id, default_val, setting_type)
                            log.debug(f"Saved default value for {setting_id} to config: {default_val}")
                            
                            # Trigger action for default values to register environment variables
                            if hasattr(widget, "setting_config"):
                                action_name = widget.setting_config.get("action_name")
                                if action_name:
                                    log.debug(f"Triggering action for default value: {action_name} = {default_val}")
                                    self._trigger_action(action_name, default_val)
                        finally:
                            setattr(widget, "_loading", False)
                    else:
                        # Set empty string as default for settings without explicit defaults
                        setattr(widget, "_loading", True)
                        try:
                            widget.set_value("")
                            log.debug(f"Set {setting_id} to empty string default")
                            
                            # Save the empty string default to the config file
                            setting_type = widget.setting_config.get("type") if hasattr(widget, "setting_config") else None
                            self.storage.set_setting_value(self.group_id, setting_id, "", setting_type)
                            log.debug(f"Saved empty string default for {setting_id} to config")
                            
                            # Trigger action for empty string defaults to register environment variables
                            if hasattr(widget, "setting_config"):
                                action_name = widget.setting_config.get("action_name")
                                if action_name:
                                    log.debug(f"Triggering action for empty string default: {action_name} = ''")
                                    self._trigger_action(action_name, "")
                        finally:
                            setattr(widget, "_loading", False)

    def get_group_config(self):
        """Get current configuration values from all widgets in this group"""
        config = {}
        for setting_id, widget in self.setting_widgets.items():
            if hasattr(widget, "get_value"):
                config[setting_id] = widget.get_value()
        return {self.group_id: config}

    def _restore_defaults(self):
        """Restore all settings to their default values"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Restore Defaults",
            f"Are you sure you want to restore all settings in '{self.group_config.get('name', 'this group')}' to their default values?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # Get default values
            defaults = {}
            settings = self.group_config.get("settings", [])
            log.debug(f"Restoring defaults for {len(settings)} settings")

            for i, setting in enumerate(settings):
                # Use the same setting_id generation logic as in setup_ui
                setting_label = (
                    setting.get("label", "").lower().replace(" ", "_").replace("-", "_")
                )
                if setting_label:
                    setting_id = setting_label
                else:
                    setting_id = f"setting_{i}"
                setting_type = setting.get("type", "string")

                # Skip dividers and buttons as they don't have values
                if setting_type in ["divider", "button"]:
                    continue

                if setting_type == "string":
                    default_val = setting.get("default_value", "")
                    defaults[setting_id] = default_val
                    log.debug(f"Setting {setting_id} default to: {default_val}")
                elif setting_type == "boolean":
                    default_val = setting.get("default_value", "")
                    # Convert string to boolean - "true", "1", "yes" are truthy, everything else is falsy
                    bool_val = default_val.lower() in ("true", "1", "yes", "on")
                    defaults[setting_id] = bool_val
                    log.debug(f"Setting {setting_id} default to: {bool_val}")
                elif setting_type == "enum":
                    default_val = setting.get("default_value", "")
                    defaults[setting_id] = default_val
                    log.debug(f"Setting {setting_id} default to: {default_val}")
                elif setting_type == "spinbox":
                    default_val = setting.get("default_value", "0")
                    # Convert string to integer, default to 0 if invalid
                    try:
                        int_val = int(default_val)
                        defaults[setting_id] = int_val
                        log.debug(f"Setting {setting_id} default to: {int_val}")
                    except (ValueError, TypeError):
                        defaults[setting_id] = 0
                        log.debug(
                            f"Setting {setting_id} default to: 0 (invalid default)"
                        )

            log.debug(f"Restoring {len(defaults)} default values: {defaults}")

            # Save and apply defaults
            self.storage.reset_group_to_defaults(self.group_id, defaults)
            self.load_values()

            QtWidgets.QMessageBox.information(
                self,
                "Defaults Restored",
                "All settings have been restored to their default values.",
            )

    def get_widget_values(self):
        """Get current widget values for this group"""
        config = {}
        for setting_id, widget in self.setting_widgets.items():
            if hasattr(widget, "get_value"):
                config[setting_id] = widget.get_value()
        return config


class LocalConfigWindow(QtWidgets.QWidget):
    """Main window for local configuration"""

    def __init__(self, settings: Dict[str, Any], parent=None):
        super().__init__(parent)

        self.settings = settings
        self.storage = LocalConfigStorage()

        # Set window properties immediately (canonical Qt approach)
        project_name = self.storage.project_name
        menu_item_name = self.settings.get("menu_item_name", "User Config")
        title = f"{menu_item_name} - {project_name}" if project_name else menu_item_name
        self.setWindowTitle(title)
        # Minimum size will be calculated based on content after UI is built
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

        # Add project selector if enabled
        if self.settings.get("show_project_selector", True):
            self._create_project_selector(layout)

        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()

        # Add tabs for each enabled group
        log.debug(f"Settings structure: {self.settings}")
        groups = self.settings.get("tab_groups", [])
        log.debug(f"Found {len(groups)} groups")

        for group in groups:
            if not group.get("enabled", True):
                continue

            title = group.get("name", "Untitled Group")

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
        from ayon_local_config.style import clear_stylesheet_cache

        clear_stylesheet_cache()  # Force reload
        stylesheet = load_stylesheet()
        print(f"DEBUG: Loaded stylesheet length: {len(stylesheet)}")
        print(f"DEBUG: Stylesheet preview: {stylesheet[:200]}...")

        # Test with a simple hardcoded stylesheet to verify styling works
        test_stylesheet = """
        QWidget {
            background-color: #2C313A;
            color: #D3D8DE;
            font-family: "Noto Sans";
            font-size: 9pt;
        }
        QPushButton {
            background-color: #434a56;
            border: 1px solid #373D48;
            padding: 8px 16px;
            color: #D3D8DE;
        }
        QPushButton:hover {
            background-color: #4E5565;
        }
        QLineEdit {
            background-color: #21252B;
            border: 1px solid #373D48;
            padding: 6px 8px;
            color: #D3D8DE;
        }
        QTabBar::tab {
            background-color: #21252B;
            color: #99A3B2;
            border: 1px solid #373D48;
            padding: 6px 10px;
        }
        QTabBar::tab:selected {
            background-color: #434a56;
            color: #F0F2F5;
        }
        /* Divider styling */
        DividerSettingWidget {
            background: transparent;
            margin: 8px 0px;
            padding: 4px 0px;
        }
        DividerSettingWidget QFrame {
            background-color: #373D48;
            border: none;
            min-width: 2px;
            min-height: 2px;
        }
        DividerSettingWidget QLabel {
            color: #D3D8DE;
            font-weight: 600;
            font-size: 10px;
            margin: 2px 0px;
            padding: 2px 0px;
            background: transparent;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-height: 16px;
            max-height: 20px;
        }
        /* Horizontal divider styling */
        DividerSettingWidget[orientation="horizontal"] {
            margin: 12px 0px;
            padding: 6px 0px;
        }
        DividerSettingWidget[orientation="horizontal"] QFrame {
            background-color: #373D48;
            border: none;
            min-width: 100%;
            min-height: 1px;
            max-height: 1px;
        }
        /* Vertical divider styling */
        DividerSettingWidget[orientation="vertical"] {
            margin: 0px 8px;
            padding: 0px 4px;
            min-width: 1px;
            max-width: 1px;
        }
        DividerSettingWidget[orientation="vertical"] QFrame {
            background-color: #373D48;
            border: none;
            min-width: 1px;
            min-height: 100%;
            max-width: 1px;
        }
        """
        print("DEBUG: Applying test stylesheet...")
        self.setStyleSheet(test_stylesheet)

    def _load_values_after_show(self):
        """Load values after window is shown to prevent layout interference"""
        if hasattr(self, "status_bar"):
            self.status_bar.setText("Loading values...")

        # Load config once and pass to all widgets to avoid repeated file loading
        config = self.storage.load_config()

        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, "load_values_from_config"):
                tab_widget.load_values_from_config(config)
            elif hasattr(tab_widget, "load_values"):
                tab_widget.load_values()

        # Trigger actions for existing values to ensure environment variables are registered
        self._trigger_actions_for_existing_values(config)

        # Calculate and set content-based minimum size
        self._set_content_based_minimum_size()

        if hasattr(self, "status_bar"):
            self.status_bar.setText("Ready")

    def _trigger_actions_for_existing_values(self, config):
        """Trigger actions for existing values to ensure environment variables are registered"""
        try:
            # Get the current project config
            project_config = config.get("projects", {}).get(self.storage.project_name, {})
            user_settings = project_config.get("user_settings", {})
            
            # Trigger actions for settings that have action_name defined
            for setting_id, value in user_settings.items():
                # Find the setting definition to get the action_name
                for group in self.settings.get("tab_groups", []):
                    for setting in group.get("settings", []):
                        if setting.get("action_name") and setting.get("label"):
                            # Generate setting_id from label to match
                            setting_label = setting["label"]
                            generated_id = self._generate_setting_id(setting_label)
                            if generated_id == setting_id:
                                action_name = setting["action_name"]
                                if action_name:
                                    log.debug(f"Triggering action for existing value: {action_name} = {value}")
                                    self._trigger_action(action_name, value, config)
                                break
        except Exception as e:
            log.error(f"Error triggering actions for existing values: {e}")

    def _generate_setting_id(self, setting_label: str) -> str:
        """Generate a setting ID from a label"""
        if not setting_label:
            return ""
        return setting_label.lower().replace(" ", "_").replace("-", "_")

    def _trigger_action(self, action_name: str, value, config=None):
        """Trigger an action when a setting value changes"""
        log.debug(f"Triggering action: {action_name} with value: {value}")
        try:
            # Get the full project config data for the action
            if config is None:
                full_config = self.storage.load_config()
            else:
                full_config = config
            project_config = full_config.get("projects", {}).get(self.storage.project_name, {})
            
            # Try to get current UI values if we have access to tab_widget
            current_ui_values = {}
            if hasattr(self, 'tab_widget'):
                try:
                    for i in range(self.tab_widget.count()):
                        tab_widget = self.tab_widget.widget(i)
                        if hasattr(tab_widget, "get_widget_values"):
                            tab_values = tab_widget.get_widget_values()
                            current_ui_values.update(tab_values)
                except Exception as e:
                    log.debug(f"Could not get current UI values: {e}")
            
            # Merge saved config with current UI values (UI values take precedence)
            user_settings = project_config.get("user_settings", {}).copy()
            user_settings.update(current_ui_values)
            
            # Pass the full project config with all nested structures
            config_data = project_config.copy()
            config_data["user_settings"] = user_settings

            # Add the specific setting value to the config data
            config_data["_triggered_setting_value"] = value

            # Execute the action
            from ayon_local_config.plugin import execute_action_by_name

            success = execute_action_by_name(action_name, config_data, "")

            if success:
                log.debug(
                    f"Successfully triggered action {action_name} on value change with value: {value}"
                )
            else:
                log.warning(f"Failed to trigger action {action_name} on value change")

        except Exception as e:
            log.error(f"Error triggering action {action_name}: {e}")

    def _set_content_based_minimum_size(self):
        """Calculate and set minimum size based on content"""
        try:
            # Get the current size of the window
            current_size = self.size()
            log.debug(
                f"Current window size: {current_size.width()}x{current_size.height()}"
            )

            # Calculate the minimum size needed for content
            min_width = 0
            min_height = 0

            # Check each tab to find the maximum content requirements
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)

                # Force the tab widget to update its layout
                tab_widget.updateGeometry()

                # Get the preferred size for the tab content
                hint = None
                if hasattr(tab_widget, "sizeHint"):
                    hint = tab_widget.sizeHint()
                elif hasattr(tab_widget, "minimumSizeHint"):
                    hint = tab_widget.minimumSizeHint()

                if hint and hint.isValid():
                    min_width = max(min_width, hint.width())
                    min_height = max(min_height, hint.height())
                    log.debug(f"Tab {i} hint: {hint.width()}x{hint.height()}")
                else:
                    # Fallback: use the current size of the tab
                    tab_size = tab_widget.size()
                    min_width = max(min_width, tab_size.width())
                    min_height = max(min_height, tab_size.height())
                    log.debug(f"Tab {i} size: {tab_size.width()}x{tab_size.height()}")

            log.debug(f"Content requirements: {min_width}x{min_height}")

            # Add padding for window chrome (title bar, borders, footer, etc.)
            # and ensure reasonable minimums
            min_width = max(min_width + 100, 500)  # Add 100px for chrome, minimum 500px
            min_height = max(
                min_height + 150, 400
            )  # Add 150px for chrome, minimum 400px

            # Set the calculated minimum size
            self.setMinimumSize(min_width, min_height)

            # Calculate optimal size (content size + some extra space for comfort)
            optimal_width = min_width + 200  # Add extra space for comfort
            optimal_height = min_height + 100  # Reduced extra space for height

            # Resize to optimal size if current size is significantly different
            current_width = current_size.width()
            current_height = current_size.height()

            log.debug(f"Optimal size: {optimal_width}x{optimal_height}")
            log.debug(
                f"Size difference: width={abs(current_width - optimal_width)}, height={abs(current_height - optimal_height)}"
            )

            # Always resize to optimal size to ensure content-based sizing
            # This ensures the window is sized appropriately for its content
            self.resize(optimal_width, optimal_height)
            log.debug(
                f"Resized window to optimal content-based size: {optimal_width}x{optimal_height}"
            )

            log.debug(f"Set content-based minimum size: {min_width}x{min_height}")

        except Exception as e:
            log.error(f"Failed to calculate content-based minimum size: {e}")
            # Fallback to reasonable defaults
            self.setMinimumSize(500, 400)

    def recalculate_minimum_size(self):
        """Recalculate and update minimum size based on current content"""
        self._set_content_based_minimum_size()

    def force_resize_to_content(self):
        """Force resize the window to fit its content optimally"""
        self._set_content_based_minimum_size()

    def restore_defaults(self):
        """Restore all settings to their default values"""
        try:
            log.debug("Restoring default values...")
            self.status_bar.setText("Restoring defaults...")

            # Restore defaults for all groups
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, "_restore_defaults"):
                    tab_widget._restore_defaults()

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
            config_data = self.get_all_config_data()

            # Execute the action
            success = execute_action_by_name(action_name, config_data, "")

            if success:
                log.debug(f"Successfully executed action: {action_name}")
                self.status_bar.setText(f"Executed {action_name}")
            else:
                log.warning(f"Failed to execute action: {action_name}")
                self.status_bar.setText(f"Failed to execute {action_name}")

        except Exception as e:
            log.error(f"Error executing action {action_name}: {e}")
            self.status_bar.setText(f"Error executing {action_name}")

    def get_all_config_data(self):
        """Get current configuration data from all groups"""
        config_data = {}

        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, "get_group_config"):
                group_config = tab_widget.get_group_config()
                config_data.update(group_config)

        return config_data

    def _create_project_selector(self, layout):
        """Create project selector widget"""
        try:
            # Create project selector container
            project_selector_widget = QtWidgets.QWidget()
            project_selector_widget.setObjectName("project_selector")
            project_selector_layout = QtWidgets.QHBoxLayout(project_selector_widget)
            project_selector_layout.setContentsMargins(10, 10, 10, 10)
            project_selector_layout.setSpacing(10)

            # Project label
            project_label = QtWidgets.QLabel("Project:")
            project_label.setObjectName("project_label")
            project_selector_layout.addWidget(project_label)

            # Project dropdown
            self.project_combo = QtWidgets.QComboBox()
            self.project_combo.setObjectName("project_combo")
            self.project_combo.setMinimumWidth(200)

            # Get available projects
            available_projects = self.storage.get_available_projects()
            # Don't add "default" as fallback - let the user see empty list if no projects

            # Add projects to combo box
            for project in available_projects:
                self.project_combo.addItem(project)

            # Set current project - try last selected first, then current, then first available
            last_selected = self.storage.get_last_selected_project()
            current_project = self.storage.project_name

            selected_project = None
            if last_selected and last_selected in available_projects:
                selected_project = last_selected
                log.debug(f"Using last selected project: {last_selected}")
            elif current_project in available_projects:
                selected_project = current_project
                log.debug(f"Using current project: {current_project}")
            elif available_projects:
                selected_project = available_projects[0]
                log.debug(f"Using first available project: {available_projects[0]}")

            if selected_project:
                self.project_combo.setCurrentText(selected_project)
                # Update storage to match selection
                self.storage.project_name = selected_project
                # Save as last selected
                self.storage.set_last_selected_project(selected_project)
            else:
                # No projects available - this should be handled gracefully
                log.warning("No projects available for selection")

            # Connect signal
            self.project_combo.currentTextChanged.connect(self._on_project_changed)
            project_selector_layout.addWidget(self.project_combo)

            # Add stretch to push everything to the left
            project_selector_layout.addStretch()

            # Add to main layout
            layout.addWidget(project_selector_widget)

            log.debug(
                f"Created project selector with {len(available_projects)} projects"
            )

        except Exception as e:
            log.error(f"Failed to create project selector: {e}")

    def _on_project_changed(self, project_name):
        """Handle project selection change"""
        try:
            log.debug(f"Project changed to: {project_name}")

            # Update storage project name
            self.storage.project_name = project_name

            # Save as last selected project
            self.storage.set_last_selected_project(project_name)

            # Update window title
            menu_item_name = self.settings.get("menu_item_name", "User Config")
            self.setWindowTitle(f"{menu_item_name} - {project_name}")

            # Note: Project-specific environment variables are now handled by AYON Tools Environment Variables

            # Reload all values for the new project
            self._reload_settings_for_project(project_name)

            log.debug(f"Switched to project: {project_name}")

        except Exception as e:
            log.error(f"Failed to change project: {e}")

    def _reload_settings_for_project(self, project_name):
        """Reload settings for a specific project"""
        try:
            if hasattr(self, "status_bar"):
                self.status_bar.setText(f"Loading settings for {project_name}...")

            # Update storage project name first
            self.storage.project_name = project_name

            # Load config for the new project
            config = self.storage.load_config()

            # Update all tab widgets with the new project's settings
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, "load_values_from_config"):
                    tab_widget.load_values_from_config(config)
                elif hasattr(tab_widget, "load_values"):
                    tab_widget.load_values()

            if hasattr(self, "status_bar"):
                self.status_bar.setText(f"Loaded settings for {project_name}")

            log.debug(f"Successfully reloaded settings for project: {project_name}")

        except Exception as e:
            log.error(f"Failed to reload settings for project {project_name}: {e}")
            if hasattr(self, "status_bar"):
                self.status_bar.setText(f"Error loading settings for {project_name}")

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
        log.debug("Local Config window closed")
        # Don't delete the window, just hide it
        self.hide()
        event.ignore()  # Don't actually close, just hide
