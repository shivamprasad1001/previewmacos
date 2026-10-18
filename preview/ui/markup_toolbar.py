"""
macOS style secondary Markup Toolbar providing sketch, highlighter, shapes, 
text, note, signature, color palettes, and crop actions.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QColorDialog, QMenu, 
    QSpinBox, QComboBox, QLabel, QButtonGroup
)
from PyQt6.QtGui import QColor, QAction, QIcon, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from preview.core.annotations import AnnotationType
from preview.icons import MacIconFactory

class MarkupToolbar(QWidget):
    """macOS-authentic secondary markup toolbar."""

    tool_changed = pyqtSignal(AnnotationType)
    stroke_color_changed = pyqtSignal(QColor)
    stroke_width_changed = pyqtSignal(float)
    fill_color_changed = pyqtSignal(QColor)
    font_size_changed = pyqtSignal(int)
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

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False)

        # 0. Pointer / Selection / Deselect
        self.pointer_btn = QToolButton()
        self.pointer_btn.setFixedSize(28, 28)
        self.pointer_btn.setCheckable(True)
        self.pointer_btn.setChecked(True)
        self.pointer_btn.setToolTip("Pointer / Select (Esc)")
        self.pointer_btn.clicked.connect(self.unselect_all)
        self.btn_group.addButton(self.pointer_btn)
        layout.addWidget(self.pointer_btn)

        # 1. Marquee / Selection / Crop box
        self.select_btn = self._create_tool_button("select", "Selection / Crop Box", AnnotationType.CROP_BOX)
        layout.addWidget(self.select_btn)

        # 2. Shapes Dropdown Button
        self.shapes_btn = QToolButton()
        self.shapes_btn.setFixedSize(28, 28)
        self.shapes_btn.setCheckable(True)
        self.shapes_btn.setToolTip("Shapes")
        self.shapes_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_shapes_menu()
        layout.addWidget(self.shapes_btn)

        # 3. Sketch / Pen
        self.pen_btn = self._create_tool_button("pen", "Sketch / Pen", AnnotationType.PEN)
        layout.addWidget(self.pen_btn)

        # 4. Highlighter
        self.highlighter_btn = self._create_tool_button("highlighter", "Highlighter", AnnotationType.HIGHLIGHTER)
        layout.addWidget(self.highlighter_btn)

        # 5. Text Box
        self.text_btn = self._create_tool_button("text", "Text Box", AnnotationType.TEXT)
        layout.addWidget(self.text_btn)

        # 6. Sticky Note
        self.note_btn = self._create_tool_button("note", "Sticky Note", AnnotationType.NOTE)
        layout.addWidget(self.note_btn)

        # 6.5 Redaction Tool
        self.redact_btn = self._create_tool_button("redact", "Redact / Blackout Info", AnnotationType.REDACT)
        layout.addWidget(self.redact_btn)

        # 7. Signature Tool
        self.sign_btn = QToolButton()
        self.sign_btn.setFixedSize(28, 28)
        self.sign_btn.setToolTip("Sign Document")
        self.sign_btn.clicked.connect(self.signature_requested.emit)
        layout.addWidget(self.sign_btn)

        # Thin 1px separator
        sep = QWidget()
        sep.setFixedSize(1, 18)
        sep.setStyleSheet("background-color: rgba(128, 128, 128, 0.25);")
        layout.addWidget(sep)

        # 8. Border / Stroke Color Picker
        self.color_btn = QToolButton()
        self.color_btn.setFixedSize(28, 28)
        self.color_btn.setToolTip("Border / Stroke Color")
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        self.color_btn.clicked.connect(self._choose_stroke_color)
        layout.addWidget(self.color_btn)

        # 9. Fill Color Picker
        self.fill_btn = QToolButton()
        self.fill_btn.setFixedSize(28, 28)
        self.fill_btn.setToolTip("Fill Color")
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)
        self.fill_btn.clicked.connect(self._choose_fill_color)
        layout.addWidget(self.fill_btn)

        # 10. Line Style / Thickness Selector
        self.width_btn = QToolButton()
        self.width_btn.setFixedSize(28, 28)
        self.width_btn.setToolTip("Line Style / Thickness (3 px)")
        self._setup_width_menu()
        layout.addWidget(self.width_btn)

        # 11. Font Size
        self.font_spin = QSpinBox()
        self.font_spin.setFixedHeight(28)
        self.font_spin.setRange(8, 72)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setToolTip("Font Size")
        self.font_spin.valueChanged.connect(self._on_font_size_changed)
        layout.addWidget(self.font_spin)

        layout.addStretch()

        # 12. Crop Action Button
        self.crop_btn = QToolButton()
        self.crop_btn.setFixedSize(28, 28)
        self.crop_btn.setToolTip("Crop Selection")
        self.crop_btn.setEnabled(False)
        self.crop_btn.clicked.connect(self.crop_requested.emit)
        layout.addWidget(self.crop_btn)

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
        self.select_btn.setIcon(MacIconFactory.create_icon("select", "#ffffff" if self.select_btn.isChecked() else col, 16))
        self.shapes_btn.setIcon(MacIconFactory.create_icon("shapes", "#ffffff" if self.shapes_btn.isChecked() else col, 16))
        self.pen_btn.setIcon(MacIconFactory.create_icon("pen", "#ffffff" if self.pen_btn.isChecked() else col, 16))
        self.highlighter_btn.setIcon(MacIconFactory.create_icon("highlighter", "#ffffff" if self.highlighter_btn.isChecked() else col, 16))
        self.text_btn.setIcon(MacIconFactory.create_icon("text", "#ffffff" if self.text_btn.isChecked() else col, 16))
        self.note_btn.setIcon(MacIconFactory.create_icon("note", "#ffffff" if self.note_btn.isChecked() else col, 16))
        self.redact_btn.setIcon(MacIconFactory.create_icon("redact", "#ffffff" if self.redact_btn.isChecked() else col, 16))
        self.sign_btn.setIcon(MacIconFactory.create_icon("sign", col, 16))
        self.width_btn.setIcon(MacIconFactory.create_icon("line_style", col, 16))
        self.crop_btn.setIcon(MacIconFactory.create_icon("crop", col, 16))

    def _setup_shapes_menu(self):
        menu = QMenu(self)
        
        shapes = [
            ("Rectangle", AnnotationType.RECTANGLE),
            ("Rounded Rectangle", AnnotationType.ROUNDED_RECT),
            ("Oval / Circle", AnnotationType.ELLIPSE),
            ("Line", AnnotationType.LINE),
            ("Arrow", AnnotationType.ARROW),
        ]
        
        for name, stype in shapes:
            action = QAction(name, self)
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

    def _choose_stroke_color(self):
        col = QColorDialog.getColor(self.stroke_color, self, "Select Stroke Color")
        if col.isValid():
            self.stroke_color = col
            self._update_color_button_icon(self.color_btn, col)
            self.stroke_color_changed.emit(col)

    def _choose_fill_color(self):
        menu = QMenu(self)
        transparent_action = QAction("No Fill (Transparent)", self)
        transparent_action.triggered.connect(lambda: self._set_fill_color(QColor(Qt.GlobalColor.transparent)))
        menu.addAction(transparent_action)
        
        custom_action = QAction("Choose Fill Color...", self)
        custom_action.triggered.connect(self._pick_custom_fill)
        menu.addAction(custom_action)

        self.fill_btn.setMenu(menu)
        self.fill_btn.showMenu()

    def _pick_custom_fill(self):
        col = QColorDialog.getColor(self.fill_color, self, "Select Fill Color")
        if col.isValid():
            self._set_fill_color(col)

    def _set_fill_color(self, col: QColor):
        self.fill_color = col
        self._update_color_button_icon(self.fill_btn, col, is_fill=True)
        self.fill_color_changed.emit(col)

    def _update_color_button_icon(self, btn: QToolButton, color: QColor, is_fill: bool = False):
        pix = QPixmap(18, 18)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not is_fill:
            # Stroke / Border color button: hollow rounded square with distinct colored border
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color, 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawRoundedRect(2, 2, 14, 14, 3, 3)
        else:
            if color.alpha() == 0:
                # Draw red diagonal slash for transparent (No Fill)
                p.setPen(QPen(QColor("#ff3b30"), 1.8))
                p.drawEllipse(1, 1, 16, 16)
                p.drawLine(3, 15, 15, 3)
            else:
                p.setBrush(QBrush(color))
                p.setPen(QPen(QColor(255, 255, 255, 160), 1))
                p.drawRoundedRect(1, 1, 16, 16, 4, 4)
        p.end()
        btn.setIcon(QIcon(pix))

    def _on_font_size_changed(self, size: int):
        self.font_size = size
        self.font_size_changed.emit(size)

    def set_crop_enabled(self, enabled: bool):
        self.crop_btn.setEnabled(enabled)
