"""Window chrome events, theme switching, dialogs, and update checker mixin."""

import os
from typing import Optional

from PyQt6.QtWidgets import QApplication, QFileDialog, QGraphicsOpacityEffect, QLabel, QMessageBox
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QKeyEvent, QMouseEvent, QPixmap
from PyQt6.QtCore import Qt, QEasingCurve, QEvent, QPoint, QPropertyAnimation, QSettings

from preview.theme import MacTheme, ThemeManager
from preview.core.annotations import AnnotationType
from preview.core.history import ActionCommand
from preview.core.updater import UpdateCheckWorker, UpdateInfo
from preview.ui.adjust_color_dialog import AdjustColorDialog
from preview.ui.adjust_size_dialog import AdjustSizeDialog
from preview.ui.signature_dialog import SignatureDialog
from preview.ui.inspector_dialog import InspectorDialog
from preview.ui.about_dialog import AboutDialog
from preview.ui.batch_dialog import BatchConvertDialog
from preview.ui.update_dialog import UpdateDialog, UpdateBanner


class WindowEventsAndToolsMixin:
    """Window drag/resize events, theme management, tool dialogs, and updater integration."""

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._update_window_chrome_state()

    def _update_window_chrome_state(self):
        is_max = self.isMaximized()
        if hasattr(self, 'root_layout'):
            m = 0 if is_max else 10
            self.root_layout.setContentsMargins(m, m, m, m)
        if hasattr(self, 'shadow_effect'):
            self.shadow_effect.setEnabled(not is_max)
        if hasattr(self, 'toolbar_widget'):
            self.toolbar_widget.update_title_geometry()
        if hasattr(self, 'window_controls'):
            col = self._get_icon_color()
            self.window_controls.update_icons(col)

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.ActivationChange:
            if hasattr(self, 'traffic_cluster'):
                self.traffic_cluster.set_active_state(self.isActiveWindow())
        elif event.type() == QEvent.Type.WindowStateChange:
            self._update_window_chrome_state()
        super().changeEvent(event)

    def _get_resize_edge(self, pos: QPoint) -> Optional[Qt.Edge]:
        if not getattr(self, "is_frameless", False) or self.isMaximized():
            return None
        margin = 6
        w = self.width()
        h = self.height()
        x = pos.x()
        y = pos.y()

        left = (x <= margin)
        right = (x >= w - margin)
        top = (y <= 3)
        bottom = (y >= h - margin)

        if top and left:
            return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        if top and right:
            return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        if bottom and left:
            return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        if bottom and right:
            return Qt.Edge.BottomEdge | Qt.Edge.RightEdge
        if left:
            return Qt.Edge.LeftEdge
        if right:
            return Qt.Edge.RightEdge
        if top:
            return Qt.Edge.TopEdge
        if bottom:
            return Qt.Edge.BottomEdge
        return None

    def mouseMoveEvent(self, event: QMouseEvent):
        if getattr(self, "is_frameless", False) and not self.isMaximized():
            edge = self._get_resize_edge(event.position().toPoint())
            if edge:
                if (edge & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge)) and (edge & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge)):
                    if (edge & Qt.Edge.TopEdge and edge & Qt.Edge.LeftEdge) or (edge & Qt.Edge.BottomEdge and edge & Qt.Edge.RightEdge):
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    else:
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                elif edge & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                super().mouseMoveEvent(event)
                return
        self.unsetCursor()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent):
        self.unsetCursor()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def start_window_drag(self, event: Optional[QMouseEvent] = None) -> bool:
        """Initiate native OS window manager move (Wayland / X11 / macOS / Windows)."""
        self.unsetCursor()

        if self.isMaximized():
            self._toggle_maximize()
            QApplication.processEvents()

        win_handle = self.windowHandle()
        if not win_handle:
            self.winId()
            win_handle = self.windowHandle()

        if win_handle and hasattr(win_handle, "startSystemMove"):
            try:
                if win_handle.startSystemMove():
                    return True
            except Exception as e:
                print(f"[window] startSystemMove failed: {e}")
        return False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "is_frameless", False):
            edge = self._get_resize_edge(event.position().toPoint())
            if edge:
                win_handle = self.windowHandle()
                if win_handle and hasattr(win_handle, "startSystemResize"):
                    win_handle.startSystemResize(edge)
                    return
            elif event.position().y() <= 40:
                if self.start_window_drag(event):
                    event.accept()
                    return
        super().mousePressEvent(event)

    def _toggle_frameless_mode(self, enabled: bool):
        self.is_frameless = enabled
        if hasattr(self, 'window_controls'):
            self.window_controls.setVisible(enabled)
        elif hasattr(self, 'traffic_cluster'):
            self.traffic_cluster.setVisible(enabled)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, enabled)
        self.show()

    def _detect_system_theme(self) -> str:
        return ThemeManager.follow_system_theme()

    def _on_theme_manager_changed(self, new_theme: str):
        if self.current_theme != new_theme:
            self.current_theme = new_theme
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
            self._apply_theme(self.current_theme, animate=True)

    def _on_system_color_scheme_changed(self, scheme):
        if getattr(self, "appearance_mode", "auto") == "auto":
            target = MacTheme.DARK if scheme == Qt.ColorScheme.Dark else MacTheme.LIGHT
            if self.current_theme != target:
                self.current_theme = target
                if hasattr(self, 'theme_btn'):
                    self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
                self._apply_theme(self.current_theme, animate=True)

    def _set_appearance_mode(self, mode: str):
        self.appearance_mode = mode
        if hasattr(self, "theme_auto_act"):
            self.theme_auto_act.setChecked(mode == "auto")
        if hasattr(self, "theme_dark_act"):
            self.theme_dark_act.setChecked(mode == MacTheme.DARK)
        if hasattr(self, "theme_light_act"):
            self.theme_light_act.setChecked(mode == MacTheme.LIGHT)
        if hasattr(self, "theme_manager"):
            self.theme_manager.set_mode(mode)
            resolved = self.theme_manager.get_resolved_theme()
        else:
            resolved = ThemeManager.follow_system_theme() if mode == "auto" else mode
        if self.current_theme != resolved:
            self.current_theme = resolved
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText("")
            self._apply_theme(self.current_theme, animate=True)

    def _toggle_theme(self):
        new_mode = MacTheme.LIGHT if self.current_theme == MacTheme.DARK else MacTheme.DARK
        self._set_appearance_mode(new_mode)

    def apply_theme(self, theme_name: str, animate: bool = False):
        self._apply_theme(theme_name, animate=animate)

    def _apply_theme(self, theme_name: str, animate: bool = False):
        self.current_theme = theme_name
        if animate and self.isVisible() and hasattr(self, "window_frame"):
            pix = self.window_frame.grab()
            overlay = QLabel(self.window_frame)
            overlay.setPixmap(pix)
            overlay.resize(self.window_frame.size())
            overlay.show()
            overlay.raise_()

            effect = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(200)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.finished.connect(overlay.deleteLater)
            self._theme_anim = anim

            qss = MacTheme.get_stylesheet(theme_name)
            self.setStyleSheet(qss)
            self._update_all_icons()
            self.sidebar.thumb_list.update()
            self.traffic_cluster.update()
            for child, method in (
                (getattr(self, "sidebar", None),         "update_theme"),
                (getattr(self, "tab_container", None),   "update_theme"),
                (getattr(self, "markup_bar", None),      "update_theme"),
                (getattr(self, "organize_bar", None),    "update_theme"),
                (getattr(self, "inspector_panel", None), "update_theme"),
            ):
                if child is None:
                    continue
                fn = getattr(child, method, None)
                if callable(fn):
                    try:
                        fn(theme_name)
                    except Exception as e:
                        print(f"[theme] {type(child).__name__}.{method} failed: {e}")
            self._sync_toolbar_contexts()
            anim.start()
        else:
            qss = MacTheme.get_stylesheet(theme_name)
            self.setStyleSheet(qss)
            self._update_all_icons()
            self.sidebar.thumb_list.update()
            self.traffic_cluster.update()
            for child, method in (
                (getattr(self, "sidebar", None),         "update_theme"),
                (getattr(self, "tab_container", None),   "update_theme"),
                (getattr(self, "markup_bar", None),      "update_theme"),
                (getattr(self, "organize_bar", None),    "update_theme"),
                (getattr(self, "inspector_panel", None), "update_theme"),
            ):
                if child is None:
                    continue
                fn = getattr(child, method, None)
                if callable(fn):
                    try:
                        fn(theme_name)
                    except Exception as e:
                        print(f"[theme] {type(child).__name__}.{method} failed: {e}")
            self._sync_toolbar_contexts()

    def _rotate_left(self):
        if self.canvas and (self.canvas.crop_box or self.canvas._selected_annotation):
            self.canvas.rotate_selection(-90)
            return
        if self.document:
            page = self.canvas.current_page
            self.document.rotate_page(page, -90)
            self.canvas.zoom_to_fit()
            def undo_rot():
                self.document.rotate_page(page, 90)
                self.canvas.zoom_to_fit()
            def redo_rot():
                self.document.rotate_page(page, -90)
                self.canvas.zoom_to_fit()
            self.canvas.history.push(ActionCommand("Rotate Left", undo_rot, redo_rot))

    def _rotate_right(self):
        if self.canvas and (self.canvas.crop_box or self.canvas._selected_annotation):
            if self.document and self.document.is_pdf and self.canvas.crop_box and not self.canvas._selected_annotation:
                pass
            else:
                self.canvas.rotate_selection(90)
                return
        if self.document:
            page = self.canvas.current_page
            self.document.rotate_page(page, 90)
            self.canvas.zoom_to_fit()
            def undo_rot():
                self.document.rotate_page(page, -90)
                self.canvas.zoom_to_fit()
            def redo_rot():
                self.document.rotate_page(page, 90)
                self.canvas.zoom_to_fit()
            self.canvas.history.push(ActionCommand("Rotate Right", undo_rot, redo_rot))

    def _open_adjust_color(self):
        if not self.document:
            return
        if self.document.is_pdf or not self.document._pil_image:
            QMessageBox.information(
                self,
                "Adjust Color",
                "Color adjustment is available only for image documents."
            )
            return

        page = self.canvas.current_page
        img = self.document._pil_image
        self._color_page = page
        self._color_initial_image = img.copy()
        self._color_last_committed = img.copy()

        if not self.color_dialog:
            self.color_dialog = AdjustColorDialog(img, self)
            self.color_dialog.adjustments_applied.connect(self._on_color_live_preview)
            self.color_dialog.adjustments_committed.connect(self._on_color_adjustments_committed)
        else:
            self.color_dialog.set_image(img)

        self.color_dialog.show()
        self.color_dialog.raise_()
        self.color_dialog.activateWindow()

    def _on_color_live_preview(self, new_img):
        if self.document and not self.document.is_pdf and hasattr(self, "_color_page"):
            self.document.update_image(new_img, self._color_page)
            self.canvas.update()

    def _on_color_adjustments_committed(self, new_img):
        if not self.document or self.document.is_pdf or not hasattr(self, "_color_page"):
            return
        page = self._color_page
        before_img = getattr(self, "_color_last_committed", self._color_initial_image).copy()
        after_img = new_img.copy()
        self._color_last_committed = after_img.copy()

        self.document.update_image(after_img, page)
        self.canvas.update()

        def undo_color():
            if self.document and not self.document.is_pdf:
                self.document.update_image(before_img, page)
                self.canvas.update()

        def redo_color():
            if self.document and not self.document.is_pdf:
                self.document.update_image(after_img, page)
                self.canvas.update()

        self.canvas.history.push(ActionCommand("Adjust Color", undo_color, redo_color))

    def _on_color_adjustments_applied(self, new_img, old_img, page):
        """Maintained for backward compatibility with direct callers/tests."""
        if self.document:
            self.document.update_image(new_img, page)
            self.canvas.update()
            def undo_color():
                self.document.update_image(old_img, page)
                self.canvas.update()
            def redo_color():
                self.document.update_image(new_img, page)
                self.canvas.update()
            self.canvas.history.push(ActionCommand("Adjust Color", undo_color, redo_color))

    def _open_adjust_size(self):
        if not self.document or not self.document._pil_image or self.document.is_pdf:
            QMessageBox.information(self, "Adjust Size", "Size adjustment is available only for image documents.")
            return

        page = self.canvas.current_page
        old_img = self.document._pil_image.copy()
        file_sz = self.document.metadata.get("file_size", 0)
        if file_sz <= 0 and getattr(self.document, "file_path", None) and os.path.isfile(self.document.file_path):
            try:
                file_sz = os.path.getsize(self.document.file_path)
            except OSError:
                file_sz = 0
        dialog = AdjustSizeDialog(self.document._pil_image, file_sz, self)

        def on_size(resized):
            self.document.update_image(resized, page)
            def undo_sz():
                self.document.update_image(old_img, page)
            def redo_sz():
                self.document.update_image(resized, page)
            self.canvas.history.push(ActionCommand("Adjust Size", undo_sz, redo_sz))

        dialog.size_applied.connect(on_size)
        dialog.exec()

    def _open_batch_dialog(self):
        initial_paths = []
        if self.document and not self.document.is_pdf:
            if self.document.image_paths:
                initial_paths = list(self.document.image_paths)
            elif self.document.file_path:
                initial_paths = [self.document.file_path]
        dialog = BatchConvertDialog(image_paths=initial_paths, parent=self)
        dialog.exec()

    def _open_signature_dialog(self):
        dialog = SignatureDialog(self)
        dialog.signature_selected.connect(self._on_signature_selected)
        dialog.exec()

    def _on_signature_selected(self, sig_pixmap):
        self.canvas.active_signature_pixmap = sig_pixmap
        self.canvas.set_active_tool(AnnotationType.SIGNATURE)
        self._show_status("Click anywhere on the document to stamp your signature.")

    def _add_image_overlay(self):
        """Opens a file dialog to select an image overlay to place on the document, like Canva."""
        if not self.document:
            self._show_status("Open an image or PDF document first to add an image overlay.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Image Overlay",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.svg *.gif);;All Files (*)"
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._show_status("Failed to load image for overlay.")
            return

        self.set_markup_visible(True)
        self.canvas.add_image_overlay(pixmap)
        self._show_status("Image overlay added. Drag to reposition, resize with corner handles.")

    def _show_inspector(self):
        if not self.document:
            return
        if not self.inspector_dialog:
            self.inspector_dialog = InspectorDialog(self.document.metadata, self)
        self.inspector_dialog.show()
        self.inspector_dialog.raise_()

    def _on_search(self):
        query = self.search_edit.text().strip()
        if not self.document or not query:
            self.canvas.search_results.clear()
            self.canvas.update()
            return

        results = self.document.search_text(query)
        self.canvas.search_results = results
        if results:
            first_match = results[0]
            self.canvas.set_page(first_match.page_num)
            self.sidebar.select_page(first_match.page_num)
            self._show_status(f"Found {len(results)} matches for '{query}'")
        else:
            self._show_status(f"No matches found for '{query}'")
        self.canvas.update()

    def _update_status(self):
        if self.document:
            w, h = self.document.get_page_size(self.canvas.current_page)
            curr = self.canvas.current_page + 1
            tot = self.document.page_count
            p_text = f"Page {curr} of {tot} - {int(w)} × {int(h)} pt"
            self.page_status_label.setText(p_text)
            self.page_badge.setText(f"{curr} of {tot}")
            self.page_badge.setVisible(tot > 1)
            self.toolbar_widget.update_title_geometry()

            zoom_str = "Fit" if getattr(self.canvas, '_auto_fit', False) else f"{int(self.canvas.zoom * 100)}%"
            if hasattr(self, "floating_pill") and self.floating_pill:
                if tot > 1:
                    self.floating_pill.show_status(f"Page {curr} of {tot}  •  {zoom_str}")
                else:
                    self.floating_pill.show_status(f"{zoom_str}  •  {int(w)} × {int(h)} pt")
            if hasattr(self, "slideshow_hud") and self.slideshow_hud and getattr(self, "_is_slideshow", False):
                self.slideshow_hud.update_page_info(curr, tot)
        else:
            self.page_status_label.setText("No document")
            self.page_badge.setVisible(False)
            self.toolbar_widget.update_title_geometry()

        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            self.inspector_panel.set_document(self.document, self.canvas.current_page if self.document else 0)

    def _show_status(self, msg: str, timeout: int = 4000):
        self.page_status_label.setText(msg)
        if hasattr(self, "floating_pill") and self.floating_pill:
            self.floating_pill.show_status(msg)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def open_settings_dialog(self):
        """Opens the Studio Settings & Preferences multi-tab dialog."""
        from preview.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.settings_changed.connect(self._on_settings_applied)
        dlg.exec()

    def _on_settings_applied(self, cfg: dict):
        """Applies configuration changes immediately across the main window."""
        if "theme" in cfg:
            theme_choice = str(cfg["theme"]).lower()
            if theme_choice == "system":
                theme_choice = "auto"
            self._set_appearance_mode(theme_choice)

        if "startup_mode" in cfg:
            self.set_workspace_mode(str(cfg["startup_mode"]))

        if "default_pen_width" in cfg and hasattr(self, "markup_bar"):
            self.markup_bar.stroke_width = float(cfg["default_pen_width"])
            self.canvas.stroke_width = float(cfg["default_pen_width"])

        if "default_highlight_color" in cfg and hasattr(self, "markup_bar"):
            self.markup_bar.stroke_color = QColor(str(cfg["default_highlight_color"]))

        if "canvas_background_tone" in cfg and hasattr(self, "canvas"):
            tone = str(cfg["canvas_background_tone"])
            if tone == "Obsidian":
                self.canvas.setStyleSheet("background-color: #141518;")
            elif tone == "Charcoal":
                self.canvas.setStyleSheet("background-color: #1e2026;")
            elif tone == "Custom" and "custom_canvas_color" in cfg:
                self.canvas.setStyleSheet(f"background-color: {cfg['custom_canvas_color']};")

    def _show_help(self, page_id: str = "what-is-preview"):
        if not hasattr(self, "_help_window") or self._help_window is None:
            from preview.ui.help_window import HelpWindow
            self._help_window = HelpWindow(theme=self.current_theme, parent=self)
        else:
            self._help_window.current_theme = self.current_theme
            self._help_window._apply_theme()
        if page_id:
            self._help_window.navigate_to(page_id)
        self._help_window.show()
        self._help_window.raise_()
        self._help_window.activateWindow()

    def _show_shortcuts_guide(self):
        self._show_help(page_id="shortcuts")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F1:
            self._show_help()
            event.accept()
            return

        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_I:
                self._add_image_overlay()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V and not (hasattr(self, "search_edit") and self.search_edit.hasFocus()):
                clipboard = QApplication.clipboard()
                pixmap = clipboard.pixmap()
                if not pixmap.isNull():
                    self.set_markup_visible(True)
                    self.canvas.add_image_overlay(pixmap)
                    event.accept()
                    return
        if getattr(self, "_is_fullscreen_image", False) or getattr(self, "_is_slideshow", False) or self.isFullScreen():
            if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
                self.toggle_fullscreen(auto_advance=False)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Space:
                self._toggle_slideshow_timer()
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.next_page()
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                self.prev_page()
                event.accept()
                return
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen(auto_advance=False)
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()
        if hasattr(self, "slideshow_hud") and self.slideshow_hud and self.slideshow_hud.isVisible():
            self.slideshow_hud._reposition()
            if getattr(self, "_is_fullscreen_image", False):
                self.canvas.zoom_to_fit()
        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            if w < 860:
                self.set_inspector_visible(False)
        if hasattr(self, "markup_bar") and hasattr(self.markup_bar, "handle_resize"):
            self.markup_bar.handle_resize(w)

        # Responsive toolbar adaptation: collapse buttons to icon-only when narrow (< 1060px)
        if hasattr(self, "mode_view_btn") and hasattr(self, "mode_edit_btn") and hasattr(self, "mode_organize_btn"):
            if w < 1060:
                self.mode_view_btn.setText("")
                self.mode_edit_btn.setText("")
                self.mode_organize_btn.setText("")
                self.mode_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                self.mode_edit_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                self.mode_organize_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            else:
                self.mode_view_btn.setText("View")
                self.mode_edit_btn.setText("Edit")
                self.mode_organize_btn.setText("Organize")
                self.mode_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                self.mode_edit_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                self.mode_organize_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        if hasattr(self, "search_edit"):
            self.search_edit.setFixedWidth(90 if w < 1024 else 130)

        if hasattr(self, "open_btn"):
            if w < 960:
                self.open_btn.setText("")
                self.open_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            else:
                self.open_btn.setText("Open")
                self.open_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        if w < 820 and hasattr(self, "sidebar") and self.sidebar.isVisible():
            self.set_sidebar_visible(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not paths:
            return

        # If a document is already open, automatically open in a new tab
        if self.document is not None:
            if len(paths) == 1 and os.path.isdir(paths[0]):
                self.new_tab()
                self.open_folder(paths[0])
            elif len(paths) == 1:
                self.new_tab(paths[0])
            else:
                self.new_tab_files(paths)
            return

        # If a single directory was dropped, open folder
        if len(paths) == 1 and os.path.isdir(paths[0]):
            self.open_folder(paths[0])
        elif len(paths) == 1:
            self.open_file(paths[0])
        else:
            self.open_files(paths)

    def _check_for_updates_startup(self):
        """Non-blocking background check for new versions on launch."""
        if os.environ.get("CI") or os.environ.get("PREVIEW_TESTING"):
            return
        settings = QSettings("TriviLabs", "PreviewMacOS")
        auto_check = settings.value("check_updates_on_startup", True, type=bool)
        if not auto_check:
            return

        import time
        last_check = settings.value("last_update_check_time", 0.0, type=float)
        now = time.time()
        # Check at most once every 24 hours automatically
        if now - last_check < 86400:
            return

        self._start_update_check(is_manual=False)

    def _check_for_updates_manual(self):
        """User-initiated manual update check with visual progress feedback."""
        self._show_status("Checking for updates...", 3000)
        self._start_update_check(is_manual=True)

    def _start_update_check(self, is_manual: bool = False):
        if self._update_worker and self._update_worker.isRunning():
            return

        from preview import __version__
        self._update_worker = UpdateCheckWorker(current_version=__version__, is_manual=is_manual, parent=self)
        if is_manual:
            self._update_worker.update_available.connect(self._show_update_dialog)
            self._update_worker.no_update_available.connect(self._on_no_update_manual)
            self._update_worker.check_failed.connect(self._on_update_check_failed_manual)
        else:
            self._update_worker.update_available.connect(self._on_update_available_startup)

        self._update_worker.start()

    def _on_update_available_startup(self, update_info: UpdateInfo):
        """Displays non-intrusive in-app banner when background check finds an update."""
        import time
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("last_update_check_time", time.time())

        # If user marked this specific version as skipped, honor their preference
        skipped = settings.value("skipped_version", "", type=str)
        if skipped == update_info.version:
            return

        if not self.update_banner:
            self.update_banner = UpdateBanner(update_info, self)
            self.update_banner.view_requested.connect(lambda: self._show_update_dialog(update_info))
            # Insert above the splitter
            idx = self.main_layout.indexOf(self.splitter)
            if idx >= 0:
                self.main_layout.insertWidget(idx, self.update_banner)
            else:
                self.main_layout.addWidget(self.update_banner)
        else:
            self.update_banner.setVisible(True)

        # Show popup notification asking the user to update
        self._show_update_dialog(update_info)

    def _show_update_dialog(self, update_info: UpdateInfo):
        """Opens macOS Sparkle style software update sheet."""
        if self.update_banner:
            self.update_banner.setVisible(False)
        from preview import __version__
        dlg = UpdateDialog(update_info, current_version=__version__, parent=self)
        dlg.exec()

    def _on_no_update_manual(self, current_ver: str):
        """Shows informative dialog confirming the user has the newest version."""
        import time
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("last_update_check_time", time.time())

        msg = QMessageBox(self)
        msg.setWindowTitle("Software Update")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.png")
        if os.path.exists(icon_path):
            msg.setIconPixmap(QPixmap(icon_path).scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("<h3>You're up to date!</h3>")
        msg.setInformativeText(f"Preview {current_ver} is currently the newest version available.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _on_update_check_failed_manual(self, err: str):
        """Shows warning dialog when manual update check fails."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Software Update")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("<h3>Unable to Check for Updates</h3>")
        msg.setInformativeText(f"Could not connect to the update server:\n{err}\n\nPlease check your internet connection and try again.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

