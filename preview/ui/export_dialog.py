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
                 current_page: int = 0, document: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Export")
        self.setFixedSize(480, 420)
        self.setModal(True)

        self.current_file_path = current_file_path or ""
        self.page_count = max(1, page_count)
        self.current_page = current_page
        self.document = document

        base_name = "Untitled"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        self.default_name = f"{base_name} - Export"

        self.selected_path: Optional[str] = None
        self.selected_format: str = "PDF"
        self.selected_quality: int = 90
        self.selected_dpi: int = 150
        self.export_all_pages: bool = True
        self.reduce_file_size: bool = False

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

        # 2b. Quartz Filter / Presets (Reduce File Size)
        self.filter_widget = QWidget()
        row_filter = QHBoxLayout(self.filter_widget)
        row_filter.setContentsMargins(0, 0, 0, 0)
        filter_lbl = QLabel("Quartz Filter:")
        filter_lbl.setFixedWidth(90)
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("None")
        self.filter_combo.addItem("Reduce File Size")
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        row_filter.addWidget(filter_lbl)
        row_filter.addWidget(self.filter_combo)
        layout.addWidget(self.filter_widget)

        # Size estimation label
        self.size_estimate_label = QLabel()
        self.size_estimate_label.setStyleSheet("color: #0a84ff; font-size: 11px; margin-left: 90px; font-weight: 500;")
        self.size_estimate_label.setVisible(False)
        layout.addWidget(self.size_estimate_label)

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
        is_pdf = (fmt == "PDF")
        self.filter_widget.setVisible(is_pdf)
        if not is_pdf:
            self.size_estimate_label.setVisible(False)
        else:
            if self.filter_combo.currentText() == "Reduce File Size":
                self.size_estimate_label.setVisible(True)

    def _on_filter_changed(self, text: str):
        if text == "Reduce File Size":
            self.reduce_file_size = True
            before_bytes, after_bytes = self._get_size_estimation()
            reduction_pct = max(0, int((1.0 - (after_bytes / max(1, before_bytes))) * 100))
            b_str = self._format_size(before_bytes)
            a_str = self._format_size(after_bytes)
            self.size_estimate_label.setText(f"Estimated: {b_str} → {a_str} (~{reduction_pct}% reduction)")
            self.size_estimate_label.setVisible(True)
        else:
            self.reduce_file_size = False
            self.size_estimate_label.setVisible(False)

    def _get_size_estimation(self) -> tuple[int, int]:
        if self.document and hasattr(self.document, "estimate_reduced_size"):
            return self.document.estimate_reduced_size()
        if self.current_file_path and os.path.exists(self.current_file_path):
            bs = os.path.getsize(self.current_file_path)
            return bs, max(1024, int(bs * 0.35))
        return 1024 * 1024, int(1024 * 1024 * 0.35)

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        if num_bytes < 1024:
            return f"{num_bytes} B"
        elif num_bytes < 1024 * 1024:
            return f"{num_bytes / 1024:.1f} KB"
        else:
            return f"{num_bytes / (1024 * 1024):.1f} MB"

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
        self.reduce_file_size = (fmt == "PDF" and self.filter_combo.currentText() == "Reduce File Size")
        if hasattr(self, "radio_all"):
            self.export_all_pages = self.radio_all.isChecked()
        else:
            self.export_all_pages = True

        self.accept()
