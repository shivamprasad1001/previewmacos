"""
High-definition vector icon renderer for macOS Preview and Studio Pro interface.
Combines local SVG assets, built-in high-fidelity physical tool vectors, and
high-DPI PyQt6 renderers with light/dark theme tint support.
Licensed under ISC by Lucide contributors.
"""

import logging
import os
import re
from typing import Optional, Dict, Union
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF

# Directory resolution for icons
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_ICON_DIRS = [
    os.path.join(CURRENT_DIR, "assets", "icons"),
    os.path.join(os.path.dirname(CURRENT_DIR), "assets", "icons"),
]

# Exact mapping from logical names to Lucide / Studio icon SVG filenames
ICON_MAP: Dict[str, str] = {
    # Header bar
    "sidebar": "panel-left",
    "panel-left": "panel-left",
    "toolbar": "panel-top",
    "panel-top": "panel-top",
    "toggle-toolbar": "panel-top",
    "back": "chevron-left",
    "forward": "chevron-right",
    "arrow_left": "chevron-left",
    "arrow_right": "chevron-right",
    "chevron-left": "chevron-left",
    "chevron-right": "chevron-right",
    "open": "folder-open",
    "folder": "folder-open",
    "folder-open": "folder-open",
    "arrow_down": "chevron-down",
    "chevron-down": "chevron-down",
    "view": "eye",
    "mode_view": "eye",
    "eye": "eye",
    "edit": "pencil",
    "mode_edit": "pencil",
    "pencil": "pencil",
    "organize": "layout-grid",
    "mode_organize": "layout-grid",
    "contact_sheet": "layout-grid",
    "layout-grid": "layout-grid",
    "zoom_in": "zoom-in",
    "zoom-in": "zoom-in",
    "zoom_out": "zoom-out",
    "zoom-out": "zoom-out",
    "zoom_fit": "maximize-2",
    "rotate": "rotate-cw",
    "rotate_cw": "rotate-cw",
    "rotate_right": "rotate-cw",
    "rotate_left": "rotate-ccw",
    "rotate-cw": "rotate-cw",
    "rotate-ccw": "rotate-ccw",
    "markup": "pen-tool",
    "pen-tool": "pen-tool",
    "search": "search",
    "info": "info",
    "inspector": "info",
    "theme": "moon",
    "moon": "moon",
    "sun": "sun",

    # Edit & Markup tools
    "select": "box-select",
    "box-select": "box-select",
    "select_box": "box-select",
    "select_oval": "select_oval",
    "lasso": "lasso",
    "select_lasso": "lasso",
    "pointer": "mouse-pointer",
    "mouse-pointer": "mouse-pointer",
    "mouse-pointer-2": "mouse-pointer-2",
    "text_select": "text-cursor",
    "text-cursor": "text-cursor",
    "hand": "hand",
    "pan": "hand",
    "pen": "pen",
    "sketch": "pen",
    "text": "type",
    "type": "type",
    "underline": "underline",
    "strikethrough": "strikethrough",
    "note": "sticky-note",
    "sticky-note": "sticky-note",
    "shapes": "shapes",
    "redact": "redact",
    "square-dashed": "square-dashed",
    "sign": "signature",
    "signature": "signature",
    "image": "image",
    "image-plus": "image-plus",
    "overlay": "image-plus",
    "image_overlay": "image-plus",
    "crop": "crop",
    "color_adjust": "sliders-horizontal",
    "sliders-horizontal": "sliders-horizontal",
    "adjust": "sliders-horizontal",
    "size_adjust": "scaling",
    "scaling": "scaling",
    "maximize-2": "maximize-2",
    "maximize": "maximize",
    "minimize": "minimize",
    "fullscreen": "maximize",
    "more": "sliders-horizontal",
    "undo": "undo-2",
    "undo-2": "undo-2",
    "redo": "redo-2",
    "redo-2": "redo-2",

    # Realistic Everyday Physical Tools
    # 1. Chisel-Tip Highlighter
    "highlighter": "highlighter",
    "chisel_highlighter": "chisel-highlighter",
    "chisel-highlighter": "chisel-highlighter",
    "marker": "highlighter",
    "highlight": "highlighter",
    "felt_tip": "highlighter",
    "chisel": "chisel-highlighter",

    # 2. Fountain Pen / Ink Pen
    "fountain_pen": "fountain-pen",
    "fountain-pen": "fountain-pen",
    "ink_pen": "fountain-pen",
    "ink-pen": "fountain-pen",
    "nib": "fountain-pen",
    "calligraphy": "fountain-pen",
    "fountain_pen_vertical": "fountain-pen-vertical",
    "fountain-pen-vertical": "fountain-pen-vertical",

    # 3. Rubber Stamp
    "stamp": "rubber-stamp",
    "rubber_stamp": "rubber-stamp",
    "rubber-stamp": "rubber-stamp",
    "approved": "rubber-stamp",
    "seal": "rubber-stamp",
    "watermark": "rubber-stamp",

    # 4. Crop Shears / Scissors
    "scissors": "scissors",
    "shears": "scissors",
    "crop_shears": "crop-shears",
    "crop-shears": "crop-shears",
    "cut": "scissors",
    "snip": "scissors",

    # 5. Magnifying Loupe
    "loupe": "loupe",
    "magnifier": "loupe",
    "magnifying_loupe": "loupe",
    "magnifying-loupe": "loupe",
    "jeweler_loupe": "loupe",
    "zoom_loupe": "loupe",

    # 6. Adjustment Sliders / Hardware Equalizer
    "sliders": "sliders",
    "equalizer": "sliders",
    "adjustment_sliders": "sliders",
    "sliders-vertical": "sliders-vertical",
    "sliders_vertical": "sliders-vertical",
    "sliders_horizontal": "sliders-horizontal",
    "controls": "sliders",
    "tuning": "sliders",
    "faders": "sliders",

    # 7. Settings Gear
    "gear": "gear",
    "settings": "settings",
    "cog": "gear",
    "preferences": "gear",
    "options": "gear",
    "config": "gear",

    # 8. Standard Window Controls
    "window_close": "window-close",
    "window-close": "window-close",
    "traffic_close": "window-close",
    "traffic-close": "window-close",
    "win_close": "window-close",
    "window_minimize": "window-minimize",
    "window-minimize": "window-minimize",
    "traffic_minimize": "window-minimize",
    "traffic-minimize": "window-minimize",
    "win_minimize": "window-minimize",
    "window_maximize": "window-maximize",
    "window-maximize": "window-maximize",
    "traffic_maximize": "window-maximize",
    "traffic-maximize": "window-maximize",
    "win_maximize": "window-maximize",
    "window_fullscreen": "window-maximize",
    "window_restore": "window-restore",
    "window-restore": "window-restore",
    "restore": "window-restore",
    "unmaximize": "window-restore",

    # Shapes submenu
    "rectangle": "square",
    "square": "square",
    "oval": "circle",
    "circle": "circle",
    "line": "minus",
    "minus": "minus",
    "arrow": "arrow-right",
    "arrow-right": "arrow-right",
    "callout": "message-square",
    "message-square": "message-square",

    # Organize Mode
    "duplicate": "copy",
    "copy": "copy",
    "trash": "trash-2",
    "delete": "trash-2",
    "trash-2": "trash-2",
    "insert_blank": "file-plus-2",
    "file-plus-2": "file-plus-2",
    "insert_file": "file-up",
    "file-up": "file-up",
    "merge": "merge",
    "split": "split",
    "export": "share",
    "share": "share",
    "download": "download",

    # Sidebar & Inspector
    "thumbnails": "layout-list",
    "layout-list": "layout-list",
    "outline": "list-tree",
    "list-tree": "list-tree",
    "doc_proxy": "file-text",
    "file-text": "file-text",
    "format": "palette",
    "layers": "list",
    "palette": "palette",
    "list": "list",

    # Text formatting
    "bold": "bold",
    "italic": "italic",
    "align-left": "align-left",
    "align-center": "align-center",
    "align-right": "align-right",
    "line_style": "minus",
    "check": "check",
    "x": "x",
    "close": "x",
    "plus": "plus",
}


