"""
macOS-style secondary Markup Toolbar providing sketch, highlighter, shapes,
text, note, signature, color palettes, context-aware formatting, and crop actions.

Visual language matches macOS Sonoma/Sequoia Preview:
  * Segmented pill groups with hairline dividers
  * Context-aware formatting row (shape / text / selection / redaction / default)
  * Responsive overflow when horizontal space is tight
  * Full dark/light theme parity via update_theme()
"""

from enum import Enum
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QColorDialog, QMenu,
    QSpinBox, QComboBox, QFontComboBox, QLabel, QButtonGroup, QFrame,
    QSizePolicy,
)
from PyQt6.QtGui import (
    QColor, QAction, QActionGroup, QIcon, QPixmap, QPainter, QBrush, QPen,
    QPolygonF, QFont, QKeySequence,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPointF

from preview.core.annotations import AnnotationItem, AnnotationType
from preview.icons import MacIconFactory
from preview.theme import StudioTheme


class ThemeName(str, Enum):
    DARK = "dark"
    LIGHT = "light"


def _resolve_theme(theme) -> str:
    if isinstance(theme, ThemeName):
        return theme.value
    if isinstance(theme, str):
        return theme
    return getattr(theme, "value", "dark")


def _safe_icon(name: str, color: str, size: int) -> QIcon:
    try:
        return MacIconFactory.create_icon(name, color, size)
    except Exception:
        return QIcon()


def _safe_dropdown(name: str, color: str, w: int = 36, h: int = 22) -> QIcon:
    try:
        return MacIconFactory.create_dropdown_tool_icon(name, color, w, h)
    except Exception:
        try:
            return MacIconFactory.create_icon(name, color, 18)
        except Exception:
            return QIcon()


class MarkupToolbar(QWidget):
    """macOS-authentic markup toolbar with context-aware formatting row."""

    tool_changed = pyqtSignal(AnnotationType)
    stroke_color_changed = pyqtSignal(QColor)
    stroke_width_changed = pyqtSignal(float)
    stroke_style_changed = pyqtSignal(str)   # "solid" | "dash" | "dot" | "dashdot"
    fill_color_changed = pyqtSignal(QColor)
    fill_opacity_changed = pyqtSignal(int)   # 0-100
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

    _COMPACT_BREAKPOINT = 940
    _TIGHT_BREAKPOINT = 1350
    _ICON = 20
    _BTN = 32

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("markupToolbar")
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._theme: str = "dark"
        self._theme_col: str = StudioTheme.DARK_TEXT_PRIMARY

        self.current_tool: AnnotationType = AnnotationType.NONE
        self.stroke_color: QColor = QColor("#ff3b30")
        self.stroke_width: float = 3.0
        self.stroke_style: str = "solid"
        self.fill_color: QColor = QColor(Qt.GlobalColor.transparent)
        self.font_size: int = 16
        self._current_select_icon: str = "box-select"
        self.selected_annotation: Optional[AnnotationItem] = None

        self._setup_ui()
        self._apply_style()
        self._refresh_tool_icons()
        self._refresh_menu_icons()
        self.update_context_row()
        self.handle_resize(self.width())

    # ==================================================================
    #  SETUP
    # ==================================================================
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.primary_strip = QWidget()
        self.primary_strip.setObjectName("primaryStrip")
        self.primary_strip.setFixedHeight(44)
        self.strip_layout = QHBoxLayout(self.primary_strip)
        self.strip_layout.setContentsMargins(12, 5, 12, 5)
        self.strip_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False)

        # --- Group 1: Navigation ---
        self.pointer_btn = self._make_nav_button("pointer", "Select / Pointer (Esc)")
        self.pointer_btn.setChecked(True)
        self.pointer_btn.clicked.connect(self.unselect_all)
        self.btn_group.addButton(self.pointer_btn)

        self.hand_btn = self._make_nav_button("hand", "Hand / Pan Document (Space+Drag)")
        self.hand_btn.clicked.connect(self._select_hand_tool)
        self.btn_group.addButton(self.hand_btn)

        self.strip_layout.addWidget(self._make_group([self.pointer_btn, self.hand_btn]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 2: Text Markup & Notes ---
        self.text_btn = self._make_tool_button("text", "Text Box (T)", AnnotationType.TEXT)
        self.highlighter_btn = self._make_tool_button("chisel_highlighter", "Highlighter (Shift+H)", AnnotationType.HIGHLIGHTER)
        self.underline_tool_btn = self._make_tool_button("underline", "Underline Text Markup (U)", AnnotationType.UNDERLINE)
        self.strikethrough_tool_btn = self._make_tool_button("strikethrough", "Strikethrough (S)", AnnotationType.STRIKETHROUGH)
        self.strikethrough_btn = self.strikethrough_tool_btn
        self.note_btn = self._make_tool_button("note", "Sticky Note (N)", AnnotationType.NOTE)
        self.strip_layout.addWidget(self._make_group([
            self.text_btn, self.highlighter_btn, self.underline_tool_btn,
            self.strikethrough_tool_btn, self.note_btn,
        ]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 3: Drawing ---
        self.pen_btn = self._make_tool_button("fountain_pen", "Sketch / Pen (P)", AnnotationType.PEN)
        self.strip_layout.addWidget(self._make_group([self.pen_btn]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 4: Shapes ---
        self.shapes_btn = QToolButton()
        self.shapes_btn.setObjectName("shapesBtn")
        self.shapes_btn.setFixedSize(40, 32)
        self.shapes_btn.setIconSize(QSize(36, 22))
        self.shapes_btn.setCheckable(True)
        self.shapes_btn.setToolTip("Shapes (Shift+S)")
        self.shapes_btn.setAccessibleName("Shapes")
        self.shapes_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_shapes_menu()
        self.btn_group.addButton(self.shapes_btn)
        self.strip_layout.addWidget(self._make_group([self.shapes_btn]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 5: Privacy / Signature / Overlay ---
        self.redact_btn = self._make_tool_button("redact", "Redact / Blackout (Shift+R)", AnnotationType.REDACT)
        self.sign_btn = self._make_icon_action("rubber_stamp", "Sign Document (K)", self.signature_requested)
        self.stamp_btn = self.sign_btn
        self.image_overlay_btn = self._make_icon_action(
            "image_overlay", "Add Image Overlay (Ctrl+Shift+I)", self.image_overlay_requested,
        )
        self.strip_layout.addWidget(self._make_group([
            self.redact_btn, self.sign_btn, self.image_overlay_btn,
        ]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 6a: Selection tools (ALWAYS visible) ---
        self.select_btn = QToolButton()
        self.select_btn.setObjectName("selectBtn")
        self.select_btn.setFixedSize(40, 32)
        self.select_btn.setIconSize(QSize(36, 22))
        self.select_btn.setCheckable(True)
        self.select_btn.setToolTip("Selection Tools (Rectangular, Oval, Lasso)")
        self.select_btn.setAccessibleName("Selection Tools")
        self.select_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_select_menu()
        self.btn_group.addButton(self.select_btn)
        self.group_select = self._make_group([self.select_btn])
        self.strip_layout.addWidget(self.group_select)

        # --- Group 6b: Image operations (COLLAPSIBLE on compact) ---
        self.crop_btn = self._make_icon_action("crop_shears", "Crop Selection (Ctrl+K)", self.crop_requested)
        self.crop_btn.setEnabled(False)
        self.rotate_btn = self._make_icon_action("rotate_left", "Rotate Left 90° (Ctrl+L)", self.rotate_requested)

        # Page-level rotate-right. Selection rotation is a separate action fired
        # from the "Rotate Selection (90°)" button in the selection context view.
        self.rotate_selection_btn = self._make_icon_action(
            "rotate_right", "Rotate Page Right 90° (Ctrl+R)", self.rotate_right_requested,
        )
        self.rotate_right_btn = self.rotate_selection_btn

        self.color_adjust_btn = self._make_icon_action("color_adjust", "Adjust Color (Ctrl+Alt+C)", self.adjust_color_requested)
        self.size_adjust_btn = self._make_icon_action("size_adjust", "Adjust Size (Ctrl+Alt+S)", self.adjust_size_requested)
        self.group_image = self._make_group([
            self.crop_btn, self.rotate_btn, self.rotate_selection_btn,
            self.color_adjust_btn, self.size_adjust_btn,
        ])
        self.strip_layout.addWidget(self.group_image)
        self.strip_layout.addWidget(self._make_divider())

        # --- Overflow button (visible on compact) ---
        self.overflow_btn = QToolButton()
        self.overflow_btn.setObjectName("overflowBtn")
        self.overflow_btn.setFixedSize(38, 32)
        self.overflow_btn.setToolTip("More Tools")
        self.overflow_btn.setAccessibleName("More Tools")
        self.overflow_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_overflow_menu()
        self.overflow_btn.setVisible(False)
        self.strip_layout.addWidget(self.overflow_btn)
        self.strip_layout.addWidget(self._make_divider())

        # --- Group 7: History ---
        self.undo_btn = self._make_icon_action("arrow_left", "Undo (Ctrl+Z)", self.undo_requested)
        self.redo_btn = self._make_icon_action("arrow_right", "Redo (Ctrl+Shift+Z)", self.redo_requested)
        self.strip_layout.addWidget(self._make_group([self.undo_btn, self.redo_btn]))
        self.strip_layout.addWidget(self._make_divider())

        # --- Context-aware formatting row ---
        self._build_context_bar()
        self.strip_layout.addWidget(self.context_bar, 1)

        root.addWidget(self.primary_strip)

    def _build_context_bar(self) -> None:
        """Build the five context sub-views (no QStackedWidget — size hint is minimal)."""
        self.context_bar = QWidget()
        self.context_bar.setObjectName("contextFormattingBar")
        self.context_bar.setFixedHeight(32)
        c = QHBoxLayout(self.context_bar)
        c.setContentsMargins(4, 0, 4, 0)
        c.setSpacing(0)

        self._context_views: List[QWidget] = []

        # 0 — Shape format
        self.shape_format_widget = QWidget()
        sf = QHBoxLayout(self.shape_format_widget)
        sf.setContentsMargins(0, 0, 0, 0)
        sf.setSpacing(8)
        sf.addWidget(self._section_label("Shape Format:"))

        self.color_btn = QToolButton()
        self.color_btn.setFixedSize(36, 24)
        self.color_btn.setToolTip("Border / Stroke Color")
        self.color_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_stroke_color_menu()
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        sf.addWidget(self.color_btn)

        self.fill_btn = QToolButton()
        self.fill_btn.setFixedSize(36, 24)
        self.fill_btn.setToolTip("Fill Color")
        self.fill_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_fill_color_menu()
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)
        sf.addWidget(self.fill_btn)

        self.width_btn = QToolButton()
        self.width_btn.setFixedSize(36, 24)
        self.width_btn.setToolTip(
            f"Line Style: Solid · Thickness {int(self.stroke_width)} px"
        )
        self._setup_width_menu()
        sf.addWidget(self.width_btn)

        opacity_label = QLabel("Opacity")
        opacity_label.setObjectName("contextSectionLabel")
        sf.addWidget(opacity_label)

        self.fill_opacity_spin = QSpinBox()
        self.fill_opacity_spin.setRange(0, 100)
        self.fill_opacity_spin.setValue(100)
        self.fill_opacity_spin.setSuffix("%")
        self.fill_opacity_spin.setFixedHeight(24)
        self.fill_opacity_spin.setFixedWidth(60)
        self.fill_opacity_spin.setToolTip("Fill opacity")
        self.fill_opacity_spin.valueChanged.connect(self._on_fill_opacity_changed)
        sf.addWidget(self.fill_opacity_spin)

        sf.addStretch()
        self._context_views.append(self.shape_format_widget)

        # 1 — Text format
        self.text_format_widget = QWidget()
        tf = QHBoxLayout(self.text_format_widget)
        tf.setContentsMargins(0, 0, 0, 0)
        tf.setSpacing(6)
        tf.addWidget(self._section_label("Text Format:"))

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(24)
        self.font_combo.setFixedWidth(130)
        self.font_combo.setToolTip("Font Family")
        self.font_combo.currentFontChanged.connect(lambda f: self.font_family_changed.emit(f.family()))
        tf.addWidget(self.font_combo)

        self.font_spin = QSpinBox()
        self.font_spin.setFixedHeight(24)
        self.font_spin.setFixedWidth(48)
        self.font_spin.setRange(8, 72)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setToolTip("Font Size")
        self.font_spin.valueChanged.connect(self._on_font_size_changed)
        tf.addWidget(self.font_spin)

        self.bold_btn = self._make_style_toggle("B", "Bold (Ctrl+B)", bold=True)
        self.bold_btn.toggled.connect(self.font_bold_changed.emit)
        tf.addWidget(self.bold_btn)

        self.italic_btn = self._make_style_toggle("I", "Italic (Ctrl+I)", italic=True)
        self.italic_btn.toggled.connect(self.font_italic_changed.emit)
        tf.addWidget(self.italic_btn)

        self.underline_btn = self._make_style_toggle("U", "Underline (Ctrl+U)", underline=True)
        self.underline_btn.toggled.connect(self.font_underline_changed.emit)
        tf.addWidget(self.underline_btn)

        self.strike_btn = self._make_style_toggle("S", "Strikethrough", strike=True)
        self.strike_btn.toggled.connect(self.font_strikethrough_changed.emit)
        tf.addWidget(self.strike_btn)

        self.text_options_btn = QToolButton()
        self.text_options_btn.setFixedSize(32, 24)
        self.text_options_btn.setToolTip("Text Alignment & Presets")
        self.text_options_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_text_options_menu()
        tf.addWidget(self.text_options_btn)

        tf.addStretch()
        self._context_views.append(self.text_format_widget)

        # 2 — Selection active
        self.selection_format_widget = QWidget()
        sel = QHBoxLayout(self.selection_format_widget)
        sel.setContentsMargins(0, 0, 0, 0)
        sel.setSpacing(10)
        sel.addWidget(self._section_label("Selection Active:", accent=True))

        crop_action_btn = QToolButton()
        crop_action_btn.setObjectName("primaryActionBtn")
        crop_action_btn.setText("Apply Crop (Ctrl+K)")
        crop_action_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        crop_action_btn.setFixedHeight(24)
        crop_action_btn.setMinimumWidth(135)
        crop_action_btn.setProperty("icon_name", "crop")
        crop_action_btn.clicked.connect(self.crop_requested.emit)
        sel.addWidget(crop_action_btn)
        self._sel_crop_action_btn = crop_action_btn

        rot_sel_btn = QToolButton()
        rot_sel_btn.setText("Rotate Selection (90°)")
        rot_sel_btn.setObjectName("secondaryActionBtn")
        rot_sel_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        rot_sel_btn.setFixedHeight(24)
        rot_sel_btn.setMinimumWidth(150)
        rot_sel_btn.setProperty("icon_name", "rotate_right")
        rot_sel_btn.clicked.connect(lambda: self.rotate_selection_requested.emit(90))
        sel.addWidget(rot_sel_btn)
        self._sel_rot_action_btn = rot_sel_btn

        sel.addStretch()
        self._context_views.append(self.selection_format_widget)

        # 3 — Pending redaction
        self.redact_format_widget = QWidget()
        rf = QHBoxLayout(self.redact_format_widget)
        rf.setContentsMargins(0, 0, 0, 0)
        rf.setSpacing(10)
        rf.addWidget(self._section_label("Pending Redaction:", danger=True))
        rf.addWidget(self._section_label(
            "Mark sensitive areas with black boxes, then apply permanently.", muted=True,
        ))

        apply_redact_now = QToolButton()
        apply_redact_now.setObjectName("destructiveActionBtn")
        apply_redact_now.setText("Apply Redactions Permanently")
        apply_redact_now.setFixedHeight(24)
        apply_redact_now.setMinimumWidth(190)
        apply_redact_now.clicked.connect(self.apply_redactions_requested.emit)
        rf.addWidget(apply_redact_now)

        rf.addStretch()
        self._context_views.append(self.redact_format_widget)

        # 4 — Default actions
        self.default_format_widget = QWidget()
        df = QHBoxLayout(self.default_format_widget)
        df.setContentsMargins(0, 0, 0, 0)
        df.setSpacing(8)

        self.def_lbl = self._section_label("Contextual Actions:")
        self.def_lbl.setVisible(False)
        df.addWidget(self.def_lbl)

        self.btn_adj_col = self._make_small_action(
            "color_adjust", "Adjust Color...", "Adjust Color (Ctrl+Alt+C)",
            self.adjust_color_requested,
        )
        self.btn_adj_sz = self._make_small_action(
            "size_adjust", "Adjust Size...", "Adjust Size (Ctrl+Alt+S)",
            self.adjust_size_requested,
        )
        self.btn_rot = self._make_small_action(
            "rotate_left", "Rotate Left 90°", "Rotate Left 90° (Ctrl+L)",
            self.rotate_requested,
        )
        for b in (self.btn_adj_col, self.btn_adj_sz, self.btn_rot):
            df.addWidget(b)

        df.addStretch()
        self._context_views.append(self.default_format_widget)

        for w in self._context_views:
            c.addWidget(w)
            w.setVisible(False)
        self._context_views[4].setVisible(True)  # default view

    # ----------------------------------------------------------------
    #  Widget factory helpers
    # ----------------------------------------------------------------
    def _make_nav_button(self, icon_name: str, tooltip: str) -> QToolButton:
        b = QToolButton()
        b.setFixedSize(self._BTN, self._BTN)
        b.setIconSize(QSize(self._ICON, self._ICON))
        b.setCheckable(True)
        b.setToolTip(tooltip)
        b.setAccessibleName(tooltip)
        b.setProperty("icon_name", icon_name)
        return b

    def _make_tool_button(self, icon_name: str, tooltip: str, tool_type: AnnotationType) -> QToolButton:
        b = self._make_nav_button(icon_name, tooltip)
        b.clicked.connect(lambda: self._on_tool_clicked(b, tool_type))
        self.btn_group.addButton(b)
        return b

    def _make_icon_action(self, icon_name: str, tooltip: str, signal) -> QToolButton:
        b = QToolButton()
        b.setFixedSize(self._BTN, self._BTN)
        b.setIconSize(QSize(self._ICON, self._ICON))
        b.setToolTip(tooltip)
        b.setAccessibleName(tooltip)
        b.setProperty("icon_name", icon_name)
        b.clicked.connect(signal.emit)
        return b

    def _make_small_action(self, icon_name: str, text: str, tooltip: str, signal) -> QToolButton:
        b = QToolButton()
        b.setObjectName("iconActionBtn")
        b.setText(text)
        b.setIconSize(QSize(16, 16))
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        b.setFixedSize(28, 28)
        b.setToolTip(tooltip)
        b.setAccessibleName(text)
        b.setProperty("icon_name", icon_name)
        b.clicked.connect(signal.emit)
        return b

    def _make_style_toggle(self, text: str, tooltip: str, *, bold=False, italic=False,
                           underline=False, strike=False) -> QToolButton:
        b = QToolButton()
        b.setFixedSize(24, 24)
        b.setCheckable(True)
        b.setText(text)
        b.setToolTip(tooltip)
        styles = ["font-size: 12px;"]
        if bold:      styles.append("font-weight: 700;")
        if italic:    styles.append("font-style: italic; font-family: serif;")
        if underline: styles.append("text-decoration: underline;")
        if strike:    styles.append("text-decoration: line-through;")
        b.setStyleSheet(" ".join(styles))
        return b

    def _section_label(self, text: str, *, accent=False, danger=False, muted=False) -> QLabel:
        lbl = QLabel(text)
        if accent:   lbl.setObjectName("contextAccentLabel")
        elif danger: lbl.setObjectName("contextDangerLabel")
        elif muted:  lbl.setObjectName("contextMutedLabel")
        else:        lbl.setObjectName("contextSectionLabel")
        return lbl

    def _make_group(self, buttons: List[QToolButton]) -> QFrame:
        g = QFrame()
        g.setObjectName("markupGroup")
        g.setFixedHeight(34)
        g.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        gl = QHBoxLayout(g)
        gl.setContentsMargins(1, 1, 1, 1)
        gl.setSpacing(2)
        for b in buttons:
            gl.addWidget(b)
        return g

    def _make_divider(self) -> QWidget:
        sep = QFrame()
        sep.setObjectName("markupGroupSeparator")
        sep.setFixedSize(1, 20)
        sep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return sep

    # ==================================================================
    #  THEME
    # ==================================================================
    def _icon_color(self) -> str:
        return (StudioTheme.DARK_TEXT_PRIMARY
                if self._theme == "dark"
                else StudioTheme.LIGHT_TEXT_PRIMARY)

    def update_theme(self, theme_name) -> None:
        new_theme = _resolve_theme(theme_name)
        if new_theme == self._theme:
            return
        self._theme = new_theme
        self._theme_col = self._icon_color()
        self._apply_style()
        self._refresh_tool_icons()
        self._refresh_menu_icons()
        self._update_color_button_icon(self.color_btn, self.stroke_color)
        self._update_color_button_icon(self.fill_btn, self.fill_color, is_fill=True)

    def update_icons(self, color_hex: str) -> None:
        """Backward-compatible: accept explicit color and refresh all icons."""
        self._theme_col = color_hex
        self._refresh_tool_icons()
        self._refresh_menu_icons()

    def _apply_style(self) -> None:
        is_dark = self._theme == "dark"
        s = StudioTheme

        bg             = s.DARK_BG_WINDOW   if is_dark else s.LIGHT_BG_WINDOW
        border         = s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE
        group_bg       = s.DARK_BG_CARD     if is_dark else s.LIGHT_BG_CARD
        group_bdr      = s.DARK_BORDER      if is_dark else s.LIGHT_BORDER
        btn_hover      = s.DARK_BG_HOVER    if is_dark else s.LIGHT_BG_HOVER
        btn_press      = s.DARK_BG_ACTIVE   if is_dark else s.LIGHT_BG_ACTIVE
        text_primary   = s.DARK_TEXT_PRIMARY   if is_dark else s.LIGHT_TEXT_PRIMARY
        text_secondary = s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY
        accent         = s.DARK_ACCENT      if is_dark else s.LIGHT_ACCENT
        danger         = s.DARK_DANGER      if is_dark else s.LIGHT_DANGER

        self.setStyleSheet(f"""
            #markupToolbar {{ background-color: {bg}; }}
            #primaryStrip  {{ background-color: {bg}; }}
            #markupGroup {{
                background-color: {group_bg};
                border: 1px solid {group_bdr};
                border-radius: 7px;
            }}
            #markupGroupSeparator {{ background-color: {border}; border: none; }}
            #primaryStrip QToolButton {{
                background: transparent;
                border: none;
                border-radius: 5px;
                color: {text_primary};
            }}
            #primaryStrip QToolButton:hover {{ background-color: {btn_hover}; }}
            #primaryStrip QToolButton:pressed {{ background-color: {btn_press}; }}
            #primaryStrip QToolButton:checked {{
                background-color: {accent};
                color: #ffffff;
            }}
            #primaryStrip QToolButton:disabled {{ color: {text_secondary}; }}
            #contextSectionLabel {{
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 600;
                color: {text_secondary};
            }}
            #contextAccentLabel {{
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 700;
                color: {accent};
            }}
            #contextDangerLabel {{
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 700;
                color: {danger};
            }}
            #contextMutedLabel {{
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                color: {text_secondary};
            }}
            #primaryActionBtn {{
                background-color: {accent};
                color: #ffffff;
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 600;
                padding: 2px 10px;
                border: none;
                border-radius: 4px;
            }}
            #primaryActionBtn:hover {{
                background-color: {accent};
            }}
            #secondaryActionBtn {{
                background: transparent;
                color: {text_primary};
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                padding: 2px 10px;
                border: 1px solid {group_bdr};
                border-radius: 4px;
            }}
            #secondaryActionBtn:hover {{ background-color: {btn_hover}; }}
            #destructiveActionBtn {{
                background-color: {danger};
                color: #ffffff;
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 600;
                padding: 2px 10px;
                border: none;
                border-radius: 4px;
            }}
            #contextFormattingBar {{
                background: transparent;
                border-left: 1px solid {border};
                padding-left: 8px;
            }}
            #contextFormattingBar QComboBox,
            #contextFormattingBar QFontComboBox,
            #contextFormattingBar QSpinBox {{
                background-color: {group_bg};
                color: {text_primary};
                border: 1px solid {group_bdr};
                border-radius: 4px;
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                padding: 1px 4px;
            }}
            #contextFormattingBar QToolButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {text_primary};
            }}
            #contextFormattingBar QToolButton:hover {{ background-color: {btn_hover}; }}
            #contextFormattingBar QToolButton:checked {{
                background-color: {accent};
                color: #ffffff;
            }}
            #iconActionBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            #iconActionBtn:hover {{ background-color: {btn_hover}; }}
        """)

    # ==================================================================
    #  ICONS
    # ==================================================================
    def _refresh_tool_icons(self) -> None:
        c = self._theme_col
        def ic(name, size=18):
            return _safe_icon(name, c, size)

        self.pointer_btn.setIcon(ic("pointer"))
        self.hand_btn.setIcon(ic("hand"))
        self.select_btn.setIcon(_safe_dropdown(self._current_select_icon, c))
        self.shapes_btn.setIcon(_safe_dropdown("shapes", c))
        self.pen_btn.setIcon(ic("fountain_pen"))
        self.highlighter_btn.setIcon(ic("chisel_highlighter"))
        self.underline_tool_btn.setIcon(ic("underline"))
        self.strikethrough_tool_btn.setIcon(ic("strikethrough"))
        self.text_btn.setIcon(ic("text"))
        self.note_btn.setIcon(ic("note"))
        self.redact_btn.setIcon(ic("redact"))
        self.sign_btn.setIcon(ic("rubber_stamp"))
        self.image_overlay_btn.setIcon(ic("image_overlay"))
        self.crop_btn.setIcon(ic("crop_shears"))
        self.rotate_btn.setIcon(ic("rotate_left"))
        self.rotate_selection_btn.setIcon(ic("rotate_right"))
        self.color_adjust_btn.setIcon(ic("color_adjust"))
        self.size_adjust_btn.setIcon(ic("size_adjust"))
        self.overflow_btn.setIcon(ic("more"))
        self.undo_btn.setIcon(ic("arrow_left"))
        self.redo_btn.setIcon(ic("arrow_right"))
        self.text_options_btn.setIcon(_safe_dropdown("text", c, 32, 24))
        self.width_btn.setIcon(_safe_dropdown("line_style", c, 32, 24))

        self.btn_adj_col.setIcon(ic("color_adjust", 16))
        self.btn_adj_sz.setIcon(ic("size_adjust", 16))
        self.btn_rot.setIcon(ic("rotate_left", 16))

    def _refresh_menu_icons(self) -> None:
        """Refresh QAction icons in all menus to match the current theme."""
        c = self._theme_col
        for btn in (self.overflow_btn, self.select_btn, self.shapes_btn,
                    self.width_btn, self.text_options_btn):
            menu = btn.menu()
            if not menu:
                continue
            for action in menu.actions():
                name = action.data()
                if isinstance(name, str) and name:
                    action.setIcon(_safe_icon(name, c, 16))

    # ==================================================================
    #  MENUS
    # ==================================================================
    def _setup_overflow_menu(self) -> None:
        menu = QMenu(self)
        c = self._theme_col

        def add(menu_, text, icon_name, shortcut, signal_or_callable):
            act = QAction(_safe_icon(icon_name, c, 16), text, self)
            act.setData(icon_name)
            if shortcut:
                act.setShortcut(shortcut)
            if callable(signal_or_callable) and not hasattr(signal_or_callable, "emit"):
                act.triggered.connect(signal_or_callable)
            else:
                act.triggered.connect(signal_or_callable.emit)
            menu_.addAction(act)
            return act

        self._overflow_crop_act = add(menu, "Crop Selection", "crop", "Ctrl+K", self.crop_requested)
        add(menu, "Rotate Left 90°", "rotate_left", "Ctrl+L", self.rotate_requested)
        self._overflow_rot_sel_act = add(
            menu, "Rotate Selection 90°", "rotate_right", "Ctrl+R",
            lambda: self.rotate_selection_requested.emit(90),
        )
        menu.addSeparator()
        add(menu, "Adjust Color...", "color_adjust", "Ctrl+Alt+C", self.adjust_color_requested)
        add(menu, "Adjust Size...", "size_adjust", "Ctrl+Alt+S", self.adjust_size_requested)
        menu.addSeparator()

        sel_menu = menu.addMenu("Selection Tools")
        sel_menu.setIcon(_safe_icon("box-select", c, 16))
        for name, atype, icon_name in [
            ("Rectangular Selection", AnnotationType.CROP_BOX,   "box-select"),
            ("Oval Selection",        AnnotationType.CROP_OVAL,  "select_oval"),
            ("Lasso Selection",       AnnotationType.CROP_LASSO, "lasso"),
        ]:
            act = QAction(_safe_icon(icon_name, c, 16), name, self)
            act.setData(icon_name)
            act.triggered.connect(lambda _, t=atype, i=icon_name: self._select_crop_tool(t, i))
            sel_menu.addAction(act)

        loupe_act = menu.addAction(_safe_icon("loupe", c, 16), "Magnifier (Loupe)")
        loupe_act.setData("loupe")
        loupe_act.triggered.connect(lambda: self._select_shape_tool(AnnotationType.LOUPE))

        menu.addSeparator()
        add(menu, "Add Image Overlay...", "image_overlay", "Ctrl+Shift+I", self.image_overlay_requested)

        self.overflow_btn.setMenu(menu)

    def _setup_select_menu(self) -> None:
        menu = QMenu(self)
        c = self._theme_col
        for name, atype, icon_name in [
            ("Rectangular Selection", AnnotationType.CROP_BOX,   "box-select"),
            ("Oval Selection",        AnnotationType.CROP_OVAL,  "select_oval"),
            ("Lasso Selection",       AnnotationType.CROP_LASSO, "lasso"),
        ]:
            act = QAction(_safe_icon(icon_name, c, 16), name, self)
            act.setData(icon_name)
            act.triggered.connect(lambda _, t=atype, i=icon_name: self._select_crop_tool(t, i))
            menu.addAction(act)
        self.select_btn.setMenu(menu)

    def _setup_shapes_menu(self) -> None:
        menu = QMenu(self)
        c = self._theme_col
        for name, stype, icon_name in [
            ("Rectangle",         AnnotationType.RECTANGLE,    "square"),
            ("Rounded Rectangle", AnnotationType.ROUNDED_RECT, "shapes"),
            ("Oval",              AnnotationType.ELLIPSE,      "circle"),
            ("Line",              AnnotationType.LINE,         "minus"),
            ("Arrow",             AnnotationType.ARROW,        "arrow_right"),
            ("Callout Bubble",    AnnotationType.CALLOUT,      "callout"),
            ("Magnifier (Loupe)", AnnotationType.LOUPE,        "loupe"),
        ]:
            act = QAction(_safe_icon(icon_name, c, 16), name, self)
            act.setData(icon_name)
            act.triggered.connect(lambda _, t=stype: self._select_shape_tool(t))
            menu.addAction(act)
        self.shapes_btn.setMenu(menu)

    def _setup_width_menu(self) -> None:
        """Menu with line style presets (solid/dash/dot/dashdot) and pixel widths."""
        menu = QMenu(self)

        style_group = QActionGroup(self)
        style_group.setExclusive(True)
        for label, key, preview in [
            ("Solid",    "solid",   "───────"),
            ("Dashed",   "dash",    "── ── ──"),
            ("Dotted",   "dot",     "· · · · ·"),
            ("Dash-Dot", "dashdot", "── · ── ·"),
        ]:
            act = QAction(f"{label}  {preview}", self)
            act.setCheckable(True)
            act.setChecked(key == self.stroke_style)
            act.setData(key)
            act.triggered.connect(lambda _, k=key: self._set_stroke_style(k))
            style_group.addAction(act)
            menu.addAction(act)

        menu.addSeparator()

        width_group = QActionGroup(self)
        width_group.setExclusive(True)
        for w in [1.0, 2.0, 3.0, 5.0, 8.0, 12.0]:
            act = QAction(f"{int(w)} px", self)
            act.setCheckable(True)
            act.setChecked(abs(w - self.stroke_width) < 0.01)
            act.setData(w)
            act.triggered.connect(lambda _, val=w: self._set_width(val))
            width_group.addAction(act)
            menu.addAction(act)

        self.width_btn.setMenu(menu)
        self._width_menu = menu

    def _setup_text_options_menu(self) -> None:
        menu = QMenu(self)
        for label, align in [
            ("Align Left",   Qt.AlignmentFlag.AlignLeft),
            ("Align Center", Qt.AlignmentFlag.AlignHCenter),
            ("Align Right",  Qt.AlignmentFlag.AlignRight),
        ]:
            act = QAction(label, self)
            act.triggered.connect(lambda _, a=align: self.text_align_changed.emit(a))
            menu.addAction(act)
        menu.addSeparator()
        for sz in [10, 12, 14, 16, 20, 24, 32, 48, 64]:
            act = QAction(f"{sz} pt", self)
            act.triggered.connect(lambda _, s=sz: self.font_spin.setValue(s))
            menu.addAction(act)
        self.text_options_btn.setMenu(menu)

    def _setup_stroke_color_menu(self) -> None:
        menu = QMenu(self)
        presets = [
            ("Red", "#ff3b30"), ("Orange", "#ff9500"), ("Yellow", "#ffcc00"),
            ("Green", "#34c759"), ("Cyan", "#30b0c7"), ("Blue", "#007aff"),
            ("Purple", "#af52de"), ("Pink", "#ff2d55"), ("Black", "#000000"),
            ("Gray", "#8e8e93"), ("White", "#ffffff"),
        ]
        for name, hex_val in presets:
            col = QColor(hex_val)
            act = QAction(self._create_swatch_icon(col), name, self)
            act.triggered.connect(lambda _, c=col: self._set_stroke_color(c))
            menu.addAction(act)
        menu.addSeparator()
        act = QAction("Show Colors...", self)
        act.triggered.connect(self._choose_custom_stroke_color)
        menu.addAction(act)
        self.color_btn.setMenu(menu)

    def _setup_fill_color_menu(self) -> None:
        menu = QMenu(self)
        act = QAction(self._create_transparent_swatch_icon(), "No Fill (Transparent)", self)
        act.triggered.connect(lambda: self._set_fill_color(QColor(Qt.GlobalColor.transparent)))
        menu.addAction(act)
        menu.addSeparator()
        presets = [
            ("Red", "#ff3b30"), ("Orange", "#ff9500"), ("Yellow", "#ffcc00"),
            ("Green", "#34c759"), ("Cyan", "#30b0c7"), ("Blue", "#007aff"),
            ("Purple", "#af52de"), ("Pink", "#ff2d55"), ("Black", "#000000"),
            ("Gray", "#8e8e93"), ("White", "#ffffff"),
        ]
        for name, hex_val in presets:
            col = QColor(hex_val)
            act = QAction(self._create_swatch_icon(col), name, self)
            act.triggered.connect(lambda _, c=col: self._set_fill_color(c))
            menu.addAction(act)
        menu.addSeparator()
        act = QAction("Show Colors...", self)
        act.triggered.connect(self._choose_custom_fill_color)
        menu.addAction(act)
        self.fill_btn.setMenu(menu)

    # ==================================================================
    #  TOOL LOGIC
    # ==================================================================
    def _select_hand_tool(self) -> None:
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.hand_btn.setChecked(True)
        self.current_tool = AnnotationType.HAND
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def _on_tool_clicked(self, clicked_btn: QToolButton, tool_type: AnnotationType) -> None:
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

    def unselect_all(self) -> None:
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.pointer_btn.setChecked(True)
        self.current_tool = AnnotationType.NONE
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def _select_crop_tool(self, tool_type: AnnotationType, icon_name: str) -> None:
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.select_btn.setChecked(True)
        self.current_tool = tool_type
        self._current_select_icon = icon_name
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    def _select_shape_tool(self, tool_type: AnnotationType) -> None:
        for b in self.btn_group.buttons():
            b.setChecked(False)
        self.shapes_btn.setChecked(True)
        self.current_tool = tool_type
        self._refresh_tool_icons()
        self.tool_changed.emit(self.current_tool)
        self.update_context_row()

    # ==================================================================
    #  CONTEXT ROW
    # ==================================================================
    def _set_context_view(self, idx: int) -> None:
        for i, w in enumerate(self._context_views):
            w.setVisible(i == idx)
        self.context_bar.updateGeometry()

    def set_selected_annotation(self, annot: Optional[AnnotationItem]) -> None:
        self.selected_annotation = annot
        self.update_context_row()

    def update_context_row(self) -> None:
        """Swap context sub-view. Programmatic widget updates are signal-guarded."""
        if self.selected_annotation:
            t = self.selected_annotation.item_type
            if t in (AnnotationType.TEXT, AnnotationType.NOTE, AnnotationType.CALLOUT):
                self._set_context_view(1)
                self._sync_text_format_controls(self.selected_annotation)
                return
            elif t in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT,
                       AnnotationType.ELLIPSE, AnnotationType.LINE, AnnotationType.ARROW,
                       AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                self._set_context_view(0)
                self._update_color_button_icon(self.color_btn, self.selected_annotation.stroke_color)
                self._update_color_button_icon(self.fill_btn, self.selected_annotation.fill_color, is_fill=True)
                return
            elif t == AnnotationType.REDACT:
                self._set_context_view(3)
                return

        if self.current_tool in (AnnotationType.TEXT, AnnotationType.NOTE,
                                 AnnotationType.UNDERLINE, AnnotationType.STRIKETHROUGH):
            self._set_context_view(1)
        elif self.current_tool in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT,
                                   AnnotationType.ELLIPSE, AnnotationType.LINE,
                                   AnnotationType.ARROW, AnnotationType.PEN,
                                   AnnotationType.HIGHLIGHTER):
            self._set_context_view(0)
        elif self.current_tool in (AnnotationType.CROP_BOX, AnnotationType.CROP_OVAL,
                                   AnnotationType.CROP_LASSO):
            self._set_context_view(2)
        elif self.current_tool == AnnotationType.REDACT:
            self._set_context_view(3)
        else:
            self._set_context_view(4)

    def _sync_text_format_controls(self, annot: AnnotationItem) -> None:
        """Sync text-format widgets to the annotation WITHOUT emitting signals."""
        self.font_combo.blockSignals(True)
        self.font_spin.blockSignals(True)
        self.bold_btn.blockSignals(True)
        self.italic_btn.blockSignals(True)
        self.underline_btn.blockSignals(True)
        self.strike_btn.blockSignals(True)
        try:
            self.font_combo.setCurrentFont(QFont(getattr(annot, "font_family", "Helvetica")))
            self.font_spin.setValue(int(getattr(annot, "font_size", 16)))
            self.bold_btn.setChecked(bool(getattr(annot, "is_bold", False)))
            self.italic_btn.setChecked(bool(getattr(annot, "is_italic", False)))
            self.underline_btn.setChecked(bool(getattr(annot, "is_underline", False)))
            self.strike_btn.setChecked(bool(getattr(annot, "is_strikethrough", False)))
        finally:
            self.font_combo.blockSignals(False)
            self.font_spin.blockSignals(False)
            self.bold_btn.blockSignals(False)
            self.italic_btn.blockSignals(False)
            self.underline_btn.blockSignals(False)
            self.strike_btn.blockSignals(False)

    # ==================================================================
    #  COLORS
    # ==================================================================
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

    def _update_color_button_icon(self, btn: QToolButton, color: QColor, is_fill: bool = False) -> None:
        pix = QPixmap(28, 16)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not is_fill:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
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

        arrow = QColor(self._theme_col)
        p.setPen(QPen(QColor(arrow.red(), arrow.green(), arrow.blue(), 75), 1.0))
        p.drawLine(QPointF(17.5, 2.5), QPointF(17.5, 13.5))
        cx, cy = 23.5, 8.0
        tri = QPolygonF([
            QPointF(cx - 2.8, cy - 1.8),
            QPointF(cx + 2.8, cy - 1.8),
            QPointF(cx, cy + 2.0),
        ])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(arrow))
        p.drawPolygon(tri)
        p.end()
        btn.setIcon(QIcon(pix))
        btn.setIconSize(QSize(28, 16))

    def _choose_custom_stroke_color(self) -> None:
        col = QColorDialog.getColor(self.stroke_color, self, "Select Stroke Color")
        if col.isValid():
            self._set_stroke_color(col)

    def _choose_custom_fill_color(self) -> None:
        col = QColorDialog.getColor(self.fill_color, self, "Select Fill Color")
        if col.isValid():
            self._set_fill_color(col)

    def _set_stroke_color(self, col: QColor) -> None:
        self.stroke_color = col
        self._update_color_button_icon(self.color_btn, col)
        self.stroke_color_changed.emit(col)

    def _set_fill_color(self, col: QColor) -> None:
        self.fill_color = col
        self._update_color_button_icon(self.fill_btn, col, is_fill=True)
        if hasattr(self, "fill_opacity_spin"):
            pct = int(round(col.alphaF() * 100))
            self.fill_opacity_spin.blockSignals(True)
            self.fill_opacity_spin.setValue(pct)
            self.fill_opacity_spin.blockSignals(False)
        self.fill_color_changed.emit(col)

    def _on_fill_opacity_changed(self, value: int) -> None:
        new_color = QColor(self.fill_color)
        new_color.setAlphaF(value / 100.0)
        self.fill_color = new_color
        self._update_color_button_icon(self.fill_btn, new_color, is_fill=True)
        self.fill_opacity_changed.emit(value)

    def _set_stroke_style(self, style: str) -> None:
        self.stroke_style = style
        self.width_btn.setToolTip(
            f"Line Style: {style.capitalize()} · Thickness {int(self.stroke_width)} px"
        )
        self.stroke_style_changed.emit(style)

    def _set_width(self, val: float) -> None:
        self.stroke_width = val
        self.width_btn.setToolTip(
            f"Line Style: {self.stroke_style.capitalize()} · Thickness {int(val)} px"
        )
        self.stroke_width_changed.emit(val)

    def _on_font_size_changed(self, size: int) -> None:
        self.font_size = size
        self.font_size_changed.emit(size)

    # ==================================================================
    #  CONTEXT / SHORTCUTS
    # ==================================================================
    def set_context(self, has_selection: bool = False,
                    pending_redactions: int = 0,
                    has_document: bool = True) -> None:
        """Enable/disable context-dependent buttons."""
        self.crop_btn.setEnabled(has_selection and has_document)
        self.rotate_selection_btn.setEnabled(has_document)
        self.rotate_btn.setEnabled(has_document)
        self.rotate_right_btn.setEnabled(has_document)
        self.color_adjust_btn.setEnabled(has_document)
        self.size_adjust_btn.setEnabled(has_document)
        self.redact_btn.setEnabled(has_document)
        self.sign_btn.setEnabled(has_document)
        self.image_overlay_btn.setEnabled(has_document)
        if hasattr(self, "_overflow_crop_act"):
            self._overflow_crop_act.setEnabled(has_selection and has_document)

    def set_crop_enabled(self, enabled: bool) -> None:
        """Backward-compat: enable crop action."""
        self.crop_btn.setEnabled(enabled)
        if hasattr(self, "_overflow_crop_act"):
            self._overflow_crop_act.setEnabled(enabled)

    def shortcut_specs(self) -> List[Tuple[QKeySequence, object]]:
        """Hand to the window so it can create QShortcut objects with correct focus scope."""
        return [
            (QKeySequence("Ctrl+Z"),       self.undo_requested),
            (QKeySequence("Ctrl+Shift+Z"), self.redo_requested),
            (QKeySequence("Ctrl+K"),       self.crop_requested),
            (QKeySequence("Ctrl+L"),       self.rotate_requested),
            (QKeySequence("Ctrl+R"),       self.rotate_right_requested),
            (QKeySequence("Ctrl+Alt+C"),   self.adjust_color_requested),
            (QKeySequence("Ctrl+Alt+S"),   self.adjust_size_requested),
            (QKeySequence("Ctrl+Shift+I"), self.image_overlay_requested),
        ]

    # ==================================================================
    #  RESPONSIVE
    # ==================================================================
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.handle_resize(self.width())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.handle_resize(event.size().width())

    def handle_resize(self, width: int) -> None:
        """Collapse image-op group below breakpoint; small actions switch to icon-only when tight."""
        compact = width < self._COMPACT_BREAKPOINT
        if compact != (not self.group_image.isVisible()):
            self.group_image.setVisible(not compact)
            self.overflow_btn.setVisible(compact)
            self.strip_layout.invalidate()
            self.updateGeometry()

        is_tight = width < self._TIGHT_BREAKPOINT
        self.def_lbl.setVisible(not is_tight)
        for btn, label in (
            (self.btn_adj_col, "Adjust Color..."),
            (self.btn_adj_sz,  "Adjust Size..."),
            (self.btn_rot,     "Rotate Left 90°"),
        ):
            if is_tight:
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                btn.setFixedSize(28, 28)
            else:
                btn.setText(label)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                btn.setFixedHeight(28)
                btn.setMinimumWidth(115)
                btn.setMaximumWidth(160)
            btn.updateGeometry()