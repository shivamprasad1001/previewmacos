"""
macOS style 'Adjust Color' window featuring real-time histogram and sliders.
Optimized for ultra-responsive live adjustments on high-resolution images.
"""

from typing import Optional, List
from PIL import Image

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QSlider, QPushButton, QCheckBox, QFrame, QWidget
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPaintEvent
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from preview.core.color_adjust import ColorAdjustEngine

class HistogramWidget(QWidget):
    """Renders real-time RGB histogram graph."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(84)
        self.r_hist: List[int] = [0] * 256
        self.g_hist: List[int] = [0] * 256
        self.b_hist: List[int] = [0] * 256

    def update_histogram(self, image: Image.Image):
        try:
            r, g, b = ColorAdjustEngine.get_histogram(image)
            self.r_hist, self.g_hist, self.b_hist = r, g, b
            self.update()
        except Exception:
            pass

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background card
        painter.setBrush(QBrush(QColor("#18181a")))
        painter.setPen(QPen(QColor("#38383a"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        max_val = max(max(self.r_hist), max(self.g_hist), max(self.b_hist), 1)
        w = self.width() - 8
        h = self.height() - 8

        # Draw RGB overlapping histogram curves
        channels = [
            (self.r_hist, QColor(255, 69, 58, 140)),
            (self.g_hist, QColor(50, 215, 75, 140)),
            (self.b_hist, QColor(10, 132, 255, 140))
        ]

        for hist_data, col in channels:
            painter.setPen(QPen(col, 1.2))
            for i in range(255):
                x1 = 4 + (i / 255.0) * w
                x2 = 4 + ((i + 1) / 255.0) * w
                y1 = self.height() - 4 - (hist_data[i] / max_val) * h
                y2 = self.height() - 4 - (hist_data[i + 1] / max_val) * h
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

class AdjustColorDialog(QDialog):
    """Apple macOS Adjust Color floating utility panel."""

    adjustments_applied = pyqtSignal(object)       # Emits adjusted PIL Image (live preview)
    adjustments_committed = pyqtSignal(object)     # Emits adjusted PIL Image (when finished/released)

    def __init__(self, base_image: Image.Image, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Color")
        self.setMinimumSize(320, 460)
        self.resize(340, 520)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        self.original_image: Image.Image = base_image.copy()
        self.current_preview: Image.Image = self.original_image.copy()

        # Real-time debounce timer (20ms) so rapid slider dragging is fluid and glitch-free
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(20)
        self._debounce_timer.timeout.connect(self._do_apply_changes)

        self._setup_ui()
        self.histogram.update_histogram(self.original_image)

    def set_image(self, base_image: Image.Image):
        """Update source image when a new document or image is opened."""
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self.original_image = base_image.copy()
        self.current_preview = self.original_image.copy()
        self._reset_all(silent=True)
        self.histogram.update_histogram(self.original_image)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Histogram
        self.histogram = HistogramWidget()
        layout.addWidget(self.histogram)

        # Auto levels & Reset
        btn_row = QHBoxLayout()
        self.auto_btn = QPushButton("Auto Levels")
        self.auto_btn.clicked.connect(self._on_auto_levels)
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self._reset_all)
        btn_row.addWidget(self.auto_btn)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        grid = QGridLayout()
        grid.setSpacing(8)

        # Exposure
        grid.addWidget(QLabel("Exposure:"), 0, 0)
        self.exposure_slider = self._create_slider()
        grid.addWidget(self.exposure_slider, 0, 1)

        # Contrast
        grid.addWidget(QLabel("Contrast:"), 1, 0)
        self.contrast_slider = self._create_slider()
        grid.addWidget(self.contrast_slider, 1, 1)

        # Saturation
        grid.addWidget(QLabel("Saturation:"), 2, 0)
        self.saturation_slider = self._create_slider()
        grid.addWidget(self.saturation_slider, 2, 1)

        # Temperature
        grid.addWidget(QLabel("Temperature:"), 3, 0)
        self.temp_slider = self._create_slider()
        grid.addWidget(self.temp_slider, 3, 1)

        # Tint
        grid.addWidget(QLabel("Tint:"), 4, 0)
        self.tint_slider = self._create_slider()
        grid.addWidget(self.tint_slider, 4, 1)

        # Sharpness
        grid.addWidget(QLabel("Sharpness:"), 5, 0)
        self.sharp_slider = self._create_slider()
        grid.addWidget(self.sharp_slider, 5, 1)

        layout.addLayout(grid)

        # Sepia
        self.sepia_check = QCheckBox("Sepia Tone")
        self.sepia_check.toggled.connect(self._apply_changes)
        layout.addWidget(self.sepia_check)

        layout.addStretch()

        # Close / Apply
        actions_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Revert")
        self.cancel_btn.clicked.connect(self._on_revert)
        self.done_btn = QPushButton("Done")
        self.done_btn.setStyleSheet("background-color: #0a84ff; color: white;")
        self.done_btn.clicked.connect(self._on_done)
        actions_row.addWidget(self.cancel_btn)
        actions_row.addWidget(self.done_btn)
        layout.addLayout(actions_row)

    def _create_slider(self) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.valueChanged.connect(self._apply_changes)
        slider.sliderReleased.connect(self._on_slider_released)
        return slider

    def _get_params(self):
        return (
            self.exposure_slider.value() / 100.0,
            self.contrast_slider.value() / 100.0,
            self.saturation_slider.value() / 100.0,
            self.temp_slider.value() / 100.0,
            self.tint_slider.value() / 100.0,
            self.sharp_slider.value() / 100.0,
            self.sepia_check.isChecked()
        )

    def _apply_changes(self):
        if hasattr(self, "_debounce_timer"):
            self._debounce_timer.start()
        else:
            self._do_apply_changes()

    def _do_apply_changes(self):
        exp, con, sat, temp, tint, sharp, sepia = self._get_params()
        enhanced = ColorAdjustEngine.adjust(
            self.original_image,
            exposure=exp, contrast=con, saturation=sat,
            temperature=temp, tint=tint, sharpness=sharp, sepia=sepia
        )
        self.current_preview = enhanced
        self.histogram.update_histogram(enhanced)
        self.adjustments_applied.emit(enhanced)

    def _on_slider_released(self):
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self._do_apply_changes()
        self.adjustments_committed.emit(self.current_preview)

    def _on_done(self):
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self._do_apply_changes()
        self.adjustments_committed.emit(self.current_preview)
        self.accept()

    def _on_auto_levels(self):
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self._reset_all(silent=True)
        enhanced = ColorAdjustEngine.auto_levels(self.original_image)
        self.original_image = enhanced.copy()
        self.current_preview = enhanced.copy()
        self.histogram.update_histogram(enhanced)
        self.adjustments_applied.emit(enhanced)
        self.adjustments_committed.emit(enhanced)

    def _reset_all(self, silent: bool = False):
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self.exposure_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.saturation_slider.blockSignals(True)
        self.temp_slider.blockSignals(True)
        self.tint_slider.blockSignals(True)
        self.sharp_slider.blockSignals(True)
        self.sepia_check.blockSignals(True)

        self.exposure_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)
        self.temp_slider.setValue(0)
        self.tint_slider.setValue(0)
        self.sharp_slider.setValue(0)
        self.sepia_check.setChecked(False)

        self.exposure_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)
        self.saturation_slider.blockSignals(False)
        self.temp_slider.blockSignals(False)
        self.tint_slider.blockSignals(False)
        self.sharp_slider.blockSignals(False)
        self.sepia_check.blockSignals(False)

        if not silent:
            self.current_preview = self.original_image.copy()
            self.histogram.update_histogram(self.original_image)
            self.adjustments_applied.emit(self.original_image)
            self.adjustments_committed.emit(self.original_image)

    def _on_revert(self):
        if hasattr(self, "_debounce_timer") and self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self._reset_all()
        self.reject()

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
