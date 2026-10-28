"""
High-definition vector icon renderer for macOS Preview tools using Lucide icons.
All icons are loaded locally from assets/icons/ without network dependencies.
Licensed under ISC by Lucide contributors.
"""

import os
import re
from typing import Optional, Dict
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF

# Directory resolution for icons
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_ICON_DIRS = [
    os.path.join(CURRENT_DIR, "assets", "icons"),
    os.path.join(os.path.dirname(CURRENT_DIR), "assets", "icons"),
]

# Exact mapping from logical names to Lucide icon SVG filenames
ICON_MAP: Dict[str, str] = {
    # Header bar
    "sidebar": "panel-left",
    "panel-left": "panel-left",
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
    "highlighter": "highlighter",
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
    "loupe": "search",

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


class Icon:
    """Unified Lucide icon provider for TriviLabs Preview."""

    _svg_cache: Dict[str, str] = {}

    @classmethod
    def _find_svg_file(cls, name: str) -> Optional[str]:
        base_name = ICON_MAP.get(name, name)
        # Try both mapped name and raw name
        for candidate in [base_name, name]:
            filename = f"{candidate}.svg"
            for d in ASSETS_ICON_DIRS:
                path = os.path.join(d, filename)
                if os.path.isfile(path):
                    return path
        return None

    @classmethod
    def _load_svg_text(cls, name: str) -> Optional[str]:
        base_name = ICON_MAP.get(name, name)
        if base_name in cls._svg_cache:
            return cls._svg_cache[base_name]

        file_path = cls._find_svg_file(name)
        if not file_path:
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                cls._svg_cache[base_name] = content
                return content
        except Exception:
            return None

    @classmethod
    def pixmap(
        cls,
        name: str,
        color: Optional[str] = None,
        size: int = 18,
        stroke_width: float = 1.75,
        scale_factor: int = 2,
    ) -> QPixmap:
        """Renders an icon to high-DPI QPixmap with vector precision."""
        svg_text = cls._load_svg_text(name)
        target_color = color or "#f5f5f7"

        if not svg_text:
            # Fallback blank pixmap
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            return pix

        # Replace stroke="currentColor" and stroke-width
        modified_svg = svg_text.replace("currentColor", target_color)
        if stroke_width != 2:
            modified_svg = re.sub(
                r'stroke-width="[^"]*"',
                f'stroke-width="{stroke_width}"',
                modified_svg,
            )

        # Set pixel dimensions for crisp rendering
        render_px = size * scale_factor
        modified_svg = re.sub(
            r'width="[^"]*"', f'width="{render_px}"', modified_svg, count=1
        )
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
        color: Optional[str] = None,
        size: int = 18,
        stroke_width: float = 1.75,
        with_dropdown: bool = False,
    ) -> QIcon:
        """Returns a QIcon with the given Lucide symbol and style parameters."""
        base_pix = cls.pixmap(name, color=color, size=size, stroke_width=stroke_width)

        if not with_dropdown:
            return QIcon(base_pix)

        # Draw a small dropdown chevron on the bottom-right
        target_color = color or "#f5f5f7"
        w = size + 8
        h = size
        composite = QPixmap(w * 2, h * 2)
        composite.fill(Qt.GlobalColor.transparent)

        painter = QPainter(composite)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Draw main icon at 2x
        painter.drawPixmap(0, 0, base_pix.scaled(size * 2, size * 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

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
        color_hex: str = "#f5f5f7",
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

        # Draw subtle macOS downward chevron on the right (no separator line)
        color = QColor(color_hex)
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
        color_hex: str = "#f5f5f7",
        size: int = 18,
        with_dropdown: bool = False,
    ) -> QIcon:
        return Icon.get(name, color=color_hex, size=size, with_dropdown=with_dropdown)

    @staticmethod
    def create_dropdown_tool_icon(
        name: str,
        color_hex: str = "#f5f5f7",
        width: int = 38,
        height: int = 32,
    ) -> QIcon:
        return Icon.create_dropdown_tool_icon(
            name, color_hex=color_hex, width=width, height=height
        )