# Built-in high-fidelity vector definitions for realistic physical tools and studio controls.
# These provide standalone execution resilience even if filesystem assets are detached.
BUILTIN_SVGS: Dict[str, str] = {
    "panel-top": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<rect width="18" height="18" x="3" y="3" rx="2" />'
        '<path d="M3 9h18" />'
        '</svg>'
    ),
    # 1. Chisel-Tip Highlighter: angled chisel nib with facet line, collar, and barrel
    "highlighter": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m9.5 11.5 7.5-7.5a2.12 2.12 0 0 1 3 3l-7.5 7.5" />'
        '<line x1="14" y1="7" x2="17" y2="10" />'
        '<path d="m9.5 11.5-2.5 2.5 3 3 2.5-2.5z" />'
        '<path d="M7 14 3.5 17.5l1 3.5L8 19.5l2-2" />'
        '<line x1="3.5" y1="17.5" x2="8" y2="19.5" opacity="0.6" />'
        '<line x1="2" y1="22" x2="10" y2="22" stroke-width="2.2" opacity="0.5" />'
        '</svg>'
    ),
    "chisel-highlighter": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m9.5 11.5 7.5-7.5a2.12 2.12 0 0 1 3 3l-7.5 7.5" />'
        '<line x1="14" y1="7" x2="17" y2="10" />'
        '<path d="m9.5 11.5-2.5 2.5 3 3 2.5-2.5z" />'
        '<path d="M7 14 3.5 17.5l1 3.5L8 19.5l2-2" />'
        '<line x1="3.5" y1="17.5" x2="8" y2="19.5" opacity="0.6" />'
        '<line x1="2" y1="22" x2="10" y2="22" stroke-width="2.2" opacity="0.5" />'
        '</svg>'
    ),

    # 2. Fountain Pen / Ink Pen: classic nib with breather hole, ink slit, collar, and barrel
    "fountain-pen": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2.5 21.5c1-3.5 2.5-6.5 4.5-7.5l6-6 3 3-6 6c-1 2-4 3.5-7.5 4.5Z" />'
        '<circle cx="9" cy="15" r="1.2" fill="currentColor" />'
        '<line x1="2.5" y1="21.5" x2="8.2" y2="15.8" />'
        '<line x1="12" y1="7" x2="17" y2="12" />'
        '<path d="m13 8 5.5-5.5a1.5 1.5 0 0 1 2.1 0l.9.9a1.5 1.5 0 0 1 0 2.1L16 11" />'
        '</svg>'
    ),
    "fountain-pen-vertical": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 2C10 6 7 9 7 13c0 2 1.5 3 2.5 3.5v4.5h5v-4.5c1-.5 2.5-1.5 2.5-3.5 0-4-3-7-5-11z" />'
        '<circle cx="12" cy="11.5" r="1.3" fill="currentColor" />'
        '<line x1="12" y1="2" x2="12" y2="10.2" />'
        '<line x1="8.5" y1="16.5" x2="15.5" y2="16.5" />'
        '</svg>'
    ),

    # 3. Rubber Stamp: wooden ergonomic handle, base block, rubber cushion, dashed impression mark
    "rubber-stamp": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9.5 3a2.5 2.5 0 0 1 5 0c0 1.5-.8 2.6-1.5 3.5V9h-2V6.5C10.3 5.6 9.5 4.5 9.5 3z" />'
        '<rect x="3.5" y="9" width="17" height="4" rx="1.5" />'
        '<path d="M5 13v2.5a.5.5 0 0 0 .5.5h13a.5.5 0 0 0 .5-.5V13" />'
        '<line x1="3" y1="20.5" x2="21" y2="20.5" stroke-dasharray="2.5 1.5" stroke-width="2" />'
        '</svg>'
    ),

    # 4. Crop Shears / Scissors: twin finger loops, central pivot screw, sharp crossed blades
    "scissors": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="6" cy="18" r="3" />'
        '<circle cx="18" cy="18" r="3" />'
        '<path d="M8.2 15.8 20 4" />'
        '<path d="m15.8 15.8-3.8-3.8" />'
        '<path d="M10.2 10.2 4 4" />'
        '<circle cx="12" cy="12" r="1.4" fill="currentColor" />'
        '</svg>'
    ),
    "crop-shears": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="6" cy="18" r="3" />'
        '<circle cx="18" cy="18" r="3" />'
        '<path d="M8.2 15.8 20 4" />'
        '<path d="m15.8 15.8-3.8-3.8" />'
        '<path d="M10.2 10.2 4 4" />'
        '<line x1="14" y1="6" x2="19" y2="5" opacity="0.6" />'
        '<circle cx="12" cy="12" r="1.4" fill="currentColor" />'
        '</svg>'
    ),

    # 5. Handheld Optical Magnifying Loupe: double concentric bezel, glass reflection arc, knurled handle
    "loupe": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="10" cy="10" r="7.5" />'
        '<circle cx="10" cy="10" r="5" stroke-width="1.2" opacity="0.6" />'
        '<path d="M7 7.5a4 4 0 0 1 4.5-2" stroke-linecap="round" />'
        '<path d="m15.5 15.5 2 2" stroke-width="2.5" />'
        '<path d="m17.5 17.5 4 4" stroke-width="2.8" stroke-linecap="round" />'
        '</svg>'
    ),

    # 6. Precision Sliders / Hardware Equalizer: 3 vertical tracks with tactile fader thumb-blocks
    "sliders": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="5" y1="3" x2="5" y2="21" />'
        '<rect x="2.5" y="12" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="2.5" y1="14.5" x2="7.5" y2="14.5" stroke-width="1.5" />'
        '<line x1="12" y1="3" x2="12" y2="21" />'
        '<rect x="9.5" y="6" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="9.5" y1="8.5" x2="14.5" y2="8.5" stroke-width="1.5" />'
        '<line x1="19" y1="3" x2="19" y2="21" />'
        '<rect x="16.5" y="14" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="16.5" y1="16.5" x2="21.5" y2="16.5" stroke-width="1.5" />'
        '</svg>'
    ),
    "sliders-vertical": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="5" y1="3" x2="5" y2="21" />'
        '<rect x="2.5" y="12" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="2.5" y1="14.5" x2="7.5" y2="14.5" stroke-width="1.5" />'
        '<line x1="12" y1="3" x2="12" y2="21" />'
        '<rect x="9.5" y="6" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="9.5" y1="8.5" x2="14.5" y2="8.5" stroke-width="1.5" />'
        '<line x1="19" y1="3" x2="19" y2="21" />'
        '<rect x="16.5" y="14" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="16.5" y1="16.5" x2="21.5" y2="16.5" stroke-width="1.5" />'
        '</svg>'
    ),
    "sliders-horizontal": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="3" y1="5" x2="21" y2="5" />'
        '<rect x="12" y="2.5" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="14.5" y1="2.5" x2="14.5" y2="7.5" stroke-width="1.5" />'
        '<line x1="3" y1="12" x2="21" y2="12" />'
        '<rect x="6" y="9.5" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="8.5" y1="9.5" x2="8.5" y2="14.5" stroke-width="1.5" />'
        '<line x1="3" y1="19" x2="21" y2="19" />'
        '<rect x="14" y="16.5" width="5" height="5" rx="1" fill="currentColor" fill-opacity="0.15" />'
        '<line x1="16.5" y1="16.5" x2="16.5" y2="21.5" stroke-width="1.5" />'
        '</svg>'
    ),

    # 7. Precision Settings Mechanical Gear: 8-tooth mechanical cog with center bore
    "gear": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />'
        '</svg>'
    ),
    "settings": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />'
        '</svg>'
    ),

    # 8. Standard Window Controls (macOS / Studio controls)
    "window-close": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="18" y1="6" x2="6" y2="18" />'
        '<line x1="6" y1="6" x2="18" y2="18" />'
        '</svg>'
    ),
    "window-minimize": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="5" y1="12" x2="19" y2="12" />'
        '</svg>'
    ),
    "window-maximize": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="15 3 21 3 21 9" />'
        '<line x1="21" y1="3" x2="14" y2="10" />'
        '<polyline points="9 21 3 21 3 15" />'
        '<line x1="3" y1="21" x2="10" y2="14" />'
        '</svg>'
    ),
    "window-restore": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="4 14 10 14 10 20" />'
        '<polyline points="20 10 14 10 14 4" />'
        '<line x1="14" y1="10" x2="21" y2="3" />'
        '<line x1="3" y1="21" x2="10" y2="14" />'
        '</svg>'
    ),

    # Built-in fallbacks for standard Lucide symbols (used if disk directory is detached)
    "pencil": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" />'
        '</svg>'
    ),
    "pen": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />'
        '</svg>'
    ),
    "eye": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" />'
        '</svg>'
    ),
    "layout-grid": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<rect width="7" height="7" x="3" y="3" rx="1" /><rect width="7" height="7" x="14" y="3" rx="1" />'
        '<rect width="7" height="7" x="14" y="14" rx="1" /><rect width="7" height="7" x="3" y="14" rx="1" />'
        '</svg>'
    ),
    "folder-open": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2" />'
        '</svg>'
    ),
    "search": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />'
        '</svg>'
    ),
    "check": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="20 6 9 17 4 12" />'
        '</svg>'
    ),
    "x": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M18 6 6 18" /><path d="m6 6 12 12" />'
        '</svg>'
    ),
}


