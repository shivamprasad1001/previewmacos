"""
macOS-style Organize Action Bar for Mode C: Page and Document Management.

Exposes page rotation, flipping, cropping, resizing, insertion, deletion,
duplication, reordering, merging, splitting, compression, and export.

Visual language follows macOS Sonoma/Sequoia Preview:
  * Segmented pill groups with 1px hairline borders
  * SF Symbols-style 16px icons rendered via MacIconFactory
  * Separator hairlines between logical groups
  * Responsive collapse to icon-only below 780px
  * Context-aware button enable/disable via set_context()
"""

from enum import Enum
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QLabel, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QKeySequence

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


def _icon_or_blank(name: str, color: str, size: int) -> QIcon:
    """Create an icon; return a blank QIcon if the factory lookup fails."""
    try:
        return MacIconFactory.create_icon(name, color, size)
    except Exception:
        return QIcon()


class OrganizeActionBar(QWidget):
    """Secondary toolbar for Mode C (Organize), 44px tall, macOS-styled."""

    # --- Page rotation / orientation ---
    rotate_left_requested = pyqtSignal()
    rotate_right_requested = pyqtSignal()
    flip_horizontal_requested = pyqtSignal()
    flip_vertical_requested = pyqtSignal()

    # --- Page geometry ---
    crop_requested = pyqtSignal()
    resize_requested = pyqtSignal()

    # --- Page lifecycle ---
    duplicate_page_requested = pyqtSignal()
    insert_blank_requested = pyqtSignal()
    insert_file_requested = pyqtSignal()
    insert_clipboard_requested = pyqtSignal()
    delete_page_requested = pyqtSignal()

    # --- Page ordering ---
    move_up_requested = pyqtSignal()
    move_down_requested = pyqtSignal()

    # --- Document-level ---
    merge_requested = pyqtSignal()
    split_requested = pyqtSignal()
    reduce_size_requested = pyqtSignal()
    export_requested = pyqtSignal()

    _ICON_SIZE = QSize(16, 16)
    _COMPACT_BREAKPOINT = 780

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("organizeActionBar")
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._theme: str = "dark"
        self._compact: bool = False
        self._all_buttons: List[QToolButton] = []

        self._setup_ui()
        self._apply_style()
        self.update_icons(self._icon_color())

    # ==================================================================
    #  SIZING
    # ==================================================================
    def sizeHint(self) -> QSize:
        hint = self._layout.sizeHint()
        return QSize(max(320, hint.width()), 44)

    def minimumSizeHint(self) -> QSize:
        return QSize(280, 44)

    # ==================================================================
    #  UI
    # ==================================================================
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(6)
        self._layout = layout

        self._title = QLabel("Page Management")
        self._title.setObjectName("organizeTitle")
        self._title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._title)
        layout.addStretch(1)

        # Group 1 — Orientation
        self.rot_left_btn = self._make_button(
            "Rotate Left", "rotate_left", "Rotate page 90° left (Ctrl+L)",
            self.rotate_left_requested,
        )
        self.rot_right_btn = self._make_button(
            "Rotate Right", "rotate_right", "Rotate page 90° right (Ctrl+R)",
            self.rotate_right_requested,
        )
        self.flip_h_btn = self._make_button(
            "Flip H", "flip_horizontal", "Flip page horizontally",
            self.flip_horizontal_requested,
        )
        self.flip_v_btn = self._make_button(
            "Flip V", "flip_vertical", "Flip page vertically",
            self.flip_vertical_requested,
        )
        layout.addWidget(self._make_group([
            self.rot_left_btn, self.rot_right_btn, self.flip_h_btn, self.flip_v_btn,
        ]))
        layout.addWidget(self._make_divider())

        # Group 2 — Page lifecycle
        self.dup_btn = self._make_button(
            "Duplicate", "duplicate", "Duplicate selected page (Ctrl+D)",
            self.duplicate_page_requested,
        )
        self.insert_blank_btn = self._make_button(
            "Insert Blank", "file-plus-2", "Insert blank page after selection",
            self.insert_blank_requested,
        )
        self.insert_file_btn = self._make_button(
            "Insert File…", "file-up", "Insert pages from file (Ctrl+Shift+I)",
            self.insert_file_requested,
        )
        self.insert_clipboard_btn = self._make_button(
            "Paste Page", "clipboard", "Insert page from clipboard (Ctrl+V)",
            self.insert_clipboard_requested,
        )
        self.del_btn = self._make_button(
            "Delete", "trash", "Delete selected page(s)",
            self.delete_page_requested,
            danger=True,
        )
        layout.addWidget(self._make_group([
            self.dup_btn, self.insert_blank_btn, self.insert_file_btn,
            self.insert_clipboard_btn, self.del_btn,
        ]))
        layout.addWidget(self._make_divider())

        # Group 3 — Geometry & ordering
        self.crop_btn = self._make_button(
            "Crop", "crop", "Crop page to selection",
            self.crop_requested,
        )
        self.resize_btn = self._make_button(
            "Resize…", "resize", "Adjust page dimensions",
            self.resize_requested,
        )
        self.move_up_btn = self._make_button(
            "Move Up", "arrow-up", "Move page up (Ctrl+↑)",
            self.move_up_requested,
        )
        self.move_down_btn = self._make_button(
            "Move Down", "arrow-down", "Move page down (Ctrl+↓)",
            self.move_down_requested,
        )
        layout.addWidget(self._make_group([
            self.crop_btn, self.resize_btn, self.move_up_btn, self.move_down_btn,
        ]))

        layout.addStretch(1)

        # Group 4 — Document operations
        self.merge_btn = self._make_button(
            "Merge…", "merge", "Combine multiple PDFs into one",
            self.merge_requested,
        )
        self.split_btn = self._make_button(
            "Split…", "split", "Split or extract pages from this document",
            self.split_requested,
        )
        self.reduce_btn = self._make_button(
            "Reduce Size", "minimize", "Compress and reduce file size",
            self.reduce_size_requested,
        )
        self.export_btn = self._make_button(
            "Export…", "export", "Export all pages (Ctrl+E)",
            self.export_requested,
        )
        layout.addWidget(self._make_group([
            self.merge_btn, self.split_btn, self.reduce_btn, self.export_btn,
        ]))

    def _make_button(self, text: str, icon_name: str, tooltip: str,
                     signal, danger: bool = False) -> QToolButton:
        btn = QToolButton(self)
        btn.setObjectName("organizeBtnDanger" if danger else "organizeBtn")
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setAccessibleName(text)
        btn.setAccessibleDescription(tooltip)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setIconSize(self._ICON_SIZE)
        btn.setFixedHeight(28)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("icon_name", icon_name)   # remembered for re-theming
        btn.clicked.connect(signal.emit)
        self._all_buttons.append(btn)
        return btn

    def _make_group(self, buttons: List[QToolButton]) -> QFrame:
        group = QFrame(self)
        group.setObjectName("organizeGroup")
        group.setFixedHeight(30)
        group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        gl = QHBoxLayout(group)
        gl.setContentsMargins(2, 1, 2, 1)
        gl.setSpacing(1)
        for b in buttons:
            gl.addWidget(b)
        return group

    def _make_divider(self) -> QWidget:
        sep = QWidget(self)
        sep.setObjectName("organizeDivider")
        sep.setFixedSize(1, 18)
        return sep

    # ==================================================================
    #  THEME
    # ==================================================================
    def _icon_color(self) -> str:
        return (StudioTheme.DARK_TEXT_PRIMARY
                if self._theme == "dark"
                else StudioTheme.LIGHT_TEXT_PRIMARY)

    def _danger_color(self) -> str:
        return (StudioTheme.DARK_DANGER
                if self._theme == "dark"
                else StudioTheme.LIGHT_DANGER)

    def update_theme(self, theme_name) -> None:
        new_theme = _resolve_theme(theme_name)
        if new_theme == self._theme:
            return
        self._theme = new_theme
        self._apply_style()
        self.update_icons(self._icon_color())

    def _apply_style(self) -> None:
        is_dark = self._theme == "dark"
        s = StudioTheme

        bg             = s.DARK_BG_WINDOW   if is_dark else s.LIGHT_BG_WINDOW
        border         = s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE
        group_bg       = s.DARK_BG_CARD     if is_dark else s.LIGHT_BG_CARD
        group_bdr      = s.DARK_BORDER      if is_dark else s.LIGHT_BORDER
        btn_hover      = s.DARK_BG_HOVER    if is_dark else s.LIGHT_BG_HOVER
        btn_press      = s.DARK_BG_ACTIVE  if is_dark else s.LIGHT_BG_ACTIVE
        text_primary   = s.DARK_TEXT_PRIMARY   if is_dark else s.LIGHT_TEXT_PRIMARY
        text_secondary = s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY
        accent         = s.DARK_ACCENT      if is_dark else s.LIGHT_ACCENT
        danger         = self._danger_color()

        self.setStyleSheet(f"""
            #organizeActionBar {{
                background-color: {bg};
                border-bottom: 1px solid {border};
            }}
            #organizeTitle {{
                color: {text_secondary};
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 600;
                padding: 0 4px;
            }}
            #organizeGroup {{
                background-color: {group_bg};
                border: 1px solid {group_bdr};
                border-radius: 7px;
            }}
            #organizeDivider {{
                background-color: {border};
                border: none;
            }}
            QToolButton#organizeBtn, QToolButton#organizeBtnDanger {{
                background: transparent;
                border: none;
                border-radius: 5px;
                padding: 3px 8px;
                font-family: {s.FONT_FAMILY};
                font-size: 11px;
                font-weight: 500;
                color: {text_primary};
            }}
            QToolButton#organizeBtn:hover, QToolButton#organizeBtnDanger:hover {{
                background-color: {btn_hover};
            }}
            QToolButton#organizeBtn:pressed, QToolButton#organizeBtnDanger:pressed {{
                background-color: {btn_press};
            }}
            QToolButton#organizeBtn:disabled, QToolButton#organizeBtnDanger:disabled {{
                color: {text_secondary};
            }}
            QToolButton#organizeBtnDanger {{
                color: {danger};
            }}
            QToolButton#organizeBtn:checked, QToolButton#organizeBtnDanger:checked {{
                background-color: {accent};
                color: #ffffff;
            }}
        """)

    # ==================================================================
    #  ICONS
    # ==================================================================
    def update_icons(self, color_hex: str) -> None:
        danger = self._danger_color()
        size = self._ICON_SIZE.width()
        for btn in self._all_buttons:
            name = btn.property("icon_name")
            if not name:
                continue
            col = danger if btn.objectName() == "organizeBtnDanger" else color_hex
            btn.setIcon(_icon_or_blank(name, col, size))

    # ==================================================================
    #  CONTEXT — enable/disable buttons based on document state
    # ==================================================================
    def set_context(self, has_document: bool,
                    page_count: int = 0,
                    current_page: int = 0) -> None:
        """Enable/disable buttons based on the current document state.

        Call this whenever the active document or the page selection changes.

        Args:
            has_document: True if any document is currently open.
            page_count:   Number of pages in the document (0 if none).
            current_page: Index of the selected page (0-based).
        """
        if not isinstance(page_count, int) or isinstance(page_count, bool):
            page_count = 0
        if not isinstance(current_page, int) or isinstance(current_page, bool):
            current_page = 0

        has_pages    = has_document and page_count >= 1
        multi_page   = has_document and page_count >= 2
        at_first     = has_pages and current_page <= 0
        at_last      = has_pages and current_page >= page_count - 1

        self.rot_left_btn.setEnabled(has_pages)
        self.rot_right_btn.setEnabled(has_pages)
        can_flip = has_pages and not getattr(self, "_is_pdf", False)
        self.flip_h_btn.setEnabled(can_flip)
        self.flip_v_btn.setEnabled(can_flip)
        flip_tip = ("Flip page horizontally" if can_flip
                    else "Flip is only available for image documents")
        flip_tip_v = ("Flip page vertically" if can_flip
                      else "Flip is only available for image documents")
        self.flip_h_btn.setToolTip(flip_tip)
        self.flip_v_btn.setToolTip(flip_tip_v)

        self.dup_btn.setEnabled(has_pages)
        self.insert_blank_btn.setEnabled(has_pages)
        self.insert_file_btn.setEnabled(has_document)
        self.insert_clipboard_btn.setEnabled(has_document)
        self.del_btn.setEnabled(multi_page)

        self.crop_btn.setEnabled(has_pages)
        self.resize_btn.setEnabled(has_pages)
        self.move_up_btn.setEnabled(has_pages and not at_first)
        self.move_down_btn.setEnabled(has_pages and not at_last)

        self.merge_btn.setEnabled(True)                    # can always start fresh
        self.split_btn.setEnabled(multi_page)
        self.reduce_btn.setEnabled(has_document)
        self.export_btn.setEnabled(has_document)

    # ==================================================================
    #  SHORTCUTS — hand these to the window so they're scoped correctly
    # ==================================================================
    def shortcut_specs(self) -> List[Tuple[QKeySequence, pyqtSignal]]:
        """Return (key sequence, signal) pairs for the caller to bind at window level.

        Do NOT bind these to individual QToolButtons — a QAbstractButton
        shortcut is window-scoped, which means e.g. pressing Delete inside a
        text field would silently delete the current page. The window should
        create QShortcut objects with WidgetWithChildrenShortcut or check
        focus state before firing.

        Delete is intentionally NOT included — its correct behavior depends
        on the active focus widget and should be wired by the window.
        """
        return [
            (QKeySequence("Ctrl+L"),         self.rotate_left_requested),
            (QKeySequence("Ctrl+R"),         self.rotate_right_requested),
            (QKeySequence("Ctrl+D"),         self.duplicate_page_requested),
            (QKeySequence("Ctrl+Shift+I"),   self.insert_file_requested),
            (QKeySequence("Ctrl+E"),         self.export_requested),
            (QKeySequence("Ctrl+Up"),        self.move_up_requested),
            (QKeySequence("Ctrl+Down"),      self.move_down_requested),
        ]

    # ==================================================================
    #  RESPONSIVE
    # ==================================================================
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        compact = self.width() < self._COMPACT_BREAKPOINT
        if compact == self._compact:
            return
        self._compact = compact
        style = (Qt.ToolButtonStyle.ToolButtonIconOnly
                 if compact
                 else Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        for btn in self._all_buttons:
            btn.setToolButtonStyle(style)
            btn.updateGeometry()
        self._title.setVisible(not compact)
        self._layout.invalidate()
        self.updateGeometry()