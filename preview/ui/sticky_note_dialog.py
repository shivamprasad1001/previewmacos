"""
macOS style Sticky Note Popover / Editor Dialog.
Replicates Apple Preview's expandable yellow note sheet.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QWidget
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

class StickyNoteDialog(QDialog):
    """Authentic Apple macOS Sticky Note floating window."""

    text_saved = pyqtSignal(str)

    def __init__(self, initial_text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Sticky Note")
        self.setFixedSize(280, 240)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._initial_text = initial_text
        self._setup_ui()

    def _setup_ui(self):
        # Yellow Post-It theme
        self.setStyleSheet("""
            QDialog {
                background-color: #fef08a;
                border: 1px solid #eab308;
                border-radius: 8px;
            }
            QLabel {
                color: #713f12;
                font-family: -apple-system, "SF Pro Text", "Inter", sans-serif;
                font-size: 11px;
                font-weight: 600;
            }
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #1c1917;
                font-family: -apple-system, "SF Pro Text", "Inter", sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }
            QPushButton {
                background-color: rgba(113, 63, 18, 0.12);
                border: 1px solid rgba(113, 63, 18, 0.25);
                border-radius: 4px;
                color: #713f12;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: rgba(113, 63, 18, 0.2);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(6)
        
        lbl_title = QLabel("📝 Note")
        header.addWidget(lbl_title)
        header.addStretch()

        done_btn = QPushButton("Done")
        done_btn.clicked.connect(self.accept)
        header.addWidget(done_btn)
        layout.addLayout(header)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setPlainText(self._initial_text)
        self.editor.setPlaceholderText("Type your note here...")
        layout.addWidget(self.editor)

    def accept(self):
        self.text_saved.emit(self.get_text())
        super().accept()

    def get_text(self) -> str:
        return self.editor.toPlainText()
