"""
macOS style Software Update Dialog & In-App Notification Banner.
Provides authentic Apple Sparkle-like UI for discovering, inspecting, 
and downloading new Preview releases.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QCheckBox, QFrame
)
from PyQt6.QtGui import QPixmap, QDesktopServices, QFont, QColor
from PyQt6.QtCore import Qt, QUrl, QSettings, pyqtSignal

from preview.core.updater import UpdateInfo
from preview import __version__

class UpdateDialog(QDialog):
    """Authentic macOS Software Update Dialog."""

    def __init__(self, update_info: UpdateInfo, current_version: str = __version__, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        
        self.setWindowTitle("Software Update")
        self.setFixedSize(540, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 20)
        main_layout.setSpacing(14)

        # 1. Top Header (Icon + Title + Subtitle)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(18)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # App Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pix)
        icon_label.setFixedSize(72, 72)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)

        # Title & Subtitle Texts
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_lbl = QLabel("A new version of Preview is available!")
        title_font = QFont("Inter", 14, QFont.Weight.Bold)
        title_lbl.setFont(title_font)
        text_layout.addWidget(title_lbl)

        sub_lbl = QLabel(
            f"Preview <b>{self.update_info.version}</b> is now available (you have <b>{self.current_version}</b>). "
            "Would you like to download it now?"
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("color: #8e8e93; font-size: 12px; line-height: 1.4;")
        text_layout.addWidget(sub_lbl)

        header_layout.addLayout(text_layout)
        main_layout.addLayout(header_layout)

        # 2. Release Notes Header
        notes_hdr = QLabel("Release Notes:")
        notes_hdr.setStyleSheet("font-weight: 600; font-size: 12px; margin-top: 4px;")
        main_layout.addWidget(notes_hdr)

        # 3. Release Notes Text Browser
        self.notes_browser = QTextBrowser()
        self.notes_browser.setOpenExternalLinks(True)
        # Convert plain release notes with markdown links / bullet points to clean HTML
        notes_html = self._format_release_notes(self.update_info.body)
        self.notes_browser.setHtml(notes_html)
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(128, 128, 128, 0.08);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        main_layout.addWidget(self.notes_browser)

        # 4. Checkbox: Auto check on startup
        settings = QSettings("TriviLabs", "PreviewMacOS")
        auto_check = settings.value("check_updates_on_startup", True, type=bool)
        self.auto_check_cb = QCheckBox("Automatically check for updates on startup")
        self.auto_check_cb.setChecked(auto_check)
        self.auto_check_cb.toggled.connect(self._toggle_auto_check)
        self.auto_check_cb.setStyleSheet("font-size: 11px; color: #8e8e93;")
        main_layout.addWidget(self.auto_check_cb)

        # 5. Bottom Buttons Bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Skip this version button
        skip_btn = QPushButton("Skip This Version")
        skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8e8e93;
                border: none;
                font-size: 12px;
                padding: 6px 8px;
            }
            QPushButton:hover {
                color: #ff453a;
                text-decoration: underline;
            }
        """)
        skip_btn.clicked.connect(self._skip_version)
        btn_layout.addWidget(skip_btn)

        btn_layout.addStretch()

        # Remind Me Later button
        later_btn = QPushButton("Remind Me Later")
        later_btn.setStyleSheet("""
            QPushButton {
                background: rgba(128, 128, 128, 0.15);
                border: 1px solid rgba(128, 128, 128, 0.25);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(128, 128, 128, 0.25);
            }
        """)
        later_btn.clicked.connect(self.reject)
        btn_layout.addWidget(later_btn)

        # Download / Install button (macOS Primary Accent Blue)
        dl_btn = QPushButton("Download Update")
        dl_btn.setDefault(True)
        dl_btn.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
            QPushButton:pressed {
                background-color: #005bb5;
            }
        """)
        dl_btn.clicked.connect(self._download_update)
        btn_layout.addWidget(dl_btn)

        main_layout.addLayout(btn_layout)

    def _format_release_notes(self, raw_body: str) -> str:
        """Formats GitHub Markdown release body into clean, styled HTML."""
        import html
        import re
        escaped = html.escape(raw_body)
        lines = []
        for line in escaped.split("\n"):
            line = line.strip()
            # Convert markdown inline styles
            line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
            line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", line)
            line = re.sub(r"`(.*?)`", r"<code style='background: rgba(128,128,128,0.2); padding: 1px 4px; border-radius: 3px;'>\1</code>", line)
            
            if line.startswith("### "):
                lines.append(f"<h4 style='margin: 8px 0 4px 0; color: #0a84ff;'>{line[4:]}</h4>")
            elif line.startswith("## "):
                lines.append(f"<h3 style='margin: 10px 0 4px 0; color: #0a84ff;'>{line[3:]}</h3>")
            elif line.startswith("# "):
                lines.append(f"<h2 style='margin: 12px 0 6px 0; color: #0a84ff;'>{line[2:]}</h2>")
            elif line.startswith("- ") or line.startswith("* "):
                lines.append(f"<li style='margin-bottom: 3px;'>{line[2:]}</li>")
            elif line:
                lines.append(f"<p style='margin: 4px 0;'>{line}</p>")
        return f"<div style='font-family: -apple-system, sans-serif; line-height: 1.5;'>{''.join(lines)}</div>"

    def _toggle_auto_check(self, checked: bool):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("check_updates_on_startup", checked)

    def _skip_version(self):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("skipped_version", self.update_info.version)
        self.reject()

    def _download_update(self):
        url = self.update_info.recommended_download_url
        QDesktopServices.openUrl(QUrl(url))
        self.accept()


class UpdateBanner(QFrame):
    """
    Subtle macOS-style floating top banner inside the main window notifying 
    the user when a new release is available.
    """

    view_requested = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, update_info: UpdateInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.update_info = update_info
        self.setFixedHeight(36)
        self.setObjectName("updateBanner")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        # Banner styling (Subtle Apple translucent banner)
        self.setStyleSheet("""
            #updateBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(10, 132, 255, 0.22), 
                    stop:1 rgba(94, 92, 230, 0.22));
                border-bottom: 1px solid rgba(10, 132, 255, 0.35);
            }
        """)

        # Icon / Badge
        badge = QLabel("✨")
        badge.setStyleSheet("font-size: 13px; background: transparent;")
        layout.addWidget(badge)

        # Message Text
        msg_lbl = QLabel(
            f"<b>Preview {self.update_info.version}</b> is now available!"
        )
        msg_lbl.setStyleSheet("font-size: 12px; background: transparent;")
        layout.addWidget(msg_lbl)

        layout.addStretch()

        # Action Button: 'What's New'
        action_btn = QPushButton("What's New && Download")
        action_btn.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
        """)
        action_btn.clicked.connect(self.view_requested.emit)
        layout.addWidget(action_btn)

        # Dismiss 'Later' button
        later_btn = QPushButton("Later")
        later_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8e8e93;
                border: none;
                font-size: 11px;
                padding: 3px 6px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        later_btn.clicked.connect(self._dismiss)
        layout.addWidget(later_btn)

        # Close '✕' Button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8e8e93;
                border: none;
                font-size: 11px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(128, 128, 128, 0.25);
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn)

    def _dismiss(self):
        self.setVisible(False)
        self.dismissed.emit()
