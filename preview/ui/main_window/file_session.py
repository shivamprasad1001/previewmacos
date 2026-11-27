"""File open/save, tab session state, and page navigation mixin for MacMainWindow."""

import os
from typing import List, Optional

from PyQt6.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QMessageBox
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QPointF, QTimer

from preview.core.document import Document
from preview.core.history import HistoryManager
from preview.theme import MacTheme
from preview.ui.save_dialog import MacSaveConfirmationDialog
from preview.ui.tab_bar import DocumentTabState


class FileSessionMixin:
    """Tab lifecycle, document loading/saving, and page navigation."""

    def _first_page(self):
        if self.document and self.document.page_count > 0:
            self.canvas.set_page(0)
            self.document.set_current_page(0)
            self.sidebar.select_page(0)
            self._update_status()

    def _last_page(self):
        if self.document and self.document.page_count > 0:
            last = self.document.page_count - 1
            self.canvas.set_page(last)
            self.document.set_current_page(last)
            self.sidebar.select_page(last)
            self._update_status()

    def is_document_modified(self) -> bool:
        """Returns True if the document has any unsaved annotations, edits, crops, or transformations."""
        if getattr(self, "_force_modified", False):
            return True
        if hasattr(self, "canvas") and self.canvas and self.canvas.is_modified:
            return True
        if hasattr(self, "document") and self.document and getattr(self.document, "is_dirty", False):
            return True
        return False

    def set_modified(self, modified: bool):
        """Sets the document modified state and synchronizes canvas history and UI indicators."""
        self._force_modified = modified
        if not modified:
            if hasattr(self, "document") and self.document:
                self.document.is_dirty = False
            if hasattr(self, "canvas") and self.canvas:
                self.canvas.history.mark_saved()
        if hasattr(self, "tabs") and 0 <= self.active_tab_index < len(self.tabs):
            self.tabs[self.active_tab_index].is_modified = modified
            self._sync_tab_bar_text(self.active_tab_index)
        self._update_modified_ui()

    def _update_modified_ui(self):
        """Updates window title ('- Edited'), traffic light dirty dot, and menu actions based on modification status."""
        is_mod = self.is_document_modified()
        if hasattr(self, "document") and self.document:
            base_name = self.document.file_name or "Untitled"
            title = f"{base_name} - Edited" if is_mod else base_name
            if hasattr(self, "_set_toolbar_title"):
                self._set_toolbar_title(title)
            elif hasattr(self, "title_label") and self.title_label:
                self.title_label.setText(title)
            self.setWindowTitle(title)
            if hasattr(self, "toolbar_widget") and self.toolbar_widget:
                self.toolbar_widget.update_title_geometry()
        if hasattr(self, "traffic_cluster") and self.traffic_cluster:
            self.traffic_cluster.btn_close.set_modified(is_mod)
        if hasattr(self, "revert_act") and self.revert_act:
            self.revert_act.setEnabled(is_mod and bool(self.document and self.document.file_path))
        if hasattr(self, "tabs") and 0 <= self.active_tab_index < len(self.tabs):
            self.tabs[self.active_tab_index].is_modified = is_mod
            self._sync_tab_bar_text(self.active_tab_index)

    def _init_tabs(self):
        initial_tab = DocumentTabState(
            title="Untitled",
            history=self.canvas.history if self.canvas else HistoryManager(on_changed=lambda m: self.canvas.document_modified.emit(m) if self.canvas else None)
        )
        self.tabs.append(initial_tab)
        self.tab_container.tab_bar.addTab(initial_tab.title)
        self.active_tab_index = 0
        self.tab_container.tab_bar.setCurrentIndex(0)
        self._update_tab_bar_visibility()

    def _update_tab_bar_visibility(self):
        visible = (len(self.tabs) > 1) or self.show_tab_bar_always
        self.tab_container.setVisible(visible)
        if hasattr(self, "toggle_tab_bar_act"):
            self.toggle_tab_bar_act.setChecked(self.show_tab_bar_always)
            self.toggle_tab_bar_act.setText("Hide Tab Bar" if self.show_tab_bar_always else "Show Tab Bar")

    def _toggle_tab_bar_visible(self):
        self.show_tab_bar_always = not self.show_tab_bar_always
        self._update_tab_bar_visibility()

    def _sync_tab_bar_text(self, idx: int):
        if hasattr(self, "tabs") and 0 <= idx < len(self.tabs) and hasattr(self, "tab_container") and idx < self.tab_container.tab_bar.count():
            tab = self.tabs[idx]
            display_text = f"{tab.title} ●" if tab.is_modified else tab.title
            self.tab_container.tab_bar.setTabText(idx, display_text)
            if tab.file_path:
                self.tab_container.tab_bar.setTabToolTip(idx, tab.file_path)

    def _save_current_tab_state(self):
        if hasattr(self, "tabs") and 0 <= self.active_tab_index < len(self.tabs):
            tab = self.tabs[self.active_tab_index]
            tab.document = self.document
            tab.file_path = self.document.file_path if self.document else None
            tab.title = self.document.file_name if self.document else "Untitled"
            tab.current_page = self.canvas.current_page if self.canvas else 0
            tab.zoom = self.canvas.zoom if self.canvas else 1.0
            tab.view_mode = self.canvas.view_mode if self.canvas else "Single"
            tab.pan_offset = QPointF(self.canvas._pan_offset) if self.canvas else QPointF(0, 0)
            tab.annotations = dict(self.canvas.annotations) if self.canvas else {}
            tab.history = self.canvas.history if self.canvas else HistoryManager()
            tab.is_modified = self.is_document_modified()
            self._sync_tab_bar_text(self.active_tab_index)

    def _load_tab_state(self, index: int):
        if not hasattr(self, "tabs") or not (0 <= index < len(self.tabs)):
            return
        tab = self.tabs[index]
        self.document = tab.document
        if self.canvas:
            self.canvas.document = tab.document
            self.canvas.annotations = tab.annotations
            self.canvas.history = tab.history
            if self.canvas.history:
                self.canvas.history.on_changed = lambda m: self.canvas.document_modified.emit(m)
            self.canvas.view_mode = tab.view_mode
            self.canvas.zoom = tab.zoom
            self.canvas._pan_offset = QPointF(tab.pan_offset)
            self.canvas.current_page = tab.current_page
            self.canvas.crop_box = None
            self.canvas._active_annotation = None
            self.canvas._selected_annotation = None

        if tab.document:
            self.sidebar.set_document(tab.document)
            self.sidebar.select_page(tab.current_page)
        else:
            self.sidebar.clear()
            if hasattr(self, "_set_toolbar_title"):
                self._set_toolbar_title("No document")
            elif hasattr(self, "title_label") and self.title_label:
                self.title_label.setText("No document")
            if hasattr(self, "page_badge") and self.page_badge:
                self.page_badge.setText("")

        self.set_modified(tab.is_modified)
        self._update_modified_ui()
        self._update_status()
        self._sync_toolbar_contexts()
        if self.canvas:
            self.canvas.update()

    def switch_to_tab(self, index: int):
        if not hasattr(self, "tabs") or not (0 <= index < len(self.tabs)):
            return
        if index == self.active_tab_index:
            return
        self._save_current_tab_state()
        self.active_tab_index = index
        self.tab_container.tab_bar.blockSignals(True)
        self.tab_container.tab_bar.setCurrentIndex(index)
        self.tab_container.tab_bar.blockSignals(False)
        self._load_tab_state(index)

    def _on_tab_bar_current_changed(self, index: int):
        if hasattr(self, "tabs") and 0 <= index < len(self.tabs) and index != self.active_tab_index:
            self.switch_to_tab(index)

    def _on_tab_moved(self, from_idx: int, to_idx: int):
        if hasattr(self, "tabs") and 0 <= from_idx < len(self.tabs) and 0 <= to_idx < len(self.tabs):
            tab = self.tabs.pop(from_idx)
            self.tabs.insert(to_idx, tab)
            self.active_tab_index = self.tab_container.tab_bar.currentIndex()

    def new_tab(self, file_path: Optional[str] = None) -> DocumentTabState:
        self._save_current_tab_state()
        hist = HistoryManager(on_changed=lambda m: self.canvas.document_modified.emit(m) if self.canvas else None)
        new_tab_state = DocumentTabState(title="Untitled", history=hist)
        self.tabs.append(new_tab_state)
        new_idx = len(self.tabs) - 1
        self.tab_container.tab_bar.blockSignals(True)
        self.tab_container.tab_bar.addTab(new_tab_state.title)
        self.tab_container.tab_bar.blockSignals(False)
        self.switch_to_tab(new_idx)
        if file_path:
            self.open_file(file_path)
        self._update_tab_bar_visibility()
        return new_tab_state

    def new_tab_files(self, file_paths: List[str]) -> DocumentTabState:
        self._save_current_tab_state()
        hist = HistoryManager(on_changed=lambda m: self.canvas.document_modified.emit(m) if self.canvas else None)
        new_tab_state = DocumentTabState(title="Untitled", history=hist)
        self.tabs.append(new_tab_state)
        new_idx = len(self.tabs) - 1
        self.tab_container.tab_bar.blockSignals(True)
        self.tab_container.tab_bar.addTab(new_tab_state.title)
        self.tab_container.tab_bar.blockSignals(False)
        self.switch_to_tab(new_idx)
        self.open_files(file_paths)
        self._update_tab_bar_visibility()
        return new_tab_state

    def close_tab(self, index: Optional[int] = None) -> bool:
        if index is None:
            index = self.active_tab_index
        if not hasattr(self, "tabs") or not (0 <= index < len(self.tabs)):
            return False

        tab_to_close = self.tabs[index]
        if tab_to_close.is_modified or (index == self.active_tab_index and self.is_document_modified()):
            if index != self.active_tab_index:
                self.switch_to_tab(index)
            if not self.maybe_save_changes():
                return False

        self.tabs.pop(index)
        self.tab_container.tab_bar.blockSignals(True)
        self.tab_container.tab_bar.removeTab(index)
        self.tab_container.tab_bar.blockSignals(False)

        if not self.tabs:
            self.new_tab()
        else:
            new_active = min(index, len(self.tabs) - 1)
            self.active_tab_index = -1
            self.switch_to_tab(new_active)

        self._update_tab_bar_visibility()
        return True

    def cycle_tab(self, forward: bool = True):
        if len(self.tabs) > 1:
            step = 1 if forward else -1
            next_idx = (self.active_tab_index + step) % len(self.tabs)
            self.switch_to_tab(next_idx)

    def select_next_tab(self):
        self.cycle_tab(forward=True)

    def select_previous_tab(self):
        self.cycle_tab(forward=False)

    def _on_new_tab_triggered(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Document in New Tab", "",
            "Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tiff);;PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*.*)"
        )
        if paths:
            if len(paths) == 1:
                self.new_tab(paths[0])
            else:
                self.new_tab_files(paths)
        else:
            self.new_tab()

    def maybe_save_changes(self) -> bool:
        """
        Prompts user if document has unsaved modifications.
        Offers Don't Save, Cancel, and Save (as new copy).
        Returns True if safe to close or navigate away, False if cancelled.
        """
        if not self.is_document_modified():
            return True
        if not self.document:
            return True

        # In CI, testing, or headless environments, do not block execution with modal dialogs
        if os.environ.get("CI") or os.environ.get("PREVIEW_TESTING") or getattr(self, "_skip_save_prompt", False):
            return True

        has_path = bool(self.document.file_path and os.path.exists(self.document.file_path))
        doc_name = self.document.file_name or "Untitled"
        theme = getattr(self, "current_theme", MacTheme.DARK)

        dialog = MacSaveConfirmationDialog(doc_name, has_file_path=has_path, theme=theme, parent=self)
        dialog.exec()

        if dialog.result_code == MacSaveConfirmationDialog.CANCEL:
            return False
        elif dialog.result_code == MacSaveConfirmationDialog.DONT_SAVE:
            self.set_modified(False)
            return True
        elif dialog.result_code in (MacSaveConfirmationDialog.SAVE, MacSaveConfirmationDialog.SAVE_AS_NEW_COPY):
            return self._save_as_new_copy_direct()

        return False

    def closeEvent(self, event: QCloseEvent):
        """Intercepts window close to prompt for unsaved edits across all tabs."""
        if getattr(self, "_update_worker", None) and self._update_worker.isRunning():
            self._update_worker.quit()
            self._update_worker.wait(500)
        for i in range(len(getattr(self, "tabs", []))):
            tab = self.tabs[i]
            if tab.is_modified or (i == self.active_tab_index and self.is_document_modified()):
                if i != self.active_tab_index:
                    self.switch_to_tab(i)
                if not self.maybe_save_changes():
                    event.ignore()
                    return
        event.accept()

    def open_file(self, file_path: str):
        if not self.maybe_save_changes():
            return
        try:
            self.document = Document(file_path)
            self._bind_document()
            self._add_recent_file(file_path)
        except Exception as e:
            from preview.core.document import PasswordRequiredError
            if isinstance(e, PasswordRequiredError) or "password" in str(e).lower():
                pwd, ok = QInputDialog.getText(
                    self, "Password Required",
                    f"'{os.path.basename(file_path)}' is password protected.\nEnter Password:",
                    QLineEdit.EchoMode.Password
                )
                if ok and pwd:
                    try:
                        doc = Document()
                        doc.load_file(file_path, password=pwd)
                        self.document = doc
                        self._bind_document()
                        self._add_recent_file(file_path)
                        return
                    except Exception as err:
                        QMessageBox.critical(self, "Password Error", str(err))
                        return
            QMessageBox.critical(self, "Error Opening File", f"Could not open {file_path}:\n{str(e)}")

    def open_files(self, file_paths: List[str]):
        if not self.maybe_save_changes():
            return
        try:
            self.document = Document()
            self.document.load_files(file_paths)
            self._bind_document()
            if file_paths:
                self._add_recent_file(file_paths[0])
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Images", f"Could not open images:\n{str(e)}")

    def open_folder(self, folder_path: str):
        if not self.maybe_save_changes():
            return
        try:
            self.document = Document()
            self.document.load_folder(folder_path)
            self._bind_document()
            self._add_recent_file(folder_path)
            self._show_status(f"Loaded folder with {self.document.page_count} images.")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Folder", f"Could not open folder {folder_path}:\n{str(e)}")

    def _bind_document(self):
        if not self.document:
            return
        self.document.document_changed.connect(self._on_doc_changed)
        self.document.page_changed.connect(self._on_doc_page_changed)

        self.sidebar.set_document(self.document)
        self.canvas.set_document(self.document)

        self.set_modified(False)
        self._update_modified_ui()
        self._update_status()

        if hasattr(self, "tabs") and 0 <= self.active_tab_index < len(self.tabs):
            tab = self.tabs[self.active_tab_index]
            tab.document = self.document
            tab.file_path = self.document.file_path
            tab.title = self.document.file_name or "Untitled"
            tab.current_page = 0
            tab.zoom = self.canvas.zoom
            tab.view_mode = self.canvas.view_mode
            tab.pan_offset = QPointF(0, 0)
            tab.annotations = self.canvas.annotations
            tab.history = self.canvas.history
            tab.is_modified = False
            self._sync_tab_bar_text(self.active_tab_index)

        # Re-fit image/page to canvas after layout is settled
        QTimer.singleShot(60, self.canvas.zoom_to_fit)

    def next_page(self):
        if self.document and self.canvas.current_page < self.document.page_count - 1:
            nxt = self.canvas.current_page + 1
            self.canvas.set_page(nxt)
            self.document.set_current_page(nxt)
            self.sidebar.select_page(nxt)
            self._update_status()

    def prev_page(self):
        if self.document and self.canvas.current_page > 0:
            prv = self.canvas.current_page - 1
            self.canvas.set_page(prv)
            self.document.set_current_page(prv)
            self.sidebar.select_page(prv)
            self._update_status()

    def _open_file_dialog(self, force_new_tab: bool = False):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Document or Images", "",
            "Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tiff);;PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*.*)"
        )
        if not paths:
            return

        # If a document is already open or force_new_tab is requested, automatically open in a new tab
        if force_new_tab or self.document is not None:
            if len(paths) == 1:
                self.new_tab(paths[0])
            else:
                self.new_tab_files(paths)
            return

        if len(paths) == 1:
            self.open_file(paths[0])
        else:
            self.open_files(paths)

    def _open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder of Images")
        if folder:
            if self.document is not None:
                self.new_tab()
            self.open_folder(folder)

    def _save_file(self):
        return self._save_file_direct()

    def _save_file_direct(self) -> bool:
        """Saves document in-place, replacing the original file."""
        if not self.document:
            return True
        if self.document.file_path:
            try:
                self.document.save_with_annotations(self.document.file_path, self.canvas.annotations)
                self.set_modified(False)
                self._show_status("Document saved successfully.")
                return True
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save document:\n{str(e)}")
                return False
        else:
            return self._save_as_file()

    def _save_as_file(self):
        return self._save_as_new_copy_direct()

    def _save_as_new_copy_direct(self) -> bool:
        """Prompts for a new file location and saves the document as a new copy, leaving the original untouched."""
        if not self.document:
            return True

        orig_path = self.document.file_path
        if orig_path:
            dir_name = os.path.dirname(orig_path)
            base, ext = os.path.splitext(os.path.basename(orig_path))
            suggested_name = os.path.join(dir_name, f"{base} (Edited){ext}")
        else:
            ext = ".pdf" if getattr(self.document, "is_pdf", False) else ".png"
            suggested_name = f"Untitled (Edited){ext}"

        path, _ = QFileDialog.getSaveFileName(
            self, "Save As New Copy", suggested_name,
            "PDF Document (*.pdf);;PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        if not path:
            return False

        try:
            self.document.save_with_annotations(path, self.canvas.annotations)
            self.document.file_path = os.path.abspath(path)
            self.document.file_name = os.path.basename(path)
            self._add_recent_file(path)
            self.set_modified(False)
            self._show_status(f"Saved new copy to {os.path.basename(path)}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save As Error", f"Could not save copy:\n{str(e)}")
            return False

    def _revert_to_original(self):
        """Prompts and reloads original document from disk, discarding all unsaved edits."""
        if not self.document or not self.document.file_path:
            return
        if not self.is_document_modified():
            self._show_status("Document has not been modified.")
            return

        res = QMessageBox.question(
            self,
            "Revert Document",
            f"Are you sure you want to revert “{self.document.file_name}” to its original version?\n\nAll unsaved annotations, crops, and edits will be discarded.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            orig_path = self.document.file_path
            self.set_modified(False)
            self.open_file(orig_path)
            self._show_status("Reverted to original document.")

    def _go_to_page_dialog(self):
        if not self.document or self.document.page_count <= 0:
            return
        page_num, ok = QInputDialog.getInt(
            self, "Go to Page",
            f"Enter page number (1 - {self.document.page_count}):",
            value=self.document.current_page + 1,
            min=1, max=self.document.page_count
        )
        if ok:
            idx = page_num - 1
            self.canvas.set_page(idx)
            self.document.set_current_page(idx)
            self.sidebar.select_page(idx)
            self._update_status()

