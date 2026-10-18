"""
macOS style 'Manage Signatures' dialog where users can draw, save, and insert signatures.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QListWidget, QListWidgetItem, QLineEdit
)
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QPixmap, QIcon, QMouseEvent, QPaintEvent
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QSize

class SignaturePad(QWidget):
    """Drawing canvas for vector signatures."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(160)
        self.strokes: List[List[QPointF]] = []
        self._current_stroke: List[QPointF] = []

    def clear(self):
        self.strokes.clear()
        self._current_stroke.clear()
        self.update()

    def has_signature(self) -> bool:
        return any(len(s) > 1 for s in self.strokes)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._current_stroke = [event.position()]
            self.strokes.append(self._current_stroke)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self._current_stroke:
            self._current_stroke.append(event.position())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Pad background
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#d2d2d7"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

        # Baseline signature guide line
        base_y = self.height() * 0.72
        painter.setPen(QPen(QColor("#c7c7cc"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(20, base_y), QPointF(self.width() - 20, base_y))

        # "Sign here" placeholder text if empty
        if not self.has_signature():
            painter.setPen(QColor("#aeaeb2"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sign using your trackpad or mouse here")

        # Draw ink strokes
        pen = QPen(QColor("#000000"), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        for stroke in self.strokes:
            if len(stroke) > 1:
                path = QPainterPath()
                path.moveTo(stroke[0])
                for pt in stroke[1:]:
                    path.lineTo(pt)
                painter.drawPath(path)

    def get_signature_pixmap(self) -> QPixmap:
        """Renders transparent PNG pixmap of the drawn signature."""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#000000"), 3.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        for stroke in self.strokes:
            if len(stroke) > 1:
                path = QPainterPath()
                path.moveTo(stroke[0])
                for pt in stroke[1:]:
                    path.lineTo(pt)
                p.drawPath(path)
        p.end()
        return pixmap

class SignatureDialog(QDialog):
    """Apple macOS Signature modal."""

    signature_selected = pyqtSignal(QPixmap)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Signatures")
        self.setFixedSize(400, 320)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        header = QLabel("Create Signature")
        header.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(header)

        self.pad = SignaturePad()
        layout.addWidget(self.pad)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.pad.clear)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()

        insert_btn = QPushButton("Insert Signature")
        insert_btn.setStyleSheet("background-color: #0a84ff; color: white; padding: 4px 14px;")
        insert_btn.clicked.connect(self._on_insert)
        btn_row.addWidget(insert_btn)

        layout.addLayout(btn_row)

    def _on_insert(self):
        if self.pad.has_signature():
            pix = self.pad.get_signature_pixmap()
            self.signature_selected.emit(pix)
            self.accept()
        else:
            self.reject()
