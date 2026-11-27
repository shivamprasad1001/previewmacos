"""Export, print, and PDF manipulation actions mixin for MacMainWindow."""

import os

from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QLineEdit, QMessageBox
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt

from preview.core.document import Document
from preview.ui.export_dialog import MacExportDialog


class ExportPrintMixin:
    """PDF operations, export dialogs, printing, and text extraction."""

    def _set_pdf_view_mode(self, mode: str):
        self.canvas.set_view_mode(mode)
        if hasattr(self, "single_mode_act"):
            self.single_mode_act.setChecked(mode == "Single")
        if hasattr(self, "two_up_mode_act"):
            self.two_up_mode_act.setChecked(mode == "Two-Up")
        self._show_status(f"PDF view mode: {mode}")

    def _set_pdf_password(self):
        if not self.document or not self.document.is_pdf:
            QMessageBox.information(self, "PDF Password", "A PDF document must be open to configure encryption.")
            return
        pwd, ok = QInputDialog.getText(
            self, "Set PDF Password",
            "Enter password to encrypt document with AES-256 upon saving:",
            QLineEdit.EchoMode.Password
        )
        if ok and pwd:
            self.document.set_pdf_password(pwd)
            self._show_status("PDF security password set. Save document to apply encryption.")

    def _merge_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files to Merge", "", "PDF Documents (*.pdf)"
        )
        if len(paths) < 2:
            QMessageBox.information(self, "Merge PDFs", "Please select at least 2 PDF files to merge.")
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF As", "Merged.pdf", "PDF Document (*.pdf)"
        )
        if out_path:
            if Document.merge_pdfs(paths, out_path):
                self.open_file(out_path)
                self._show_status(f"Successfully merged {len(paths)} PDFs.")
            else:
                QMessageBox.critical(self, "Merge Error", "Could not merge selected PDFs.")

    def _split_pdf(self):
        if not self.document or not self.document.is_pdf:
            QMessageBox.information(self, "Split PDF", "A PDF document must be open to extract pages.")
            return
        rng_str, ok = QInputDialog.getText(
            self, "Split PDF / Extract Pages",
            f"Enter page numbers or ranges to extract (e.g. 1-3, 5) [1 - {self.document.page_count}]:",
            text=f"1-{self.document.page_count}"
        )
        if ok and rng_str.strip():
            page_indices = []
            try:
                for part in rng_str.split(","):
                    part = part.strip()
                    if "-" in part:
                        start_s, end_s = part.split("-", 1)
                        s = int(start_s.strip()) - 1
                        e = int(end_s.strip()) - 1
                        for i in range(max(0, s), min(self.document.page_count, e + 1)):
                            if i not in page_indices:
                                page_indices.append(i)
                    else:
                        idx = int(part) - 1
                        if 0 <= idx < self.document.page_count and idx not in page_indices:
                            page_indices.append(idx)
            except Exception:
                QMessageBox.warning(self, "Invalid Range", "Invalid page range specified.")
                return

            if not page_indices:
                QMessageBox.warning(self, "No Pages", "No valid pages specified in range.")
                return

            out_path, _ = QFileDialog.getSaveFileName(
                self, "Save Extracted PDF As", "Extracted.pdf", "PDF Document (*.pdf)"
            )
            if out_path:
                if self.document.split_pdf(out_path, page_indices):
                    self.open_file(out_path)
                    self._show_status(f"Extracted {len(page_indices)} pages.")
                else:
                    QMessageBox.critical(self, "Split Error", "Could not extract pages.")

    def _insert_page_from_file_menu(self):
        if self.document:
            self.sidebar._insert_page_from_file(self.document.current_page)

    def _apply_redactions_menu(self):
        if not self.document or not self.document.is_pdf:
            return
        reply = QMessageBox.question(
            self, "Apply Permanent Redactions",
            "Are you sure you want to permanently burn all redactions into this PDF?\nThis will sanitize and permanently remove underlying text and imagery.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.document.apply_permanent_redactions()
            self.canvas.update()
            self._show_status("Permanent redactions applied.")

    def _export_as_pdf(self):
        if not self.document:
            return
        default_dir = os.path.dirname(self.document.file_path) if self.document.file_path else os.path.expanduser("~/Documents")
        base = os.path.splitext(self.document.file_name)[0]
        initial_path = os.path.join(default_dir, f"{base}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Export as PDF", initial_path, "PDF Document (*.pdf)")
        if path:
            try:
                self.document.save_with_annotations(path, self.canvas.annotations)
                self._show_status(f"Exported to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _export_file(self):
        if not self.document:
            return
        dlg = MacExportDialog(
            current_file_path=self.document.file_path,
            page_count=self.document.page_count,
            current_page=self.canvas.current_page,
            document=self.document,
            parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_path:
            try:
                target_page = None if dlg.export_all_pages else self.canvas.current_page
                if dlg.selected_format == "PDF" and dlg.export_all_pages:
                    self.document.export_all_to_pdf(dlg.selected_path, reduce_size=dlg.reduce_file_size)
                else:
                    self.document.export_document(
                        dlg.selected_path,
                        format_name=dlg.selected_format,
                        quality=dlg.selected_quality,
                        page_idx=target_page,
                        reduce_size=dlg.reduce_file_size
                    )
                self._show_status(f"Exported to {os.path.basename(dlg.selected_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _print_file(self):
        if not self.document:
            return
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Document")
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self._render_to_printer(printer)
                self._show_status("Document sent to printer.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _print_preview_file(self):
        if not self.document:
            return
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_dialog.setWindowTitle("Print Preview")
            preview_dialog.resize(900, 700)
            preview_dialog.paintRequested.connect(self._render_to_printer)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Print Preview Error", str(e))

    def _render_to_printer(self, printer):
        if not self.document:
            return
        painter = QPainter(printer)
        try:
            page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            for p_idx in range(self.document.page_count):
                if p_idx > 0:
                    printer.newPage()
                pix = self.document.render_page(p_idx, zoom=2.0)
                scaled = pix.scaled(
                    page_rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                x = page_rect.left() + (page_rect.width() - scaled.width()) / 2
                y = page_rect.top() + (page_rect.height() - scaled.height()) / 2
                painter.drawPixmap(int(x), int(y), scaled)
        finally:
            painter.end()

    def _copy_current_page_text(self):
        if not self.document:
            return
        txt = self.document.extract_text(self.canvas.current_page)
        if txt.strip():
            QApplication.clipboard().setText(txt)
            self._show_status(f"Copied {len(txt)} characters to clipboard.")
        else:
            self._show_status("No selectable text on this page.")

    def _extract_all_text(self):
        if not self.document:
            return
        txt = self.document.extract_text(None)
        if txt.strip():
            QApplication.clipboard().setText(txt)
            self._show_status(f"Copied full document text ({len(txt)} chars) to clipboard.")
        else:
            self._show_status("No selectable text in document.")

