"""
macOS style 'Inspector' window (Cmd+I) showing file, image, and PDF metadata.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QGridLayout, QLabel
)
from PyQt6.QtCore import Qt

class InspectorDialog(QDialog):
    """Apple macOS Inspector panel (`Cmd+I`)."""

    def __init__(self, metadata: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Inspector")
        self.setMinimumSize(320, 360)
        self.resize(360, 440)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        self.metadata = metadata
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        tabs = QTabWidget()

        # Tab 1: General Info
        general_widget = QWidget()
        g_layout = QGridLayout(general_widget)
        g_layout.setSpacing(10)

        rows = [
            ("Document Name:", str(self.metadata.get("title", "Untitled"))),
            ("Format:", str(self.metadata.get("format", "Unknown"))),
            ("File Size:", self._format_bytes(self.metadata.get("file_size", 0))),
            ("Pages:", str(self.metadata.get("page_count", 1))),
            ("Dimensions:", str(self.metadata.get("dimensions", "—"))),
            ("DPI / Resolution:", str(self.metadata.get("dpi", 72))),
            ("Color Mode:", str(self.metadata.get("mode", "RGB"))),
        ]

        for i, (label, val) in enumerate(rows):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: 600; color: #8e8e93;")
            val_lbl = QLabel(val)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            g_layout.addWidget(lbl, i, 0, Qt.AlignmentFlag.AlignRight)
            g_layout.addWidget(val_lbl, i, 1)

        tabs.addTab(general_widget, "General Info")

        # Tab 2: PDF Metadata (if present)
        if "author" in self.metadata or "producer" in self.metadata:
            pdf_widget = QWidget()
            p_layout = QGridLayout(pdf_widget)
            p_layout.setSpacing(10)

            pdf_rows = [
                ("Author:", str(self.metadata.get("author", "—"))),
                ("Subject:", str(self.metadata.get("subject", "—"))),
                ("Keywords:", str(self.metadata.get("keywords", "—"))),
                ("Producer:", str(self.metadata.get("producer", "—"))),
                ("Creator:", str(self.metadata.get("creator", "—"))),
            ]

            for i, (label, val) in enumerate(pdf_rows):
                lbl = QLabel(label)
                lbl.setStyleSheet("font-weight: 600; color: #8e8e93;")
                val_lbl = QLabel(val)
                val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                p_layout.addWidget(lbl, i, 0, Qt.AlignmentFlag.AlignRight)
                p_layout.addWidget(val_lbl, i, 1)

            tabs.addTab(pdf_widget, "PDF Details")

        layout.addWidget(tabs)

    def _format_bytes(self, num_bytes: int) -> str:
        if not num_bytes:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if num_bytes < 1024:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024
        return f"{num_bytes:.1f} TB"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
