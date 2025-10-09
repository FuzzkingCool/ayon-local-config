# -*- coding: utf-8 -*-
"""Color definition utilities for AYON styling."""

from qtpy import QtGui


def parse_color(color_string):
    """Parse color string into QColor object."""
    if not color_string:
        return QtGui.QColor()
    
    # Handle hex colors
    if color_string.startswith('#'):
        return QtGui.QColor(color_string)
    
    # Handle rgb/rgba colors
    if color_string.startswith('rgb'):
        # Extract numbers from rgb(r,g,b) or rgba(r,g,b,a)
        import re
        numbers = re.findall(r'\d+', color_string)
        if len(numbers) >= 3:
            r = int(numbers[0])
            g = int(numbers[1])
            b = int(numbers[2])
            a = int(numbers[3]) if len(numbers) > 3 else 255
            return QtGui.QColor(r, g, b, a)
    
    # Handle hsl colors
    if color_string.startswith('hsl'):
        import re
        numbers = re.findall(r'(\d+(?:\.\d+)?)', color_string)
        if len(numbers) >= 3:
            h = float(numbers[0])
            s = float(numbers[1])
            l = float(numbers[2])
            return QtGui.QColor.fromHslF(h/360.0, s/100.0, l/100.0)
    
    # Fallback to QColor constructor
    return QtGui.QColor(color_string)
