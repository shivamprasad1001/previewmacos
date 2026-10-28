"""
macOS Theme definitions and styles for Preview app on Linux.
Provides pixel-faithful macOS styling for both Dark and Light modes.
"""

import sys
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QGuiApplication

class MacTheme:
    DARK = "dark"
    LIGHT = "light"

    # Dark Mode
    DARK_BG_WINDOW = "#1e1e1e"
    DARK_BG_TOOLBAR = "#28282b"
    DARK_BG_SIDEBAR = "#202022"
    DARK_BG_CANVAS = "#141416"
    DARK_BG_CARD = "#2a2a2d"
    DARK_TEXT_PRIMARY = "#f5f5f7"
    DARK_TEXT_SECONDARY = "#98989d"
    DARK_BORDER = "#38383a"
    DARK_ACCENT = "#0a84ff"
    DARK_HOVER = "#363639"
    DARK_ACTIVE = "#444448"

    # Light Mode
    LIGHT_BG_WINDOW = "#f5f5f7"
    LIGHT_BG_TOOLBAR = "#f0f0f3"
    LIGHT_BG_SIDEBAR = "#e8e8ed"
    LIGHT_BG_CANVAS = "#ececf0"
    LIGHT_BG_CARD = "#ffffff"
    LIGHT_TEXT_PRIMARY = "#1d1d1f"
    LIGHT_TEXT_SECONDARY = "#6e6e73"
    LIGHT_BORDER = "#d2d2d7"
    LIGHT_ACCENT = "#0a84ff"
    LIGHT_HOVER = "#e5e5ea"
    LIGHT_ACTIVE = "#d8d8de"

    # Traffic light colors
    TRAFFIC_RED = "#ff5f57"
    TRAFFIC_RED_BORDER = "#e0443e"
    TRAFFIC_YELLOW = "#febc2e"
    TRAFFIC_YELLOW_BORDER = "#dea123"
    TRAFFIC_GREEN = "#28c840"
    TRAFFIC_GREEN_BORDER = "#1aab29"

    # Design Tokens - Spacing Scale (4/8/12/16/24)
    SPACE_4 = 4
    SPACE_8 = 8
    SPACE_12 = 12
    SPACE_16 = 16
    SPACE_24 = 24

    # Design Tokens - Radii Scale (6/8/12)
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12

    # Design Tokens - Dimensions
    HEADER_HEIGHT = 48
    TOOLBAR_HEIGHT = 44
    BTN_SIZE = 32
    FONT_SIZE_BASE = 13

    @classmethod
    def get_stylesheet(cls, mode: str = "dark") -> str:
        if mode == cls.LIGHT:
            return cls._light_stylesheet()
        return cls._dark_stylesheet()

    @classmethod
    def _dark_stylesheet(cls) -> str:
        return f"""
        QMainWindow {{
            background: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
            font-family: "Inter", -apple-system, sans-serif;
        }}
        
        #rootContainer {{
            background: transparent;
        }}

        #windowFrame {{
            background-color: {cls.DARK_BG_WINDOW};
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.10);
        }}

        QWidget {{
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 13px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        /* Clean macOS Menu Bar */
        #macMenubar {{
            background-color: {cls.DARK_BG_WINDOW};
            color: {cls.DARK_TEXT_PRIMARY};
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            padding: 2px 10px;
            font-size: 12px;
            font-family: "Inter", -apple-system, sans-serif;
        }}

        #macMenubar::item {{
            background: transparent;
            padding: 3px 9px;
            border-radius: 4px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #macMenubar::item:selected {{
            background-color: rgba(255, 255, 255, 0.12);
        }}

        /* Unified macOS Header Bar (48px tall, 1px bottom border) */
        #macToolbar {{
            background-color: {cls.DARK_BG_TOOLBAR};
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            padding: 0px 16px;
            min-height: 48px;
            max-height: 48px;
            height: 48px;
        }}

        #toolbarDivider {{
            background-color: rgba(255, 255, 255, 0.12);
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 20px;
            min-height: 20px;
            max-height: 20px;
        }}
        
        #windowTitleLabel {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 550;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #pageBadge {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #98989d;
            background-color: rgba(255, 255, 255, 0.09);
            border-radius: 4px;
            padding: 1px 6px;
        }}

        #markupToolbar, #organizeActionBar {{
            background-color: {cls.DARK_BG_SIDEBAR};
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 0px 12px;
            min-height: 44px;
            max-height: 44px;
            height: 44px;
        }}

        #primaryStrip {{
            background: transparent;
            min-height: 44px;
            max-height: 44px;
            height: 44px;
        }}

        #markupGroup {{
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 6px;
            padding: 1px;
            min-height: 34px;
            max-height: 34px;
        }}

        #markupGroupSeparator {{
            background-color: rgba(255, 255, 255, 0.12);
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 18px;
        }}

        #markupGroup QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 2px;
            min-height: 32px;
            max-height: 32px;
            min-width: 32px;
            max-width: 32px;
        }}

        #markupGroup QToolButton#selectBtn,
        #markupGroup QToolButton#shapesBtn,
        #overflowBtn {{
            min-width: 40px;
            max-width: 44px;
            min-height: 32px;
            max-height: 32px;
        }}

        #markupGroup QToolButton:hover, #overflowBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            border-color: transparent;
        }}

        #markupGroup QToolButton:pressed, #overflowBtn:pressed {{
            background-color: rgba(255, 255, 255, 0.14);
            border-color: transparent;
        }}

        #markupGroup QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            border: 1px solid {cls.DARK_ACCENT};
            border-radius: 6px;
            color: #ffffff;
        }}

        #markupGroup QToolButton:focus, #overflowBtn:focus, QToolButton:focus, QPushButton:focus {{
            outline: 2px solid {cls.DARK_ACCENT};
            outline-offset: 1px;
        }}

        #markupGroup QToolButton:disabled, #overflowBtn:disabled {{
            color: #555558;
            opacity: 0.35;
        }}

        #contextFormattingBar {{
            background: transparent;
            border: none;
            padding: 0px 4px;
            min-height: 32px;
            max-height: 32px;
        }}

        #contextFormattingBar QToolButton {{
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 3px 10px;
            font-size: 12px;
            font-weight: 500;
            min-height: 28px;
            max-height: 28px;
            min-width: 28px;
            max-width: none;
        }}

        #contextFormattingBar QToolButton:hover {{
            background-color: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.14);
        }}

        #contextFormattingBar QToolButton:pressed {{
            background-color: rgba(255, 255, 255, 0.18);
        }}

        #contextFormattingBar QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            border-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Icon-only Buttons & Standard Buttons (28px height, 6px radius, flat 8% hover / 14% pressed) */
        QToolButton, QPushButton {{
            background-color: transparent;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 2px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        QToolButton:hover, QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.16);
        }}

        QToolButton:pressed, QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.14);
            border-color: rgba(255, 255, 255, 0.22);
        }}

        QToolButton:checked, QPushButton:checked {{
            background-color: {cls.DARK_ACCENT};
            border-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        QToolButton::menu-indicator {{
            image: none;
            width: 0px;
        }}

        /* Joined Segmented Control Pairs */
        #prevBtn, #zoomOutBtn {{
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }}

        #nextBtn, #zoomInBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            border-left: none;
        }}

        #openMainBtn {{
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            padding: 0px 8px 0px 6px;
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        #openMainBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
        }}
        #openMainBtn:pressed {{
            background-color: rgba(255, 255, 255, 0.14);
        }}

        #openArrowBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: none;
            padding: 0px;
            background-color: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        #openArrowBtn:hover {{
            background-color: rgba(255, 255, 255, 0.08);
        }}
        #openArrowBtn:pressed {{
            background-color: rgba(255, 255, 255, 0.14);
        }}

        /* Markup Pill Button (Primary Button) */
        #markupPillBtn {{
            border-radius: 6px;
            padding: 0px 14px;
            font-size: 13px;
            font-weight: 600;
            background-color: rgba(10, 132, 255, 0.16);
            border: 1px solid rgba(10, 132, 255, 0.45);
            color: #0a84ff;
            min-height: 32px;
            max-height: 32px;
        }}

        #markupPillBtn:hover {{
            background-color: rgba(10, 132, 255, 0.26);
            border-color: #0a84ff;
        }}

        #markupPillBtn:pressed {{
            background-color: #0071e3;
            color: #ffffff;
        }}

        #markupPillBtn:checked {{
            background-color: {cls.DARK_ACCENT};
            border-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        /* Sidebar Segmented Control Tabs */
        #sidebarSegmented {{
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 2px;
            margin: 6px 8px;
        }}
        #sidebarSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 5px;
            color: #98989d;
            font-size: 11px;
            font-weight: 500;
            padding: 3px 6px;
            min-height: 24px;
            max-height: 24px;
        }}
        #sidebarSegmented QToolButton:hover {{
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.06);
        }}
        #sidebarSegmented QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Empty State in Canvas */
        #emptyStateOverlay {{
            background: transparent;
        }}
        #emptyStateCard {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 36px 44px;
        }}
        #emptyStateCard[dragHover="true"] {{
            border: 2px dashed {cls.DARK_ACCENT};
            background-color: rgba(10, 132, 255, 0.08);
        }}
        #emptyStateTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        #emptyStateHint {{
            font-size: 12px;
            color: {cls.DARK_TEXT_SECONDARY};
        }}
        #emptyStateOpenBtn {{
            background-color: {cls.DARK_ACCENT};
            border: 1px solid {cls.DARK_ACCENT};
            border-radius: 6px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 32px;
        }}
        #emptyStateOpenBtn:hover {{
            background-color: #0071e3;
        }}

        /* Search Field with Magnifier and Focus Ring in Accent Color */
        #macSearchField {{
            background-color: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding-left: 6px;
            padding-right: 10px;
            min-height: 28px;
            max-height: 28px;
            font-size: 12px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #macSearchField:focus {{
            border: 2px solid {cls.DARK_ACCENT};
            background-color: rgba(255, 255, 255, 0.11);
        }}

        /* Traffic light buttons */
        #trafficClose {{
            background-color: {cls.TRAFFIC_RED};
            border: 1px solid {cls.TRAFFIC_RED_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficClose:hover {{
            background-color: #ff3b30;
        }}

        #trafficMinimize {{
            background-color: {cls.TRAFFIC_YELLOW};
            border: 1px solid {cls.TRAFFIC_YELLOW_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficMinimize:hover {{
            background-color: #ff9500;
        }}

        #trafficMaximize {{
            background-color: {cls.TRAFFIC_GREEN};
            border: 1px solid {cls.TRAFFIC_GREEN_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficMaximize:hover {{
            background-color: #34c759;
        }}

        /* Sidebar Styling & Splitter */
        #macSidebar {{
            background-color: {cls.DARK_BG_SIDEBAR};
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }}

        #sidebarHeader {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            background-color: transparent;
        }}

        #sidebarDropdown {{
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 5px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 500;
        }}

        #sidebarDropdown:hover {{
            background-color: rgba(255, 255, 255, 0.12);
        }}

        QSplitter::handle:horizontal {{
            background-color: rgba(255, 255, 255, 0.08);
            width: 1px;
        }}

        QSplitter::handle:horizontal:hover {{
            background-color: {cls.DARK_ACCENT};
            width: 2px;
        }}

        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 6px 4px;
        }}

        QListWidget::item {{
            background: transparent;
            border: none;
            border-radius: 6px;
        }}

        QListWidget::item:selected {{
            background: transparent;
        }}

        /* Document Canvas Background */
        #documentCanvas {{
            background-color: {cls.DARK_BG_CANVAS};
            border: none;
        }}

        QScrollArea {{
            background-color: {cls.DARK_BG_CANVAS};
            border: none;
        }}

        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.22);
            min-height: 30px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.38);
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background: rgba(255, 255, 255, 0.22);
            min-width: 30px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0px;
            height: 0px;
        }}

        /* Search input & text inputs */
        QLineEdit {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            padding: 3px 8px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: 12px;
            selection-background-color: {cls.DARK_ACCENT};
        }}

        QLineEdit:focus {{
            border: 1px solid {cls.DARK_ACCENT};
            background-color: rgba(255, 255, 255, 0.12);
        }}

        /* SpinBox & Font Controls */
        QSpinBox {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 2px 4px 2px 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: 12px;
            min-height: 24px;
        }}

        QSpinBox:focus {{
            border: 2px solid {cls.DARK_ACCENT};
            background-color: rgba(255, 255, 255, 0.12);
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background: transparent;
            border: none;
            width: 14px;
        }}

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: rgba(255, 255, 255, 0.10);
            border-radius: 2px;
        }}

        /* Dropdown & ComboBox */
        QFontComboBox, QComboBox {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            padding: 2px 8px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: 12px;
            min-height: 24px;
        }}

        QFontComboBox:focus, QComboBox:focus {{
            border: 2px solid {cls.DARK_ACCENT};
            background-color: rgba(255, 255, 255, 0.12);
        }}

        QFontComboBox::drop-down, QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}

        QFontComboBox QAbstractItemView, QComboBox QAbstractItemView {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            selection-background-color: {cls.DARK_ACCENT};
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 4px;
        }}

        /* Dialogs and Popovers */
        QDialog {{
            background-color: {cls.DARK_BG_WINDOW};
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QTabWidget::pane {{
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            background-color: {cls.DARK_BG_CARD};
            padding: 8px;
        }}

        QTabBar::tab {{
            background-color: transparent;
            color: {cls.DARK_TEXT_SECONDARY};
            border: none;
            padding: 5px 12px;
            border-radius: 6px;
            margin: 2px;
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            background-color: rgba(255, 255, 255, 0.15);
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        /* Slider */
        QSlider::groove:horizontal {{
            height: 4px;
            background: {cls.DARK_BORDER};
            border-radius: 2px;
        }}

        QSlider::sub-page:horizontal {{
            background: {cls.DARK_ACCENT};
            border-radius: 2px;
        }}

        QSlider::handle:horizontal {{
            background: #ffffff;
            border: 1px solid #777777;
            width: 14px;
            margin-top: -5px;
            margin-bottom: -5px;
            border-radius: 7px;
        }}

        /* Tooltips */
        QToolTip {{
            background-color: #2b2b2e;
            color: #ffffff;
            border: 1px solid #4a4a4d;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
        }}

        /* Menus */
        QMenu {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 8px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 5px 18px 5px 10px;
            border-radius: 4px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QMenu::item:selected {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {cls.DARK_BORDER};
            margin: 3px 6px;
        }}

        QStatusBar, #macStatusBar {{
            background-color: {cls.DARK_BG_TOOLBAR};
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: 11px;
            font-family: "Inter", -apple-system, sans-serif;
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 2px 12px;
            min-height: 24px;
            max-height: 24px;
        }}

        #macStatusBar QLabel {{
            color: {cls.DARK_TEXT_SECONDARY};
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        }}

        /* Floating Status Pill */
        #floatingStatusPill {{
            background-color: rgba(36, 36, 40, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 14px;
        }}

        #floatingStatusLabel {{
            color: #f5f5f7;
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        }}

        /* Workspace Mode Switcher Segmented Control */
        #modeSegmented {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 1px;
        }}
        #modeSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 5px;
            color: #98989d;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 8px;
            min-height: 24px;
            max-height: 24px;
        }}
        #modeSegmented QToolButton:hover {{
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.06);
        }}
        #modeSegmented QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Context Formatting Bar */
        #contextFormattingBar {{
            background-color: #1a1a1c;
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 2px 10px;
        }}

        /* Organize Action Bar */
        #organizeActionBar {{
            background-color: {cls.DARK_BG_SIDEBAR};
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 2px 10px;
        }}

        /* Collapsible Right Inspector Panel */
        #macInspectorPanel {{
            background-color: {cls.DARK_BG_SIDEBAR};
            border-left: 1px solid rgba(255, 255, 255, 0.08);
        }}
        #macInspectorPanel QScrollArea,
        #macInspectorPanel QScrollArea > QWidget > QWidget {{
            background: transparent;
            border: none;
        }}
        #inspectorHeader {{
            background-color: {cls.DARK_BG_TOOLBAR};
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}
        #inspectorSegmented {{
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            padding: 1px;
        }}
        #inspectorSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 4px;
            color: #98989d;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 6px;
        }}
        #inspectorSegmented QToolButton:hover {{
            color: #ffffff;
        }}
        #inspectorSegmented QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}
        #inspectorCloseBtn {{
            background: transparent;
            border: none;
            color: #98989d;
            font-size: 14px;
            font-weight: 600;
        }}
        #inspectorCloseBtn:hover {{
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.12);
            border-radius: 4px;
        }}
        #inspectorCard {{
            background-color: {cls.DARK_BG_CARD};
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }}
        #inspectorAnnotList {{
            background-color: {cls.DARK_BG_WINDOW};
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: 12px;
            outline: none;
        }}
        #inspectorAnnotList::item {{
            padding: 6px 8px;
            border-radius: 4px;
        }}
        #inspectorAnnotList::item:hover {{
            background-color: rgba(255, 255, 255, 0.06);
        }}
        #inspectorAnnotList::item:selected {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}
        """

    @classmethod
    def _light_stylesheet(cls) -> str:
        return f"""
        QMainWindow {{
            background: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-family: "Inter", -apple-system, sans-serif;
        }}
        
        #rootContainer {{
            background: transparent;
        }}

        #windowFrame {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border-radius: 10px;
            border: 1px solid rgba(0, 0, 0, 0.15);
        }}

        QWidget {{
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 13px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        /* Clean macOS Menu Bar */
        #macMenubar {{
            background-color: {cls.LIGHT_BG_WINDOW};
            color: {cls.LIGHT_TEXT_PRIMARY};
            border: none;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            padding: 2px 10px;
            font-size: 12px;
            font-family: "Inter", -apple-system, sans-serif;
        }}

        #macMenubar::item {{
            background: transparent;
            padding: 3px 9px;
            border-radius: 4px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #macMenubar::item:selected {{
            background-color: rgba(0, 0, 0, 0.08);
        }}

        /* Unified macOS Header Bar (48px tall, 1px bottom border) */
        #macToolbar {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            border: none;
            border-bottom: 1px solid rgba(0, 0, 0, 0.12);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            padding: 0px 16px;
            min-height: 48px;
            max-height: 48px;
            height: 48px;
        }}

        #toolbarDivider {{
            background-color: rgba(0, 0, 0, 0.12);
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 20px;
            min-height: 20px;
            max-height: 20px;
        }}
        
        #windowTitleLabel {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 550;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #pageBadge {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #6e6e73;
            background-color: rgba(0, 0, 0, 0.06);
            border-radius: 4px;
            padding: 1px 6px;
        }}

        #markupToolbar, #organizeActionBar {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: none;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding: 0px 12px;
            min-height: 44px;
            max-height: 44px;
            height: 44px;
        }}

        #primaryStrip {{
            background: transparent;
            min-height: 44px;
            max-height: 44px;
            height: 44px;
        }}

        #markupGroup {{
            background-color: rgba(0, 0, 0, 0.03);
            border: 1px solid rgba(0, 0, 0, 0.07);
            border-radius: 6px;
            padding: 1px;
            min-height: 34px;
            max-height: 34px;
        }}

        #markupGroupSeparator {{
            background-color: rgba(0, 0, 0, 0.10);
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 18px;
        }}

        #markupGroup QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 2px;
            min-height: 32px;
            max-height: 32px;
            min-width: 32px;
            max-width: 32px;
        }}

        #markupGroup QToolButton#selectBtn,
        #markupGroup QToolButton#shapesBtn,
        #overflowBtn {{
            min-width: 40px;
            max-width: 44px;
            min-height: 32px;
            max-height: 32px;
        }}

        #markupGroup QToolButton:hover, #overflowBtn:hover {{
            background-color: rgba(0, 0, 0, 0.06);
            border-color: transparent;
        }}

        #markupGroup QToolButton:pressed, #overflowBtn:pressed {{
            background-color: rgba(0, 0, 0, 0.12);
            border-color: transparent;
        }}

        #markupGroup QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border: 1px solid {cls.LIGHT_ACCENT};
            border-radius: 6px;
            color: #ffffff;
        }}

        #markupGroup QToolButton:focus, #overflowBtn:focus, QToolButton:focus, QPushButton:focus {{
            outline: 2px solid {cls.LIGHT_ACCENT};
            outline-offset: 1px;
        }}

        #markupGroup QToolButton:disabled, #overflowBtn:disabled {{
            color: #8e8e93;
            opacity: 0.35;
        }}

        #contextFormattingBar {{
            background: transparent;
            border: none;
            padding: 0px 4px;
            min-height: 32px;
            max-height: 32px;
        }}

        #contextFormattingBar QToolButton {{
            background-color: rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 3px 10px;
            font-size: 12px;
            font-weight: 500;
            min-height: 28px;
            max-height: 28px;
            min-width: 28px;
            max-width: none;
        }}

        #contextFormattingBar QToolButton:hover {{
            background-color: rgba(0, 0, 0, 0.08);
            border-color: rgba(0, 0, 0, 0.12);
        }}

        #contextFormattingBar QToolButton:pressed {{
            background-color: rgba(0, 0, 0, 0.14);
        }}

        #contextFormattingBar QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Markup Pill Button (Primary Button) */
        #markupPillBtn {{
            border-radius: 6px;
            padding: 0px 14px;
            font-size: 13px;
            font-weight: 600;
            background-color: rgba(10, 132, 255, 0.12);
            border: 1px solid rgba(10, 132, 255, 0.38);
            color: #0a84ff;
            min-height: 32px;
            max-height: 32px;
        }}

        #markupPillBtn:hover {{
            background-color: rgba(10, 132, 255, 0.20);
            border-color: #0a84ff;
        }}

        #markupPillBtn:pressed {{
            background-color: #0071e3;
            color: #ffffff;
        }}

        #markupPillBtn:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        /* Sidebar Segmented Control Tabs */
        #sidebarSegmented {{
            background-color: rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 6px;
            padding: 2px;
            margin: 6px 8px;
        }}
        #sidebarSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 5px;
            color: #6e6e73;
            font-size: 11px;
            font-weight: 500;
            padding: 3px 6px;
            min-height: 24px;
            max-height: 24px;
        }}
        #sidebarSegmented QToolButton:hover {{
            color: {cls.LIGHT_TEXT_PRIMARY};
            background-color: rgba(0, 0, 0, 0.04);
        }}
        #sidebarSegmented QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Empty State in Canvas */
        #emptyStateOverlay {{
            background: transparent;
        }}
        #emptyStateCard {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 36px 44px;
        }}
        #emptyStateCard[dragHover="true"] {{
            border: 2px dashed {cls.LIGHT_ACCENT};
            background-color: rgba(10, 132, 255, 0.06);
        }}
        #emptyStateTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}
        #emptyStateHint {{
            font-size: 12px;
            color: {cls.LIGHT_TEXT_SECONDARY};
        }}
        #emptyStateOpenBtn {{
            background-color: {cls.LIGHT_ACCENT};
            border: 1px solid {cls.LIGHT_ACCENT};
            border-radius: 6px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 32px;
        }}
        #emptyStateOpenBtn:hover {{
            background-color: #0071e3;
        }}

        /* Icon-only Buttons & Standard Buttons (28px height, 6px radius, flat 8% hover / 14% pressed) */
        QToolButton, QPushButton {{
            background-color: transparent;
            border: 1px solid rgba(0, 0, 0, 0.10);
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 2px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        QToolButton:hover, QPushButton:hover {{
            background-color: rgba(0, 0, 0, 0.08);
            border-color: rgba(0, 0, 0, 0.16);
        }}

        QToolButton:pressed, QPushButton:pressed {{
            background-color: rgba(0, 0, 0, 0.14);
            border-color: rgba(0, 0, 0, 0.22);
        }}

        QToolButton:checked, QPushButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        QToolButton::menu-indicator {{
            image: none;
            width: 0px;
        }}

        /* Joined Segmented Control Pairs */
        #prevBtn, #zoomOutBtn {{
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border-right: 1px solid rgba(0, 0, 0, 0.08);
        }}

        #nextBtn, #zoomInBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            border-left: none;
        }}

        #openMainBtn {{
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-right: 1px solid rgba(0, 0, 0, 0.10);
            padding: 0px 8px 0px 6px;
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}
        #openMainBtn:hover {{
            background-color: rgba(0, 0, 0, 0.06);
        }}
        #openMainBtn:pressed {{
            background-color: rgba(0, 0, 0, 0.12);
        }}

        #openArrowBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-left: none;
            padding: 0px;
            background-color: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}
        #openArrowBtn:hover {{
            background-color: rgba(0, 0, 0, 0.06);
        }}
        #openArrowBtn:pressed {{
            background-color: rgba(0, 0, 0, 0.12);
        }}

        /* Markup Pill Button (rounded 14px pill) */
        #markupPillBtn {{
            border-radius: 14px;
            padding: 0px 12px;
            font-size: 12px;
            font-weight: 500;
            background-color: rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.12);
        }}

        #markupPillBtn:hover {{
            background-color: rgba(0, 0, 0, 0.08);
        }}

        #markupPillBtn:pressed {{
            background-color: rgba(0, 0, 0, 0.14);
        }}

        #markupPillBtn:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        /* Search Field with Magnifier and Focus Ring in Accent Color */
        #macSearchField {{
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 14px;
            padding-left: 6px;
            padding-right: 10px;
            min-height: 28px;
            max-height: 28px;
            font-size: 12px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #macSearchField:focus {{
            border: 2px solid {cls.LIGHT_ACCENT};
            background-color: #ffffff;
        }}

        /* Traffic light buttons */
        #trafficClose {{
            background-color: {cls.TRAFFIC_RED};
            border: 1px solid {cls.TRAFFIC_RED_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficClose:hover {{
            background-color: #ff3b30;
        }}

        #trafficMinimize {{
            background-color: {cls.TRAFFIC_YELLOW};
            border: 1px solid {cls.TRAFFIC_YELLOW_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficMinimize:hover {{
            background-color: #ff9500;
        }}

        #trafficMaximize {{
            background-color: {cls.TRAFFIC_GREEN};
            border: 1px solid {cls.TRAFFIC_GREEN_BORDER};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
            padding: 0;
            margin: 0;
        }}
        #trafficMaximize:hover {{
            background-color: #34c759;
        }}

        /* Sidebar Styling & Splitter */
        #macSidebar {{
            background-color: rgba(232, 232, 237, 0.90);
            border-right: 1px solid rgba(0, 0, 0, 0.12);
        }}

        #sidebarHeader {{
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            background-color: transparent;
        }}

        #sidebarDropdown {{
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 5px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 500;
        }}

        #sidebarDropdown:hover {{
            background-color: rgba(0, 0, 0, 0.10);
        }}

        QSplitter::handle:horizontal {{
            background-color: rgba(0, 0, 0, 0.12);
            width: 1px;
        }}

        QSplitter::handle:horizontal:hover {{
            background-color: {cls.LIGHT_ACCENT};
            width: 2px;
        }}

        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 6px 4px;
        }}

        QListWidget::item {{
            background: transparent;
            border: none;
            border-radius: 6px;
        }}

        QListWidget::item:selected {{
            background: transparent;
        }}

        /* Document Canvas Background */
        #documentCanvas {{
            background-color: {cls.LIGHT_BG_CANVAS};
            border: none;
        }}

        QScrollArea {{
            background-color: {cls.LIGHT_BG_CANVAS};
            border: none;
        }}

        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.22);
            min-height: 30px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.38);
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background: rgba(0, 0, 0, 0.22);
            min-width: 30px;
            border-radius: 4px;
            margin: 1px;
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0px;
            height: 0px;
        }}

        /* Search input & text inputs */
        QLineEdit {{
            background-color: rgba(255, 255, 255, 0.85);
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            padding: 3px 8px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: 12px;
            selection-background-color: {cls.LIGHT_ACCENT};
        }}

        QLineEdit:focus {{
            border: 1px solid {cls.LIGHT_ACCENT};
            background-color: #ffffff;
        }}

        /* SpinBox & Font Controls */
        QSpinBox {{
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 6px;
            padding: 2px 4px 2px 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: 12px;
            min-height: 24px;
        }}

        QSpinBox:focus {{
            border: 2px solid {cls.LIGHT_ACCENT};
            background-color: #ffffff;
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background: transparent;
            border: none;
            width: 14px;
        }}

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: rgba(0, 0, 0, 0.06);
            border-radius: 2px;
        }}

        /* Dropdown & ComboBox */
        QFontComboBox, QComboBox {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            padding: 2px 8px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: 12px;
            min-height: 24px;
        }}

        QFontComboBox:focus, QComboBox:focus {{
            border: 2px solid {cls.LIGHT_ACCENT};
            background-color: #ffffff;
        }}

        QFontComboBox::drop-down, QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}

        QFontComboBox QAbstractItemView, QComboBox QAbstractItemView {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            selection-background-color: {cls.LIGHT_ACCENT};
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 4px;
        }}

        /* Dialogs and Popovers */
        QDialog {{
            background-color: {cls.LIGHT_BG_WINDOW};
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        QTabWidget::pane {{
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            background-color: {cls.LIGHT_BG_CARD};
            padding: 8px;
        }}

        QTabBar::tab {{
            background-color: transparent;
            color: {cls.LIGHT_TEXT_SECONDARY};
            border: none;
            padding: 5px 12px;
            border-radius: 6px;
            margin: 2px;
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            background-color: rgba(0, 0, 0, 0.08);
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        /* Slider */
        QSlider::groove:horizontal {{
            height: 4px;
            background: {cls.LIGHT_BORDER};
            border-radius: 2px;
        }}

        QSlider::sub-page:horizontal {{
            background: {cls.LIGHT_ACCENT};
            border-radius: 2px;
        }}

        QSlider::handle:horizontal {{
            background: #ffffff;
            border: 1px solid #c0c0c5;
            width: 14px;
            margin-top: -5px;
            margin-bottom: -5px;
            border-radius: 7px;
        }}

        /* Tooltips */
        QToolTip {{
            background-color: #ffffff;
            color: #1d1d1f;
            border: 1px solid #d2d2d7;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
        }}

        /* Menus */
        QMenu {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 8px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 5px 18px 5px 10px;
            border-radius: 4px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        QMenu::item:selected {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {cls.LIGHT_BORDER};
            margin: 3px 6px;
        }}

        QStatusBar, #macStatusBar {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: 11px;
            font-family: "Inter", -apple-system, sans-serif;
            border: none;
            border-top: 1px solid rgba(0, 0, 0, 0.08);
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 2px 12px;
            min-height: 24px;
            max-height: 24px;
        }}

        #macStatusBar QLabel {{
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        }}

        /* Floating Status Pill */
        #floatingStatusPill {{
            background-color: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 14px;
        }}

        #floatingStatusLabel {{
            color: #1d1d1f;
            font-family: "Inter", -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        }}

        /* Workspace Mode Switcher Segmented Control */
        #modeSegmented {{
            background-color: rgba(0, 0, 0, 0.06);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 6px;
            padding: 1px;
        }}
        #modeSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 5px;
            color: #6e6e73;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 8px;
            min-height: 24px;
            max-height: 24px;
        }}
        #modeSegmented QToolButton:hover {{
            color: #000000;
            background-color: rgba(0, 0, 0, 0.04);
        }}
        #modeSegmented QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Context Formatting Bar */
        #contextFormattingBar {{
            background-color: #f7f7f9;
            border: none;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding: 2px 10px;
        }}

        /* Organize Action Bar */
        #organizeActionBar {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: none;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding: 2px 10px;
        }}

        /* Collapsible Right Inspector Panel */
        #macInspectorPanel {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border-left: 1px solid rgba(0, 0, 0, 0.08);
        }}
        #macInspectorPanel QScrollArea,
        #macInspectorPanel QScrollArea > QWidget > QWidget {{
            background: transparent;
            border: none;
        }}
        #inspectorHeader {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        }}
        #inspectorSegmented {{
            background-color: rgba(0, 0, 0, 0.06);
            border-radius: 5px;
            padding: 1px;
        }}
        #inspectorSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: 4px;
            color: #6e6e73;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 6px;
        }}
        #inspectorSegmented QToolButton:hover {{
            color: #000000;
        }}
        #inspectorSegmented QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}
        #inspectorCloseBtn {{
            background: transparent;
            border: none;
            color: #6e6e73;
            font-size: 14px;
            font-weight: 600;
        }}
        #inspectorCloseBtn:hover {{
            color: #000000;
            background-color: rgba(0, 0, 0, 0.10);
            border-radius: 4px;
        }}
        #inspectorCard {{
            background-color: {cls.LIGHT_BG_CARD};
            border-radius: 6px;
            border: 1px solid rgba(0, 0, 0, 0.08);
        }}
        #inspectorAnnotList {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: 12px;
            outline: none;
        }}
        #inspectorAnnotList::item {{
            padding: 6px 8px;
            border-radius: 4px;
        }}
        #inspectorAnnotList::item:hover {{
            background-color: rgba(0, 0, 0, 0.04);
        }}
        #inspectorAnnotList::item:selected {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}
        """


