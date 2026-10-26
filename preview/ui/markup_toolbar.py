"""
macOS style secondary Markup Toolbar providing sketch, highlighter, shapes, 
text, note, signature, color palettes, and crop actions.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QColorDialog, QMenu, 
    QSpinBox, QComboBox, QFontComboBox, QLabel, QButtonGroup
)
from PyQt6.QtGui import QColor, QAction, QIcon, QPixmap, QPainter, QBrush, QPen, QPolygonF
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPointF

from preview.core.annotations import AnnotationType
from preview.icons import MacIconFactory

class MarkupToolbar(QWidget):
    """macOS-authentic secondary markup toolbar."""

    tool_changed = pyqtSignal(AnnotationType)
    stroke_color_changed = pyqtSignal(QColor)
    stroke_width_changed = pyqtSignal(float)
    fill_color_changed = pyqtSignal(QColor)
    font_size_changed = pyqtSignal(int)
    font_family_changed = pyqtSignal(str)
    font_bold_changed = pyqtSignal(bool)
    font_italic_changed = pyqtSignal(bool)
    font_underline_changed = pyqtSignal(bool)
    text_align_changed = pyqtSignal(object)
    adjust_color_requested = pyqtSignal()
    adjust_size_requested = pyqtSignal()
    rotate_requested = pyqtSignal()
    rotate_selection_requested = pyqtSignal(int)
    crop_requested = pyqtSignal()
    signature_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("markupToolbar")
        self.setFixedHeight(38)

        self.current_tool: AnnotationType = AnnotationType.NONE
        self.stroke_color: QColor = QColor("#ff3b30")
        self.fill_color: QColor = QColor(Qt.GlobalColor.transparent)
        self.stroke_width: float = 3.0
        self.font_size: int = 16
        self._theme_col: str = "#f5f5f7"
        self._current_select_icon: str = "select"

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False)

        # 0. Pointer / Selection / Deselect
        self.pointer_btn = QToolButton()
        self.pointer_btn.setFixedSize(28, 28)
        self.pointer_btn.setCheckable(True)
        self.pointer_btn.setChecked(True)
        self.pointer_btn.setToolTip("Pointer / Select (Esc) - Learn more (F1)")
        self.pointer_btn.clicked.connect(self.unselect_all)
        self.btn_group.addButton(self.pointer_btn)
        layout.addWidget(self.pointer_btn)

        # 1. Selection Options Dropdown Button: [ Marquee | ▼ ]
        self.select_btn = QToolButton()
        self.select_btn.setFixedSize(36, 28)
        self.select_btn.setCheckable(True)
        self.select_btn.setToolTip("Selection Tools (Rectangular, Oval, Lasso) - Learn more (F1)")
        self.select_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_select_menu()
        self.btn_group.addButton(self.select_btn)
        layout.addWidget(self.select_btn)

        # 2. Shapes Dropdown Button: [ Shapes | ▼ ]
        self.shapes_btn = QToolButton()
        self.shapes_btn.setFixedSize(36, 28)
        self.shapes_btn.setCheckable(True)
        self.shapes_btn.setToolTip("Shapes (Rectangle, Oval, Line, Arrow) - Learn more (F1)")
        self.shapes_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_shapes_menu()
        layout.addWidget(self.shapes_btn)

        # 3. Sketch / Pen
        self.pen_btn = self._create_tool_button("pen", "Sketch / Pen - Learn more (F1)", AnnotationType.PEN)
        layout.addWidget(self.pen_btn)

        # 4. Highlighter
        self.highlighter_btn = self._create_tool_button("highlighter", "Highlighter - Learn more (F1)", AnnotationType.HIGHLIGHTER)
        layout.addWidget(self.highlighter_btn)

        # 5. Text Box
        self.text_btn = self._create_tool_button("text", "Text Box - Learn more (F1)", AnnotationType.TEXT)
        layout.addWidget(self.text_btn)

        # 6. Sticky Note
        self.note_btn = self._create_tool_button("note", "Sticky Note - Learn more (F1)", AnnotationType.NOTE)
        layout.addWidget(self.note_btn)

        # 6.5 Redaction Tool
        self.redact_btn = self._create_tool_button("redact", "Redact / Blackout Info - Learn more (F1)", AnnotationType.REDACT)
        layout.addWidget(self.redact_btn)

        # 7. Signature Tool
        self.sign_btn = QToolButton()
        self.sign_btn.setFixedSize(28, 28)
        self.sign_btn.setToolTip("Sign Document - Learn more (F1)")
        self.sign_btn.clicked.connect(self.signature_requested.emit)
        layout.addWidget(self.sign_btn)

        # Thin 1px separator
        sep = QWidget()
        sep.setFixedSize(1, 18)
        sep.setStyleSheet("background-color: rgba(128, 128, 128, 0.25);")
        layout.addWidget(sep)

        # 8. Border / Stroke Color Dropdown Button: [ Swatch | ▼ ]
        self.color_btn = QToolButton()
        self.color_btn.setFixedSize(36, 28)
        self.color_btn.setToolTip("Border / Stroke Color")
        self.color_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_stroke_color_menu()
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        layout.addWidget(self.color_btn)

        # 9. Fill Color Dropdown Button: [ Swatch | ▼ ]
        self.fill_btn = QToolButton()
        self.fill_btn.setFixedSize(36, 28)
        self.fill_btn.setToolTip("Fill Color")
        self.fill_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_fill_color_menu()
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)
        layout.addWidget(self.fill_btn)

        # 10. Line Style / Thickness Dropdown Button: [ Lines | ▼ ]
        self.width_btn = QToolButton()
        self.width_btn.setFixedSize(36, 28)
        self.width_btn.setToolTip("Line Style / Thickness (3 px)")
        self._setup_width_menu()
        layout.addWidget(self.width_btn)

        # 11. Font Controls
        self.font_spin = QSpinBox()
        self.font_spin.setFixedHeight(28)
        self.font_spin.setFixedWidth(50)
        self.font_spin.setRange(8, 72)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setToolTip("Font Size")
        self.font_spin.valueChanged.connect(self._on_font_size_changed)
        layout.addWidget(self.font_spin)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(28)
        self.font_combo.setFixedWidth(130)
        self.font_combo.setToolTip("Font Family")
        self.font_combo.currentFontChanged.connect(lambda f: self.font_family_changed.emit(f.family()))
        layout.addWidget(self.font_combo)

        # Bold (B) toggle button
        self.bold_btn = QToolButton()
        self.bold_btn.setFixedSize(26, 28)
        self.bold_btn.setCheckable(True)
        self.bold_btn.setText("B")
        self.bold_btn.setStyleSheet("font-weight: 700; font-size: 13px;")
        self.bold_btn.setToolTip("Bold (Ctrl+B)")
        self.bold_btn.toggled.connect(self.font_bold_changed.emit)
        layout.addWidget(self.bold_btn)

        # Italic (I) toggle button
        self.italic_btn = QToolButton()
        self.italic_btn.setFixedSize(26, 28)
        self.italic_btn.setCheckable(True)
        self.italic_btn.setText("I")
        self.italic_btn.setStyleSheet("font-style: italic; font-size: 13px; font-family: serif;")
        self.italic_btn.setToolTip("Italic (Ctrl+I)")
        self.italic_btn.toggled.connect(self.font_italic_changed.emit)
        layout.addWidget(self.italic_btn)

        # Underline (U) toggle button
        self.underline_btn = QToolButton()
        self.underline_btn.setFixedSize(26, 28)
        self.underline_btn.setCheckable(True)
        self.underline_btn.setText("U")
        self.underline_btn.setStyleSheet("text-decoration: underline; font-size: 13px;")
        self.underline_btn.setToolTip("Underline (Ctrl+U)")
        self.underline_btn.toggled.connect(self.font_underline_changed.emit)
        layout.addWidget(self.underline_btn)

        # Text Style / Alignment Dropdown Button: [ A | ▼ ]
        self.text_options_btn = QToolButton()
        self.text_options_btn.setFixedSize(36, 28)
        self.text_options_btn.setToolTip("Text Alignment & Quick Styles")
        self.text_options_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_text_options_menu()
        layout.addWidget(self.text_options_btn)

        layout.addStretch()

        # Thin 1px separator
        sep2 = QWidget()
        sep2.setFixedSize(1, 18)
        sep2.setStyleSheet("background-color: rgba(128, 128, 128, 0.25);")
        layout.addWidget(sep2)

        # 12. Adjust Color Action Button
        self.color_adjust_btn = QToolButton()
        self.color_adjust_btn.setFixedSize(28, 28)
        self.color_adjust_btn.setToolTip("Adjust Color (Ctrl+Alt+C) - Learn more (F1)")
        self.color_adjust_btn.clicked.connect(self.adjust_color_requested.emit)
        layout.addWidget(self.color_adjust_btn)

        # 13. Adjust Size Action Button
        self.size_adjust_btn = QToolButton()
        self.size_adjust_btn.setFixedSize(28, 28)
        self.size_adjust_btn.setToolTip("Adjust Size (Ctrl+Alt+S) - Learn more (F1)")
        self.size_adjust_btn.clicked.connect(self.adjust_size_requested.emit)
        layout.addWidget(self.size_adjust_btn)

        # 14. Rotate Left Action Button
        self.rotate_btn = QToolButton()
        self.rotate_btn.setFixedSize(28, 28)
        self.rotate_btn.setToolTip("Rotate Left 90° (Ctrl+L) - Learn more (F1)")
        self.rotate_btn.clicked.connect(self.rotate_requested.emit)
        layout.addWidget(self.rotate_btn)

        # 15. Crop Action Button
        self.crop_btn = QToolButton()
        self.crop_btn.setFixedSize(28, 28)
        self.crop_btn.setToolTip("Crop Selection (Ctrl+K) - Learn more (F1)")
        self.crop_btn.setEnabled(False)
        self.crop_btn.clicked.connect(self.crop_requested.emit)
        layout.addWidget(self.crop_btn)

        # 16. Rotate Selection Action Button
        self.rotate_selection_btn = QToolButton()
        self.rotate_selection_btn.setFixedSize(28, 28)
        self.rotate_selection_btn.setToolTip("Rotate Selection 90° (Ctrl+R) - Learn more (F1)")
        self.rotate_selection_btn.setEnabled(False)
        self.rotate_selection_btn.clicked.connect(lambda: self.rotate_selection_requested.emit(90))
        layout.addWidget(self.rotate_selection_btn)

        self._refresh_tool_icons()

    def _create_tool_button(self, icon_name: str, tooltip: str, tool_type: AnnotationType) -> QToolButton:
        btn = QToolButton()
        btn.setFixedSize(28, 28)
        btn.setCheckable(True)
        btn.setToolTip(tooltip)
        self.btn_group.addButton(btn)
        btn.clicked.connect(lambda checked, b=btn, t=tool_type: self._on_tool_clicked(t, b))
        return btn

    def _on_tool_clicked(self, tool_type: AnnotationType, btn: QToolButton):
        if self.current_tool == tool_type:
            # Clicking active tool button again toggles it off -> resets to Pointer!
            self.unselect_all()
        else:
            for b in self.btn_group.buttons():
                b.setChecked(b is btn)
            self.shapes_btn.setChecked(False)
            self.current_tool = tool_type
            self._refresh_tool_icons()
            self.tool_changed.emit(self.current_tool)

    def unselect_all(self):
        """Unchecks all markup tools and resets tool state to pointer mode."""
        for btn in self.btn_group.buttons():
            btn.setChecked(btn is self.pointer_btn)
        self.shapes_btn.setChecked(False)
        self.current_tool = AnnotationType.NONE
        self.crop_btn.setEnabled(False)
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)

    def update_icons(self, color_hex: str):
        """Re-renders all markup tool icons with the active theme color."""
        self._theme_col = color_hex
        self._refresh_tool_icons()
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)

    def _refresh_tool_icons(self):
        col = self._theme_col
        self.pointer_btn.setIcon(MacIconFactory.create_icon("pointer", "#ffffff" if self.pointer_btn.isChecked() else col, 16))
        
        # Segmented Dropdown Buttons with visible chevron down [ Icon | ▼ ]
        sel_icon = getattr(self, "_current_select_icon", "select")
        self.select_btn.setIcon(MacIconFactory.create_dropdown_tool_icon(sel_icon, "#ffffff" if self.select_btn.isChecked() else col, 28, 16))
        self.shapes_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("shapes", "#ffffff" if self.shapes_btn.isChecked() else col, 28, 16))
        self.width_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("line_style", col, 28, 16))
        self.text_options_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("text", col, 28, 16))

        # Standard tool buttons
        self.pen_btn.setIcon(MacIconFactory.create_icon("pen", "#ffffff" if self.pen_btn.isChecked() else col, 16))
        self.highlighter_btn.setIcon(MacIconFactory.create_icon("highlighter", "#ffffff" if self.highlighter_btn.isChecked() else col, 16))
        self.text_btn.setIcon(MacIconFactory.create_icon("text", "#ffffff" if self.text_btn.isChecked() else col, 16))
        self.note_btn.setIcon(MacIconFactory.create_icon("note", "#ffffff" if self.note_btn.isChecked() else col, 16))
        self.redact_btn.setIcon(MacIconFactory.create_icon("redact", "#ffffff" if self.redact_btn.isChecked() else col, 16))
        self.sign_btn.setIcon(MacIconFactory.create_icon("sign", col, 16))
        self.color_adjust_btn.setIcon(MacIconFactory.create_icon("color_adjust", col, 16))
        self.size_adjust_btn.setIcon(MacIconFactory.create_icon("size_adjust", col, 16))
        self.rotate_btn.setIcon(MacIconFactory.create_icon("rotate_left", col, 16))
        self.crop_btn.setIcon(MacIconFactory.create_icon("crop", col, 16))
        self.rotate_selection_btn.setIcon(MacIconFactory.create_icon("rotate_right", col, 16))

    def _setup_select_menu(self):
        menu = QMenu(self)
        
        rect_action = QAction("Rectangular Selection", self)
        rect_action.triggered.connect(lambda: self._select_selection_tool(AnnotationType.CROP_BOX, "Rectangular Selection", "select"))
        menu.addAction(rect_action)
        
        oval_action = QAction("Oval / Elliptical Selection", self)
        oval_action.triggered.connect(lambda: self._select_selection_tool(AnnotationType.CROP_OVAL, "Oval Selection", "select_oval"))
        menu.addAction(oval_action)
        
        lasso_action = QAction("Lasso Selection", self)
        lasso_action.triggered.connect(lambda: self._select_selection_tool(AnnotationType.CROP_LASSO, "Lasso Selection", "select_lasso"))
        menu.addAction(lasso_action)
        
        self.select_btn.setMenu(menu)

    def _select_selection_tool(self, tool_type: AnnotationType, label: str, icon_name: str = "select"):
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.shapes_btn.setChecked(False)
        self.select_btn.setChecked(True)
        self.select_btn.setToolTip(f"{label} (Active)")
        self.current_tool = tool_type
        self._current_select_icon = icon_name
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)

    def _setup_shapes_menu(self):
        menu = QMenu(self)
        
        shapes = [
            ("Rectangle", AnnotationType.RECTANGLE, None),
            ("Rounded Rectangle", AnnotationType.ROUNDED_RECT, None),
            ("Oval / Circle", AnnotationType.ELLIPSE, None),
            ("Line", AnnotationType.LINE, None),
            ("Arrow", AnnotationType.ARROW, None),
            ("Speech Bubble / Callout", AnnotationType.CALLOUT, "callout"),
            ("Magnifier Loupe", AnnotationType.LOUPE, "loupe"),
        ]
        
        for name, stype, icon_name in shapes:
            action = QAction(name, self)
            if icon_name:
                action.setIcon(MacIconFactory.create_icon(icon_name, self._theme_col, 16))
            action.triggered.connect(lambda _, t=stype: self._select_shape_tool(t))
            menu.addAction(action)

        self.shapes_btn.setMenu(menu)

    def _select_shape_tool(self, tool_type: AnnotationType):
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.shapes_btn.setChecked(True)
        self.current_tool = tool_type
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)

    def _setup_width_menu(self):
        menu = QMenu(self)
        for w in [1.0, 2.0, 3.0, 5.0, 8.0, 12.0]:
            action = QAction(f"{int(w)} px", self)
            action.triggered.connect(lambda _, val=w: self._set_width(val))
            menu.addAction(action)
        self.width_btn.setMenu(menu)
        self.width_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    def _set_width(self, val: float):
        self.stroke_width = val
        self.width_btn.setToolTip(f"Line Style / Thickness ({int(val)} px)")
        self.stroke_width_changed.emit(val)

    def _create_swatch_icon(self, color: QColor) -> QIcon:
        pix = QPixmap(14, 14)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(color))
        p.setPen(QPen(QColor(128, 128, 128, 90), 1))
        p.drawRoundedRect(QRectF(1, 1, 12, 12), 3, 3)
        p.end()
        return QIcon(pix)

    def _create_transparent_swatch_icon(self) -> QIcon:
        pix = QPixmap(14, 14)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#ff3b30"), 1.6))
        p.drawEllipse(QRectF(1, 1, 12, 12))
        p.drawLine(QPointF(3, 11), QPointF(11, 3))
        p.end()
        return QIcon(pix)

    def _setup_stroke_color_menu(self):
        menu = QMenu(self)
        presets = [
            ("Red", "#ff3b30"),
            ("Orange", "#ff9500"),
            ("Yellow", "#ffcc00"),
            ("Green", "#34c759"),
            ("Cyan", "#30b0c7"),
            ("Blue", "#007aff"),
            ("Purple", "#af52de"),
            ("Pink", "#ff2d55"),
            ("Black", "#000000"),
            ("Gray", "#8e8e93"),
            ("White", "#ffffff"),
        ]
        for name, hex_val in presets:
            col = QColor(hex_val)
            action = QAction(self._create_swatch_icon(col), name, self)
            action.triggered.connect(lambda _, c=col: self._set_stroke_color(c))
            menu.addAction(action)

        menu.addSeparator()
        custom_action = QAction("Show Colors...", self)
        custom_action.triggered.connect(self._choose_custom_stroke_color)
        menu.addAction(custom_action)

        self.color_btn.setMenu(menu)

    def _setup_fill_color_menu(self):
        menu = QMenu(self)
        transparent_action = QAction(self._create_transparent_swatch_icon(), "No Fill (Transparent)", self)
        transparent_action.triggered.connect(lambda: self._set_fill_color(QColor(Qt.GlobalColor.transparent)))
        menu.addAction(transparent_action)

        menu.addSeparator()
        presets = [
            ("Red", "#ff3b30"),
            ("Orange", "#ff9500"),
            ("Yellow", "#ffcc00"),
            ("Green", "#34c759"),
            ("Cyan", "#30b0c7"),
            ("Blue", "#007aff"),
            ("Purple", "#af52de"),
            ("Pink", "#ff2d55"),
            ("Black", "#000000"),
            ("Gray", "#8e8e93"),
            ("White", "#ffffff"),
        ]
        for name, hex_val in presets:
            col = QColor(hex_val)
            action = QAction(self._create_swatch_icon(col), name, self)
            action.triggered.connect(lambda _, c=col: self._set_fill_color(c))
            menu.addAction(action)

        menu.addSeparator()
        custom_action = QAction("Show Colors...", self)
        custom_action.triggered.connect(self._choose_custom_fill_color)
        menu.addAction(custom_action)

        self.fill_btn.setMenu(menu)

    def _choose_custom_stroke_color(self):
        col = QColorDialog.getColor(self.stroke_color, self, "Select Stroke Color")
        if col.isValid():
            self._set_stroke_color(col)

    def _choose_custom_fill_color(self):
        col = QColorDialog.getColor(self.fill_color, self, "Select Fill Color")
        if col.isValid():
            self._set_fill_color(col)

    def _set_stroke_color(self, col: QColor):
        self.stroke_color = col
        self._update_color_button_icon(self.color_btn, col)
        self.stroke_color_changed.emit(col)

    def _set_fill_color(self, col: QColor):
        self.fill_color = col
        self._update_color_button_icon(self.fill_btn, col, is_fill=True)
        self.fill_color_changed.emit(col)

    def _setup_text_options_menu(self):
        menu = QMenu(self)

        align_left = QAction("Align Left", self)
        align_left.triggered.connect(lambda: self.text_align_changed.emit(Qt.AlignmentFlag.AlignLeft))
        menu.addAction(align_left)

        align_center = QAction("Align Center", self)
        align_center.triggered.connect(lambda: self.text_align_changed.emit(Qt.AlignmentFlag.AlignHCenter))
        menu.addAction(align_center)

        align_right = QAction("Align Right", self)
        align_right.triggered.connect(lambda: self.text_align_changed.emit(Qt.AlignmentFlag.AlignRight))
        menu.addAction(align_right)

        menu.addSeparator()

        for sz in [10, 12, 14, 16, 20, 24, 32, 48, 64]:
            action = QAction(f"{sz} pt", self)
            action.triggered.connect(lambda _, s=sz: self.font_spin.setValue(s))
            menu.addAction(action)

        self.text_options_btn.setMenu(menu)

    def _update_color_button_icon(self, btn: QToolButton, color: QColor, is_fill: bool = False):
        pix = QPixmap(28, 16)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not is_fill:
            # Stroke / Border color button: hollow rounded square with distinct colored border
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawRoundedRect(QRectF(1.5, 1.5, 13.0, 13.0), 3, 3)
        else:
            if color.alpha() == 0:
                # Draw red diagonal slash for transparent (No Fill)
                p.setPen(QPen(QColor("#ff3b30"), 1.8))
                p.drawEllipse(QRectF(1.5, 1.5, 13.0, 13.0))
                p.drawLine(QPointF(3.5, 12.5), QPointF(12.5, 3.5))
            else:
                p.setBrush(QBrush(color))
                p.setPen(QPen(QColor(255, 255, 255, 160), 0.8))
                p.drawRoundedRect(QRectF(1.5, 1.5, 13.0, 13.0), 3, 3)

        # Subtle vertical separator line
        arrow_col = QColor(self._theme_col)
        p.setPen(QPen(QColor(arrow_col.red(), arrow_col.green(), arrow_col.blue(), 75), 1.0))
        p.drawLine(QPointF(17.5, 2.5), QPointF(17.5, 13.5))

        # Dropdown arrow triangle on the right
        cx = 23.5
        cy = 8.0
        tri = QPolygonF([
            QPointF(cx - 2.8, cy - 1.8),
            QPointF(cx + 2.8, cy - 1.8),
            QPointF(cx, cy + 2.0)
        ])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(arrow_col))
        p.drawPolygon(tri)

        p.end()
        btn.setIcon(QIcon(pix))
        btn.setIconSize(QSize(28, 16))

    def _on_font_size_changed(self, size: int):
        self.font_size = size
        self.font_size_changed.emit(size)

    def set_crop_enabled(self, enabled: bool):
        self.crop_btn.setEnabled(enabled)
        self.rotate_selection_btn.setEnabled(enabled)
        self.rotate_selection_btn.setToolTip("Rotate Selection 90° (Ctrl+R)" if enabled else "Rotate Selection (select an area first)")
