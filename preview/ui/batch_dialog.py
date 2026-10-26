"""
macOS-styled Batch Image Resizing & Format Conversion Dialog.
Provides multithreaded batch processing, format conversion (JPEG, PNG, WebP, TIFF),
proportional scaling, max-dimension constraints, and EXIF metadata preservation.
"""

import os
from typing import List, Optional, Dict, Any
from PIL import Image

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QComboBox, QCheckBox, QPushButton, QSlider,
    QProgressBar, QFileDialog, QWidget, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont


class BatchProcessWorker(QThread):
    """Background worker thread for batch image processing."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(int, int, list)  # success_count, fail_count, errors

    def __init__(
        self,
        image_paths: List[str],
        output_dir: str,
        format_name: str,
        quality: int = 90,
        dimension_mode: str = "original",
        scale_pct: float = 100.0,
        max_width: int = 1920,
        max_height: int = 1080,
        preserve_exif: bool = True
    ):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.format_name = format_name
        self.quality = quality
        self.dimension_mode = dimension_mode
        self.scale_pct = scale_pct
        self.max_width = max_width
        self.max_height = max_height
        self.preserve_exif = preserve_exif
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        success = 0
        failed = 0
        errors = []
        ext_map = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WebP": ".webp",
            "TIFF": ".tiff"
        }
        out_ext = ext_map.get(self.format_name, ".jpg")

        total = len(self.image_paths)
        for idx, src_path in enumerate(self.image_paths):
            if self._is_cancelled:
                break
            fname = os.path.basename(src_path)
            self.progress.emit(idx + 1, total, fname)
            try:
                with Image.open(src_path) as img:
                    exif = img.getexif() if self.preserve_exif else None

                    orig_w, orig_h = img.size
                    new_w, new_h = orig_w, orig_h

                    if self.dimension_mode == "scale" and self.scale_pct > 0:
                        factor = self.scale_pct / 100.0
                        new_w = max(1, int(orig_w * factor))
                        new_h = max(1, int(orig_h * factor))
                    elif self.dimension_mode == "fit" and self.max_width > 0 and self.max_height > 0:
                        ratio = min(self.max_width / orig_w, self.max_height / orig_h)
                        new_w = max(1, int(orig_w * ratio))
                        new_h = max(1, int(orig_h * ratio))

                    if (new_w, new_h) != (orig_w, orig_h):
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    save_img = img
                    if self.format_name == "JPEG" and save_img.mode in ("RGBA", "P"):
                        save_img = save_img.convert("RGB")
                    elif self.format_name == "TIFF" and save_img.mode == "P":
                        save_img = save_img.convert("RGB")

                    base = os.path.splitext(fname)[0]
                    dest_path = os.path.join(self.output_dir, f"{base}{out_ext}")

                    save_kwargs = {}
                    if self.format_name in ("JPEG", "WebP"):
                        save_kwargs["quality"] = self.quality
                    if self.preserve_exif and exif:
                        save_kwargs["exif"] = exif

                    save_img.save(dest_path, format=self.format_name, **save_kwargs)
                    success += 1
            except Exception as e:
                failed += 1
                errors.append(f"{fname}: {str(e)}")

        self.finished.emit(success, failed, errors)


class BatchConvertDialog(QDialog):
    """macOS-authentic Batch Image Resizing & Format Conversion Sheet."""

    def __init__(
        self,
        image_paths: Optional[List[str]] = None,
        default_output_dir: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Batch Resize / Convert Images")
        self.setFixedSize(500, 480)
        self.setModal(True)

        self.image_paths: List[str] = list(image_paths) if image_paths else []
        self.output_dir: str = default_output_dir or os.path.expanduser("~/Pictures/Exported")
        self.worker: Optional[BatchProcessWorker] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header Title
        title_label = QLabel("Batch Resize / Convert Images")
        title_label.setFont(QFont("Inter", 13, QFont.Weight.DemiBold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 1. Source Images Summary & Add Button
        row_files = QHBoxLayout()
        self.files_label = QLabel(f"{len(self.image_paths)} images selected")
        self.files_label.setStyleSheet("font-weight: 500;")
        self.add_files_btn = QPushButton("Add Images...")
        self.add_files_btn.clicked.connect(self._on_add_files)
        row_files.addWidget(self.files_label)
        row_files.addStretch()
        row_files.addWidget(self.add_files_btn)
        layout.addLayout(row_files)

        # 2. Target Format
        row_fmt = QHBoxLayout()
        fmt_lbl = QLabel("Target Format:")
        fmt_lbl.setFixedWidth(110)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WebP", "TIFF"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        row_fmt.addWidget(fmt_lbl)
        row_fmt.addWidget(self.format_combo)
        layout.addLayout(row_fmt)

        # 3. Quality Slider (visible for JPEG and WebP)
        self.quality_widget = QWidget()
        row_qual = QHBoxLayout(self.quality_widget)
        row_qual.setContentsMargins(0, 0, 0, 0)
        qual_lbl = QLabel("Output Quality:")
        qual_lbl.setFixedWidth(110)
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

        # 4. Dimension Resize Mode
        row_dim = QHBoxLayout()
        dim_lbl = QLabel("Dimensions:")
        dim_lbl.setFixedWidth(110)
        self.dim_combo = QComboBox()
        self.dim_combo.addItem("Original Size (100%)", "original")
        self.dim_combo.addItem("Scale by Percentage", "scale")
        self.dim_combo.addItem("Fit into Max Dimensions", "fit")
        self.dim_combo.currentIndexChanged.connect(self._on_dim_mode_changed)
        row_dim.addWidget(dim_lbl)
        row_dim.addWidget(self.dim_combo)
        layout.addLayout(row_dim)

        # 4b. Scale percentage input
        self.scale_widget = QWidget()
        row_scale = QHBoxLayout(self.scale_widget)
        row_scale.setContentsMargins(0, 0, 0, 0)
        scale_lbl = QLabel("Scale:")
        scale_lbl.setFixedWidth(110)
        self.scale_edit = QLineEdit("50")
        self.scale_edit.setFixedWidth(70)
        pct_lbl = QLabel("%")
        row_scale.addWidget(scale_lbl)
        row_scale.addWidget(self.scale_edit)
        row_scale.addWidget(pct_lbl)
        row_scale.addStretch()
        layout.addWidget(self.scale_widget)
        self.scale_widget.setVisible(False)

        # 4c. Fit dimensions input
        self.fit_widget = QWidget()
        row_fit = QHBoxLayout(self.fit_widget)
        row_fit.setContentsMargins(0, 0, 0, 0)
        fit_lbl = QLabel("Max Size:")
        fit_lbl.setFixedWidth(110)
        self.max_w_edit = QLineEdit("1920")
        self.max_w_edit.setFixedWidth(65)
        x_lbl = QLabel("×")
        self.max_h_edit = QLineEdit("1080")
        self.max_h_edit.setFixedWidth(65)
        px_lbl = QLabel("px")
        row_fit.addWidget(fit_lbl)
        row_fit.addWidget(self.max_w_edit)
        row_fit.addWidget(x_lbl)
        row_fit.addWidget(self.max_h_edit)
        row_fit.addWidget(px_lbl)
        row_fit.addStretch()
        layout.addWidget(self.fit_widget)
        self.fit_widget.setVisible(False)

        # 5. Options: EXIF preservation
        self.exif_check = QCheckBox("Preserve EXIF metadata")
        self.exif_check.setChecked(True)
        layout.addWidget(self.exif_check)

        # 6. Output Destination Directory
        row_dest = QHBoxLayout()
        dest_lbl = QLabel("Destination:")
        dest_lbl.setFixedWidth(110)
        self.dest_edit = QLineEdit(self.output_dir)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_dest)
        row_dest.addWidget(dest_lbl)
        row_dest.addWidget(self.dest_edit)
        row_dest.addWidget(self.browse_btn)
        layout.addLayout(row_dest)

        # 7. Progress Bar & Status (Initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #8e8e93; font-size: 11px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(128, 128, 128, 0.2);")
        layout.addWidget(div)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(84)
        self.cancel_btn.clicked.connect(self._on_cancel_or_close)

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setObjectName("primaryButton")
        self.convert_btn.setDefault(True)
        self.convert_btn.setFixedWidth(84)
        self.convert_btn.clicked.connect(self._on_start_convert)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.convert_btn)
        layout.addLayout(btn_row)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images to Batch Process", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif);;All Files (*)"
        )
        if files:
            for f in files:
                if f not in self.image_paths:
                    self.image_paths.append(f)
            self.files_label.setText(f"{len(self.image_paths)} images selected")

    def _on_format_changed(self, fmt: str):
        is_lossy = fmt in ("JPEG", "WebP")
        self.quality_widget.setVisible(is_lossy)

    def _on_dim_mode_changed(self, idx: int):
        mode = self.dim_combo.currentData()
        self.scale_widget.setVisible(mode == "scale")
        self.fit_widget.setVisible(mode == "fit")

    def _on_browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder", self.dest_edit.text())
        if folder:
            self.output_dir = folder
            self.dest_edit.setText(folder)

    def _on_start_convert(self):
        if not self.image_paths:
            QMessageBox.warning(self, "No Images", "Please select at least one image to process.")
            return

        dest = self.dest_edit.text().strip()
        if not dest:
            QMessageBox.warning(self, "Invalid Destination", "Please specify a destination folder.")
            return

        fmt = self.format_combo.currentText()
        quality = self.quality_slider.value()
        dim_mode = self.dim_combo.currentData()
        
        try:
            scale_pct = float(self.scale_edit.text().strip())
        except ValueError:
            scale_pct = 100.0

        try:
            max_w = int(self.max_w_edit.text().strip())
            max_h = int(self.max_h_edit.text().strip())
        except ValueError:
            max_w, max_h = 1920, 1080

        preserve_exif = self.exif_check.isChecked()

        # Update UI state for processing
        self.convert_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Starting batch conversion...")

        self.worker = BatchProcessWorker(
            image_paths=self.image_paths,
            output_dir=dest,
            format_name=fmt,
            quality=quality,
            dimension_mode=dim_mode,
            scale_pct=scale_pct,
            max_width=max_w,
            max_height=max_h,
            preserve_exif=preserve_exif
        )
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, current: int, total: int, fname: str):
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"Processing ({current}/{total}): {fname}")

    def _on_worker_finished(self, success: int, failed: int, errors: list):
        self.progress_bar.setValue(100)
        if failed == 0:
            self.status_label.setText(f"Done! Successfully converted {success} images.")
        else:
            self.status_label.setText(f"Finished: {success} converted, {failed} failed.")
        self.convert_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.cancel_btn.setText("Close")

    def _on_cancel_or_close(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(500)
        self.reject()
