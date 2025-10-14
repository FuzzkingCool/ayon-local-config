# -*- coding: utf-8 -*-
import os
import copy
import json
import collections

from .color_defs import parse_color

current_dir = os.path.dirname(os.path.abspath(__file__))


class _Cache:
    stylesheet = None
    font_ids = None
    colors_data = None
    objected_colors = None


def get_style_image_path(image_name):
    """Get path to style image file."""
    # All filenames are lowered
    image_name = image_name.lower()
    # Make sure filename has png extension
    if not image_name.endswith(".png"):
        image_name += ".png"
    filepath = os.path.join(current_dir, "images", image_name)
    if os.path.exists(filepath):
        return filepath
    return None


def _get_colors_raw_data():
    """Read data file with stylesheet fill values."""
    data_path = os.path.join(current_dir, "data.json")
    with open(data_path, "r") as data_stream:
        data = json.load(data_stream)
    return data


def get_colors_data():
    """Only color data from stylesheet data."""
    if _Cache.colors_data is None:
        data = _get_colors_raw_data()
        color_data = data.get("color") or {}
        _Cache.colors_data = color_data
    return copy.deepcopy(_Cache.colors_data)


def _convert_color_values_to_objects(value):
    """Parse all string values in dictionary to Color definitions."""
    if isinstance(value, dict):
        output = {}
        for _key, _value in value.items():
            output[_key] = _convert_color_values_to_objects(_value)
        return output

    if not isinstance(value, str):
        raise TypeError((
            "Unexpected type in colors data '{}'. Expected 'str' or 'dict'."
        ).format(str(type(value))))
    return parse_color(value)


def get_objected_colors(*keys):
    """Colors parsed from stylesheet data into color definitions."""
    if _Cache.objected_colors is None:
        colors_data = get_colors_data()
        output = {}
        for key, value in colors_data.items():
            output[key] = _convert_color_values_to_objects(value)

        _Cache.objected_colors = output

    output = _Cache.objected_colors
    for key in keys:
        output = output[key]
    return copy.deepcopy(output)


def _load_stylesheet():
    """Load stylesheet and trigger all related callbacks."""
    style_path = os.path.join(current_dir, "style.css")
    with open(style_path, "r") as style_file:
        stylesheet = style_file.read()

    data = _get_colors_raw_data()
    print(f"DEBUG: Loaded color data keys: {list(data.keys())}")

    data_deque = collections.deque()
    for item in data.items():
        data_deque.append(item)

    fill_data = {}
    while data_deque:
        key, value = data_deque.popleft()
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                new_key = "{}:{}".format(key, sub_key)
                data_deque.append((new_key, sub_value))
            continue
        fill_data[key] = value
    
    print(f"DEBUG: Fill data keys: {list(fill_data.keys())[:10]}...")  # Show first 10 keys
    
    # Debug: Show some key-value pairs
    for key, value in list(fill_data.items())[:5]:
        print(f"DEBUG: Key '{key}' -> Value '{value}'")

    for key, value in fill_data.items():
        replacement_key = "{" + key + "}"
        stylesheet = stylesheet.replace(replacement_key, str(value))
    
    # Debug: Check if color replacement worked
    print(f"DEBUG: Color replacement - found {stylesheet.count('{color:')} unreplaced color variables")
    if stylesheet.count('{color:') > 0:
        print(f"DEBUG: First unreplaced variable: {stylesheet[stylesheet.find('{color:'):stylesheet.find('{color:')+20]}")
    
    return stylesheet


def _load_font():
    """Load and register fonts into Qt application."""
    from qtpy import QtGui

    # Check if font ids are still loaded
    if _Cache.font_ids is not None:
        for font_id in tuple(_Cache.font_ids):
            font_families = QtGui.QFontDatabase.applicationFontFamilies(
                font_id
            )
            # Reset font if font id is not available
            if not font_families:
                _Cache.font_ids = None
                break

    if _Cache.font_ids is None:
        _Cache.font_ids = []
        fonts_dirpath = os.path.join(current_dir, "fonts")
        font_dirs = []
        font_dirs.append(os.path.join(fonts_dirpath, "Noto_Sans"))
        font_dirs.append(os.path.join(
            fonts_dirpath,
            "Noto_Sans_Mono",
            "static",
            "NotoSansMono"
        ))

        loaded_fonts = []
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for filename in os.listdir(font_dir):
                    if os.path.splitext(filename)[1] not in [".ttf"]:
                        continue
                    full_path = os.path.join(font_dir, filename)
                    font_id = QtGui.QFontDatabase.addApplicationFont(full_path)
                    _Cache.font_ids.append(font_id)
                    font_families = QtGui.QFontDatabase.applicationFontFamilies(
                        font_id
                    )
                    loaded_fonts.extend(font_families)
        if loaded_fonts:
            print("Registered font families: {}".format(", ".join(loaded_fonts)))


def load_stylesheet():
    """Load and return AYON Qt stylesheet."""
    if _Cache.stylesheet is None:
        _Cache.stylesheet = _load_stylesheet()
    _load_font()
    return _Cache.stylesheet


def clear_stylesheet_cache():
    """Clear the stylesheet cache to force reload."""
    _Cache.stylesheet = None
    _Cache.colors_data = None
    _Cache.objected_colors = None