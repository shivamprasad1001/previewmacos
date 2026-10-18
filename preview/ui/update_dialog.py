"""
macOS style Software Update Dialog & In-App Notification Banner.
Provides authentic Apple Sparkle-like UI for discovering, inspecting, 
downloading, and auto-installing new Preview releases.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QCheckBox, QFrame, QProgressBar, QApplication
)
from PyQt6.QtGui import QPixmap, QDesktopServices, QFont, QColor
from PyQt6.QtCore import Qt, QUrl, QSettings, pyqtSignal

from preview.core.updater import UpdateInfo, UpdateDownloadWorker, install_update
from preview import __version__

class UpdateDialog(QDialog):
    """Authentic macOS Software Update Dialog with live in-app download and installation."""

    def __init__(self, update_info: UpdateInfo, current_version: str = __version__, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.download_worker: Optional[UpdateDownloadWorker] = None
        self.downloaded_filepath: Optional[str] = None
        
        self.setWindowTitle("Software Update")
        self.setFixedSize(540, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 20)
        main_layout.setSpacing(12)

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

        self.sub_lbl = QLabel(
            f"Preview <b>{self.update_info.version}</b> is now available (you have <b>{self.current_version}</b>). "
            "Would you like to update now?"
        )
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setStyleSheet("color: #8e8e93; font-size: 12px; line-height: 1.4;")
        text_layout.addWidget(self.sub_lbl)

        header_layout.addLayout(text_layout)
        main_layout.addLayout(header_layout)

        # 2. Release Notes Header
        self.notes_hdr = QLabel("Release Notes:")
        self.notes_hdr.setStyleSheet("font-weight: 600; font-size: 12px; margin-top: 2px;")
        main_layout.addWidget(self.notes_hdr)

        # 3. Release Notes Text Browser
        self.notes_browser = QTextBrowser()
        self.notes_browser.setOpenExternalLinks(True)
        notes_html = self._format_release_notes(self.update_info.body)
        self.notes_browser.setHtml(notes_html)
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(128, 128, 128, 0.08);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        main_layout.addWidget(self.notes_browser)

        # 4. In-App Download Progress Container (Hidden until user clicks Update)
        self.download_container = QWidget()
        dl_layout = QVBoxLayout(self.download_container)
        dl_layout.setContentsMargins(0, 4, 0, 4)
        dl_layout.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(128, 128, 128, 0.25);
                border-radius: 6px;
                background-color: rgba(128, 128, 128, 0.12);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a84ff, stop:1 #30b0c7);
                border-radius: 5px;
            }
        """)
        dl_layout.addWidget(self.progress_bar)

        info_row = QHBoxLayout()
        self.dl_status_lbl = QLabel("Downloading update package...")
        self.dl_status_lbl.setStyleSheet("font-size: 11px; color: #8e8e93;")
        self.dl_speed_lbl = QLabel("")
        self.dl_speed_lbl.setStyleSheet("font-size: 11px; color: #8e8e93; font-weight: 500;")
        info_row.addWidget(self.dl_status_lbl)
        info_row.addStretch()
        info_row.addWidget(self.dl_speed_lbl)
        dl_layout.addLayout(info_row)

        self.download_container.setVisible(False)
        main_layout.addWidget(self.download_container)

        # 5. Checkbox: Auto check on startup
        settings = QSettings("TriviLabs", "PreviewMacOS")
        auto_check = settings.value("check_updates_on_startup", True, type=bool)
        self.auto_check_cb = QCheckBox("Automatically check for updates on startup")
        self.auto_check_cb.setChecked(auto_check)
        self.auto_check_cb.toggled.connect(self._toggle_auto_check)
        self.auto_check_cb.setStyleSheet("font-size: 11px; color: #8e8e93;")
        main_layout.addWidget(self.auto_check_cb)

        # 6. Bottom Buttons Bar
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)

        # Skip this version button
        self.skip_btn = QPushButton("Skip This Version")
        self.skip_btn.setStyleSheet("""
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
        self.skip_btn.clicked.connect(self._skip_version)
        self.btn_layout.addWidget(self.skip_btn)

        self.btn_layout.addStretch()

        # Remind Me Later button
        self.later_btn = QPushButton("Remind Me Later")
        self.later_btn.setStyleSheet("""
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
        self.later_btn.clicked.connect(self.reject)
        self.btn_layout.addWidget(self.later_btn)

        # Update Now Button (Primary Accent Blue)
        self.update_btn = QPushButton("Update Now")
        self.update_btn.setDefault(True)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #0a84ff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
            QPushButton:pressed {
                background-color: #005bb5;
            }
            QPushButton:disabled {
                background-color: rgba(10, 132, 255, 0.4);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.btn_layout.addWidget(self.update_btn)

        main_layout.addLayout(self.btn_layout)

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

    def _on_update_clicked(self):
        if self.downloaded_filepath:
            self._install_and_restart()
            return

        download_url = self.update_info.recommended_download_url
        if not download_url.endswith((".deb", ".exe")):
            QDesktopServices.openUrl(QUrl(self.update_info.html_url))
            self.accept()
            return

        # Prepare cache destination
        cache_dir = os.path.expanduser("~/.cache/preview-macos/updates")
        os.makedirs(cache_dir, exist_ok=True)
        filename = os.path.basename(download_url.split("?")[0])
        target_path = os.path.join(cache_dir, filename)

        # Switch UI to downloading state
        self.notes_browser.setMaximumHeight(140)
        self.download_container.setVisible(True)
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Downloading...")
        self.skip_btn.setVisible(False)
        self.later_btn.setText("Cancel")
        self.later_btn.clicked.disconnect()
        self.later_btn.clicked.connect(self._cancel_download)

        # Start background download worker
        self.download_worker = UpdateDownloadWorker(download_url, target_path, parent=self)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.failed.connect(self._on_download_failed)
        self.download_worker.start()

    def _on_download_progress(self, percent: int, downloaded: int, total: int, speed: float):
        self.progress_bar.setValue(percent)
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        self.dl_status_lbl.setText(f"Downloading update... {dl_mb:.1f} MB of {tot_mb:.1f} MB ({percent}%)")
        self.dl_speed_lbl.setText(f"{speed:.1f} MB/s")

    def _on_download_finished(self, target_path: str):
        self.downloaded_filepath = target_path
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(128, 128, 128, 0.25);
                border-radius: 6px;
                background-color: rgba(128, 128, 128, 0.12);
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 5px;
            }
        """)
        self.dl_status_lbl.setText("✨ Update downloaded successfully! Ready to install.")
        self.dl_speed_lbl.setText("100%")
        self.later_btn.setText("Install on Quit")
        self.later_btn.clicked.disconnect()
        self.later_btn.clicked.connect(self.accept)

        self.update_btn.setText("Restart && Install Now")
        self.update_btn.setEnabled(True)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2da84a;
            }
            QPushButton:pressed {
                background-color: #23863a;
            }
        """)

    def _on_download_failed(self, err: str):
        self.download_container.setVisible(False)
        self.notes_browser.setMaximumHeight(16777215)
        self.update_btn.setText("Retry Update")
        self.update_btn.setEnabled(True)
        self.skip_btn.setVisible(True)
        self.later_btn.setText("Remind Me Later")
        self.later_btn.clicked.disconnect()
        self.later_btn.clicked.connect(self.reject)

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Download Failed", f"Could not download update package:\n{err}")

    def _cancel_download(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
        self.reject()

    def _install_and_restart(self):
        if not self.downloaded_filepath:
            return
        success, msg = install_update(self.downloaded_filepath)
        if success:
            self.accept()
            QApplication.instance().quit()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Installation Error", msg)


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

        self.setStyleSheet("""
            #updateBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(10, 132, 255, 0.22), 
                    stop:1 rgba(94, 92, 230, 0.22));
                border-bottom: 1px solid rgba(10, 132, 255, 0.35);
            }
        """)

        badge = QLabel("✨")
        badge.setStyleSheet("font-size: 13px; background: transparent;")
        layout.addWidget(badge)

        msg_lbl = QLabel(
            f"<b>Preview {self.update_info.version}</b> is now available!"
        )
        msg_lbl.setStyleSheet("font-size: 12px; background: transparent;")
        layout.addWidget(msg_lbl)

        layout.addStretch()

        action_btn = QPushButton("What's New && Update")
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
