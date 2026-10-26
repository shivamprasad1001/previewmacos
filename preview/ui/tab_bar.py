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
from preview.theme import MacTheme



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
            bg_bar = "#1c1c1e"
            border_bottom = "rgba(255, 255, 255, 0.12)"
            tab_bg = "transparent"
            tab_color = "#98989d"
            tab_sel_bg = "#2c2c2e"
            tab_sel_color = "#f5f5f7"
            tab_sel_border = "rgba(255, 255, 255, 0.16)"
            tab_hover_bg = "rgba(255, 255, 255, 0.08)"
            tab_hover_color = "#ffffff"
            close_hover = "rgba(255, 255, 255, 0.20)"
        else:
            bg_bar = "#e5e5ea"
            border_bottom = "rgba(0, 0, 0, 0.14)"
            tab_bg = "transparent"
            tab_color = "#636366"
            tab_sel_bg = "#ffffff"
            tab_sel_color = "#1c1c1e"
            tab_sel_border = "rgba(0, 0, 0, 0.12)"
            tab_hover_bg = "rgba(0, 0, 0, 0.06)"
            tab_hover_color = "#000000"
            close_hover = "rgba(0, 0, 0, 0.15)"

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
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
                font-weight: 450;
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
                font-weight: 550;
                border: 1px solid {tab_sel_border};
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
                border-radius: 7px;
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
        bg_bar = "#1c1c1e" if is_dark else "#e5e5ea"
        border_b = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.14)"
        btn_hover = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.10)"
        btn_col = "#c7c7cc" if is_dark else "#3a3a3c"

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
