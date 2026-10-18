"""
macOS style 'About Preview' window.
Displays application identity, developer Shivam Prasad, and attribution to TriviLabs.in.
"""

import os
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from preview import __version__

class AboutDialog(QDialog):
    """Apple macOS styled 'About Preview' dialog."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("About Document Viewer")
        self.setFixedSize(360, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 1. App Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pix)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 2. App Title & Version
        title_label = QLabel("Document Viewer")
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; margin-top: 4px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        version_label = QLabel(f"Version {__version__} (Multiplatform Edition)")
        version_label.setStyleSheet("font-size: 12px; color: #8e8e93;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        check_updates_btn = QPushButton("Check for Updates...")
        check_updates_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        check_updates_btn.setStyleSheet("""
            QPushButton {
                background: rgba(128, 128, 128, 0.12);
                border: 1px solid rgba(128, 128, 128, 0.25);
                border-radius: 5px;
                padding: 3px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(128, 128, 128, 0.22);
            }
        """)
        check_updates_btn.clicked.connect(self._on_check_updates_clicked)
        layout.addWidget(check_updates_btn, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(6)

        # 3. Developer & Attribution Card
        dev_card = QLabel(
            "<div style='text-align: center; line-height: 1.6;'>"
            "<b style='font-size: 13px;'>Developer:</b> <span style='font-size: 13px; color: #0a84ff;'>Shivam Prasad</span><br/>"
            "<b style='font-size: 13px;'>Powered by:</b> <a href='https://trivilabs.in' style='color: #0a84ff; text-decoration: none; font-weight: 600;'>TriviLabs.in</a>"
            "</div>"
        )
        dev_card.setOpenExternalLinks(True)
        dev_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_card.setStyleSheet("background: rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 10px 14px;")
        layout.addWidget(dev_card)

        # 4. Feature Summary Description
        desc_label = QLabel(
            "<div style='text-align: center; color: #98989d; font-size: 11px; line-height: 1.4;'>"
            "A pixel-faithful reconstruction of Apple macOS Preview.<br/>"
            "Features multi-page PDF rendering, universal image editing, Apple Markup toolbar, "
            "color & size adjustments, vector signatures, and high-DPI scaling."
            "</div>"
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        layout.addStretch()

        # 5. Close Button
        close_btn = QPushButton("Done")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("background-color: #0a84ff; color: white; padding: 5px 16px; border-radius: 6px; font-weight: 600;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def _on_check_updates_clicked(self):
        parent = self.parent()
        self.accept()
        if parent and hasattr(parent, "_check_for_updates_manual"):
            parent._check_for_updates_manual()
