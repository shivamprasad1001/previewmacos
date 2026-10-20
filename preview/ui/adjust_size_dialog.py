"""
macOS style 'Adjust Size' dialog with proportional scaling, unit selection, and size preview.
"""

from typing import Optional, Tuple
from PIL import Image

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QComboBox, QCheckBox, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

class AdjustSizeDialog(QDialog):
    """Apple macOS Adjust Size modal."""

    size_applied = pyqtSignal(object)  # Emits resized PIL Image

    def __init__(self, image: Image.Image, original_file_size: int = 0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Size")
        self.setMinimumSize(360, 340)
        self.resize(390, 370)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        self.image = image
        self.orig_w = image.width
        self.orig_h = image.height
        self.orig_file_size = original_file_size
        self.aspect_ratio = self.orig_w / max(1.0, float(self.orig_h))

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Preset selector
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Fit into:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "640 × 480",
            "800 × 600",
            "1024 × 768",
            "1280 × 800",
            "1920 × 1080 (Full HD)",
            "3840 × 2160 (4K UHD)"
        ])
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo)
        layout.addLayout(preset_row)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Width
        grid.addWidget(QLabel("Width:"), 0, 0)
        self.width_edit = QLineEdit(str(self.orig_w))
        self.width_edit.textEdited.connect(self._on_width_edited)
        grid.addWidget(self.width_edit, 0, 1)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["pixels", "percent"])
        self.unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        grid.addWidget(self.unit_combo, 0, 2)

        # Height
        grid.addWidget(QLabel("Height:"), 1, 0)
        self.height_edit = QLineEdit(str(self.orig_h))
        self.height_edit.textEdited.connect(self._on_height_edited)
        grid.addWidget(self.height_edit, 1, 1)

        self.unit_label = QLabel("pixels")
        grid.addWidget(self.unit_label, 1, 2)

        # Resolution
        grid.addWidget(QLabel("Resolution:"), 2, 0)
        self.res_edit = QLineEdit("72")
        grid.addWidget(self.res_edit, 2, 1)
        grid.addWidget(QLabel("pixels/inch"), 2, 2)

        layout.addLayout(grid)

        # Checkboxes
        self.proportional_check = QCheckBox("Scale proportionally")
        self.proportional_check.setChecked(True)
        layout.addWidget(self.proportional_check)

        self.resample_check = QCheckBox("Resample image")
        self.resample_check.setChecked(True)
        layout.addWidget(self.resample_check)

        # Resulting size calculation
        self.size_summary_label = QLabel(f"Resulting size: {self._format_bytes(self.orig_file_size)}")
        self.size_summary_label.setStyleSheet("color: #8e8e93; font-size: 11px;")
        layout.addWidget(self.size_summary_label)

        layout.addStretch()

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #0a84ff; color: white; padding: 4px 14px;")
        ok_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _on_width_edited(self, text: str):
        if not self.proportional_check.isChecked():
            return
        try:
            val = float(text)
            if self.unit_combo.currentText() == "pixels":
                h_val = int(val / self.aspect_ratio)
                self.height_edit.setText(str(max(1, h_val)))
            elif self.unit_combo.currentText() == "percent":
                self.height_edit.setText(str(val))
        except ValueError:
            pass

    def _on_height_edited(self, text: str):
        if not self.proportional_check.isChecked():
            return
        try:
            val = float(text)
            if self.unit_combo.currentText() == "pixels":
                w_val = int(val * self.aspect_ratio)
                self.width_edit.setText(str(max(1, w_val)))
            elif self.unit_combo.currentText() == "percent":
                self.width_edit.setText(str(val))
        except ValueError:
            pass

    def _on_preset_selected(self, index: int):
        presets = {
            1: (640, 480),
            2: (800, 600),
            3: (1024, 768),
            4: (1280, 800),
            5: (1920, 1080),
            6: (3840, 2160),
        }
        if index in presets:
            pw, ph = presets[index]
            self.unit_combo.setCurrentText("pixels")
            self.width_edit.setText(str(pw))
            self.height_edit.setText(str(ph))

    def _on_unit_changed(self, index: int):
        unit = self.unit_combo.currentText()
        self.unit_label.setText(unit)
        if unit == "percent":
            self.width_edit.setText("100")
            self.height_edit.setText("100")
        else:
            self.width_edit.setText(str(self.orig_w))
            self.height_edit.setText(str(self.orig_h))

    def _on_apply(self):
        try:
            unit = self.unit_combo.currentText()
            if unit == "pixels":
                target_w = max(1, int(float(self.width_edit.text())))
                target_h = max(1, int(float(self.height_edit.text())))
            else:
                pct_w = float(self.width_edit.text()) / 100.0
                pct_h = float(self.height_edit.text()) / 100.0
                target_w = max(1, int(self.orig_w * pct_w))
                target_h = max(1, int(self.orig_h * pct_h))

            resized = self.image.resize((target_w, target_h), Image.Resampling.LANCZOS)
            self.size_applied.emit(resized)
            self.accept()
        except Exception:
            self.reject()

    def _format_bytes(self, num_bytes: int) -> str:
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