class Icon:
    """Unified high-definition icon provider for macOS Preview and Studio Pro."""

    _svg_cache: Dict[str, str] = {}
    _current_theme: str = "dark"

    THEME_COLORS: Dict[str, str] = {
        "dark": "#f5f5f7",
        "light": "#1c1c1e",
        "accent": "#0a84ff",
        "danger": "#ff453a",
        "success": "#30d158",
        "warning": "#ffd60a",
        "muted_dark": "#98989d",
        "muted_light": "#86868b",
    }

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Sets active studio theme ('dark' or 'light')."""
        cls._current_theme = "light" if theme.lower() in ("light", "white", "day") else "dark"

    @classmethod
    def get_theme_color(cls, theme: Optional[str] = None) -> str:
        """Returns the default foreground icon color for the active or given theme."""
        t = theme.lower() if theme else cls._current_theme
        return cls.THEME_COLORS.get(t, cls.THEME_COLORS["dark"])

    @classmethod
    def _find_svg_file(cls, name: str) -> Optional[str]:
        base_name = ICON_MAP.get(name, name)
        # Try mapped base_name, raw name, and hyphenated variations
        candidates = [base_name, name, base_name.replace("_", "-"), name.replace("_", "-")]
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            filename = f"{candidate}.svg"
            for d in ASSETS_ICON_DIRS:
                path = os.path.join(d, filename)
                if os.path.isfile(path):
                    return path
        return None

    @classmethod
    def _generate_fallback_svg(cls, name: str) -> str:
        """Generates a crisp geometric fallback SVG when an icon asset is not found."""
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="3" width="18" height="18" rx="4"/>'
            '<circle cx="12" cy="12" r="3"/>'
            '</svg>'
        )

    @classmethod
    def _load_svg_text(cls, name: str) -> str:
        base_name = ICON_MAP.get(name, name)
        if base_name in cls._svg_cache:
            return cls._svg_cache[base_name]
        if name in cls._svg_cache:
            return cls._svg_cache[name]

        # 1. Try file on disk
        file_path = cls._find_svg_file(name)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    cls._svg_cache[base_name] = content
                    return content
            except OSError:
                logging.getLogger(__name__).warning("Failed to read SVG icon %s", file_path, exc_info=True)

        # 2. Try embedded built-in SVGs (matches exact or normalized key)
        candidates = [
            base_name,
            name,
            base_name.replace("_", "-"),
            name.replace("_", "-"),
            base_name.replace("-", "_"),
            name.replace("-", "_"),
        ]
        for candidate in candidates:
            if candidate in BUILTIN_SVGS:
                content = BUILTIN_SVGS[candidate]
                cls._svg_cache[base_name] = content
                return content

        # 3. Dynamic generic fallback to ensure a clean vector shape is always returned
        fallback = cls._generate_fallback_svg(name)
        cls._svg_cache[base_name] = fallback
        return fallback

    @classmethod
    def pixmap(
        cls,
        name: str,
        color: Optional[Union[str, QColor]] = None,
        size: int = 18,
        stroke_width: float = 1.75,
        scale_factor: int = 2,
    ) -> QPixmap:
        """Renders an icon to high-DPI QPixmap with vector precision and theme tinting."""
        svg_text = cls._load_svg_text(name)

        # Resolve target color (supports str hex and QColor)
        if isinstance(color, QColor):
            target_color = color.name(QColor.NameFormat.HexArgb) if color.alpha() < 255 else color.name()
        elif color:
            target_color = str(color)
        else:
            target_color = cls.get_theme_color()

        if not svg_text:
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            return pix

        # Replace stroke="currentColor" and fill="currentColor"
        modified_svg = svg_text.replace("currentColor", target_color)
        if stroke_width != 2:
            modified_svg = re.sub(
                r'stroke-width="[^"]*"',
                f'stroke-width="{stroke_width}"',
                modified_svg,
            )

        # Set pixel dimensions for crisp rendering
        render_px = size * scale_factor
        if 'width="' in modified_svg:
            modified_svg = re.sub(
                r'width="[^"]*"', f'width="{render_px}"', modified_svg, count=1
            )
        if 'height="' in modified_svg:
            modified_svg = re.sub(
                r'height="[^"]*"', f'height="{render_px}"', modified_svg, count=1
            )

        pix = QPixmap()
        pix.loadFromData(modified_svg.encode("utf-8"))
        if not pix.isNull():
            pix.setDevicePixelRatio(float(scale_factor))
            return pix

        # Fallback empty pixmap
        blank = QPixmap(size, size)
        blank.fill(Qt.GlobalColor.transparent)
        return blank

    @classmethod
    def get(
        cls,
        name: str,
        color: Optional[Union[str, QColor]] = None,
        size: int = 18,
        stroke_width: float = 1.75,
        with_dropdown: bool = False,
    ) -> QIcon:
        """Returns a QIcon with the given Lucide/Studio symbol and style parameters."""
        base_pix = cls.pixmap(name, color=color, size=size, stroke_width=stroke_width)

        if not with_dropdown:
            return QIcon(base_pix)

        # Draw a small dropdown chevron on the bottom-right
        if isinstance(color, QColor):
            target_color = color.name(QColor.NameFormat.HexArgb) if color.alpha() < 255 else color.name()
        elif color:
            target_color = str(color)
        else:
            target_color = cls.get_theme_color()

        w = size + 8
        h = size
        composite = QPixmap(w * 2, h * 2)
        composite.fill(Qt.GlobalColor.transparent)

        painter = QPainter(composite)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Draw main icon at 2x
        painter.drawPixmap(
            0,
            0,
            base_pix.scaled(
                size * 2,
                size * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
        )

        # Draw triangle
        qcol = QColor(target_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(qcol))
        cx = float(w * 2 - 8)
        cy = float(h * 2 - 10)
        tri = QPolygonF([
            QPointF(cx - 5.0, cy),
            QPointF(cx + 5.0, cy),
            QPointF(cx, cy + 5.0)
        ])
        painter.drawPolygon(tri)
        painter.end()

        composite.setDevicePixelRatio(2.0)
        return QIcon(composite)

    @classmethod
    def create_dropdown_tool_icon(
        cls,
        name: str,
        color_hex: Optional[Union[str, QColor]] = None,
        width: int = 36,
        height: int = 22,
    ) -> QIcon:
        """Creates a sleek unified macOS tool icon with main symbol on left and dropdown chevron on right."""
        scale = 2
        pixmap = QPixmap(width * scale, height * scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        pixmap.setDevicePixelRatio(scale)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw main icon (18-20px glyph)
        main_size = min(20, height - 2) if height >= 20 else 16
        stroke_w = 1.75
        icon_pix = cls.pixmap(name, color=color_hex, size=main_size, stroke_width=stroke_w, scale_factor=scale)
        ix = 2
        iy = int((height - main_size) / 2)
        painter.drawPixmap(ix, iy, icon_pix)

        # Resolve color for chevron
        if isinstance(color_hex, QColor):
            color = color_hex
        elif color_hex:
            color = QColor(str(color_hex))
        else:
            color = QColor(cls.get_theme_color())

        # Draw subtle macOS downward chevron on the right (no separator line)
        chevron_color = QColor(color.red(), color.green(), color.blue(), 200)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(chevron_color))
        cx = float(width - 6.5)
        cy = float(height) / 2.0
        tri = QPolygonF([
            QPointF(cx - 2.8, cy - 1.8),
            QPointF(cx + 2.8, cy - 1.8),
            QPointF(cx, cy + 2.0),
        ])
        painter.drawPolygon(tri)
        painter.end()

        return QIcon(pixmap)


class MacIconFactory:
    """Backward-compatible wrapper mapping MacIconFactory calls to Icon."""

    @staticmethod
    def create_icon(
        name: str,
        color_hex: Optional[Union[str, QColor]] = None,
        size: int = 18,
        with_dropdown: bool = False,
    ) -> QIcon:
        return Icon.get(name, color=color_hex, size=size, with_dropdown=with_dropdown)

    @staticmethod
    def create_dropdown_tool_icon(
        name: str,
        color_hex: Optional[Union[str, QColor]] = None,
        width: int = 38,
        height: int = 32,
    ) -> QIcon:
        return Icon.create_dropdown_tool_icon(
            name, color_hex=color_hex, width=width, height=height
        )

    @staticmethod
    def get_icon(name: str, color_hex: Optional[Union[str, QColor]] = None, size: int = 18) -> QIcon:
        return Icon.get(name, color=color_hex, size=size)

    @staticmethod
    def pixmap(name: str, color_hex: Optional[Union[str, QColor]] = None, size: int = 18) -> QPixmap:
        return Icon.pixmap(name, color=color_hex, size=size)
