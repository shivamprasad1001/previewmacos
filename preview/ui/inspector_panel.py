"""
macOS-styled Collapsible Right Inspector Panel for Preview on Linux.
Provides context-aware document metadata, live annotation properties,
annotation layer management, and embedded image color adjustments.
"""

import os
from typing import Optional, List, Dict, Any
from PIL import Image

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QToolButton, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox,
    QSlider, QComboBox, QFontComboBox, QPlainTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QSizePolicy, QColorDialog, QMessageBox
)
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPointF

from preview.core.document import Document
from preview.core.annotations import AnnotationItem, AnnotationType
from preview.core.color_adjust import ColorAdjustEngine
from preview.icons import MacIconFactory
from preview.theme import MacTheme
from preview.ui.adjust_color_dialog import HistogramWidget


class MacInspectorPanel(QWidget):
    """
    Collapsible 3-tab inspector panel:
      Tab 0: Properties / Format (Context-aware for selected annotation or document info)
      Tab 1: Annotations List (Layer view of markups on active page)
      Tab 2: Adjustments (Live RGB histogram and image enhancement sliders)
    """

    close_requested = pyqtSignal()
    annotation_updated = pyqtSignal()
    apply_redaction_requested = pyqtSignal()
    color_adjusted = pyqtSignal(object)  # Emits adjusted PIL Image
    color_reset_requested = pyqtSignal()
    delete_annotation_requested = pyqtSignal(object)
    duplicate_annotation_requested = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macInspectorPanel")
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.document: Optional[Document] = None
        self.current_page: int = 0
        self.selected_annotation: Optional[AnnotationItem] = None
        self.current_theme: str = "dark"
        self._updating_ui: bool = False

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar with Segmented Tab Switcher and Close Button
        header = QWidget()
        header.setObjectName("inspectorHeader")
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 6, 10, 6)
        h_layout.setSpacing(8)

        # Segmented Tab Buttons: [ Format | Layers | Adjust ] (Evenly Spaced)
        self.seg_container = QWidget()
        self.seg_container.setObjectName("inspectorSegmented")
        self.seg_container.setFixedHeight(30)
        seg_layout = QHBoxLayout(self.seg_container)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)

        self.tab_info_btn = QToolButton()
        self.tab_info_btn.setText("Format")
        self.tab_info_btn.setCheckable(True)
        self.tab_info_btn.setChecked(True)
        self.tab_info_btn.setFixedHeight(26)
        self.tab_info_btn.setToolTip("Document & Selection Properties")
        self.tab_info_btn.setAccessibleName("Format Tab")
        self.tab_info_btn.clicked.connect(lambda: self.set_active_tab(0))
        seg_layout.addWidget(self.tab_info_btn, 1)

        self.tab_annots_btn = QToolButton()
        self.tab_annots_btn.setText("Layers")
        self.tab_annots_btn.setCheckable(True)
        self.tab_annots_btn.setFixedHeight(26)
        self.tab_annots_btn.setToolTip("Page Annotations & Layers")
        self.tab_annots_btn.setAccessibleName("Layers Tab")
        self.tab_annots_btn.clicked.connect(lambda: self.set_active_tab(1))
        seg_layout.addWidget(self.tab_annots_btn, 1)

        self.tab_adjust_btn = QToolButton()
        self.tab_adjust_btn.setText("Adjust")
        self.tab_adjust_btn.setCheckable(True)
        self.tab_adjust_btn.setFixedHeight(26)
        self.tab_adjust_btn.setToolTip("Color Adjustments & Histogram")
        self.tab_adjust_btn.setAccessibleName("Adjust Tab")
        self.tab_adjust_btn.clicked.connect(lambda: self.set_active_tab(2))
        seg_layout.addWidget(self.tab_adjust_btn, 1)

        h_layout.addWidget(self.seg_container, 1)

        # Collapse / Close button with Lucide close icon
        self.close_btn = QToolButton()
        self.close_btn.setObjectName("inspectorCloseBtn")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setIcon(MacIconFactory.create_icon("close", "#98989d", 14))
        self.close_btn.setToolTip("Hide Inspector (Ctrl+I)")
        self.close_btn.setAccessibleName("Hide Inspector")
        self.close_btn.clicked.connect(self.close_requested.emit)
        h_layout.addWidget(self.close_btn)

        main_layout.addWidget(header)

        # 1-px horizontal separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setObjectName("inspectorDivider")
        main_layout.addWidget(sep)

        # 2. Stacked Content Area with 16px Padding
        self.stack = QStackedWidget()
        
        # Tab 0: Properties / Format
        self.properties_scroll = QScrollArea()
        self.properties_scroll.setWidgetResizable(True)
        self.properties_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.properties_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(16, 16, 16, 16)
        self.properties_layout.setSpacing(12)
        self.properties_scroll.setWidget(self.properties_container)
        self.stack.addWidget(self.properties_scroll)

        # Tab 1: Annotations Layers
        self.annots_container = QWidget()
        annots_layout = QVBoxLayout(self.annots_container)
        annots_layout.setContentsMargins(16, 16, 16, 16)
        annots_layout.setSpacing(10)

        annots_header = QLabel("Annotations on Page")
        annots_header.setStyleSheet("font-weight: 600; font-size: 12px; color: #98989d;")
        annots_layout.addWidget(annots_header)

        self.annot_list = QListWidget()
        self.annot_list.setObjectName("inspectorAnnotList")
        self.annot_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.annot_list.currentRowChanged.connect(self._on_annot_list_row_changed)
        annots_layout.addWidget(self.annot_list, 1)

        annots_btn_row = QHBoxLayout()
        annots_btn_row.setSpacing(6)
        self.del_annot_btn = QPushButton("Delete Selected")
        self.del_annot_btn.clicked.connect(self._delete_current_annotation)
        annots_btn_row.addWidget(self.del_annot_btn)

        self.clear_annots_btn = QPushButton("Clear All")
        self.clear_annots_btn.clicked.connect(self._clear_all_annotations)
        annots_btn_row.addWidget(self.clear_annots_btn)
        annots_layout.addLayout(annots_btn_row)

        self.stack.addWidget(self.annots_container)

        # Tab 2: Live Adjustments & Histogram
        self.adjust_scroll = QScrollArea()
        self.adjust_scroll.setWidgetResizable(True)
        self.adjust_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.adjust_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.adjust_container = QWidget()
        self.adjust_layout = QVBoxLayout(self.adjust_container)
        self.adjust_layout.setContentsMargins(16, 16, 16, 16)
        self.adjust_layout.setSpacing(12)
        self._setup_adjustments_tab()
        self.adjust_scroll.setWidget(self.adjust_container)
        self.stack.addWidget(self.adjust_scroll)

        main_layout.addWidget(self.stack, 1)

        self._refresh_properties_view()

    def set_active_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        self.tab_info_btn.setChecked(index == 0)
        self.tab_annots_btn.setChecked(index == 1)
        self.tab_adjust_btn.setChecked(index == 2)
        if index == 1:
            self.refresh_annotations_list()

    def _setup_adjustments_tab(self):
        # RGB Histogram Graph
        hist_label = QLabel("RGB Histogram")
        hist_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #98989d;")
        self.adjust_layout.addWidget(hist_label)

        self.histogram_widget = HistogramWidget(self)
        self.histogram_widget.setFixedHeight(75)
        self.hist_widget = self.histogram_widget
        self.adjust_layout.addWidget(self.histogram_widget)

        # Sliders Section
        self.sliders: Dict[str, QSlider] = {}
        slider_defs = [
            ("Exposure", "exposure", -100, 100, 0),
            ("Contrast", "contrast", -100, 100, 0),
            ("Highlights", "highlights", -100, 100, 0),
            ("Shadows", "shadows", -100, 100, 0),
            ("Saturation", "saturation", -100, 100, 0),
            ("Temperature", "temperature", -100, 100, 0),
            ("Tint", "tint", -100, 100, 0),
            ("Sharpness", "sharpness", -100, 100, 0),
        ]

        for label_text, key, min_v, max_v, def_v in slider_defs:
            row = QWidget()
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(75)
            lbl.setStyleSheet("font-size: 11px;")
            r_lay.addWidget(lbl)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(def_v)
            slider.valueChanged.connect(self._on_slider_adjusted)
            self.sliders[key] = slider
            r_lay.addWidget(slider, 1)

            val_lbl = QLabel(f"{def_v}")
            val_lbl.setFixedWidth(28)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setStyleSheet("font-size: 11px; color: #98989d;")
            slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(f"{v}"))
            r_lay.addWidget(val_lbl)

            self.adjust_layout.addWidget(row)

        btn_row = QHBoxLayout()
        self.auto_btn = QPushButton("Auto Levels")
        self.auto_btn.clicked.connect(self._auto_adjust)
        btn_row.addWidget(self.auto_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_adjustments)
        btn_row.addWidget(self.reset_btn)
        self.adjust_layout.addLayout(btn_row)

        self.adjust_layout.addStretch()

    def set_document(self, doc: Optional[Document], current_page: int = 0):
        self.document = doc
        self.current_page = current_page
        self._refresh_properties_view()
        self.refresh_annotations_list()
        self.update_histogram()

    def set_selected_annotation(self, annot: Optional[AnnotationItem]):
        self.selected_annotation = annot
        self._refresh_properties_view()
        if annot:
            # Switch to properties tab automatically when user clicks an annotation
            self.set_active_tab(0)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            l = item.layout()
            if l is not None:
                self._clear_layout(l)

    def _refresh_properties_view(self):
        # Clear existing properties widgets
        self._clear_layout(self.properties_layout)

        if self.selected_annotation:
            self._build_annotation_properties(self.selected_annotation)
        elif self.document:
            self._build_document_properties(self.document)
        else:
            empty_lbl = QLabel("No document selected.\nOpen a file or select an annotation to inspect.")
            empty_lbl.setWordWrap(True)
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #98989d; padding: 40px 12px; font-size: 12px; line-height: 1.4;")
            self.properties_layout.addWidget(empty_lbl)

        self.properties_layout.addStretch()

    def _build_annotation_properties(self, annot: AnnotationItem):
        type_name = str(annot.item_type.name).replace("_", " ").title()
        
        # Header with type icon and label
        hdr_box = QHBoxLayout()
        title_lbl = QLabel(f"<b>{type_name}</b>")
        title_lbl.setStyleSheet("font-size: 14px;")
        hdr_box.addWidget(title_lbl, 1)

        self.annot_del_btn = QToolButton()
        self.annot_del_btn.setText("🗑")
        self.annot_del_btn.setToolTip("Delete this annotation")
        self.annot_del_btn.clicked.connect(lambda: self.delete_annotation_requested.emit(annot))
        hdr_box.addWidget(self.annot_del_btn)
        self.properties_layout.addLayout(hdr_box)

        # Style section (Stroke, Fill, Width, Opacity)
        self.style_card = QFrame()
        self.style_card.setObjectName("inspectorCard")
        s_lay = QVBoxLayout(self.style_card)
        s_lay.setContentsMargins(10, 10, 10, 10)
        s_lay.setSpacing(8)

        sec_lbl = QLabel("APPEARANCE")
        sec_lbl.setStyleSheet("font-weight: 700; font-size: 10px; color: #98989d; letter-spacing: 0.5px;")
        s_lay.addWidget(sec_lbl)

        # Stroke Color
        stroke_row = QHBoxLayout()
        stroke_lbl = QLabel("Border:")
        stroke_lbl.setStyleSheet("font-size: 12px;")
        self.stroke_btn = QToolButton()
        self.stroke_btn.setFixedSize(50, 24)
        self._update_color_button(self.stroke_btn, annot.stroke_color)
        self.stroke_btn.clicked.connect(lambda: self._pick_color("stroke"))
        stroke_row.addWidget(stroke_lbl)
        stroke_row.addStretch()
        stroke_row.addWidget(self.stroke_btn)
        s_lay.addLayout(stroke_row)

        # Fill Color (for shapes)
        if annot.item_type in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, 
                               AnnotationType.ELLIPSE, AnnotationType.CALLOUT):
            fill_row = QHBoxLayout()
            fill_lbl = QLabel("Fill:")
            fill_lbl.setStyleSheet("font-size: 12px;")
            self.fill_btn = QToolButton()
            self.fill_btn.setFixedSize(50, 24)
            self._update_color_button(self.fill_btn, annot.fill_color, is_fill=True)
            self.fill_btn.clicked.connect(lambda: self._pick_color("fill"))
            fill_row.addWidget(fill_lbl)
            fill_row.addStretch()
            fill_row.addWidget(self.fill_btn)
            s_lay.addLayout(fill_row)

        # Line Width
        width_row = QHBoxLayout()
        w_lbl = QLabel("Line Width:")
        w_lbl.setStyleSheet("font-size: 12px;")
        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(0.5, 30.0)
        self.w_spin.setSingleStep(0.5)
        self.w_spin.setValue(annot.stroke_width)
        self.w_spin.valueChanged.connect(self._on_width_changed)
        self.width_spin = self.w_spin
        width_row.addWidget(w_lbl)
        width_row.addStretch()
        width_row.addWidget(self.w_spin)
        s_lay.addLayout(width_row)

        self.properties_layout.addWidget(self.style_card)

        # Typography Section (if Text, Note, or Callout)
        if annot.item_type in (AnnotationType.TEXT, AnnotationType.NOTE, AnnotationType.CALLOUT):
            text_box = QFrame()
            text_box.setObjectName("inspectorCard")
            t_lay = QVBoxLayout(text_box)
            t_lay.setContentsMargins(10, 10, 10, 10)
            t_lay.setSpacing(8)

            t_sec = QLabel("TYPOGRAPHY")
            t_sec.setStyleSheet("font-weight: 700; font-size: 10px; color: #98989d; letter-spacing: 0.5px;")
            t_lay.addWidget(t_sec)

            # Font Family & Size
            f_row = QHBoxLayout()
            self.font_combo = QFontComboBox()
            self.font_combo.setCurrentFont(QFont(annot.font_family))
            self.font_combo.currentFontChanged.connect(lambda f: self._on_font_family_changed(f.family()))
            f_row.addWidget(self.font_combo, 1)

            self.f_size_spin = QSpinBox()
            self.f_size_spin.setRange(8, 96)
            self.f_size_spin.setValue(annot.font_size)
            self.f_size_spin.valueChanged.connect(self._on_font_size_changed)
            f_row.addWidget(self.f_size_spin)
            t_lay.addLayout(f_row)

            # Text content editor
            t_lay.addWidget(QLabel("Content:"))
            self.text_edit = QPlainTextEdit()
            self.text_edit.setPlainText(annot.text)
            self.text_edit.setMaximumHeight(70)
            self.text_edit.textChanged.connect(self._on_text_content_changed)
            t_lay.addWidget(self.text_edit)

            self.properties_layout.addWidget(text_box)

        # Redaction Specific Card
        if annot.item_type == AnnotationType.REDACT:
            redact_box = QFrame()
            redact_box.setObjectName("inspectorCard")
            r_lay = QVBoxLayout(redact_box)
            r_lay.setContentsMargins(10, 10, 10, 10)
            r_lay.setSpacing(8)

            r_sec = QLabel("PRIVACY REDACTION")
            r_sec.setStyleSheet("font-weight: 700; font-size: 10px; color: #ff453a;")
            r_lay.addWidget(r_sec)

            info_msg = QLabel("<b>Status: Pending</b><br>This region is queued for permanent blackout. Applying redaction permanently scrubs all covered text and pixels.")
            info_msg.setWordWrap(True)
            info_msg.setStyleSheet("font-size: 11px; color: #98989d;")
            r_lay.addWidget(info_msg)

            apply_btn = QPushButton("Apply Permanent Redaction")
            apply_btn.setStyleSheet("background-color: #ff3b30; color: #ffffff; font-weight: 600;")
            apply_btn.clicked.connect(self.apply_redaction_requested.emit)
            r_lay.addWidget(apply_btn)

            self.properties_layout.addWidget(redact_box)

        # Geometry Section (Bounds)
        geom_box = QFrame()
        geom_box.setObjectName("inspectorCard")
        g_lay = QVBoxLayout(geom_box)
        g_lay.setContentsMargins(10, 10, 10, 10)
        g_lay.setSpacing(6)

        g_sec = QLabel("GEOMETRY")
        g_sec.setStyleSheet("font-weight: 700; font-size: 10px; color: #98989d; letter-spacing: 0.5px;")
        g_lay.addWidget(g_sec)

        b = annot.get_bounds()
        dims = QLabel(f"W: {int(b.width())} px   H: {int(b.height())} px<br>X: {int(b.x())} px    Y: {int(b.y())} px")
        dims.setStyleSheet("font-size: 11px; color: #98989d; font-family: monospace;")
        g_lay.addWidget(dims)

        self.properties_layout.addWidget(geom_box)

    def _build_document_properties(self, doc: Document):
        meta = doc.metadata or {}
        
        # Document Summary Card
        card = QFrame()
        card.setObjectName("inspectorCard")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(10, 10, 10, 10)
        c_lay.setSpacing(8)

        lbl = QLabel("DOCUMENT INFO")
        lbl.setStyleSheet("font-weight: 700; font-size: 10px; color: #98989d; letter-spacing: 0.5px;")
        c_lay.addWidget(lbl)

        # File Name
        fname = os.path.basename(doc.file_path) if doc.file_path else "Untitled"
        f_lbl = QLabel(f"<b>File:</b> {fname}")
        f_lbl.setWordWrap(True)
        c_lay.addWidget(f_lbl)

        # Dimensions & Pages
        pg_info = f"{doc.page_count} Pages" if doc.page_count > 1 else "1 Page"
        pg_lbl = QLabel(f"<b>Pages:</b> {pg_info} (Active: {self.current_page + 1})")
        pg_lbl.setWordWrap(True)
        c_lay.addWidget(pg_lbl)

        if meta.get("file_size"):
            sz = meta["file_size"]
            sz_str = f"{sz / (1024*1024):.2f} MB" if sz > 1024*1024 else f"{sz / 1024:.1f} KB"
            sz_lbl = QLabel(f"<b>Size:</b> {sz_str}")
            sz_lbl.setWordWrap(True)
            c_lay.addWidget(sz_lbl)

        w_pt, h_pt = doc.get_page_size(self.current_page)
        w_in, h_in = w_pt / 72.0, h_pt / 72.0
        dims_str = f"{w_in:.2f} × {h_in:.2f} in ({int(w_pt)} × {int(h_pt)} pt)"
        dims_lbl = QLabel(f"<b>Dimensions:</b> {dims_str}")
        dims_lbl.setWordWrap(True)
        c_lay.addWidget(dims_lbl)

        fmt = meta.get("format") or ("PDF" if doc.is_pdf else "Image")
        fmt_lbl = QLabel(f"<b>Kind:</b> {fmt} Document")
        fmt_lbl.setWordWrap(True)
        c_lay.addWidget(fmt_lbl)

        self.properties_layout.addWidget(card)

        # Metadata Details Card
        if doc.is_pdf:
            pdf_card = QFrame()
            pdf_card.setObjectName("inspectorCard")
            p_lay = QVBoxLayout(pdf_card)
            p_lay.setContentsMargins(10, 10, 10, 10)
            p_lay.setSpacing(6)

            p_lbl = QLabel("PDF METADATA")
            p_lbl.setStyleSheet("font-weight: 700; font-size: 10px; color: #98989d; letter-spacing: 0.5px;")
            p_lay.addWidget(p_lbl)

            for key in ["title", "author", "creator", "producer", "creationDate"]:
                val = meta.get(key)
                if val:
                    k_disp = key.replace("Date", " Date").capitalize()
                    m_lbl = QLabel(f"<b>{k_disp}:</b> {val}")
                    m_lbl.setWordWrap(True)
                    p_lay.addWidget(m_lbl)

            enc = "Password Encrypted (AES-256)" if meta.get("encrypted") else "None"
            enc_lbl = QLabel(f"<b>Security:</b> {enc}")
            enc_lbl.setWordWrap(True)
            p_lay.addWidget(enc_lbl)

            self.properties_layout.addWidget(pdf_card)

    def refresh_annotations_list(self):
        self.annot_list.blockSignals(True)
        self.annot_list.clear()

        win = self.window()
        canvas = getattr(win, "canvas", None)
        if not canvas or self.current_page not in canvas.annotations:
            self.annot_list.blockSignals(False)
            return

        annots = canvas.annotations[self.current_page]
        for idx, a in enumerate(annots):
            t_name = str(a.item_type.name).replace("_", " ").title()
            preview = f"{t_name} #{idx + 1}"
            if a.text and a.item_type in (AnnotationType.TEXT, AnnotationType.NOTE):
                preview += f": \"{a.text[:15]}\""

            item = QListWidgetItem(preview)
            item.setData(Qt.ItemDataRole.UserRole, a)
            self.annot_list.addItem(item)
            if a == self.selected_annotation:
                self.annot_list.setCurrentItem(item)

        self.annot_list.blockSignals(False)

    def _on_annot_list_row_changed(self, row: int):
        if row < 0:
            return
        item = self.annot_list.item(row)
        if item:
            annot = item.data(Qt.ItemDataRole.UserRole)
            win = self.window()
            canvas = getattr(win, "canvas", None)
            if canvas:
                canvas._selected_annotation = annot
                canvas.update()
                self.set_selected_annotation(annot)

    def _delete_current_annotation(self):
        if self.selected_annotation:
            self.delete_annotation_requested.emit(self.selected_annotation)

    def _clear_all_annotations(self):
        win = self.window()
        canvas = getattr(win, "canvas", None)
        if canvas and self.current_page in canvas.annotations and canvas.annotations[self.current_page]:
            ans = QMessageBox.question(
                self, "Clear All Annotations",
                "Are you sure you want to delete all markups on this page?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ans == QMessageBox.StandardButton.Yes:
                canvas.annotations[self.current_page].clear()
                canvas._selected_annotation = None
                canvas.update()
                self.set_selected_annotation(None)
                self.refresh_annotations_list()

    def update_histogram(self):
        if not self.document:
            return
        try:
            pix = self.document.get_pixmap(self.current_page, dpi=72)
            # Convert to PIL Image for histogram computation
            img = Image.fromqpixmap(pix)
            self.histogram_widget.update_histogram(img)
        except Exception:
            pass

    def _on_slider_adjusted(self):
        if not self.document:
            return
        settings = {k: s.value() for k, s in self.sliders.items()}
        try:
            pil_img = self.document.get_pil_image(self.current_page)
            if pil_img:
                adj = ColorAdjustEngine.apply_adjustments(pil_img, settings)
                self.color_adjusted.emit(adj)
                self.histogram_widget.update_histogram(adj)
        except Exception:
            pass

    def _auto_adjust(self):
        self.sliders["contrast"].setValue(15)
        self.sliders["exposure"].setValue(5)
        self.sliders["saturation"].setValue(10)
        self.sliders["sharpness"].setValue(20)

    def reset_adjustments(self):
        for s in self.sliders.values():
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)
        self.color_reset_requested.emit()
        self.update_histogram()

    # --- Property Change Callbacks ---
    def _pick_color(self, target: str):
        if not self.selected_annotation:
            return
        initial = self.selected_annotation.stroke_color if target == "stroke" else self.selected_annotation.fill_color
        col = QColorDialog.getColor(initial, self, f"Select {target.capitalize()} Color")
        if col.isValid():
            if target == "stroke":
                self.selected_annotation.stroke_color = col
                self._update_color_button(self.stroke_btn, col)
            else:
                self.selected_annotation.fill_color = col
                self._update_color_button(self.fill_btn, col, is_fill=True)
            self.annotation_updated.emit()

    def _update_color_button(self, btn: QToolButton, col: QColor, is_fill: bool = False):
        if is_fill and col.alpha() == 0:
            btn.setStyleSheet("background-color: transparent; border: 1px dashed #888; border-radius: 4px;")
            btn.setText("None")
        else:
            btn.setStyleSheet(f"background-color: {col.name()}; border: 1px solid rgba(255,255,255,0.2); border-radius: 4px;")
            btn.setText("")

    def _on_width_changed(self, val: float):
        if self.selected_annotation:
            self.selected_annotation.stroke_width = float(val)
            self.annotation_updated.emit()

    def _on_font_family_changed(self, fam: str):
        if self.selected_annotation:
            self.selected_annotation.font_family = fam
            self.annotation_updated.emit()

    def _on_font_size_changed(self, sz: int):
        if self.selected_annotation:
            self.selected_annotation.font_size = int(sz)
            self.annotation_updated.emit()

    def _on_text_content_changed(self):
        if self.selected_annotation and hasattr(self, "text_edit"):
            self.selected_annotation.text = self.text_edit.toPlainText()
            self.annotation_updated.emit()

    def update_icons(self, icon_color: str):
        self.icon_color = icon_color
