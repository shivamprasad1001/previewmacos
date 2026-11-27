"""Workspace modes, fullscreen/slideshow, sidebar/inspector, and organize actions mixin."""


from PyQt6.QtWidgets import QApplication, QFileDialog, QInputDialog
from PyQt6.QtCore import QTimer, QVariantAnimation, QEasingCurve



class WorkspaceModesMixin:
    """Fullscreen, slideshow, workspace mode switching, sidebar, inspector, and organize actions."""

    def toggle_fullscreen(self, auto_advance: bool = False):
        """Presents the document image in full screen display without window toolbars or sidebars."""
        is_active = self.isFullScreen() or getattr(self, "_is_fullscreen_image", False) or getattr(self, "_is_slideshow", False)

        if is_active:
            self._is_fullscreen_image = False
            self._is_slideshow = False
            if hasattr(self, "_slideshow_timer"):
                self._slideshow_timer.stop()
            if hasattr(self, "slideshow_hud"):
                self.slideshow_hud.hide()

            self.showNormal()
            if getattr(self, "_saved_maximized", False):
                self.showMaximized()

            # Restore original chrome visibility
            self.toolbar_widget.show()
            if getattr(self, "_saved_sidebar_vis", True):
                self.sidebar.show()
            else:
                self.sidebar.hide()

            if getattr(self, "_saved_markup_vis", False):
                self.markup_bar.show()
            else:
                self.markup_bar.hide()

            if getattr(self, "_saved_organize_vis", False):
                self.organize_bar.show()
            else:
                self.organize_bar.hide()

            if hasattr(self, "inspector_panel"):
                if getattr(self, "_saved_inspector_vis", False):
                    self.inspector_panel.show()
                else:
                    self.inspector_panel.hide()

            if getattr(self, "_saved_statusbar_vis", True):
                self.status_bar.show()

            if hasattr(self, "_saved_splitter_sizes") and self._saved_splitter_sizes:
                self.splitter.setSizes(self._saved_splitter_sizes)

            self.canvas.zoom_to_fit()
            if hasattr(self, "fullscreen_btn"):
                self.fullscreen_btn.setToolTip("Full Screen (F11)")
            self._show_status("Exited full screen mode.")
        else:
            self._is_fullscreen_image = True
            self._is_slideshow = auto_advance

            # Save existing layout states
            self._saved_maximized = self.isMaximized()
            self._saved_sidebar_vis = self.sidebar.isVisible()
            self._saved_markup_vis = self.markup_bar.isVisible()
            self._saved_organize_vis = self.organize_bar.isVisible()
            self._saved_inspector_vis = hasattr(self, "inspector_panel") and self.inspector_panel.isVisible()
            self._saved_statusbar_vis = self.status_bar.isVisible()
            self._saved_splitter_sizes = self.splitter.sizes()

            # Hide all chrome so ONLY the document/image fills the screen
            self.toolbar_widget.hide()
            self.sidebar.hide()
            self.markup_bar.hide()
            self.organize_bar.hide()
            if hasattr(self, "inspector_panel"):
                self.inspector_panel.hide()
            self.status_bar.hide()

            total_w = sum(self.splitter.sizes()) if sum(self.splitter.sizes()) > 0 else self.width()
            self.splitter.setSizes([0, total_w, 0])

            self.showFullScreen()
            self.canvas.zoom_to_fit()

            if hasattr(self, "slideshow_hud") and self.slideshow_hud:
                if self.document:
                    self.slideshow_hud.update_page_info(self.canvas.current_page + 1, self.document.page_count)
                self.slideshow_hud.show()
                self.slideshow_hud.raise_()
                self.slideshow_hud._reposition()

            if auto_advance:
                if not hasattr(self, "_slideshow_timer"):
                    self._slideshow_timer = QTimer(self)
                    self._slideshow_timer.setInterval(3500)
                    self._slideshow_timer.timeout.connect(self._slideshow_advance)
                self._slideshow_timer.start()
                self.slideshow_hud.set_playing(True)
                self._show_status("Slideshow started (Press Esc to exit, Space to pause/resume)")
            else:
                if hasattr(self, "_slideshow_timer"):
                    self._slideshow_timer.stop()
                if hasattr(self, "slideshow_hud"):
                    self.slideshow_hud.set_playing(False)
                self._show_status("Full screen image mode (Press Esc or F11 to exit)")

            if hasattr(self, "fullscreen_btn"):
                self.fullscreen_btn.setToolTip("Full Screen (F11)")

        self._update_all_icons()

    def _toggle_slideshow(self):
        is_active = getattr(self, "_is_slideshow", False) or getattr(self, "_is_fullscreen_image", False)
        if is_active:
            self.toggle_fullscreen(auto_advance=False)
        else:
            self.toggle_fullscreen(auto_advance=True)

    def _toggle_slideshow_timer(self):
        if not hasattr(self, "_slideshow_timer"):
            return
        if self._slideshow_timer.isActive():
            self._slideshow_timer.stop()
            self.slideshow_hud.set_playing(False)
            self._show_status("Slideshow paused")
        else:
            self._slideshow_timer.start()
            self.slideshow_hud.set_playing(True)
            self._show_status("Slideshow playing")

    def _slideshow_advance(self):
        if not self.document:
            return
        if self.canvas.current_page < self.document.page_count - 1:
            self.next_page()
        else:
            self.canvas.set_page(0)
            self.sidebar.select_page(0)
            self._update_status()

    def _show_slideshow_controls(self, show: bool):
        if hasattr(self, "slideshow_hud") and self.slideshow_hud:
            if show and self.document:
                self.slideshow_hud.update_page_info(self.canvas.current_page + 1, self.document.page_count)
                self.slideshow_hud.show()
                self.slideshow_hud.raise_()
            else:
                self.slideshow_hud.hide()

    def _on_sidebar_page_selected(self, page_idx: int):
        self.canvas.set_page(page_idx)
        if self.document:
            self.document.set_current_page(page_idx)
        self._update_status()
        self._sync_toolbar_contexts()

    def _on_canvas_zoom_changed(self, zoom: float):
        zoom_str = "Fit" if getattr(self.canvas, '_auto_fit', False) else f"{int(zoom * 100)}%"
        self.zoom_status_label.setText(zoom_str)
        if hasattr(self, "floating_pill") and self.floating_pill:
            if self.document:
                curr = self.canvas.current_page + 1
                tot = self.document.page_count
                if tot > 1:
                    self.floating_pill.show_status(f"Page {curr} of {tot}  •  {zoom_str}")
                else:
                    self.floating_pill.show_status(zoom_str)
            else:
                self.floating_pill.show_status(zoom_str)

    def _on_doc_changed(self):
        self.sidebar.reload_thumbnails()
        self.sidebar.reload_outline()
        self.canvas.update()
        self._update_status()
        self._update_modified_ui()
        self._sync_toolbar_contexts()

    def _on_doc_page_changed(self, page_idx: int):
        self.sidebar.reload_thumbnails()
        self.canvas.update()

    def _toggle_sidebar(self):
        if hasattr(self, "_sidebar_anim") and self._sidebar_anim and self._sidebar_anim.state() == QVariantAnimation.State.Running:
            self._sidebar_anim.stop()

        is_open = self.sidebar.isVisible() and self.splitter.sizes()[0] > 10
        total_w = sum(self.splitter.sizes())

        self._sidebar_anim = QVariantAnimation(self)
        self._sidebar_anim.setDuration(120)
        self._sidebar_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if is_open:
            self._last_sidebar_width = max(160, self.splitter.sizes()[0])
            self._sidebar_anim.setStartValue(self.splitter.sizes()[0])
            self._sidebar_anim.setEndValue(0)
            def on_tick(w):
                self.splitter.setSizes([int(w), total_w - int(w)])
            self._sidebar_anim.valueChanged.connect(on_tick)
            def on_done():
                self.sidebar.setVisible(False)
                self.canvas.zoom_to_fit()
            self._sidebar_anim.finished.connect(on_done)
        else:
            self.sidebar.setVisible(True)
            target_w = getattr(self, "_last_sidebar_width", 240)
            self._sidebar_anim.setStartValue(0)
            self._sidebar_anim.setEndValue(target_w)
            def on_tick(w):
                self.splitter.setSizes([int(w), total_w - int(w)])
            self._sidebar_anim.valueChanged.connect(on_tick)
            self._sidebar_anim.finished.connect(self.canvas.zoom_to_fit)

        self._sidebar_anim.start()

    def set_sidebar_visible(self, visible: bool):
        """Sets sidebar visibility with smooth transition."""
        if not hasattr(self, "sidebar") or not hasattr(self, "splitter"):
            return
        is_open = self.sidebar.isVisible() and self.splitter.sizes()[0] > 10
        if is_open != visible:
            self._toggle_sidebar()

    def set_workspace_mode(self, mode: str):
        """Switches workspace between View, Edit, and Organize modes."""
        self.current_workspace_mode = mode

        # Update mode segmented buttons
        if hasattr(self, "mode_view_btn"):
            self.mode_view_btn.setChecked(mode == "View")
        if hasattr(self, "mode_edit_btn"):
            self.mode_edit_btn.setChecked(mode == "Edit")
        if hasattr(self, "mode_organize_btn"):
            self.mode_organize_btn.setChecked(mode == "Organize")

        if mode == "View":
            self.markup_bar.setVisible(False)
            self.organize_bar.setVisible(False)
            self.markup_toggle_btn.setChecked(False)
            self.canvas.set_markup_enabled(False)
            self.markup_bar.unselect_all()
            self.canvas.unselect_tools()
            self.set_inspector_visible(False)
            self._show_status("View Mode: Distraction-free reading")

        elif mode == "Edit":
            self.organize_bar.setVisible(False)
            self.markup_bar.setVisible(True)
            self.markup_toggle_btn.setChecked(True)
            self.canvas.set_markup_enabled(True)
            self.set_inspector_visible(True)
            if hasattr(self, "markup_bar") and hasattr(self.markup_bar, "handle_resize"):
                self.markup_bar.handle_resize(self.width())
            if self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)
            self._show_status("Edit Mode: Annotation and markup tools active")

        elif mode == "Organize":
            self.markup_bar.setVisible(False)
            self.markup_toggle_btn.setChecked(False)
            self.canvas.set_markup_enabled(False)
            self.markup_bar.unselect_all()
            self.canvas.unselect_tools()
            self.organize_bar.setVisible(True)
            self.set_inspector_visible(False)
            # Switch sidebar to Contact Sheet to present multi-page grid
            if hasattr(self.sidebar, "set_view_mode"):
                self.sidebar.set_view_mode("Contact Sheet")
            # Widen sidebar splitter for better multi-page grid display
            sizes = self.splitter.sizes()
            total_w = sum(sizes) if sum(sizes) > 0 else self.width()
            target_sb_w = min(420, max(320, int(total_w * 0.38)))
            self.splitter.setSizes([target_sb_w, max(300, total_w - target_sb_w), 0])
            self._show_status("Organize Mode: Page reordering, insertion, and document actions")

        self._sync_toolbar_contexts()
        self._update_all_icons()

    def _toggle_markup_bar(self):
        is_vis = not self.markup_bar.isVisible()
        self.set_markup_visible(is_vis)

    def set_markup_visible(self, visible: bool):
        """Shows or hides the markup toolbar by toggling the workspace mode."""
        if visible:
            self.set_workspace_mode("Edit")
        else:
            self.set_workspace_mode("View")

    def _toggle_inspector_panel(self):
        self.set_inspector_visible(not self.inspector_panel.isVisible(), animated=True)

    def set_inspector_visible(self, visible: bool, animated: bool = False):
        if not hasattr(self, "inspector_panel"):
            return
        if hasattr(self, "inspector_btn"):
            self.inspector_btn.setChecked(visible)

        if hasattr(self, "_inspector_anim") and self._inspector_anim and self._inspector_anim.state() == QVariantAnimation.State.Running:
            self._inspector_anim.stop()

        sizes = self.splitter.sizes()
        total_w = sum(sizes) if sum(sizes) > 0 else self.width()
        sb_w = sizes[0] if len(sizes) > 0 else 240
        current_insp_w = sizes[2] if len(sizes) > 2 else 0
        target_w = 280 if visible else 0

        if not animated or not self.isVisible():
            self.inspector_panel.setVisible(visible)
            if visible and self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)
            canvas_w = max(200, total_w - sb_w - target_w)
            self.splitter.setSizes([sb_w, canvas_w, target_w])
            self._update_all_icons()
            return

        if visible:
            self.inspector_panel.setVisible(True)
            if self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)

        self._inspector_anim = QVariantAnimation(self)
        self._inspector_anim.setDuration(160)
        self._inspector_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._inspector_anim.setStartValue(current_insp_w)
        self._inspector_anim.setEndValue(target_w)

        def on_tick(w):
            w_int = int(w)
            cw = max(200, total_w - sb_w - w_int)
            self.splitter.setSizes([sb_w, cw, w_int])

        def on_done():
            if not visible:
                self.inspector_panel.setVisible(False)
            self.canvas.zoom_to_fit()
            self._update_all_icons()

        self._inspector_anim.valueChanged.connect(on_tick)
        self._inspector_anim.finished.connect(on_done)
        self._inspector_anim.start()

    def _stub_flip_horizontal(self) -> None:
        if not self.document:
            return
        if self.document.is_pdf:
            self._show_status("Flip is only available for image documents.")
            return
        page = self.canvas.current_page
        self.document.flip_page_horizontal(page)
        self.canvas.zoom_to_fit()
        self._sync_toolbar_contexts()

    def _stub_flip_vertical(self) -> None:
        if not self.document:
            return
        if self.document.is_pdf:
            self._show_status("Flip is only available for image documents.")
            return
        page = self.canvas.current_page
        self.document.flip_page_vertical(page)
        self.canvas.zoom_to_fit()
        self._sync_toolbar_contexts()

    def _stub_crop(self) -> None:
        # Delegate to the canvas's existing crop pipeline (handles PIL crop + history)
        if hasattr(self.canvas, "apply_crop"):
            self.canvas.apply_crop()
            self._sync_toolbar_contexts()

    def _stub_resize(self) -> None:
        if not self.document or self.document.is_pdf:
            self._show_status("Resize is only available for image documents.")
            return
        w, h = self.document.get_page_size(self.canvas.current_page)
        new_w, ok = QInputDialog.getInt(self, "Resize Page", "New width (px):",
                                         int(w), 32, 10000, 1)
        if not ok:
            return
        new_h, ok = QInputDialog.getInt(self, "Resize Page", "New height (px):",
                                         int(h), 32, 10000, 1)
        if not ok:
            return
        if self.document.resize_page(self.canvas.current_page, new_w, new_h):
            self.canvas.zoom_to_fit()
            self._show_status(f"Resized to {new_w} × {new_h}")
            self._sync_toolbar_contexts()

    def _stub_move_up(self) -> None:
        if not self.document:
            return
        cur = self.canvas.current_page
        if cur <= 0:
            return
        if self.document.move_page(cur, cur - 1):
            self.canvas.set_page(cur - 1)
            self.document.set_current_page(cur - 1)
            self.sidebar.reload_thumbnails()
            self.sidebar.select_page(cur - 1)
            self._update_status()
            self._sync_toolbar_contexts()

    def _stub_move_down(self) -> None:
        if not self.document:
            return
        cur = self.canvas.current_page
        if cur >= self.document.page_count - 1:
            return
        if self.document.move_page(cur, cur + 1):
            self.canvas.set_page(cur + 1)
            self.document.set_current_page(cur + 1)
            self.sidebar.reload_thumbnails()
            self.sidebar.select_page(cur + 1)
            self._update_status()
            self._sync_toolbar_contexts()

    def _stub_reduce_size(self) -> None:
        if not self.document:
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Reduce File Size — Save As", "Reduced.pdf",
            "PDF Document (*.pdf)"
        )
        if not out_path:
            return
        if self.document.reduce_file_size(out_path):
            import os
            before = os.path.getsize(self.document.file_path) if (self.document.file_path and os.path.exists(self.document.file_path)) else 0
            after = os.path.getsize(out_path) if os.path.exists(out_path) else 0
            pct = int((1 - after / before) * 100) if before > 0 else 0
            self._show_status(f"Reduced from {before // 1024} KB to {after // 1024} KB ({pct}% smaller)")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Reduce Failed", "Could not reduce file size.")

    def _stub_insert_clipboard(self) -> None:
        from PIL.ImageQt import fromqimage
        clipboard = QApplication.clipboard()
        qimg = clipboard.image()
        if qimg.isNull():
            self._show_status("Clipboard does not contain an image.")
            return
        try:
            pil_img = fromqimage(qimg)
            if self.document is None:
                self._show_status("No document open — open a document first.")
                return
            if self.document.insert_from_clipboard_image(pil_img, self.canvas.current_page):
                self.sidebar.reload_thumbnails()
                self.canvas.set_page(self.canvas.current_page + 1)
                self.document.set_current_page(self.canvas.current_page)
                self.sidebar.select_page(self.canvas.current_page)
                self._show_status("Pasted image as new page.")
                self._sync_toolbar_contexts()
            else:
                self._show_status("Failed to paste image from clipboard.")
        except Exception as e:
            self._show_status(f"Clipboard paste error: {e}")

    def _undo(self) -> None:
        if hasattr(self, "canvas") and self.canvas:
            self.canvas.undo()

    def _redo(self) -> None:
        if hasattr(self, "canvas") and self.canvas:
            self.canvas.redo()

    def _apply_redactions_permanently(self) -> None:
        self._apply_redactions_menu()

    def _sync_toolbar_contexts(self) -> None:
        doc = self.document
        if hasattr(self, "organize_bar") and self.organize_bar:
            if doc is None:
                if hasattr(self.organize_bar, "set_context"):
                    self.organize_bar.set_context(has_document=False)
            else:
                if hasattr(self.organize_bar, "set_context"):
                    self.organize_bar._is_pdf = bool(getattr(doc, "is_pdf", False))
                    self.organize_bar.set_context(
                        has_document=True,
                        page_count=doc.page_count,
                        current_page=getattr(self.canvas, "current_page", doc.current_page),
                    )
        if hasattr(self, "markup_bar") and self.markup_bar:
            has_sel = bool(getattr(self.canvas, "_crop_box", None) or getattr(self.canvas, "_selected_annotation", None))
            if hasattr(self.markup_bar, "set_context"):
                self.markup_bar.set_context(
                    has_selection=has_sel,
                    pending_redactions=getattr(self, "_pending_redaction_count", 0),
                    has_document=doc is not None,
                )

    def _connect_organize_bar(self):
        self.organize_bar.rotate_left_requested.connect(self._rotate_left)
        self.organize_bar.rotate_right_requested.connect(self._rotate_right)
        self.organize_bar.duplicate_page_requested.connect(lambda: self.sidebar._duplicate_page(self.canvas.current_page))
        self.organize_bar.insert_blank_requested.connect(lambda: self.sidebar._insert_blank_page(self.canvas.current_page))
        self.organize_bar.insert_file_requested.connect(lambda: self.sidebar._insert_page_from_file(self.canvas.current_page))
        self.organize_bar.delete_page_requested.connect(lambda: self.sidebar._confirm_and_delete_page(self.canvas.current_page))
        self.organize_bar.merge_requested.connect(self._merge_pdfs)
        self.organize_bar.split_requested.connect(self._split_pdf)
        self.organize_bar.export_requested.connect(self._export_file)

        # Extended organize bar actions
        if hasattr(self.organize_bar, "flip_horizontal_requested"):
            self.organize_bar.flip_horizontal_requested.connect(self._stub_flip_horizontal)
        if hasattr(self.organize_bar, "flip_vertical_requested"):
            self.organize_bar.flip_vertical_requested.connect(self._stub_flip_vertical)
        if hasattr(self.organize_bar, "crop_requested"):
            self.organize_bar.crop_requested.connect(self._stub_crop)
        if hasattr(self.organize_bar, "resize_requested"):
            self.organize_bar.resize_requested.connect(self._stub_resize)
        if hasattr(self.organize_bar, "move_up_requested"):
            self.organize_bar.move_up_requested.connect(self._stub_move_up)
        if hasattr(self.organize_bar, "move_down_requested"):
            self.organize_bar.move_down_requested.connect(self._stub_move_down)
        if hasattr(self.organize_bar, "reduce_size_requested"):
            self.organize_bar.reduce_size_requested.connect(self._stub_reduce_size)
        if hasattr(self.organize_bar, "insert_clipboard_requested"):
            self.organize_bar.insert_clipboard_requested.connect(self._stub_insert_clipboard)

    def _connect_inspector_panel(self):
        self.inspector_panel.close_requested.connect(lambda: self.set_inspector_visible(False))
        self.inspector_panel.annotation_updated.connect(self._on_inspector_annotation_updated)
        self.inspector_panel.delete_annotation_requested.connect(self._on_inspector_delete_annotation)
        self.inspector_panel.apply_redaction_requested.connect(self._apply_redactions_menu)
        self.inspector_panel.color_adjusted.connect(self._on_inspector_color_adjusted)
        self.inspector_panel.color_reset_requested.connect(self._on_inspector_color_reset)

    def _on_annotation_selected(self, annot):
        self.markup_bar.set_selected_annotation(annot)
        if hasattr(self, "inspector_panel"):
            self.inspector_panel.set_selected_annotation(annot)
            if annot is not None and not self.inspector_panel.isVisible():
                self.set_inspector_visible(True)
        self._sync_toolbar_contexts()

    def _on_document_or_annotations_modified(self):
        self._update_modified_ui()
        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            self.inspector_panel.refresh_annotations_list()

    def _on_inspector_annotation_updated(self, annot=None):
        self.canvas.update()
        self.canvas.document_modified.emit(True)
        self._update_modified_ui()

    def _on_inspector_delete_annotation(self, annot):
        if not self.document:
            return
        annots = self.canvas.annotations.get(self.canvas.current_page, [])
        if annot in annots:
            annots.remove(annot)
        if getattr(self.canvas, "_selected_annotation", None) == annot:
            self.canvas._selected_annotation = None
        self.canvas.update()
        self.markup_bar.set_selected_annotation(None)
        self.inspector_panel.set_selected_annotation(None)
        self.inspector_panel.refresh_annotations_list()
        self.canvas.document_modified.emit(True)
        self._update_modified_ui()

    def _on_inspector_color_adjusted(self, new_img):
        if self.document and not self.document.is_pdf:
            self.document.update_image(new_img, self.canvas.current_page)
            self.canvas.update()
            self.canvas.document_modified.emit(True)
            self._update_modified_ui()

    def _on_inspector_color_reset(self):
        if hasattr(self.inspector_panel, "_original_image") and self.inspector_panel._original_image:
            self._on_inspector_color_adjusted(self.inspector_panel._original_image.copy())

