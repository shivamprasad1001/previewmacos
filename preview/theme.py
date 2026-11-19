"""
Studio Pro Design System & Theme Engine for Preview application.
Provides modern, cohesive Studio Pro styling with deep obsidian/slate backgrounds,
refined card and dock surfaces, electric blue accents, and precise design tokens.
Maintains full backwards compatibility with MacTheme.
"""

import sys
import subprocess
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QWidget


class StudioTheme:
    """
    Studio Pro Design System & Theme Engine.
    High-contrast, distraction-free standalone desktop identity.
    """
    DARK = "dark"
    LIGHT = "light"
    ANTIMATTER = "antimatter"

    # =========================================================================
    # PRECISE DESIGN TOKENS - SPACING (4, 8, 12, 16, 20, 24px)
    # =========================================================================
    SPACE_4 = 4
    SPACE_8 = 8
    SPACE_12 = 12
    SPACE_16 = 16
    SPACE_20 = 20
    SPACE_24 = 24

    # =========================================================================
    # PRECISE DESIGN TOKENS - RADII (Modern subtle rounded corners: 4, 8, 10px)
    # =========================================================================
    RADIUS_XS = 4
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 10
    RADIUS_PILL = 9999

    # =========================================================================
    # PRECISE DESIGN TOKENS - DIMENSIONS & TYPOGRAPHY
    # =========================================================================
    HEADER_HEIGHT = 48
    TOOLBAR_HEIGHT = 44
    RIBBON_HEIGHT = 42
    DOCK_HEADER_HEIGHT = 44
    TAB_HEIGHT = 28
    STATUSBAR_HEIGHT = 26
    BTN_SIZE_SM = 26
    BTN_SIZE_MD = 32
    BTN_SIZE_LG = 36
    BTN_SIZE = 32
    INPUT_HEIGHT = 28

    FONT_SIZE_XS = 11
    FONT_SIZE_SM = 12
    FONT_SIZE_BASE = 13
    FONT_SIZE_LG = 15
    FONT_SIZE_XL = 18
    FONT_FAMILY = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'

    # =========================================================================
    # STUDIO DARK PALETTE
    # =========================================================================
    # Deep obsidian/slate window & canvas background (#141518, #1a1b1f)
    DARK_BG_CANVAS = "#141518"
    DARK_BG_WINDOW = "#1a1b1f"
    DARK_BG_TOOLBAR = "#1a1b1f"
    DARK_BG_SIDEBAR = "#1e2026"
    DARK_BG_DOCK = "#1e2026"

    # Refined card and dock background (#22242a, #282a32)
    DARK_BG_CARD = "#22242a"
    DARK_BG_ELEVATED = "#282a32"
    DARK_BG_INPUT = "#22242a"
    DARK_BG_HOVER = "rgba(255, 255, 255, 0.06)"
    DARK_BG_ACTIVE = "rgba(255, 255, 255, 0.12)"

    # Clean, professional accent palette
    # Studio Electric Blue #2563eb
    DARK_ACCENT = "#2563eb"
    DARK_ACCENT_HOVER = "#3b82f6"
    DARK_ACCENT_ACTIVE = "#1d4ed8"
    DARK_ACCENT_SUBTLE = "rgba(37, 99, 235, 0.16)"
    DARK_ACCENT_BORDER = "rgba(37, 99, 235, 0.45)"

    # Emerald #10b981 for success
    DARK_SUCCESS = "#10b981"
    DARK_SUCCESS_HOVER = "#059669"
    DARK_SUCCESS_SUBTLE = "rgba(16, 185, 129, 0.16)"

    # Crimson #ef4444 for delete / close
    DARK_DANGER = "#ef4444"
    DARK_DANGER_HOVER = "#dc2626"
    DARK_DANGER_SUBTLE = "rgba(239, 68, 68, 0.18)"

    # Amber #f59e0b for warning / minimize
    DARK_WARNING = "#f59e0b"
    DARK_WARNING_HOVER = "#d97706"
    DARK_WARNING_SUBTLE = "rgba(245, 158, 11, 0.16)"

    # High-contrast text hierarchy
    DARK_TEXT_PRIMARY = "#f3f4f6"
    DARK_TEXT_SECONDARY = "#9ca3af"
    DARK_TEXT_MUTED = "#6b7280"
    DARK_TEXT_DISABLED = "#4b5563"

    # Borders
    DARK_BORDER_SUBTLE = "rgba(255, 255, 255, 0.08)"
    DARK_BORDER = "rgba(255, 255, 255, 0.12)"
    DARK_BORDER_STRONG = "rgba(255, 255, 255, 0.20)"
    DARK_BORDER_FOCUS = "#2563eb"

    # Convenient aliases for the default dark mode
    BG_CANVAS = DARK_BG_CANVAS
    BG_WINDOW = DARK_BG_WINDOW
    BG_TOOLBAR = DARK_BG_TOOLBAR
    BG_SIDEBAR = DARK_BG_SIDEBAR
    BG_DOCK = DARK_BG_DOCK
    BG_CARD = DARK_BG_CARD
    BG_ELEVATED = DARK_BG_ELEVATED
    BG_INPUT = DARK_BG_INPUT
    BG_HOVER = DARK_BG_HOVER
    BG_ACTIVE = DARK_BG_ACTIVE
    ACCENT = DARK_ACCENT
    ACCENT_HOVER = DARK_ACCENT_HOVER
    ACCENT_ACTIVE = DARK_ACCENT_ACTIVE
    ACCENT_SUBTLE = DARK_ACCENT_SUBTLE
    ACCENT_BORDER = DARK_ACCENT_BORDER
    COLOR_SUCCESS = DARK_SUCCESS
    COLOR_DANGER = DARK_DANGER
    COLOR_WARNING = DARK_WARNING
    TEXT_PRIMARY = DARK_TEXT_PRIMARY
    TEXT_SECONDARY = DARK_TEXT_SECONDARY
    TEXT_MUTED = DARK_TEXT_MUTED
    BORDER_SUBTLE = DARK_BORDER_SUBTLE
    BORDER = DARK_BORDER
    BORDER_STRONG = DARK_BORDER_STRONG

    # =========================================================================
    # STUDIO LIGHT PALETTE
    # =========================================================================
    LIGHT_BG_CANVAS = "#ececf0"  # Preserved for test compatibility
    LIGHT_BG_WINDOW = "#f8f9fa"
    LIGHT_BG_TOOLBAR = "#ffffff"
    LIGHT_BG_SIDEBAR = "#f3f4f6"
    LIGHT_BG_DOCK = "#f3f4f6"
    LIGHT_BG_CARD = "#ffffff"
    LIGHT_BG_ELEVATED = "#f9fafb"
    LIGHT_BG_INPUT = "#ffffff"
    LIGHT_BG_HOVER = "rgba(0, 0, 0, 0.05)"
    LIGHT_BG_ACTIVE = "rgba(0, 0, 0, 0.10)"

    LIGHT_ACCENT = "#2563eb"
    LIGHT_ACCENT_HOVER = "#1d4ed8"
    LIGHT_ACCENT_ACTIVE = "#1e40af"
    LIGHT_ACCENT_SUBTLE = "rgba(37, 99, 235, 0.12)"
    LIGHT_ACCENT_BORDER = "rgba(37, 99, 235, 0.35)"

    LIGHT_SUCCESS = "#10b981"
    LIGHT_SUCCESS_HOVER = "#059669"
    LIGHT_DANGER = "#ef4444"
    LIGHT_DANGER_HOVER = "#dc2626"
    LIGHT_WARNING = "#f59e0b"
    LIGHT_WARNING_HOVER = "#d97706"

    LIGHT_TEXT_PRIMARY = "#111827"
    LIGHT_TEXT_SECONDARY = "#4b5563"
    LIGHT_TEXT_MUTED = "#9ca3af"
    LIGHT_TEXT_DISABLED = "#9ca3af"

    LIGHT_BORDER_SUBTLE = "rgba(0, 0, 0, 0.06)"
    LIGHT_BORDER = "rgba(0, 0, 0, 0.12)"
    LIGHT_BORDER_STRONG = "rgba(0, 0, 0, 0.20)"
    LIGHT_BORDER_FOCUS = "#2563eb"

    @classmethod
    def get_stylesheet(cls, mode: str = "dark") -> str:
        """Returns the high-performance QSS stylesheet for the given mode."""
        if mode == cls.LIGHT:
            return cls._light_stylesheet()
        elif mode == cls.ANTIMATTER or mode == "antimatter":
            return cls._antimatter_stylesheet()
        return cls._dark_stylesheet()

    @classmethod
    def apply_theme(cls, target: QWidget, mode: str = "dark") -> None:
        """Applies the StudioTheme stylesheet to a target widget, window, or application."""
        stylesheet = cls.get_stylesheet(mode)
        target.setStyleSheet(stylesheet)

    @classmethod
    def _antimatter_stylesheet(cls) -> str:
        """Deep void-black and quantum neon violet/cyan aesthetic (Antimatter style)."""
        dark_qss = cls._dark_stylesheet()
        replaces = [
            (cls.DARK_BG_WINDOW, "#0f1117"),
            (cls.DARK_BG_CANVAS, "#08090d"),
            (cls.DARK_BG_SIDEBAR, "#12151f"),
            (cls.DARK_BG_DOCK, "#12151f"),
            (cls.DARK_BG_CARD, "#161a26"),
            (cls.DARK_BG_ELEVATED, "#1d2232"),
            (cls.DARK_ACCENT, "#8b5cf6"),
            (cls.DARK_ACCENT_HOVER, "#a855f7"),
            (cls.DARK_ACCENT_ACTIVE, "#7c3aed"),
            ("rgba(37, 99, 235, 0.16)", "rgba(139, 92, 246, 0.18)"),
            ("rgba(37, 99, 235, 0.45)", "rgba(139, 92, 246, 0.50)"),
            ("1px solid rgba(255, 255, 255, 0.10)", "1px solid rgba(139, 92, 246, 0.22)"),
        ]
        for src, dst in replaces:
            dark_qss = dark_qss.replace(src, dst)
        return dark_qss

    @classmethod
    def _dark_stylesheet(cls) -> str:
        return f"""
        QMainWindow {{
            background: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        
        #rootContainer {{
            background: transparent;
        }}

        #windowFrame {{
            background-color: {cls.DARK_BG_WINDOW};
            border-radius: {cls.RADIUS_LG}px;
            border: 1px solid rgba(255, 255, 255, 0.10);
        }}

        QWidget {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_BASE}px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        /* Studio Pro Clean Menu Bar */
        #macMenubar {{
            background-color: {cls.DARK_BG_WINDOW};
            color: {cls.DARK_TEXT_PRIMARY};
            border: none;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-top-left-radius: {cls.RADIUS_LG}px;
            border-top-right-radius: {cls.RADIUS_LG}px;
            padding: 2px 10px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-family: {cls.FONT_FAMILY};
        }}

        #macMenubar::item {{
            background: transparent;
            padding: 3px 9px;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #macMenubar::item:selected {{
            background-color: {cls.DARK_BG_HOVER};
            color: #ffffff;
        }}

        /* Unified Header Bar / Custom Titlebar (48px tall, subtle border) */
        #macToolbar {{
            background-color: {cls.DARK_BG_TOOLBAR};
            border: none;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-top-left-radius: {cls.RADIUS_LG}px;
            border-top-right-radius: {cls.RADIUS_LG}px;
            padding: 0px 14px;
            min-height: {cls.HEADER_HEIGHT}px;
            max-height: {cls.HEADER_HEIGHT}px;
            height: {cls.HEADER_HEIGHT}px;
        }}

        #toolbarDivider {{
            background-color: {cls.DARK_BORDER};
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 20px;
            min-height: 20px;
            max-height: 20px;
            margin: 0px 4px;
        }}
        
        #windowTitleLabel {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            color: {cls.DARK_TEXT_PRIMARY};
            letter-spacing: 0.2px;
        }}

        #pageBadge {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            color: {cls.DARK_TEXT_SECONDARY};
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 7px;
        }}

        /* Studio Titlebar Window Controls (Clean Modern Standalone - No Apple Traffic Lights) */
        #trafficClose, #trafficMinimize, #trafficMaximize,
        #windowCloseBtn, #windowMinBtn, #windowMaxBtn {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
            padding: 0px;
            margin: 0px;
        }}

        #trafficClose:hover, #windowCloseBtn:hover {{
            background-color: {cls.DARK_DANGER};
            border-color: {cls.DARK_DANGER_HOVER};
        }}

        #trafficClose:pressed, #windowCloseBtn:pressed {{
            background-color: {cls.DARK_DANGER_HOVER};
        }}

        #trafficMinimize:hover, #windowMinBtn:hover {{
            background-color: {cls.DARK_WARNING};
            border-color: {cls.DARK_WARNING_HOVER};
        }}

        #trafficMinimize:pressed, #windowMinBtn:pressed {{
            background-color: {cls.DARK_WARNING_HOVER};
        }}

        #trafficMaximize:hover, #windowMaxBtn:hover {{
            background-color: {cls.DARK_SUCCESS};
            border-color: {cls.DARK_SUCCESS_HOVER};
        }}

        #trafficMaximize:pressed, #windowMaxBtn:pressed {{
            background-color: {cls.DARK_SUCCESS_HOVER};
        }}

        /* Tool Ribbon & Action Bars */
        #markupToolbar, #organizeActionBar {{
            background-color: {cls.DARK_BG_DOCK};
            border: none;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            padding: 0px 12px;
            min-height: {cls.TOOLBAR_HEIGHT}px;
            max-height: {cls.TOOLBAR_HEIGHT}px;
            height: {cls.TOOLBAR_HEIGHT}px;
        }}

        #primaryStrip {{
            background: transparent;
            min-height: {cls.TOOLBAR_HEIGHT}px;
            max-height: {cls.TOOLBAR_HEIGHT}px;
            height: {cls.TOOLBAR_HEIGHT}px;
        }}

        #markupGroup {{
            background-color: {cls.DARK_BG_WINDOW};
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 1px;
            min-height: 34px;
            max-height: 34px;
        }}

        #markupGroupSeparator {{
            background-color: {cls.DARK_BORDER};
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 18px;
            margin: 0px 2px;
        }}

        #markupGroup QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {cls.RADIUS_SM}px;
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
            background-color: {cls.DARK_BG_HOVER};
            border-color: transparent;
            color: #ffffff;
        }}

        #markupGroup QToolButton:pressed, #overflowBtn:pressed {{
            background-color: {cls.DARK_BG_ACTIVE};
            border-color: transparent;
        }}

        #markupGroup QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            border: 1px solid {cls.DARK_ACCENT_HOVER};
            border-radius: {cls.RADIUS_SM}px;
            color: #ffffff;
            font-weight: 600;
        }}

        #markupGroup QToolButton:focus, #overflowBtn:focus, QToolButton:focus, QPushButton:focus {{
            outline: 2px solid {cls.DARK_ACCENT};
            outline-offset: 1px;
        }}

        #markupGroup QToolButton:disabled, #overflowBtn:disabled {{
            color: {cls.DARK_TEXT_DISABLED};
            opacity: 0.35;
        }}

        /* Context Formatting Ribbon */
        #contextFormattingBar {{
            background-color: {cls.DARK_BG_WINDOW};
            border: none;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            padding: 2px 10px;
            min-height: 34px;
            max-height: 34px;
        }}

        #contextFormattingBar QToolButton {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 3px 10px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
            min-height: 28px;
            max-height: 28px;
            min-width: 28px;
            max-width: none;
        }}

        #contextFormattingBar QToolButton:hover {{
            background-color: {cls.DARK_BG_HOVER};
            border-color: {cls.DARK_BORDER_STRONG};
        }}

        #contextFormattingBar QToolButton:pressed {{
            background-color: {cls.DARK_BG_ACTIVE};
        }}

        #contextFormattingBar QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            border-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Icon-only Buttons & Standard Buttons */
        QToolButton, QPushButton {{
            background-color: transparent;
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_PRIMARY};
            padding: 2px 8px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
        }}
        
        QToolButton:hover, QPushButton:hover {{
            background-color: {cls.DARK_BG_HOVER};
            border-color: {cls.DARK_BORDER_STRONG};
        }}

        QToolButton:pressed, QPushButton:pressed {{
            background-color: {cls.DARK_BG_ACTIVE};
            border-color: {cls.DARK_BORDER_STRONG};
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
            border-top-left-radius: {cls.RADIUS_SM}px;
            border-bottom-left-radius: {cls.RADIUS_SM}px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border-right: 1px solid {cls.DARK_BORDER_SUBTLE};
        }}

        #nextBtn, #zoomInBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: {cls.RADIUS_SM}px;
            border-bottom-right-radius: {cls.RADIUS_SM}px;
            border-left: none;
        }}

        #openMainBtn {{
            border-top-left-radius: {cls.RADIUS_SM}px;
            border-bottom-left-radius: {cls.RADIUS_SM}px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border: 1px solid {cls.DARK_BORDER};
            border-right: 1px solid {cls.DARK_BORDER_SUBTLE};
            padding: 0px 8px 0px 6px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
            background-color: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        #openMainBtn:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}
        #openMainBtn:pressed {{
            background-color: {cls.DARK_BG_ACTIVE};
        }}

        #openArrowBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: {cls.RADIUS_SM}px;
            border-bottom-right-radius: {cls.RADIUS_SM}px;
            border: 1px solid {cls.DARK_BORDER};
            border-left: none;
            padding: 0px;
            background-color: transparent;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        #openArrowBtn:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}
        #openArrowBtn:pressed {{
            background-color: {cls.DARK_BG_ACTIVE};
        }}

        /* Studio Primary Action Button */
        #markupPillBtn {{
            border-radius: 6px;
            padding: 0px 14px;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            background-color: {cls.DARK_ACCENT_SUBTLE};
            border: 1px solid {cls.DARK_ACCENT_BORDER};
            color: #60a5fa;
            min-height: 32px;
            max-height: 32px;
        }}

        #markupPillBtn:hover {{
            background-color: rgba(37, 99, 235, 0.28);
            border-color: {cls.DARK_ACCENT_HOVER};
            color: #ffffff;
        }}

        #markupPillBtn:pressed {{
            background-color: {cls.DARK_ACCENT_ACTIVE};
            color: #ffffff;
        }}

        #markupPillBtn:checked {{
            background-color: {cls.DARK_ACCENT};
            border-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        /* Document Tabs (Studio Pro Tab Bar) */
        #macTabBarContainer {{
            background-color: #16171b;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            min-height: 30px;
            max-height: 30px;
            padding: 0px 6px;
        }}

        QTabBar#macTabBar {{
            background-color: transparent;
            border: none;
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            padding: 3px 6px 0px 6px;
        }}

        QTabBar#macTabBar::tab {{
            background-color: transparent;
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_SM}px;
            font-family: {cls.FONT_FAMILY};
            font-weight: 500;
            border: 1px solid transparent;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 100px;
            max-width: 220px;
            height: 25px;
            padding: 1px 12px;
            margin-right: 2px;
        }}

        QTabBar#macTabBar::tab:selected {{
            background-color: {cls.DARK_BG_CARD};
            color: #ffffff;
            font-weight: 600;
            border: 1px solid {cls.DARK_BORDER};
            border-top: 2px solid {cls.DARK_ACCENT};
            border-bottom: none;
        }}

        QTabBar#macTabBar::tab:hover:!selected {{
            background-color: {cls.DARK_BG_HOVER};
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QTabBar#macTabBar::close-button {{
            subcontrol-position: right;
            subcontrol-origin: padding;
            margin-left: 6px;
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px;
        }}

        QTabBar#macTabBar::close-button:hover {{
            background-color: {cls.DARK_DANGER_SUBTLE};
            color: {cls.DARK_DANGER};
        }}

        #newTabBtn {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: 16px;
            font-weight: 500;
        }}

        #newTabBtn:hover {{
            background-color: {cls.DARK_BG_HOVER};
            border-color: {cls.DARK_BORDER_SUBTLE};
            color: #ffffff;
        }}

        /* Segmented Controls (Sidebar & Mode Switchers) */
        #sidebarSegmented, #modeSegmented {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 2px;
            margin: 6px 8px;
        }}

        #sidebarSegmented QToolButton, #modeSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            padding: 3px 8px;
            min-height: 24px;
            max-height: 24px;
        }}

        #sidebarSegmented QToolButton:hover, #modeSegmented QToolButton:hover {{
            color: #ffffff;
            background-color: {cls.DARK_BG_HOVER};
        }}

        #sidebarSegmented QToolButton:checked, #modeSegmented QToolButton:checked {{
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
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_LG}px;
            padding: 36px 44px;
        }}

        #emptyStateCard[dragHover="true"] {{
            border: 2px dashed {cls.DARK_ACCENT};
            background-color: {cls.DARK_ACCENT_SUBTLE};
        }}

        #emptyStateTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #emptyStateHint {{
            font-size: {cls.FONT_SIZE_SM}px;
            color: {cls.DARK_TEXT_SECONDARY};
        }}

        #emptyStateOpenBtn {{
            background-color: {cls.DARK_ACCENT};
            border: 1px solid {cls.DARK_ACCENT_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 32px;
        }}

        #emptyStateOpenBtn:hover {{
            background-color: {cls.DARK_ACCENT_ACTIVE};
            border-color: {cls.DARK_ACCENT};
        }}

        /* Search Field & Text Inputs */
        #macSearchField {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            padding-left: 8px;
            padding-right: 10px;
            min-height: 28px;
            max-height: 28px;
            font-size: {cls.FONT_SIZE_SM}px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #macSearchField:focus {{
            border: 1px solid {cls.DARK_ACCENT};
            background-color: {cls.DARK_BG_ELEVATED};
        }}

        QLineEdit {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 3px 8px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            selection-background-color: {cls.DARK_ACCENT};
        }}

        QLineEdit:focus {{
            border: 1px solid {cls.DARK_ACCENT};
            background-color: {cls.DARK_BG_ELEVATED};
        }}

        /* Sidebar Styling & Splitter */
        #macSidebar {{
            background-color: {cls.DARK_BG_WINDOW};
            border-right: 1px solid {cls.DARK_BORDER_SUBTLE};
        }}

        #sidebarHeader {{
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            background-color: transparent;
        }}

        #sidebarDropdown {{
            background-color: {cls.DARK_BG_ELEVATED};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 8px;
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        #sidebarDropdown:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}

        QSplitter::handle:horizontal {{
            background-color: {cls.DARK_BORDER_SUBTLE};
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
            background: rgba(255, 255, 255, 0.18);
            min-height: 30px;
            border-radius: {cls.RADIUS_SM}px;
            margin: 1px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.32);
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background: rgba(255, 255, 255, 0.18);
            min-width: 30px;
            border-radius: {cls.RADIUS_SM}px;
            margin: 1px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: rgba(255, 255, 255, 0.32);
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0px;
            height: 0px;
        }}

        /* SpinBox & Font Controls */
        QSpinBox {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 4px 2px 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            min-height: 24px;
        }}

        QSpinBox:focus {{
            border: 1px solid {cls.DARK_ACCENT};
            background-color: {cls.DARK_BG_ELEVATED};
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background: transparent;
            border: none;
            width: 14px;
        }}

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {cls.DARK_BG_HOVER};
            border-radius: 2px;
        }}

        /* Dropdown & ComboBox */
        QFontComboBox, QComboBox {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 8px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            min-height: 24px;
        }}

        QFontComboBox:focus, QComboBox:focus {{
            border: 1px solid {cls.DARK_ACCENT};
            background-color: {cls.DARK_BG_ELEVATED};
        }}

        QFontComboBox::drop-down, QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}

        QFontComboBox QAbstractItemView, QComboBox QAbstractItemView {{
            background-color: {cls.DARK_BG_ELEVATED};
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
            border-radius: {cls.RADIUS_SM}px;
            margin: 2px;
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            background-color: {cls.DARK_BG_ELEVATED};
            color: {cls.DARK_TEXT_PRIMARY};
            border-bottom: 2px solid {cls.DARK_ACCENT};
        }}

        /* Slider */
        QSlider::groove:horizontal {{
            height: 4px;
            background: rgba(255, 255, 255, 0.14);
            border-radius: 2px;
        }}

        QSlider::sub-page:horizontal {{
            background: {cls.DARK_ACCENT};
            border-radius: 2px;
        }}

        QSlider::handle:horizontal {{
            background: #ffffff;
            border: 1px solid {cls.DARK_ACCENT};
            width: 14px;
            margin-top: -5px;
            margin-bottom: -5px;
            border-radius: 7px;
        }}

        /* Tooltips */
        QToolTip {{
            background-color: {cls.DARK_BG_ELEVATED};
            color: {cls.DARK_TEXT_PRIMARY};
            border: 1px solid {cls.DARK_BORDER_STRONG};
            border-radius: {cls.RADIUS_SM}px;
            padding: 4px 8px;
            font-size: {cls.FONT_SIZE_XS}px;
        }}

        /* Context & Popover Menus */
        QMenu {{
            background-color: {cls.DARK_BG_ELEVATED};
            border: 1px solid {cls.DARK_BORDER_STRONG};
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 5px 18px 5px 10px;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QMenu::item:selected {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {cls.DARK_BORDER_SUBTLE};
            margin: 3px 6px;
        }}

        /* Status Bar */
        QStatusBar, #macStatusBar {{
            background-color: {cls.DARK_BG_WINDOW};
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-family: {cls.FONT_FAMILY};
            border: none;
            border-top: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-bottom-left-radius: {cls.RADIUS_LG}px;
            border-bottom-right-radius: {cls.RADIUS_LG}px;
            padding: 2px 12px;
            min-height: {cls.STATUSBAR_HEIGHT}px;
            max-height: {cls.STATUSBAR_HEIGHT}px;
        }}

        #macStatusBar QLabel {{
            color: {cls.DARK_TEXT_SECONDARY};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            background: transparent;
        }}

        /* Floating Status Pill */
        #floatingStatusPill {{
            background-color: {cls.DARK_BG_ELEVATED};
            border: 1px solid {cls.DARK_BORDER_STRONG};
            border-radius: 8px;
            padding: 2px 10px;
        }}

        #floatingStatusLabel {{
            color: {cls.DARK_TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            background: transparent;
        }}

        /* Studio Inspector Dock */
        #macInspectorPanel {{
            background-color: {cls.DARK_BG_DOCK};
            border-left: 1px solid {cls.DARK_BORDER_SUBTLE};
        }}

        #macInspectorPanel QScrollArea,
        #macInspectorPanel QScrollArea > QWidget > QWidget {{
            background: transparent;
            border: none;
        }}

        #inspectorHeader {{
            background-color: {cls.DARK_BG_CARD};
            border-bottom: 1px solid {cls.DARK_BORDER_SUBTLE};
            min-height: {cls.DOCK_HEADER_HEIGHT}px;
            max-height: {cls.DOCK_HEADER_HEIGHT}px;
        }}

        #inspectorSegmented {{
            background-color: {cls.DARK_BG_WINDOW};
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 2px;
        }}

        #inspectorSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            padding: 3px 8px;
            min-height: 24px;
        }}

        #inspectorSegmented QToolButton:hover {{
            color: #ffffff;
            background-color: {cls.DARK_BG_HOVER};
        }}

        #inspectorSegmented QToolButton:checked {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        #inspectorCloseBtn {{
            background: transparent;
            border: none;
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: 14px;
            font-weight: 600;
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px;
        }}

        #inspectorCloseBtn:hover {{
            color: {cls.DARK_DANGER};
            background-color: {cls.DARK_DANGER_SUBTLE};
        }}

        #inspectorCard {{
            background-color: {cls.DARK_BG_ELEVATED};
            border-radius: 8px;
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            padding: 8px;
        }}

        #inspectorAnnotList {{
            background-color: {cls.DARK_BG_WINDOW};
            border: 1px solid {cls.DARK_BORDER_SUBTLE};
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            outline: none;
        }}

        #inspectorAnnotList::item {{
            padding: 6px 8px;
            border-radius: {cls.RADIUS_SM}px;
        }}

        #inspectorAnnotList::item:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}

        #inspectorAnnotList::item:selected {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        /* Confirmation & Alert Dialog Cards */
        QWidget#alertCard {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_LG}px;
            padding: 24px;
        }}

        QLabel#alertTitle {{
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 600;
        }}

        QLabel#alertBody {{
            color: {cls.DARK_TEXT_SECONDARY};
            font-size: 13px;
        }}

        QPushButton#primaryButton, #btnPrimary {{
            background-color: {cls.DARK_ACCENT};
            border: 1px solid {cls.DARK_ACCENT_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 30px;
        }}

        QPushButton#primaryButton:hover, #btnPrimary:hover {{
            background-color: {cls.DARK_ACCENT_ACTIVE};
            border-color: {cls.DARK_ACCENT};
        }}

        QPushButton#btnDontSave {{
            background-color: {cls.DARK_DANGER};
            border: 1px solid {cls.DARK_DANGER_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 30px;
        }}

        QPushButton#btnDontSave:hover {{
            background-color: {cls.DARK_DANGER_HOVER};
        }}

        QPushButton#btnCancel {{
            background-color: {cls.DARK_BG_ELEVATED};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: 6px;
            color: {cls.DARK_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 500;
            padding: 6px 18px;
            min-height: 30px;
        }}

        QPushButton#btnCancel:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}

        /* Help Window Components */
        QLineEdit#helpSearchInput {{
            background-color: {cls.DARK_BG_CARD};
            border: 1px solid {cls.DARK_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 4px 8px;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QLineEdit#helpSearchInput:focus {{
            border: 1px solid {cls.DARK_ACCENT};
        }}

        QTreeWidget#helpNavTree {{
            background-color: {cls.DARK_BG_DOCK};
            border: none;
            color: {cls.DARK_TEXT_PRIMARY};
        }}

        QTreeWidget#helpNavTree::item:hover {{
            background-color: {cls.DARK_BG_HOVER};
        }}

        QTreeWidget#helpNavTree::item:selected {{
            background-color: {cls.DARK_ACCENT};
            color: #ffffff;
        }}

        QTextBrowser#helpContentBrowser {{
            background-color: {cls.DARK_BG_WINDOW};
            border: none;
            color: {cls.DARK_TEXT_PRIMARY};
        }}
        """

    @classmethod
    def _light_stylesheet(cls) -> str:
        return f"""
        QMainWindow {{
            background: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        
        #rootContainer {{
            background: transparent;
        }}

        #windowFrame {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border-radius: {cls.RADIUS_LG}px;
            border: 1px solid {cls.LIGHT_BORDER};
        }}

        QWidget {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_BASE}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        /* Studio Pro Clean Menu Bar (Light) */
        #macMenubar {{
            background-color: {cls.LIGHT_BG_WINDOW};
            color: {cls.LIGHT_TEXT_PRIMARY};
            border: none;
            border-bottom: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-top-left-radius: {cls.RADIUS_LG}px;
            border-top-right-radius: {cls.RADIUS_LG}px;
            padding: 2px 10px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-family: {cls.FONT_FAMILY};
        }}

        #macMenubar::item {{
            background: transparent;
            padding: 3px 9px;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #macMenubar::item:selected {{
            background-color: {cls.LIGHT_BG_HOVER};
        }}

        /* Header Bar / Custom Titlebar (Light) */
        #macToolbar {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            border: none;
            border-bottom: 1px solid {cls.LIGHT_BORDER};
            border-top-left-radius: {cls.RADIUS_LG}px;
            border-top-right-radius: {cls.RADIUS_LG}px;
            padding: 0px 14px;
            min-height: {cls.HEADER_HEIGHT}px;
            max-height: {cls.HEADER_HEIGHT}px;
            height: {cls.HEADER_HEIGHT}px;
        }}

        #toolbarDivider {{
            background-color: {cls.LIGHT_BORDER};
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 20px;
            min-height: 20px;
            max-height: 20px;
            margin: 0px 4px;
        }}
        
        #windowTitleLabel {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            color: {cls.LIGHT_TEXT_PRIMARY};
            letter-spacing: 0.2px;
        }}

        #pageBadge {{
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            color: {cls.LIGHT_TEXT_SECONDARY};
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 7px;
        }}

        /* Studio Titlebar Window Controls (Light) */
        #trafficClose, #trafficMinimize, #trafficMaximize,
        #windowCloseBtn, #windowMinBtn, #windowMaxBtn {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
            padding: 0px;
            margin: 0px;
        }}

        #trafficClose:hover, #windowCloseBtn:hover {{
            background-color: {cls.LIGHT_DANGER};
            border-color: {cls.LIGHT_DANGER_HOVER};
        }}

        #trafficClose:pressed, #windowCloseBtn:pressed {{
            background-color: {cls.LIGHT_DANGER_HOVER};
        }}

        #trafficMinimize:hover, #windowMinBtn:hover {{
            background-color: {cls.LIGHT_WARNING};
            border-color: {cls.LIGHT_WARNING_HOVER};
        }}

        #trafficMinimize:pressed, #windowMinBtn:pressed {{
            background-color: {cls.LIGHT_WARNING_HOVER};
        }}

        #trafficMaximize:hover, #windowMaxBtn:hover {{
            background-color: {cls.LIGHT_SUCCESS};
            border-color: {cls.LIGHT_SUCCESS_HOVER};
        }}

        #trafficMaximize:pressed, #windowMaxBtn:pressed {{
            background-color: {cls.LIGHT_SUCCESS_HOVER};
        }}

        /* Tool Ribbon & Action Bars (Light) */
        #markupToolbar, #organizeActionBar {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: none;
            border-bottom: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            padding: 0px 12px;
            min-height: {cls.TOOLBAR_HEIGHT}px;
            max-height: {cls.TOOLBAR_HEIGHT}px;
            height: {cls.TOOLBAR_HEIGHT}px;
        }}

        #primaryStrip {{
            background: transparent;
            min-height: {cls.TOOLBAR_HEIGHT}px;
            max-height: {cls.TOOLBAR_HEIGHT}px;
            height: {cls.TOOLBAR_HEIGHT}px;
        }}

        #markupGroup {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 1px;
            min-height: 34px;
            max-height: 34px;
        }}

        #markupGroupSeparator {{
            background-color: {cls.LIGHT_BORDER};
            width: 1px;
            min-width: 1px;
            max-width: 1px;
            height: 18px;
            margin: 0px 2px;
        }}

        #markupGroup QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {cls.RADIUS_SM}px;
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
            background-color: {cls.LIGHT_BG_HOVER};
            border-color: transparent;
        }}

        #markupGroup QToolButton:pressed, #overflowBtn:pressed {{
            background-color: {cls.LIGHT_BG_ACTIVE};
            border-color: transparent;
        }}

        #markupGroup QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border: 1px solid {cls.LIGHT_ACCENT_HOVER};
            border-radius: {cls.RADIUS_SM}px;
            color: #ffffff;
            font-weight: 600;
        }}

        #markupGroup QToolButton:focus, #overflowBtn:focus, QToolButton:focus, QPushButton:focus {{
            outline: 2px solid {cls.LIGHT_ACCENT};
            outline-offset: 1px;
        }}

        #markupGroup QToolButton:disabled, #overflowBtn:disabled {{
            color: {cls.LIGHT_TEXT_DISABLED};
            opacity: 0.35;
        }}

        /* Context Formatting Ribbon (Light) */
        #contextFormattingBar {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border: none;
            border-bottom: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            padding: 2px 10px;
            min-height: 34px;
            max-height: 34px;
        }}

        #contextFormattingBar QToolButton {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 3px 10px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
            min-height: 28px;
            max-height: 28px;
            min-width: 28px;
            max-width: none;
        }}

        #contextFormattingBar QToolButton:hover {{
            background-color: {cls.LIGHT_BG_HOVER};
            border-color: {cls.LIGHT_BORDER_STRONG};
        }}

        #contextFormattingBar QToolButton:pressed {{
            background-color: {cls.LIGHT_BG_ACTIVE};
        }}

        #contextFormattingBar QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Icon-only Buttons & Standard Buttons (Light) */
        QToolButton, QPushButton {{
            background-color: transparent;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 2px 8px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
        }}
        
        QToolButton:hover, QPushButton:hover {{
            background-color: {cls.LIGHT_BG_HOVER};
            border-color: {cls.LIGHT_BORDER_STRONG};
        }}

        QToolButton:pressed, QPushButton:pressed {{
            background-color: {cls.LIGHT_BG_ACTIVE};
            border-color: {cls.LIGHT_BORDER_STRONG};
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

        /* Joined Segmented Control Pairs (Light) */
        #prevBtn, #zoomOutBtn {{
            border-top-left-radius: {cls.RADIUS_SM}px;
            border-bottom-left-radius: {cls.RADIUS_SM}px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border-right: 1px solid {cls.LIGHT_BORDER_SUBTLE};
        }}

        #nextBtn, #zoomInBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: {cls.RADIUS_SM}px;
            border-bottom-right-radius: {cls.RADIUS_SM}px;
            border-left: none;
        }}

        #openMainBtn {{
            border-top-left-radius: {cls.RADIUS_SM}px;
            border-bottom-left-radius: {cls.RADIUS_SM}px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            border: 1px solid {cls.LIGHT_BORDER};
            border-right: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            padding: 0px 8px 0px 6px;
            font-size: {cls.FONT_SIZE_SM}px;
            font-weight: 500;
            background-color: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}
        #openMainBtn:hover {{
            background-color: {cls.LIGHT_BG_HOVER};
        }}

        #openArrowBtn {{
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: {cls.RADIUS_SM}px;
            border-bottom-right-radius: {cls.RADIUS_SM}px;
            border: 1px solid {cls.LIGHT_BORDER};
            border-left: none;
            padding: 0px;
            background-color: transparent;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}
        #openArrowBtn:hover {{
            background-color: {cls.LIGHT_BG_HOVER};
        }}

        /* Studio Primary Action Button (Light) */
        #markupPillBtn {{
            border-radius: 6px;
            padding: 0px 14px;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            background-color: {cls.LIGHT_ACCENT_SUBTLE};
            border: 1px solid {cls.LIGHT_ACCENT_BORDER};
            color: {cls.LIGHT_ACCENT};
            min-height: 32px;
            max-height: 32px;
        }}

        #markupPillBtn:hover {{
            background-color: rgba(37, 99, 235, 0.20);
            border-color: {cls.LIGHT_ACCENT};
        }}

        #markupPillBtn:pressed {{
            background-color: {cls.LIGHT_ACCENT_ACTIVE};
            color: #ffffff;
        }}

        #markupPillBtn:checked {{
            background-color: {cls.LIGHT_ACCENT};
            border-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        /* Document Tabs (Light) */
        #macTabBarContainer {{
            background-color: #ebecef;
            border-bottom: 1px solid {cls.LIGHT_BORDER};
            min-height: 30px;
            max-height: 30px;
            padding: 0px 6px;
        }}

        QTabBar#macTabBar {{
            background-color: transparent;
            border: none;
            border-bottom: 1px solid {cls.LIGHT_BORDER};
            padding: 3px 6px 0px 6px;
        }}

        QTabBar#macTabBar::tab {{
            background-color: transparent;
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_SM}px;
            font-family: {cls.FONT_FAMILY};
            font-weight: 500;
            border: 1px solid transparent;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 100px;
            max-width: 220px;
            height: 25px;
            padding: 1px 12px;
            margin-right: 2px;
        }}

        QTabBar#macTabBar::tab:selected {{
            background-color: {cls.LIGHT_BG_CARD};
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-weight: 600;
            border: 1px solid {cls.LIGHT_BORDER};
            border-top: 2px solid {cls.LIGHT_ACCENT};
            border-bottom: none;
        }}

        QTabBar#macTabBar::tab:hover:!selected {{
            background-color: {cls.LIGHT_BG_HOVER};
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        QTabBar#macTabBar::close-button {{
            subcontrol-position: right;
            subcontrol-origin: padding;
            margin-left: 6px;
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px;
        }}

        QTabBar#macTabBar::close-button:hover {{
            background-color: rgba(239, 68, 68, 0.15);
            color: {cls.LIGHT_DANGER};
        }}

        #newTabBtn {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: 16px;
            font-weight: 500;
        }}

        #newTabBtn:hover {{
            background-color: {cls.LIGHT_BG_HOVER};
            border-color: {cls.LIGHT_BORDER_SUBTLE};
            color: #000000;
        }}

        /* Segmented Controls (Light) */
        #sidebarSegmented, #modeSegmented {{
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 2px;
            margin: 6px 8px;
        }}

        #sidebarSegmented QToolButton, #modeSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            padding: 3px 8px;
            min-height: 24px;
            max-height: 24px;
        }}

        #sidebarSegmented QToolButton:hover, #modeSegmented QToolButton:hover {{
            color: {cls.LIGHT_TEXT_PRIMARY};
            background-color: {cls.LIGHT_BG_HOVER};
        }}

        #sidebarSegmented QToolButton:checked, #modeSegmented QToolButton:checked {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
            font-weight: 600;
        }}

        /* Empty State (Light) */
        #emptyStateOverlay {{
            background: transparent;
        }}

        #emptyStateCard {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_LG}px;
            padding: 36px 44px;
        }}

        #emptyStateCard[dragHover="true"] {{
            border: 2px dashed {cls.LIGHT_ACCENT};
            background-color: {cls.LIGHT_ACCENT_SUBTLE};
        }}

        #emptyStateTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #emptyStateHint {{
            font-size: {cls.FONT_SIZE_SM}px;
            color: {cls.LIGHT_TEXT_SECONDARY};
        }}

        #emptyStateOpenBtn {{
            background-color: {cls.LIGHT_ACCENT};
            border: 1px solid {cls.LIGHT_ACCENT_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 32px;
        }}

        #emptyStateOpenBtn:hover {{
            background-color: {cls.LIGHT_ACCENT_ACTIVE};
        }}

        /* Search & Inputs (Light) */
        #macSearchField {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            padding-left: 8px;
            padding-right: 10px;
            min-height: 28px;
            max-height: 28px;
            font-size: {cls.FONT_SIZE_SM}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        #macSearchField:focus {{
            border: 1px solid {cls.LIGHT_ACCENT};
        }}

        QLineEdit {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 3px 8px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            selection-background-color: {cls.LIGHT_ACCENT};
        }}

        QLineEdit:focus {{
            border: 1px solid {cls.LIGHT_ACCENT};
        }}

        /* Sidebar (Light) */
        #macSidebar {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border-right: 1px solid {cls.LIGHT_BORDER};
        }}

        #sidebarHeader {{
            border-bottom: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            background-color: transparent;
        }}

        #sidebarDropdown {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 8px;
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
        }}

        QSplitter::handle:horizontal {{
            background-color: {cls.LIGHT_BORDER};
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

        /* Document Canvas (Light) */
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
            background: rgba(0, 0, 0, 0.20);
            min-height: 30px;
            border-radius: {cls.RADIUS_SM}px;
            margin: 1px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.35);
        }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background: rgba(0, 0, 0, 0.20);
            min-width: 30px;
            border-radius: {cls.RADIUS_SM}px;
            margin: 1px;
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            width: 0px;
            height: 0px;
        }}

        /* SpinBox & Combos (Light) */
        QSpinBox {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 4px 2px 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            min-height: 24px;
        }}

        QSpinBox:focus {{
            border: 1px solid {cls.LIGHT_ACCENT};
        }}

        QFontComboBox, QComboBox {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 2px 8px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            min-height: 24px;
        }}

        QFontComboBox:focus, QComboBox:focus {{
            border: 1px solid {cls.LIGHT_ACCENT};
        }}

        QFontComboBox QAbstractItemView, QComboBox QAbstractItemView {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            selection-background-color: {cls.LIGHT_ACCENT};
            color: {cls.LIGHT_TEXT_PRIMARY};
            padding: 4px;
        }}

        /* Dialogs and Popovers (Light) */
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
            border-radius: {cls.RADIUS_SM}px;
            margin: 2px;
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            background-color: rgba(0, 0, 0, 0.08);
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        /* Slider (Light) */
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

        /* Tooltips & Menus (Light) */
        QToolTip {{
            background-color: #ffffff;
            color: {cls.LIGHT_TEXT_PRIMARY};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_SM}px;
            padding: 4px 8px;
            font-size: {cls.FONT_SIZE_XS}px;
        }}

        QMenu {{
            background-color: #ffffff;
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 5px 18px 5px 10px;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_PRIMARY};
        }}

        QMenu::item:selected {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {cls.LIGHT_BORDER_SUBTLE};
            margin: 3px 6px;
        }}

        /* Status Bar (Light) */
        QStatusBar, #macStatusBar {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-family: {cls.FONT_FAMILY};
            border: none;
            border-top: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-bottom-left-radius: {cls.RADIUS_LG}px;
            border-bottom-right-radius: {cls.RADIUS_LG}px;
            padding: 2px 12px;
            min-height: {cls.STATUSBAR_HEIGHT}px;
            max-height: {cls.STATUSBAR_HEIGHT}px;
        }}

        #macStatusBar QLabel {{
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            background: transparent;
        }}

        /* Floating Status Pill (Light) */
        #floatingStatusPill {{
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 8px;
        }}

        #floatingStatusLabel {{
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.FONT_SIZE_XS}px;
            font-weight: 500;
            background: transparent;
        }}

        /* Inspector Dock (Light) */
        #macInspectorPanel {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border-left: 1px solid {cls.LIGHT_BORDER};
        }}

        #macInspectorPanel QScrollArea,
        #macInspectorPanel QScrollArea > QWidget > QWidget {{
            background: transparent;
            border: none;
        }}

        #inspectorHeader {{
            background-color: {cls.LIGHT_BG_TOOLBAR};
            border-bottom: 1px solid {cls.LIGHT_BORDER};
        }}

        #inspectorSegmented {{
            background-color: rgba(0, 0, 0, 0.05);
            border-radius: 6px;
            padding: 2px;
        }}

        #inspectorSegmented QToolButton {{
            background: transparent;
            border: none;
            border-radius: {cls.RADIUS_SM}px;
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: {cls.FONT_SIZE_XS}px;
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
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: 14px;
            font-weight: 600;
            border-radius: {cls.RADIUS_SM}px;
        }}

        #inspectorCloseBtn:hover {{
            color: {cls.LIGHT_DANGER};
            background-color: rgba(239, 68, 68, 0.12);
        }}

        #inspectorCard {{
            background-color: {cls.LIGHT_BG_CARD};
            border-radius: 8px;
            border: 1px solid {cls.LIGHT_BORDER_SUBTLE};
        }}

        #inspectorAnnotList {{
            background-color: {cls.LIGHT_BG_WINDOW};
            border: 1px solid {cls.LIGHT_BORDER_SUBTLE};
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_SM}px;
            outline: none;
        }}

        #inspectorAnnotList::item {{
            padding: 6px 8px;
            border-radius: {cls.RADIUS_SM}px;
        }}

        #inspectorAnnotList::item:hover {{
            background-color: rgba(0, 0, 0, 0.04);
        }}

        #inspectorAnnotList::item:selected {{
            background-color: {cls.LIGHT_ACCENT};
            color: #ffffff;
        }}

        /* Dialogs (Light) */
        QWidget#alertCard {{
            background-color: {cls.LIGHT_BG_CARD};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: {cls.RADIUS_LG}px;
            padding: 24px;
        }}

        QLabel#alertTitle {{
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: 15px;
            font-weight: 600;
        }}

        QLabel#alertBody {{
            color: {cls.LIGHT_TEXT_SECONDARY};
            font-size: 13px;
        }}

        QPushButton#primaryButton, #btnPrimary {{
            background-color: {cls.LIGHT_ACCENT};
            border: 1px solid {cls.LIGHT_ACCENT_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 30px;
        }}

        QPushButton#primaryButton:hover, #btnPrimary:hover {{
            background-color: {cls.LIGHT_ACCENT_ACTIVE};
        }}

        QPushButton#btnDontSave {{
            background-color: {cls.LIGHT_DANGER};
            border: 1px solid {cls.LIGHT_DANGER_HOVER};
            border-radius: 6px;
            color: #ffffff;
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 600;
            padding: 6px 18px;
            min-height: 30px;
        }}

        QPushButton#btnCancel {{
            background-color: {cls.LIGHT_BG_SIDEBAR};
            border: 1px solid {cls.LIGHT_BORDER};
            border-radius: 6px;
            color: {cls.LIGHT_TEXT_PRIMARY};
            font-size: {cls.FONT_SIZE_BASE}px;
            font-weight: 500;
            padding: 6px 18px;
            min-height: 30px;
        }}
        """


