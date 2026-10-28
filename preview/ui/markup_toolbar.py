"""
macOS style secondary Markup Toolbar providing sketch, highlighter, shapes, 
text, note, signature, color palettes, context-aware formatting, and crop actions.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QColorDialog, QMenu, 
    QSpinBox, QComboBox, QFontComboBox, QLabel, QButtonGroup, QFrame, 
    QStackedWidget, QSizePolicy
)
from PyQt6.QtGui import QColor, QAction, QIcon, QPixmap, QPainter, QBrush, QPen, QPolygonF, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPointF

from preview.core.annotations import AnnotationItem, AnnotationType
from preview.icons import MacIconFactory


class MarkupToolbar(QWidget):
    """
    macOS-authentic professional editing and markup toolbar with
    logically grouped segmented toolsets, responsive overflow support,
    and a dynamic context-aware formatting bar.
    """

    tool_changed = pyqtSignal(AnnotationType)
    stroke_color_changed = pyqtSignal(QColor)
    stroke_width_changed = pyqtSignal(float)
    fill_color_changed = pyqtSignal(QColor)
    font_size_changed = pyqtSignal(int)
    font_family_changed = pyqtSignal(str)
    font_bold_changed = pyqtSignal(bool)
    font_italic_changed = pyqtSignal(bool)
    font_underline_changed = pyqtSignal(bool)
    font_strikethrough_changed = pyqtSignal(bool)
    text_align_changed = pyqtSignal(object)
    adjust_color_requested = pyqtSignal()
    adjust_size_requested = pyqtSignal()
    rotate_requested = pyqtSignal()
    rotate_right_requested = pyqtSignal()
    rotate_selection_requested = pyqtSignal(int)
    crop_requested = pyqtSignal()
    signature_requested = pyqtSignal()
    image_overlay_requested = pyqtSignal()
    apply_redactions_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("markupToolbar")

        self.current_tool: AnnotationType = AnnotationType.NONE
        self.stroke_color: QColor = QColor("#ff3b30")
        self.fill_color: QColor = QColor(Qt.GlobalColor.transparent)
        self.stroke_width: float = 3.0
        self.font_size: int = 16
        self._theme_col: str = "#f5f5f7"
        self._current_select_icon: str = "box-select"
        self.selected_annotation: Optional[AnnotationItem] = None

        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.setFixedHeight(44)

        # -------------------------------------------------------------
        # Single Unified Tool Bar (44px height)
        # -------------------------------------------------------------
        self.primary_strip = QWidget()
        self.primary_strip.setObjectName("primaryStrip")
        self.primary_strip.setFixedHeight(44)
        self.strip_layout = QHBoxLayout(self.primary_strip)
        self.strip_layout.setContentsMargins(12, 5, 12, 5)
        self.strip_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False)

        # --- Group 1: Navigation ---
        self.pointer_btn = QToolButton()
        self.pointer_btn.setFixedSize(32, 32)
        self.pointer_btn.setIconSize(QSize(20, 20))
        self.pointer_btn.setCheckable(True)
        self.pointer_btn.setChecked(True)
        self.pointer_btn.setToolTip("Select / Pointer (Esc)")
        self.pointer_btn.setAccessibleName("Select / Pointer (Esc)")
        self.pointer_btn.setAccessibleDescription("Select tool")
        self.pointer_btn.clicked.connect(self.unselect_all)
        self.btn_group.addButton(self.pointer_btn)

        self.hand_btn = QToolButton()
        self.hand_btn.setFixedSize(32, 32)
        self.hand_btn.setIconSize(QSize(20, 20))
        self.hand_btn.setCheckable(True)
        self.hand_btn.setToolTip("Hand / Pan Document (Space+Drag)")
        self.hand_btn.setAccessibleName("Hand / Pan Document")
        self.hand_btn.setAccessibleDescription("Pan tool")
        self.hand_btn.clicked.connect(self._select_hand_tool)
        self.btn_group.addButton(self.hand_btn)

        self.group_selection = self._create_tool_group([self.pointer_btn, self.hand_btn])
        self.strip_layout.addWidget(self.group_selection)
        self.sep_1 = self._create_divider()
        self.strip_layout.addWidget(self.sep_1)

        # --- Group 2: Text Markup & Notes ---
        self.text_btn = self._create_tool_button("text", "Text Box (T)", AnnotationType.TEXT)
        self.highlighter_btn = self._create_tool_button("highlighter", "Highlighter (Shift+H)", AnnotationType.HIGHLIGHTER)
        self.underline_tool_btn = self._create_tool_button("underline", "Underline Text Markup (U)", AnnotationType.UNDERLINE)
        self.strikethrough_tool_btn = self._create_tool_button("strikethrough", "Strikethrough Text Markup (S)", AnnotationType.STRIKETHROUGH)
        self.strikethrough_btn = self.strikethrough_tool_btn
        self.note_btn = self._create_tool_button("note", "Sticky Note (N)", AnnotationType.NOTE)

        self.group_text = self._create_tool_group([
            self.text_btn, self.highlighter_btn, self.underline_tool_btn, 
            self.strikethrough_tool_btn, self.note_btn
        ])
        self.strip_layout.addWidget(self.group_text)
        self.sep_2 = self._create_divider()
        self.strip_layout.addWidget(self.sep_2)

        # --- Group 3: Drawing ---
        self.pen_btn = self._create_tool_button("pen", "Sketch / Pen (P)", AnnotationType.PEN)
        self.group_drawing = self._create_tool_group([self.pen_btn])
        self.strip_layout.addWidget(self.group_drawing)
        self.sep_3 = self._create_divider()
        self.strip_layout.addWidget(self.sep_3)

        # --- Group 4: Shapes ---
        self.shapes_btn = QToolButton()
        self.shapes_btn.setObjectName("shapesBtn")
        self.shapes_btn.setFixedSize(40, 32)
        self.shapes_btn.setIconSize(QSize(36, 22))
        self.shapes_btn.setCheckable(True)
        self.shapes_btn.setToolTip("Shapes (Rectangle, Oval, Line, Arrow) (Shift+S)")
        self.shapes_btn.setAccessibleName("Shapes (Shift+S)")
        self.shapes_btn.setAccessibleDescription("Shapes dropdown")
        self.shapes_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_shapes_menu()
        self.btn_group.addButton(self.shapes_btn)

        self.group_shapes = self._create_tool_group([self.shapes_btn])
        self.strip_layout.addWidget(self.group_shapes)
        self.sep_4 = self._create_divider()
        self.strip_layout.addWidget(self.sep_4)

        # --- Group 5: Privacy, Signature & Overlay ---
        self.redact_btn = self._create_tool_button("redact", "Redact / Blackout Info (Shift+R)", AnnotationType.REDACT)
        self.sign_btn = QToolButton()
        self.sign_btn.setFixedSize(32, 32)
        self.sign_btn.setIconSize(QSize(20, 20))
        self.sign_btn.setToolTip("Sign Document (K)")
        self.sign_btn.setAccessibleName("Sign Document (K)")
        self.sign_btn.setAccessibleDescription("Sign Document")
        self.sign_btn.clicked.connect(self.signature_requested.emit)

        self.image_overlay_btn = QToolButton()
        self.image_overlay_btn.setFixedSize(32, 32)
        self.image_overlay_btn.setIconSize(QSize(20, 20))
        self.image_overlay_btn.setToolTip("Add Image Overlay (Ctrl+Shift+I)")
        self.image_overlay_btn.setAccessibleName("Add Image Overlay (Ctrl+Shift+I)")
        self.image_overlay_btn.setAccessibleDescription("Add an image overlay onto the document")
        self.image_overlay_btn.clicked.connect(self.image_overlay_requested.emit)

        self.group_privacy = self._create_tool_group([self.redact_btn, self.sign_btn, self.image_overlay_btn])
        self.strip_layout.addWidget(self.group_privacy)
        self.sep_5 = self._create_divider()
        self.strip_layout.addWidget(self.sep_5)

        # --- Group 6: Selection, Crop & Image Editing ---
        self.select_btn = QToolButton()
        self.select_btn.setObjectName("selectBtn")
        self.select_btn.setFixedSize(40, 32)
        self.select_btn.setIconSize(QSize(36, 22))
        self.select_btn.setCheckable(True)
        self.select_btn.setToolTip("Selection Tools (Rectangular, Oval, Lasso)")
        self.select_btn.setAccessibleName("Selection Tools")
        self.select_btn.setAccessibleDescription("Selection tools dropdown")
        self.select_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_select_menu()
        self.btn_group.addButton(self.select_btn)

        self.crop_btn = QToolButton()
        self.crop_btn.setFixedSize(32, 32)
        self.crop_btn.setIconSize(QSize(20, 20))
        self.crop_btn.setToolTip("Crop Selection (Ctrl+K)")
        self.crop_btn.setAccessibleName("Crop Selection (Ctrl+K)")
        self.crop_btn.setEnabled(False)
        self.crop_btn.clicked.connect(self.crop_requested.emit)

        self.rotate_btn = QToolButton()
        self.rotate_btn.setFixedSize(32, 32)
        self.rotate_btn.setIconSize(QSize(20, 20))
        self.rotate_btn.setToolTip("Rotate Left 90° (Ctrl+L)")
        self.rotate_btn.setAccessibleName("Rotate Left 90° (Ctrl+L)")
        self.rotate_btn.clicked.connect(self.rotate_requested.emit)

        self.rotate_selection_btn = QToolButton()
        self.rotate_selection_btn.setFixedSize(32, 32)
        self.rotate_selection_btn.setIconSize(QSize(20, 20))
        self.rotate_selection_btn.setToolTip("Rotate Right (Ctrl+R)")
        self.rotate_selection_btn.setAccessibleName("Rotate Right (Ctrl+R)")
        self.rotate_selection_btn.setEnabled(True)
        self.rotate_selection_btn.clicked.connect(lambda: (self.rotate_selection_requested.emit(90), self.rotate_right_requested.emit()))
        self.rotate_right_btn = self.rotate_selection_btn

        self.color_adjust_btn = QToolButton()
        self.color_adjust_btn.setFixedSize(32, 32)
        self.color_adjust_btn.setIconSize(QSize(20, 20))
        self.color_adjust_btn.setToolTip("Adjust Color (Ctrl+Alt+C)")
        self.color_adjust_btn.setAccessibleName("Adjust Color (Ctrl+Alt+C)")
        self.color_adjust_btn.clicked.connect(self.adjust_color_requested.emit)

        self.size_adjust_btn = QToolButton()
        self.size_adjust_btn.setFixedSize(32, 32)
        self.size_adjust_btn.setIconSize(QSize(20, 20))
        self.size_adjust_btn.setToolTip("Adjust Size (Ctrl+Alt+S)")
        self.size_adjust_btn.setAccessibleName("Adjust Size (Ctrl+Alt+S)")
        self.size_adjust_btn.clicked.connect(self.adjust_size_requested.emit)

        self.group_image = self._create_tool_group([
            self.select_btn, self.crop_btn, self.rotate_btn, self.rotate_selection_btn,
            self.color_adjust_btn, self.size_adjust_btn
        ])
        self.strip_layout.addWidget(self.group_image)

        # Responsive overflow button (shown when space is tight)
        self.overflow_btn = QToolButton()
        self.overflow_btn.setObjectName("overflowBtn")
        self.overflow_btn.setFixedSize(38, 32)
        self.overflow_btn.setToolTip("More Tools (•••)")
        self.overflow_btn.setAccessibleName("More Tools")
        self.overflow_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_overflow_menu()
        self.overflow_btn.setVisible(False)
        self.strip_layout.addWidget(self.overflow_btn)

        # --- Group 7: History Actions ---
        self.undo_btn = QToolButton()
        self.undo_btn.setFixedSize(32, 32)
        self.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.undo_btn.setAccessibleName("Undo (Ctrl+Z)")
        self.undo_btn.clicked.connect(self.undo_requested.emit)

        self.redo_btn = QToolButton()
        self.redo_btn.setFixedSize(32, 32)
        self.redo_btn.setToolTip("Redo (Ctrl+Shift+Z)")
        self.redo_btn.setAccessibleName("Redo (Ctrl+Shift+Z)")
        self.redo_btn.clicked.connect(self.redo_requested.emit)

        self.group_history = self._create_tool_group([self.undo_btn, self.redo_btn])
        self.strip_layout.addWidget(self.group_history)

        self.sep_6 = self._create_divider()
        self.strip_layout.addWidget(self.sep_6)

        # --- Context-Aware Formatting Bar (Integrated Inline into the 44px Tool Bar) ---
        self.context_bar = QWidget()
        self.context_bar.setObjectName("contextFormattingBar")
        self.context_bar.setFixedHeight(34)
        c_layout = QHBoxLayout(self.context_bar)
        c_layout.setContentsMargins(4, 0, 4, 0)
        c_layout.setSpacing(8)

        self.context_stack = QStackedWidget()
        self.context_stack.setFixedHeight(32)

        # Sub-view 0: Shapes & Drawing Formatting (Border, Fill, Line Thickness)
        self.shape_format_widget = QWidget()
        sf_lay = QHBoxLayout(self.shape_format_widget)
        sf_lay.setContentsMargins(0, 0, 0, 0)
        sf_lay.setSpacing(8)

        sf_lbl = QLabel("Shape Format:")
        sf_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #98989d;")
        sf_lay.addWidget(sf_lbl)

        self.color_btn = QToolButton()
        self.color_btn.setFixedSize(36, 24)
        self.color_btn.setToolTip("Border / Stroke Color")
        self.color_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_stroke_color_menu()
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        sf_lay.addWidget(self.color_btn)

        self.fill_btn = QToolButton()
        self.fill_btn.setFixedSize(36, 24)
        self.fill_btn.setToolTip("Fill Color")
        self.fill_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_fill_color_menu()
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)
        sf_lay.addWidget(self.fill_btn)

        self.width_btn = QToolButton()
        self.width_btn.setFixedSize(36, 24)
        self.width_btn.setToolTip("Line Style / Thickness (3 px)")
        self._setup_width_menu()
        sf_lay.addWidget(self.width_btn)

        sf_lay.addStretch()
        self.context_stack.addWidget(self.shape_format_widget)

        # Sub-view 1: Typography Formatting (Font Family, Size, B/I/U/S, Align)
        self.text_format_widget = QWidget()
        tf_lay = QHBoxLayout(self.text_format_widget)
        tf_lay.setContentsMargins(0, 0, 0, 0)
        tf_lay.setSpacing(6)

        tf_lbl = QLabel("Text Format:")
        tf_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #98989d;")
        tf_lay.addWidget(tf_lbl)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(24)
        self.font_combo.setFixedWidth(130)
        self.font_combo.setToolTip("Font Family")
        self.font_combo.currentFontChanged.connect(lambda f: self.font_family_changed.emit(f.family()))
        tf_lay.addWidget(self.font_combo)

        self.font_spin = QSpinBox()
        self.font_spin.setFixedHeight(24)
        self.font_spin.setFixedWidth(48)
        self.font_spin.setRange(8, 72)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setToolTip("Font Size")
        self.font_spin.valueChanged.connect(self._on_font_size_changed)
        tf_lay.addWidget(self.font_spin)

        self.bold_btn = QToolButton()
        self.bold_btn.setFixedSize(24, 24)
        self.bold_btn.setCheckable(True)
        self.bold_btn.setText("B")
        self.bold_btn.setStyleSheet("font-weight: 700; font-size: 12px;")
        self.bold_btn.setToolTip("Bold (Ctrl+B)")
        self.bold_btn.toggled.connect(self.font_bold_changed.emit)
        tf_lay.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setFixedSize(24, 24)
        self.italic_btn.setCheckable(True)
        self.italic_btn.setText("I")
        self.italic_btn.setStyleSheet("font-style: italic; font-size: 12px; font-family: serif;")
        self.italic_btn.setToolTip("Italic (Ctrl+I)")
        self.italic_btn.toggled.connect(self.font_italic_changed.emit)
        tf_lay.addWidget(self.italic_btn)

        self.underline_btn = QToolButton()
        self.underline_btn.setFixedSize(24, 24)
        self.underline_btn.setCheckable(True)
        self.underline_btn.setText("U")
        self.underline_btn.setStyleSheet("text-decoration: underline; font-size: 12px;")
        self.underline_btn.setToolTip("Underline (Ctrl+U)")
        self.underline_btn.toggled.connect(self.font_underline_changed.emit)
        tf_lay.addWidget(self.underline_btn)

        self.strike_btn = QToolButton()
        self.strike_btn.setFixedSize(24, 24)
        self.strike_btn.setCheckable(True)
        self.strike_btn.setText("S")
        self.strike_btn.setStyleSheet("text-decoration: line-through; font-size: 12px;")
        self.strike_btn.setToolTip("Strikethrough")
        self.strike_btn.toggled.connect(self.font_strikethrough_changed.emit)
        tf_lay.addWidget(self.strike_btn)

        self.text_options_btn = QToolButton()
        self.text_options_btn.setFixedSize(32, 24)
        self.text_options_btn.setToolTip("Text Alignment & Presets")
        self.text_options_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_text_options_menu()
        tf_lay.addWidget(self.text_options_btn)

        tf_lay.addStretch()
        self.context_stack.addWidget(self.text_format_widget)

        # Sub-view 2: Selection Active Context
        self.selection_format_widget = QWidget()
        sel_lay = QHBoxLayout(self.selection_format_widget)
        sel_lay.setContentsMargins(0, 0, 0, 0)
        sel_lay.setSpacing(10)

        sel_lbl = QLabel("Selection Active:")
        sel_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #0a84ff;")
        sel_lay.addWidget(sel_lbl)

        crop_action_btn = QToolButton()
        crop_action_btn.setText("Apply Crop (Ctrl+K)")
        crop_action_btn.setIcon(MacIconFactory.create_icon("crop", "#ffffff", 14))
        crop_action_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        crop_action_btn.setFixedHeight(24)
        crop_action_btn.setMinimumWidth(135)
        crop_action_btn.setStyleSheet("background-color: #0a84ff; color: #ffffff; font-weight: 600; padding: 2px 10px; border-radius: 4px;")
        crop_action_btn.clicked.connect(self.crop_requested.emit)
        sel_lay.addWidget(crop_action_btn)

        rot_sel_btn = QToolButton()
        rot_sel_btn.setText("Rotate Selection (90°)")
        rot_sel_btn.setIcon(MacIconFactory.create_icon("rotate_right", self._theme_col, 14))
        rot_sel_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        rot_sel_btn.setFixedHeight(24)
        rot_sel_btn.setMinimumWidth(150)
        rot_sel_btn.setStyleSheet("padding: 2px 10px; border-radius: 4px;")
        rot_sel_btn.clicked.connect(lambda: self.rotate_selection_requested.emit(90))
        sel_lay.addWidget(rot_sel_btn)

        sel_lay.addStretch()
        self.context_stack.addWidget(self.selection_format_widget)

        # Sub-view 3: Redaction Pending Context
        self.redact_format_widget = QWidget()
        rf_lay = QHBoxLayout(self.redact_format_widget)
        rf_lay.setContentsMargins(0, 0, 0, 0)
        rf_lay.setSpacing(10)

        rf_badge = QLabel("Pending Redaction:")
        rf_badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #ff453a;")
        rf_lay.addWidget(rf_badge)

        rf_desc = QLabel("Mark sensitive areas with black boxes, then apply permanently.")
        rf_desc.setStyleSheet("font-size: 11px; color: #98989d;")
        rf_lay.addWidget(rf_desc)

        apply_redact_now = QToolButton()
        apply_redact_now.setText("Apply Redactions Permanently")
        apply_redact_now.setFixedHeight(24)
        apply_redact_now.setMinimumWidth(190)
        apply_redact_now.setStyleSheet("background-color: #ff3b30; color: #ffffff; font-weight: 600; padding: 2px 10px; border-radius: 4px;")
        apply_redact_now.clicked.connect(self.apply_redactions_requested.emit)
        rf_lay.addWidget(apply_redact_now)

        rf_lay.addStretch()
        self.context_stack.addWidget(self.redact_format_widget)

        # Sub-view 4: Default / General Quick Actions (Roomy, Never Truncated)
        self.default_format_widget = QWidget()
        def_lay = QHBoxLayout(self.default_format_widget)
        def_lay.setContentsMargins(0, 0, 0, 0)
        def_lay.setSpacing(10)

        self.def_lbl = QLabel("Contextual Actions:")
        self.def_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #98989d;")
        self.def_lbl.setVisible(False)
        def_lay.addWidget(self.def_lbl)

        self.btn_adj_col = QToolButton()
        self.btn_adj_col.setText("Adjust Color...")
        self.btn_adj_col.setAccessibleName("Adjust Color")
        self.btn_adj_col.setIcon(MacIconFactory.create_icon("color_adjust", self._theme_col, 16))
        self.btn_adj_col.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_adj_col.setFixedSize(28, 28)
        self.btn_adj_col.setToolTip("Adjust Color (Ctrl+Alt+C)")
        self.btn_adj_col.clicked.connect(self.adjust_color_requested.emit)
        def_lay.addWidget(self.btn_adj_col)

        self.btn_adj_sz = QToolButton()
        self.btn_adj_sz.setText("Adjust Size...")
        self.btn_adj_sz.setAccessibleName("Adjust Size")
        self.btn_adj_sz.setIcon(MacIconFactory.create_icon("size_adjust", self._theme_col, 16))
        self.btn_adj_sz.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_adj_sz.setFixedSize(28, 28)
        self.btn_adj_sz.setToolTip("Adjust Size (Ctrl+Alt+S)")
        self.btn_adj_sz.clicked.connect(self.adjust_size_requested.emit)
        def_lay.addWidget(self.btn_adj_sz)

        self.btn_rot = QToolButton()
        self.btn_rot.setText("Rotate Left 90°")
        self.btn_rot.setAccessibleName("Rotate Left")
        self.btn_rot.setIcon(MacIconFactory.create_icon("rotate_left", self._theme_col, 16))
        self.btn_rot.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_rot.setFixedSize(28, 28)
        self.btn_rot.setToolTip("Rotate Left 90° (Ctrl+L)")
        self.btn_rot.clicked.connect(self.rotate_requested.emit)
        def_lay.addWidget(self.btn_rot)

        def_lay.addStretch()
        self.context_stack.addWidget(self.default_format_widget)

        c_layout.addWidget(self.context_stack)
        self.strip_layout.addWidget(self.context_bar)
        self.strip_layout.addStretch(1)

        root_layout.addWidget(self.primary_strip)

        self._refresh_tool_icons()
        self.update_context_row()
        self.handle_resize(self.width())

    def _create_tool_group(self, buttons: List[QToolButton]) -> QFrame:
        """Encapsulates buttons into a unified macOS pill segmented group."""
        group_frame = QFrame()
        group_frame.setObjectName("markupGroup")
        group_frame.setFixedHeight(34)
        group_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        glay = QHBoxLayout(group_frame)
        glay.setContentsMargins(1, 1, 1, 1)
        glay.setSpacing(2)
        for b in buttons:
            glay.addWidget(b)
        return group_frame

    def _create_divider(self) -> QWidget:
        """Subtle 1px vertical separator line placed only between logical groups."""
        sep = QFrame()
        sep.setObjectName("markupGroupSeparator")
        sep.setFixedSize(1, 20)
        sep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return sep

    def _create_tool_button(self, icon_name: str, tooltip: str, tool_type: AnnotationType) -> QToolButton:
        btn = QToolButton()
        btn.setFixedSize(32, 32)
        btn.setIconSize(QSize(20, 20))
        btn.setCheckable(True)
        btn.setToolTip(tooltip)
        btn.setAccessibleName(tooltip)
        btn.setAccessibleDescription(tooltip)
        btn.clicked.connect(lambda: self._on_tool_clicked(btn, tool_type))
        self.btn_group.addButton(btn)
        return btn

    def _setup_overflow_menu(self):
        """Constructs overflow menu for secondary actions when window space is constrained."""
        menu = QMenu(self)

        crop_act = QAction("Crop Selection", self)
        crop_act.setShortcut("Ctrl+K")
        crop_act.setIcon(MacIconFactory.create_icon("crop", self._theme_col, 16))
        crop_act.triggered.connect(self.crop_requested.emit)
        menu.addAction(crop_act)
        self._overflow_crop_act = crop_act

        rot_act = QAction("Rotate Left 90°", self)
        rot_act.setShortcut("Ctrl+L")
        rot_act.setIcon(MacIconFactory.create_icon("rotate_left", self._theme_col, 16))
        rot_act.triggered.connect(self.rotate_requested.emit)
        menu.addAction(rot_act)

        rot_sel_act = QAction("Rotate Selection 90°", self)
        rot_sel_act.setShortcut("Ctrl+R")
        rot_sel_act.setIcon(MacIconFactory.create_icon("rotate_right", self._theme_col, 16))
        rot_sel_act.triggered.connect(lambda: self.rotate_selection_requested.emit(90))
        menu.addAction(rot_sel_act)
        self._overflow_rot_sel_act = rot_sel_act

        menu.addSeparator()

        col_act = QAction("Adjust Color...", self)
        col_act.setShortcut("Ctrl+Alt+C")
        col_act.setIcon(MacIconFactory.create_icon("color_adjust", self._theme_col, 16))
        col_act.triggered.connect(self.adjust_color_requested.emit)
        menu.addAction(col_act)

        sz_act = QAction("Adjust Size...", self)
        sz_act.setShortcut("Ctrl+Alt+S")
        sz_act.setIcon(MacIconFactory.create_icon("size_adjust", self._theme_col, 16))
        sz_act.triggered.connect(self.adjust_size_requested.emit)
        menu.addAction(sz_act)

        menu.addSeparator()

        overlay_act = QAction("Add Image Overlay...", self)
        overlay_act.setShortcut("Ctrl+Shift+I")
        overlay_act.setIcon(MacIconFactory.create_icon("image_overlay", self._theme_col, 16))
        overlay_act.triggered.connect(self.image_overlay_requested.emit)
        menu.addAction(overlay_act)

        self.overflow_btn.setMenu(menu)

    def showEvent(self, event):
        super().showEvent(event)
        self.handle_resize(self.width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.handle_resize(event.size().width())

    def handle_resize(self, width: int):
        """Adapts toolbar layout dynamically when window width changes."""
        if width < 940:
            self.group_image.setVisible(False)
            self.overflow_btn.setVisible(True)
        else:
            self.group_image.setVisible(True)
            self.overflow_btn.setVisible(False)

        # Contextual actions: switch to icon-only with tooltips when space is tight (< 1350px)
        # to ensure labels are NEVER truncated. Show full labels when space is ample.
        is_tight = (width < 1350)
        if hasattr(self, "def_lbl"):
            self.def_lbl.setVisible(not is_tight)
        for btn, full_text in [
            (getattr(self, "btn_adj_col", None), "Adjust Color..."),
            (getattr(self, "btn_adj_sz", None), "Adjust Size..."),
            (getattr(self, "btn_rot", None), "Rotate Left 90°"),
        ]:
            if btn:
                if is_tight:
                    btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                    btn.setFixedSize(28, 28)
                else:
                    btn.setText(full_text)
                    btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                    btn.setFixedHeight(28)
                    btn.setMinimumWidth(115)
                    btn.setMaximumWidth(160)

    def _select_hand_tool(self):
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.hand_btn.setChecked(True)
        self.current_tool = AnnotationType.HAND
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def _on_tool_clicked(self, clicked_btn: QToolButton, tool_type: AnnotationType):
        if not clicked_btn.isChecked():
            self.unselect_all()
            return

        for b in self.btn_group.buttons():
            if b is not clicked_btn:
                b.setChecked(False)
        clicked_btn.setChecked(True)
        self.current_tool = tool_type
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def unselect_all(self):
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.pointer_btn.setChecked(True)
        self.current_tool = AnnotationType.NONE
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def set_selected_annotation(self, annot: Optional[AnnotationItem]):
        self.selected_annotation = annot
        self.update_context_row()

    def update_context_row(self):
        """Swaps context formatting sub-view based on selection or active tool."""
        if self.selected_annotation:
            t = self.selected_annotation.item_type
            if t in (AnnotationType.TEXT, AnnotationType.NOTE, AnnotationType.CALLOUT):
                self.context_stack.setCurrentIndex(1)
                self.font_combo.setCurrentFont(QFont(self.selected_annotation.font_family))
                self.font_spin.setValue(self.selected_annotation.font_size)
                return
            elif t in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, AnnotationType.ELLIPSE,
                       AnnotationType.LINE, AnnotationType.ARROW, AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                self.context_stack.setCurrentIndex(0)
                self._update_color_button_icon(self.color_btn, self.selected_annotation.stroke_color)
                self._update_color_button_icon(self.fill_btn, self.selected_annotation.fill_color, is_fill=True)
                return
            elif t == AnnotationType.REDACT:
                self.context_stack.setCurrentIndex(3)
                return

        # Based on active tool
        if self.current_tool in (AnnotationType.TEXT, AnnotationType.NOTE, AnnotationType.UNDERLINE, AnnotationType.STRIKETHROUGH):
            self.context_stack.setCurrentIndex(1)
        elif self.current_tool in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, AnnotationType.ELLIPSE,
                                   AnnotationType.LINE, AnnotationType.ARROW, AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
            self.context_stack.setCurrentIndex(0)
        elif self.current_tool in (AnnotationType.CROP_BOX, AnnotationType.CROP_OVAL, AnnotationType.CROP_LASSO):
            self.context_stack.setCurrentIndex(2)
        elif self.current_tool == AnnotationType.REDACT:
            self.context_stack.setCurrentIndex(3)
        else:
            self.context_stack.setCurrentIndex(4)

    def _setup_select_menu(self):
        menu = QMenu(self)
        tools = [
            ("Rectangular Selection", AnnotationType.CROP_BOX, "box-select"),
            ("Oval Selection", AnnotationType.CROP_OVAL, "select_oval"),
            ("Lasso Selection", AnnotationType.CROP_LASSO, "lasso")
        ]
        for name, atype, icon_name in tools:
            action = QAction(name, self)
            action.setIcon(MacIconFactory.create_icon(icon_name, self._theme_col, 16))
            action.triggered.connect(lambda _, t=atype, iname=icon_name: self._select_crop_tool(t, iname))
            menu.addAction(action)
        self.select_btn.setMenu(menu)

    def _select_crop_tool(self, tool_type: AnnotationType, icon_name: str):
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.select_btn.setChecked(True)
        self.current_tool = tool_type
        self._current_select_icon = icon_name
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def _setup_shapes_menu(self):
        menu = QMenu(self)
        shapes = [
            ("Rectangle", AnnotationType.RECTANGLE, "square"),
            ("Rounded Rectangle", AnnotationType.ROUNDED_RECT, "shapes"),
            ("Oval", AnnotationType.ELLIPSE, "circle"),
            ("Line", AnnotationType.LINE, "minus"),
            ("Arrow", AnnotationType.ARROW, "arrow_right"),
            ("Callout Bubble", AnnotationType.CALLOUT, "callout"),
            ("Magnifier (Loupe)", AnnotationType.LOUPE, "loupe"),
        ]
        for name, stype, icon_name in shapes:
            action = QAction(name, self)
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
        self.update_context_row()

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
            ("Red", "#ff3b30"), ("Orange", "#ff9500"), ("Yellow", "#ffcc00"),
            ("Green", "#34c759"), ("Cyan", "#30b0c7"), ("Blue", "#007aff"),
            ("Purple", "#af52de"), ("Pink", "#ff2d55"), ("Black", "#000000"),
            ("Gray", "#8e8e93"), ("White", "#ffffff"),
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
            ("Red", "#ff3b30"), ("Orange", "#ff9500"), ("Yellow", "#ffcc00"),
            ("Green", "#34c759"), ("Cyan", "#30b0c7"), ("Blue", "#007aff"),
            ("Purple", "#af52de"), ("Pink", "#ff2d55"), ("Black", "#000000"),
            ("Gray", "#8e8e93"), ("White", "#ffffff"),
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
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawRoundedRect(QRectF(1.5, 1.5, 13.0, 13.0), 3, 3)
        else:
            if color.alpha() == 0:
                p.setPen(QPen(QColor("#ff3b30"), 1.8))
                p.drawEllipse(QRectF(1.5, 1.5, 13.0, 13.0))
                p.drawLine(QPointF(3.5, 12.5), QPointF(12.5, 3.5))
            else:
                p.setBrush(QBrush(color))
                p.setPen(QPen(QColor(255, 255, 255, 160), 0.8))
                p.drawRoundedRect(QRectF(1.5, 1.5, 13.0, 13.0), 3, 3)

        arrow_col = QColor(self._theme_col)
        p.setPen(QPen(QColor(arrow_col.red(), arrow_col.green(), arrow_col.blue(), 75), 1.0))
        p.drawLine(QPointF(17.5, 2.5), QPointF(17.5, 13.5))

        cx, cy = 23.5, 8.0
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
        self.rotate_selection_btn.setEnabled(True)
        self.rotate_selection_btn.setToolTip("Rotate Right (Ctrl+R)")
        if hasattr(self, "_overflow_crop_act"):
            self._overflow_crop_act.setEnabled(enabled)
        if hasattr(self, "_overflow_rot_sel_act"):
            self._overflow_rot_sel_act.setEnabled(True)

    def update_icons(self, color_hex: str):
        self._theme_col = color_hex
        self._refresh_tool_icons()

    def _refresh_tool_icons(self):
        col = self._theme_col
        self.pointer_btn.setIcon(MacIconFactory.create_icon("pointer", col, 18))
        self.hand_btn.setIcon(MacIconFactory.create_icon("hand", col, 18))
        self.select_btn.setIcon(MacIconFactory.create_dropdown_tool_icon(self._current_select_icon, col, 36, 22))
        self.shapes_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("shapes", col, 36, 22))
        self.pen_btn.setIcon(MacIconFactory.create_icon("pen", col, 18))
        self.highlighter_btn.setIcon(MacIconFactory.create_icon("highlighter", col, 18))
        self.underline_tool_btn.setIcon(MacIconFactory.create_icon("underline", col, 18))
        self.strikethrough_tool_btn.setIcon(MacIconFactory.create_icon("strikethrough", col, 18))
        self.text_btn.setIcon(MacIconFactory.create_icon("text", col, 18))
        self.note_btn.setIcon(MacIconFactory.create_icon("note", col, 18))
        self.redact_btn.setIcon(MacIconFactory.create_icon("redact", col, 18))
        self.sign_btn.setIcon(MacIconFactory.create_icon("sign", col, 18))
        self.image_overlay_btn.setIcon(MacIconFactory.create_icon("image_overlay", col, 18))
        self.crop_btn.setIcon(MacIconFactory.create_icon("crop", col, 18))
        self.rotate_btn.setIcon(MacIconFactory.create_icon("rotate_left", col, 18))
        self.rotate_selection_btn.setIcon(MacIconFactory.create_icon("rotate_right", col, 18))
        self.color_adjust_btn.setIcon(MacIconFactory.create_icon("color_adjust", col, 18))
        self.size_adjust_btn.setIcon(MacIconFactory.create_icon("size_adjust", col, 18))
        self.overflow_btn.setIcon(MacIconFactory.create_icon("more", col, 18))
        self.undo_btn.setIcon(MacIconFactory.create_icon("arrow_left", col, 18))
        self.redo_btn.setIcon(MacIconFactory.create_icon("arrow_right", col, 18))
        self.text_options_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("text", col, 32, 24))
        self.width_btn.setIcon(MacIconFactory.create_dropdown_tool_icon("line_style", col, 32, 24))

        if hasattr(self, "btn_adj_col"):
            self.btn_adj_col.setIcon(MacIconFactory.create_icon("color_adjust", col, 16))
        if hasattr(self, "btn_adj_sz"):
            self.btn_adj_sz.setIcon(MacIconFactory.create_icon("size_adjust", col, 16))
        if hasattr(self, "btn_rot"):
            self.btn_rot.setIcon(MacIconFactory.create_icon("rotate_left", col, 16))

        self._update_color_button_icon(self.color_btn, self.stroke_color)
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)