class ThemeManager(QObject):
    """
    Manages application theme state and system color-scheme detection.
    Supports 'auto' (follow OS theme), 'dark', and 'light'.
    """
    theme_changed = pyqtSignal(str)  # emits "dark" or "light"
    _instance = None

    AUTO = "auto"
    DARK = MacTheme.DARK
    LIGHT = MacTheme.LIGHT

    def __init__(self, default_mode: str = "auto"):
        super().__init__()
        self._mode = default_mode  # "auto", "dark", "light"
        app = QGuiApplication.instance()
        if app and hasattr(app, "styleHints"):
            try:
                app.styleHints().colorSchemeChanged.connect(self._on_system_scheme_changed)
            except Exception:
                pass

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @classmethod
    def follow_system_theme(cls) -> str:
        """
        Detect current system theme (dark or light) via Qt styleHints,
        falling back to gsettings on GNOME/Linux or Windows registry.
        """
        app = QGuiApplication.instance()
        if app and hasattr(app, "styleHints"):
            try:
                cs = app.styleHints().colorScheme()
                if cs == Qt.ColorScheme.Light:
                    return MacTheme.LIGHT
                elif cs == Qt.ColorScheme.Dark:
                    return MacTheme.DARK
            except Exception:
                pass

        # Fallback for Linux GNOME / FreeDesktop
        try:
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=1
            )
            val = res.stdout.strip().lower()
            if "prefer-dark" in val or "dark" in val:
                return MacTheme.DARK
            elif "prefer-light" in val or "light" in val:
                return MacTheme.LIGHT
        except Exception:
            pass

        # Fallback for Windows
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return MacTheme.LIGHT if val == 1 else MacTheme.DARK
            except Exception:
                pass

        return MacTheme.DARK

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str):
        if mode not in (self.AUTO, self.DARK, self.LIGHT):
            raise ValueError(f"Unknown theme mode: {mode}")
        self._mode = mode
        resolved = self.get_resolved_theme()
        self.theme_changed.emit(resolved)

    def get_resolved_theme(self) -> str:
        if self._mode == self.AUTO:
            return self.follow_system_theme()
        return self._mode

    def _on_system_scheme_changed(self, scheme):
        if self._mode == self.AUTO:
            target = MacTheme.DARK if scheme == Qt.ColorScheme.Dark else MacTheme.LIGHT
            self.theme_changed.emit(target)

