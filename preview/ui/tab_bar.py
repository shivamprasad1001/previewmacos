"""
macOS-styled Window Tabs and Document Tab Bar for Preview macOS.
Provides multi-tab document management, tab reordering, close buttons,
and dirty state indicators.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import uuid

from PyQt6.QtWidgets import QWidget, QTabBar, QHBoxLayout, QToolButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor

from preview.core.document import Document
from preview.core.history import HistoryManager
from preview.theme import MacTheme, StudioTheme



@dataclass
class DocumentTabState:
    """Encapsulates independent document state for a single tab."""
    tab_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document: Optional[Document] = None
    file_path: Optional[str] = None
    title: str = "Untitled"
    current_page: int = 0
    zoom: float = 1.0
    view_mode: str = "Single"
    pan_offset: QPointF = field(default_factory=lambda: QPointF(0, 0))
    annotations: Dict[int, List[Any]] = field(default_factory=dict)
    history: HistoryManager = field(default_factory=HistoryManager)
    is_modified: bool = False

class MacTabBar(QTabBar):
    """Sleek macOS-styled QTabBar supporting reordering and close buttons."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macTabBar")
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setExpanding(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideMiddle)
        self.setDrawBase(False)
        self._theme: str = "dark"
        self._apply_style()

    def update_theme(self, theme_name: str):
        self._theme = theme_name
        self._apply_style()

    def _apply_style(self):
        is_dark = (self._theme == "dark")
        if is_dark:
            bg_bar = StudioTheme.DARK_BG_WINDOW
            border_bottom = StudioTheme.DARK_BORDER_SUBTLE
            tab_bg = "transparent"
            tab_color = StudioTheme.DARK_TEXT_SECONDARY
            tab_sel_bg = StudioTheme.DARK_BG_CARD
            tab_sel_color = StudioTheme.DARK_TEXT_PRIMARY
            tab_sel_border = StudioTheme.DARK_BORDER
            tab_hover_bg = StudioTheme.DARK_BG_HOVER
            tab_hover_color = "#ffffff"
            close_hover = StudioTheme.DARK_DANGER_SUBTLE
            accent = StudioTheme.DARK_ACCENT
        else:
            bg_bar = StudioTheme.LIGHT_BG_WINDOW
            border_bottom = StudioTheme.LIGHT_BORDER_SUBTLE
            tab_bg = "transparent"
            tab_color = StudioTheme.LIGHT_TEXT_SECONDARY
            tab_sel_bg = StudioTheme.LIGHT_BG_CARD
            tab_sel_color = StudioTheme.LIGHT_TEXT_PRIMARY
            tab_sel_border = StudioTheme.LIGHT_BORDER
            tab_hover_bg = StudioTheme.LIGHT_BG_HOVER
            tab_hover_color = "#000000"
            close_hover = "rgba(239, 68, 68, 0.15)"
            accent = StudioTheme.LIGHT_ACCENT

        self.setStyleSheet(f"""
            QTabBar#macTabBar {{
                background-color: {bg_bar};
                border: none;
                border-bottom: 1px solid {border_bottom};
                padding: 3px 6px 0px 6px;
            }}
            QTabBar#macTabBar::tab {{
                background-color: {tab_bg};
                color: {tab_color};
                font-size: 12px;
                font-family: {StudioTheme.FONT_FAMILY};
                font-weight: 500;
                border: 1px solid transparent;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 100px;
                max-width: 220px;
                height: 25px;
                padding: 1px 12px 1px 12px;
                margin-right: 2px;
            }}
            QTabBar#macTabBar::tab:selected {{
                background-color: {tab_sel_bg};
                color: {tab_sel_color};
                font-weight: 600;
                border: 1px solid {tab_sel_border};
                border-top: 2px solid {accent};
                border-bottom: none;
            }}
            QTabBar#macTabBar::tab:hover:!selected {{
                background-color: {tab_hover_bg};
                color: {tab_hover_color};
            }}
            QTabBar#macTabBar::close-button {{
                subcontrol-position: right;
                subcontrol-origin: padding;
                margin-left: 6px;
                border-radius: 4px;
                padding: 2px;
            }}
            QTabBar#macTabBar::close-button:hover {{
                background-color: {close_hover};
            }}
        """)

class MacTabBarContainer(QWidget):
    """Container holding MacTabBar and the '+' New Tab button."""
    new_tab_clicked = pyqtSignal()
    tab_close_requested = pyqtSignal(int)
    current_changed = pyqtSignal(int)
    tab_moved = pyqtSignal(int, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macTabBarContainer")
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(4)

        self.tab_bar = MacTabBar(self)
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        self.tab_bar.currentChanged.connect(self.current_changed.emit)
        self.tab_bar.tabMoved.connect(self.tab_moved.emit)
        layout.addWidget(self.tab_bar, 1)

        self.add_tab_btn = QToolButton(self)
        self.add_tab_btn.setObjectName("newTabBtn")
        self.add_tab_btn.setText("+")
        self.add_tab_btn.setFixedSize(22, 22)
        self.add_tab_btn.setToolTip("New Tab (Ctrl+T)")
        self.add_tab_btn.clicked.connect(self.new_tab_clicked.emit)
        layout.addWidget(self.add_tab_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def update_theme(self, theme_name: str):
        self.tab_bar.update_theme(theme_name)
        is_dark = (theme_name == "dark")
        bg_bar = StudioTheme.DARK_BG_WINDOW if is_dark else StudioTheme.LIGHT_BG_WINDOW
        border_b = StudioTheme.DARK_BORDER_SUBTLE if is_dark else StudioTheme.LIGHT_BORDER_SUBTLE
        btn_hover = StudioTheme.DARK_BG_HOVER if is_dark else StudioTheme.LIGHT_BG_HOVER
        btn_col = StudioTheme.DARK_TEXT_SECONDARY if is_dark else StudioTheme.LIGHT_TEXT_SECONDARY

        self.setStyleSheet(f"""
            #macTabBarContainer {{
                background-color: {bg_bar};
                border-bottom: 1px solid {border_b};
            }}
            #newTabBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {btn_col};
                font-size: 16px;
                font-weight: 400;
            }}
            #newTabBtn:hover {{
                background-color: {btn_hover};
                color: {"#ffffff" if is_dark else "#000000"};
            }}
        """)