class MacTheme:
    """
    Backwards-compatible MacTheme class.
    Inherits design constants and delegates to StudioTheme for modern Studio Pro aesthetics.
    Preserves all historical constants (including LIGHT_BG_CANVAS and TRAFFIC_*).
    """
    DARK = StudioTheme.DARK
    LIGHT = StudioTheme.LIGHT

    # Dark Mode (Preserved historical attributes with Studio Pro refinements)
    DARK_BG_WINDOW = "#1a1b1f"
    DARK_BG_TOOLBAR = "#1a1b1f"
    DARK_BG_SIDEBAR = "#1e2026"
    DARK_BG_CANVAS = "#141518"
    DARK_BG_CARD = "#22242a"
    DARK_TEXT_PRIMARY = "#f3f4f6"
    DARK_TEXT_SECONDARY = "#9ca3af"
    DARK_BORDER = "rgba(255, 255, 255, 0.12)"
    DARK_ACCENT = "#2563eb"
    DARK_HOVER = "rgba(255, 255, 255, 0.08)"
    DARK_ACTIVE = "rgba(255, 255, 255, 0.14)"

    # Light Mode (Preserved historical attributes)
    LIGHT_BG_WINDOW = "#f5f5f7"
    LIGHT_BG_TOOLBAR = "#f0f0f3"
    LIGHT_BG_SIDEBAR = "#e8e8ed"
    LIGHT_BG_CANVAS = "#ececf0"
    LIGHT_BG_CARD = "#ffffff"
    LIGHT_TEXT_PRIMARY = "#1d1d1f"
    LIGHT_TEXT_SECONDARY = "#6e6e73"
    LIGHT_BORDER = "#d2d2d7"
    LIGHT_ACCENT = "#2563eb"
    LIGHT_HOVER = "#e5e5ea"
    LIGHT_ACTIVE = "#d8d8de"

    # Traffic light colors (Preserved for compatibility)
    TRAFFIC_RED = "#ef4444"
    TRAFFIC_RED_BORDER = "#dc2626"
    TRAFFIC_YELLOW = "#f59e0b"
    TRAFFIC_YELLOW_BORDER = "#d97706"
    TRAFFIC_GREEN = "#10b981"
    TRAFFIC_GREEN_BORDER = "#059669"

    # Design Tokens - Spacing Scale (4, 8, 12, 16, 20, 24px)
    SPACE_4 = StudioTheme.SPACE_4
    SPACE_8 = StudioTheme.SPACE_8
    SPACE_12 = StudioTheme.SPACE_12
    SPACE_16 = StudioTheme.SPACE_16
    SPACE_20 = StudioTheme.SPACE_20
    SPACE_24 = StudioTheme.SPACE_24

    # Design Tokens - Radii Scale (4, 8, 10px)
    RADIUS_XS = StudioTheme.RADIUS_XS
    RADIUS_SM = StudioTheme.RADIUS_SM
    RADIUS_MD = StudioTheme.RADIUS_MD
    RADIUS_LG = StudioTheme.RADIUS_LG

    # Design Tokens - Dimensions
    HEADER_HEIGHT = StudioTheme.HEADER_HEIGHT
    TOOLBAR_HEIGHT = StudioTheme.TOOLBAR_HEIGHT
    BTN_SIZE = StudioTheme.BTN_SIZE
    FONT_SIZE_BASE = StudioTheme.FONT_SIZE_BASE

    @classmethod
    def get_stylesheet(cls, mode: str = "dark") -> str:
        """Delegates stylesheet generation to StudioTheme."""
        return StudioTheme.get_stylesheet(mode)

    @classmethod
    def apply_theme(cls, target: QWidget, mode: str = "dark") -> None:
        """Applies theme to target widget or application."""
        StudioTheme.apply_theme(target, mode)

    @classmethod
    def _antimatter_stylesheet(cls) -> str:
        """Deep void-black and quantum neon violet/cyan aesthetic (Antimatter style)."""
        dark_qss = cls._dark_stylesheet()
        replaces = [
            (cls.DARK_BG_WINDOW, "#0f1117"),
            (cls.DARK_BG_CANVAS, "#08090d"),
            (cls.DARK_BG_SIDEBAR, "#12151f"),
            (cls.DARK_BG_DOCK, "#12151f"),
            (cls.DARK_BG_CARD, "#161a26"),
            (cls.DARK_BG_ELEVATED, "#1d2232"),
            (cls.DARK_ACCENT, "#8b5cf6"),
            (cls.DARK_ACCENT_HOVER, "#a855f7"),
            (cls.DARK_ACCENT_ACTIVE, "#7c3aed"),
            ("rgba(37, 99, 235, 0.16)", "rgba(139, 92, 246, 0.18)"),
            ("rgba(37, 99, 235, 0.45)", "rgba(139, 92, 246, 0.50)"),
            ("1px solid rgba(255, 255, 255, 0.10)", "1px solid rgba(139, 92, 246, 0.22)"),
        ]
        for src, dst in replaces:
            dark_qss = dark_qss.replace(src, dst)
        return dark_qss

    @classmethod
    def _dark_stylesheet(cls) -> str:
        return StudioTheme._dark_stylesheet()

    @classmethod
    def _light_stylesheet(cls) -> str:
        return StudioTheme._light_stylesheet()


