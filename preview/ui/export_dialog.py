"""
macOS style Export Sheet / Dialog for Preview.
Allows choosing output format (PDF, JPEG, PNG, WebP, TIFF), compression quality, 
resolution (DPI), page range, and destination file path.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QSlider, QPushButton, QFileDialog, QRadioButton, QButtonGroup, 
    QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MacExportDialog(QDialog):
    """macOS-authentic Export dialog sheet."""

    def __init__(self, current_file_path: Optional[str] = None, page_count: int = 1, 
                 current_page: int = 0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Export")
        self.setFixedSize(460, 360)
        self.setModal(True)

        self.current_file_path = current_file_path or ""
        self.page_count = max(1, page_count)
        self.current_page = current_page

        base_name = "Untitled"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        self.default_name = f"{base_name} - Export"

        self.selected_path: Optional[str] = None
        self.selected_format: str = "PDF"
        self.selected_quality: int = 90
        self.selected_dpi: int = 150
        self.export_all_pages: bool = True

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        title_label = QLabel("Export Document")
        title_font = QFont("Inter", 13, QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 1. Export As (Filename)
        row_name = QHBoxLayout()
        name_lbl = QLabel("Export As:")
        name_lbl.setFixedWidth(90)
        self.name_edit = QLineEdit(self.default_name)
        row_name.addWidget(name_lbl)
        row_name.addWidget(self.name_edit)
        layout.addLayout(row_name)

        # 2. Format Selector
        row_fmt = QHBoxLayout()
        fmt_lbl = QLabel("Format:")
        fmt_lbl.setFixedWidth(90)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PDF", "JPEG", "PNG", "WebP", "TIFF"])
        self.fmt_combo.currentTextChanged.connect(self._on_format_changed)
        row_fmt.addWidget(fmt_lbl)
        row_fmt.addWidget(self.fmt_combo)
        layout.addLayout(row_fmt)

        # 3. Quality Slider (visible for JPEG and WebP)
        self.quality_widget = QWidget()
        row_qual = QHBoxLayout(self.quality_widget)
        row_qual.setContentsMargins(0, 0, 0, 0)
        qual_lbl = QLabel("Quality:")
        qual_lbl.setFixedWidth(90)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(90)
        self.quality_val_label = QLabel("90%")
        self.quality_val_label.setFixedWidth(40)
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_val_label.setText(f"{v}%")
        )
        row_qual.addWidget(qual_lbl)
        row_qual.addWidget(self.quality_slider)
        row_qual.addWidget(self.quality_val_label)
        layout.addWidget(self.quality_widget)
        self.quality_widget.setVisible(False)  # Hidden by default for PDF

        # 4. Resolution (DPI)
        row_dpi = QHBoxLayout()
        dpi_lbl = QLabel("Resolution:")
        dpi_lbl.setFixedWidth(90)
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItem("Screen (72 DPI)", 72)
        self.dpi_combo.addItem("Normal (150 DPI)", 150)
        self.dpi_combo.addItem("Print High-Res (300 DPI)", 300)
        self.dpi_combo.addItem("Ultra (600 DPI)", 600)
        self.dpi_combo.setCurrentIndex(1)
        row_dpi.addWidget(dpi_lbl)
        row_dpi.addWidget(self.dpi_combo)
        layout.addLayout(row_dpi)

        # 5. Page Scope (if multi-page)
        if self.page_count > 1:
            row_scope = QHBoxLayout()
            scope_lbl = QLabel("Pages:")
            scope_lbl.setFixedWidth(90)
            self.radio_all = QRadioButton(f"All ({self.page_count} pages)")
            self.radio_all.setChecked(True)
            self.radio_current = QRadioButton(f"Current Page ({self.current_page + 1})")
            
            self.scope_group = QButtonGroup(self)
            self.scope_group.addButton(self.radio_all)
            self.scope_group.addButton(self.radio_current)

            row_scope.addWidget(scope_lbl)
            row_scope.addWidget(self.radio_all)
            row_scope.addWidget(self.radio_current)
            row_scope.addStretch()
            layout.addLayout(row_scope)

        layout.addStretch()

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(128, 128, 128, 0.2);")
        layout.addWidget(div)

        # Bottom Buttons: Cancel & Save
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(84)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setDefault(True)
        self.save_btn.setFixedWidth(84)
        self.save_btn.clicked.connect(self._on_save_clicked)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _on_format_changed(self, fmt: str):
        is_lossy = fmt in ("JPEG", "WebP")
        self.quality_widget.setVisible(is_lossy)

    def _on_save_clicked(self):
        fmt = self.fmt_combo.currentText()
        ext_map = {
            "PDF": ".pdf",
            "JPEG": ".jpg",
            "PNG": ".png",
            "WebP": ".webp",
            "TIFF": ".tiff"
        }
        ext = ext_map.get(fmt, ".pdf")
        
        default_dir = os.path.dirname(self.current_file_path) if self.current_file_path else os.path.expanduser("~/Documents")
        candidate_name = self.name_edit.text().strip() or "Export"
        if not candidate_name.lower().endswith(ext):
            candidate_name += ext

        initial_path = os.path.join(default_dir, candidate_name)
        save_path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {fmt}", initial_path, f"{fmt} Files (*{ext});;All Files (*)"
        )

        if not save_path:
            return

        self.selected_path = save_path
        self.selected_format = fmt
        self.selected_quality = self.quality_slider.value()
        self.selected_dpi = self.dpi_combo.currentData() or 150
        if hasattr(self, "radio_all"):
            self.export_all_pages = self.radio_all.isChecked()
        else:
            self.export_all_pages = True

        self.accept()
