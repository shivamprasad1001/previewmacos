"""
macOS-styled Save Confirmation Dialog (Sheet Alert) for unsaved document edits.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QPixmap
from PyQt6.QtCore import Qt
from preview.theme import MacTheme

class MacSaveConfirmationDialog(QDialog):
    """
    macOS Alert Sheet prompt displayed when closing or navigating away from a document
    with unsaved modifications.

    Buttons:
    - Don't Save: Discards edits and proceeds.
    - Cancel: Aborts closing and keeps editing.
    - Save: Prompts to save the edited document (as a new copy or custom location).
    """

    CANCEL = 0
    DONT_SAVE = 1
    SAVE = 2
    # Backward compatibility alias
    SAVE_AS_NEW_COPY = 2

    def __init__(self, file_name: str, has_file_path: bool = True, theme: MacTheme = MacTheme.DARK, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.file_name = file_name
        self.has_file_path = has_file_path
        self.theme = theme
        self.result_code = self.CANCEL

        self.setObjectName("macSaveDialog")
        self.setWindowTitle("Save Changes")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)

        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        # Outer layout with margins for shadow
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        # Card container
        self.card = QWidget(self)
        self.card.setObjectName("alertCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 22, 24, 20)
        card_layout.setSpacing(14)

        # Header area: icon + titles
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # App / Document Icon
        icon_label = QLabel()
        icon_label.setObjectName("alertIcon")
        icon_label.setFixedSize(54, 54)
        icon_label.setStyleSheet("background: transparent;")
        
        icon_pix = QPixmap(54, 54)
        icon_pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(icon_pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Rounded squircle icon background
        p.setBrush(QBrush(QColor("#007aff")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(2, 2, 50, 50, 12, 12)
        
        # Document icon glyph
        p.setPen(QPen(QColor("#ffffff"), 2.2))
        p.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        p.drawText(icon_pix.rect(), Qt.AlignmentFlag.AlignCenter, "📄")
        p.end()
        icon_label.setPixmap(icon_pix)
        header_layout.addWidget(icon_label)

        # Text vertical layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        # Primary headline
        self.title_label = QLabel(
            f"Do you want to save the changes made to the document “{self.file_name}”?"
        )
        self.title_label.setObjectName("alertTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        text_layout.addWidget(self.title_label)

        # Subtitle / body text
        self.body_label = QLabel("Your changes will be lost if you don’t save them.")
        self.body_label.setObjectName("alertBody")
        self.body_label.setWordWrap(True)
        self.body_label.setFont(QFont("Inter", 10))
        text_layout.addWidget(self.body_label)

        header_layout.addLayout(text_layout)
        card_layout.addLayout(header_layout)

        # Spacing
        card_layout.addSpacing(6)

        # Buttons row: [ Don't Save ]  ...stretch...  [ Cancel ]  [ Save ]
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 1. Don't Save (Destructive action)
        self.btn_dont_save = QPushButton("Don't Save")
        self.btn_dont_save.setObjectName("btnDontSave")
        self.btn_dont_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dont_save.setShortcut("Alt+D")
        self.btn_dont_save.clicked.connect(self._on_dont_save)
        btn_layout.addWidget(self.btn_dont_save)

        btn_layout.addStretch(1)

        # 2. Cancel
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)

        # 3. Save (Primary action)
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        card_layout.addLayout(btn_layout)
        outer_layout.addWidget(self.card)

        # Soft drop shadow for authentic macOS modal sheet feel
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        self.setFixedWidth(480)

    def _apply_styling(self):
        is_dark = (self.theme == MacTheme.DARK)
        
        bg_col = "#252528" if is_dark else "#f4f4f7"
        border_col = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.15)"
        title_col = "#f5f5f7" if is_dark else "#1d1d1f"
        body_col = "#a1a1a6" if is_dark else "#515154"

        btn_bg = "#3a3a3e" if is_dark else "#e5e5ea"
        btn_hover = "#4a4a4e" if is_dark else "#d8d8de"
        btn_text = "#f5f5f7" if is_dark else "#1d1d1f"
        btn_border = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.1)"

        dont_save_text = "#ff453a" if is_dark else "#d70015"
        dont_save_hover = "rgba(255, 69, 58, 0.15)" if is_dark else "rgba(215, 0, 21, 0.12)"

        primary_bg = "#007aff"
        primary_hover = "#0062cc"

        self.setStyleSheet(f"""
            QWidget#alertCard {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 14px;
            }}
            QLabel#alertTitle {{
                color: {title_col};
            }}
            QLabel#alertBody {{
                color: {body_col};
                line-height: 1.4;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: 1px solid {btn_border};
                border-radius: 6px;
                padding: 6px 16px;
                font-family: 'Inter', -apple-system, sans-serif;
                font-size: 11pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
            QPushButton#btnDontSave {{
                color: {dont_save_text};
                border: 1px solid {border_col};
            }}
            QPushButton#btnDontSave:hover {{
                background-color: {dont_save_hover};
            }}
            QPushButton#btnPrimary {{
                background-color: {primary_bg};
                color: #ffffff;
                border: none;
                font-weight: 600;
            }}
            QPushButton#btnPrimary:hover {{
                background-color: {primary_hover};
            }}
        """)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._on_cancel()
        elif key == Qt.Key.Key_D and (event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self._on_dont_save()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_save()
        else:
            super().keyPressEvent(event)

    def _on_dont_save(self):
        self.result_code = self.DONT_SAVE
        self.accept()

    def _on_cancel(self):
        self.result_code = self.CANCEL
        self.reject()

    def _on_save(self):
        self.result_code = self.SAVE
        self.accept()