def get_stylesheet(mode: str = "dark") -> str:
    """Convenience helper to retrieve the StudioTheme stylesheet."""
    return StudioTheme.get_stylesheet(mode)


def apply_theme(target: QWidget, mode: str = "dark") -> None:
    """Convenience helper to apply the StudioTheme stylesheet to a widget, window, or app."""
    StudioTheme.apply_theme(target, mode)


class ThemeManager(QObject):
    """
    Manages application theme state and system color-scheme detection.
    Supports 'auto' (follow OS theme), 'dark', and 'light'.
    """
    theme_changed = pyqtSignal(str)  # emits "dark" or "light"
    _instance = None

    AUTO = "auto"
    DARK = StudioTheme.DARK
    LIGHT = StudioTheme.LIGHT

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
                    return StudioTheme.LIGHT
                elif cs == Qt.ColorScheme.Dark:
                    return StudioTheme.DARK
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
                return StudioTheme.DARK
            elif "prefer-light" in val or "light" in val:
                return StudioTheme.LIGHT
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
                return StudioTheme.LIGHT if val == 1 else StudioTheme.DARK
            except Exception:
                pass

        return StudioTheme.DARK

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
            target = StudioTheme.DARK if scheme == Qt.ColorScheme.Dark else StudioTheme.LIGHT
            self.theme_changed.emit(target)
