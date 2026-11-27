"""Menu bar, action wiring, and recent-files menu mixin for MacMainWindow."""

import os

from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QShortcut
from PyQt6.QtCore import QSettings, Qt

from preview.icons import MacIconFactory
from preview.theme import MacTheme


class MenusMixin:
    """Menu bar setup, visibility toggles, and recent files."""

    def _setup_menus(self):
        # Ensure QMainWindow's native outer menubar is hidden
        native_mb = self.menuBar()
        if native_mb:
            native_mb.setVisible(False)
            native_mb.setFixedHeight(0)

        # 1. Application / Logo Menu
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.png")
        if os.path.exists(icon_path):
            logo_icon = QIcon(icon_path)
        else:
            logo_icon = MacIconFactory.create_icon("doc_proxy", self._get_icon_color(), 16)

        self.logo_menu = self.top_menubar.addMenu(logo_icon, "")
        self.logo_menu.setTitle("")

        about_act = QAction("About Document Viewer", self)
        about_act.triggered.connect(self._show_about)
        self.logo_menu.addAction(about_act)

        check_updates_act = QAction("Check for Updates...", self)
        check_updates_act.triggered.connect(self._check_for_updates_manual)
        self.logo_menu.addAction(check_updates_act)

        self.logo_menu.addSeparator()

        theme_act = QAction("Toggle Dark/Light Mode", self)
        theme_act.setShortcut(QKeySequence("Ctrl+T"))
        theme_act.triggered.connect(self._toggle_theme)
        self.logo_menu.addAction(theme_act)

        pref_act = QAction("Preferences...", self)
        pref_act.setShortcut(QKeySequence("Ctrl+,"))
        pref_act.triggered.connect(self.open_settings_dialog)
        self.logo_menu.addAction(pref_act)

        self.logo_menu.addSeparator()

        hide_act = QAction("Hide Window", self)
        hide_act.setShortcut(QKeySequence("Ctrl+H"))
        hide_act.triggered.connect(self.showMinimized)
        self.logo_menu.addAction(hide_act)

        quit_act = QAction("Quit Document Viewer", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        self.logo_menu.addAction(quit_act)

        # 2. File Menu
        self.file_menu = self.top_menubar.addMenu("File")
        new_tab_act = QAction("New Tab", self)
        new_tab_act.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_act.triggered.connect(self._on_new_tab_triggered)
        self.file_menu.addAction(new_tab_act)

        open_act = QAction("Open...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open_file_dialog)
        self.file_menu.addAction(open_act)

        open_in_new_tab_act = QAction("Open in New Tab...", self)
        open_in_new_tab_act.setShortcut(QKeySequence("Ctrl+Alt+O"))
        open_in_new_tab_act.triggered.connect(self._on_new_tab_triggered)
        self.file_menu.addAction(open_in_new_tab_act)

        open_folder_act = QAction("Open Folder...", self)
        open_folder_act.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_act.triggered.connect(self._open_folder_dialog)
        self.file_menu.addAction(open_folder_act)

        self.recent_menu = self.file_menu.addMenu("Open Recent")
        self._update_recent_menu()

        self.file_menu.addSeparator()

        self.save_act = QAction("Save", self)
        self.save_act.setShortcut(QKeySequence.StandardKey.Save)
        self.save_act.triggered.connect(self._save_file)
        self.file_menu.addAction(self.save_act)

        self.save_as_act = QAction("Duplicate / Save As New Copy...", self)
        self.save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.save_as_act.triggered.connect(self._save_as_file)
        self.file_menu.addAction(self.save_as_act)

        self.revert_act = QAction("Revert to Original...", self)
        self.revert_act.setEnabled(False)
        self.revert_act.triggered.connect(self._revert_to_original)
        self.file_menu.addAction(self.revert_act)

        export_pdf_act = QAction("Export as PDF...", self)
        export_pdf_act.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_pdf_act.triggered.connect(self._export_as_pdf)
        self.file_menu.addAction(export_pdf_act)

        export_act = QAction("Export...", self)
        export_act.setShortcut(QKeySequence("Ctrl+E"))
        export_act.triggered.connect(self._export_file)
        self.file_menu.addAction(export_act)

        self.file_menu.addSeparator()

        merge_pdf_act = QAction("Merge PDFs...", self)
        merge_pdf_act.triggered.connect(self._merge_pdfs)
        self.file_menu.addAction(merge_pdf_act)

        split_pdf_act = QAction("Split PDF / Extract Pages...", self)
        split_pdf_act.triggered.connect(self._split_pdf)
        self.file_menu.addAction(split_pdf_act)

        pass_pdf_act = QAction("Set PDF Password / Encryption...", self)
        pass_pdf_act.triggered.connect(self._set_pdf_password)
        self.file_menu.addAction(pass_pdf_act)

        self.file_menu.addSeparator()

        print_act = QAction("Print...", self)
        print_act.setShortcut(QKeySequence.StandardKey.Print)
        print_act.triggered.connect(self._print_file)
        self.file_menu.addAction(print_act)

        print_prev_act = QAction("Print Preview...", self)
        print_prev_act.setShortcut(QKeySequence("Ctrl+Shift+P"))
        print_prev_act.triggered.connect(self._print_preview_file)
        self.file_menu.addAction(print_prev_act)

        self.file_menu.addSeparator()

        close_tab_act = QAction("Close Tab", self)
        close_tab_act.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_act.triggered.connect(lambda: self.close_tab())
        self.file_menu.addAction(close_tab_act)

        close_act = QAction("Close Window", self)
        close_act.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_act.triggered.connect(self.close)
        self.file_menu.addAction(close_act)

        # 3. Edit Menu
        self.edit_menu = self.top_menubar.addMenu("Edit")
        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(self.canvas.undo)
        self.edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcuts([QKeySequence("Ctrl+Shift+Z"), QKeySequence("Ctrl+Y"), QKeySequence.StandardKey.Redo])
        redo_act.triggered.connect(self.canvas.redo)
        self.edit_menu.addAction(redo_act)

        self.edit_menu.addSeparator()

        copy_text_act = QAction("Copy Current Page Text", self)
        copy_text_act.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_text_act.triggered.connect(self._copy_current_page_text)
        self.edit_menu.addAction(copy_text_act)

        extract_all_act = QAction("Extract All Text to Clipboard", self)
        extract_all_act.triggered.connect(self._extract_all_text)
        self.edit_menu.addAction(extract_all_act)

        self.edit_menu.addSeparator()

        insert_page_act = QAction("Insert Page from File...", self)
        insert_page_act.setShortcut(QKeySequence("Ctrl+Alt+P"))
        insert_page_act.triggered.connect(self._insert_page_from_file_menu)
        self.edit_menu.addAction(insert_page_act)

        overlay_act = QAction("Add Image Overlay...", self)
        overlay_act.setShortcut(QKeySequence("Ctrl+Shift+I"))
        overlay_act.triggered.connect(self._add_image_overlay)
        self.edit_menu.addAction(overlay_act)

        apply_redact_act = QAction("Apply Permanent Redactions", self)
        apply_redact_act.triggered.connect(self._apply_redactions_menu)
        self.edit_menu.addAction(apply_redact_act)

        # 4. View Menu
        self.view_menu = self.top_menubar.addMenu("View")
        self.toggle_primary_toolbar_act = QAction("Hide Toolbar", self)
        self.toggle_primary_toolbar_act.setShortcuts([
            QKeySequence("Ctrl+Alt+T"),
            QKeySequence("F8"),
        ])
        self.toggle_primary_toolbar_act.triggered.connect(self._toggle_primary_toolbar)
        self.view_menu.addAction(self.toggle_primary_toolbar_act)

        toggle_sb = QAction("Toggle Sidebar", self)
        toggle_sb.setShortcut(QKeySequence("Ctrl+B"))
        toggle_sb.triggered.connect(self._toggle_sidebar)
        self.view_menu.addAction(toggle_sb)

        toggle_inspector_act = QAction("Toggle Inspector Panel", self)
        toggle_inspector_act.setShortcuts([QKeySequence("Ctrl+I"), QKeySequence("Cmd+I")])
        toggle_inspector_act.triggered.connect(self._toggle_inspector_panel)
        self.view_menu.addAction(toggle_inspector_act)

        workspace_menu = self.view_menu.addMenu("Workspace Mode")
        act_view_mode = QAction("View Mode (Browsing)", self)
        act_view_mode.setShortcut(QKeySequence("Alt+1"))
        act_view_mode.triggered.connect(lambda: self.set_workspace_mode("View"))
        workspace_menu.addAction(act_view_mode)

        act_edit_mode = QAction("Edit Mode (Markup & Tools)", self)
        act_edit_mode.setShortcut(QKeySequence("Alt+2"))
        act_edit_mode.triggered.connect(lambda: self.set_workspace_mode("Edit"))
        workspace_menu.addAction(act_edit_mode)

        act_org_mode = QAction("Organize Mode (Pages & Documents)", self)
        act_org_mode.setShortcut(QKeySequence("Alt+3"))
        act_org_mode.triggered.connect(lambda: self.set_workspace_mode("Organize"))
        workspace_menu.addAction(act_org_mode)

        toggle_mb_act = QAction("Show Menu Bar", self, checkable=True)
        toggle_mb_act.setShortcut(QKeySequence("Ctrl+Alt+M"))
        toggle_mb_act.setChecked(True)
        toggle_mb_act.toggled.connect(self._toggle_menu_bar)
        self.view_menu.addAction(toggle_mb_act)

        toggle_sb_bar = QAction("Show Status Bar", self, checkable=True)
        toggle_sb_bar.setShortcut(QKeySequence("Ctrl+/"))
        toggle_sb_bar.setChecked(True)
        toggle_sb_bar.toggled.connect(self._toggle_status_bar)
        self.view_menu.addAction(toggle_sb_bar)

        self.toggle_tab_bar_act = QAction("Show Tab Bar", self, checkable=True)
        self.toggle_tab_bar_act.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.toggle_tab_bar_act.setChecked(self.show_tab_bar_always)
        self.toggle_tab_bar_act.triggered.connect(self._toggle_tab_bar_visible)
        self.view_menu.addAction(self.toggle_tab_bar_act)

        view_mode_menu = self.view_menu.addMenu("PDF View Mode")
        self.single_mode_act = QAction("Single Page", self, checkable=True)
        self.single_mode_act.setChecked(True)
        self.single_mode_act.triggered.connect(lambda: self._set_pdf_view_mode("Single"))
        view_mode_menu.addAction(self.single_mode_act)

        self.two_up_mode_act = QAction("Two Pages (Two-Up)", self, checkable=True)
        self.two_up_mode_act.triggered.connect(lambda: self._set_pdf_view_mode("Two-Up"))
        view_mode_menu.addAction(self.two_up_mode_act)

        slideshow_act = QAction("Start Slideshow", self)
        slideshow_act.setShortcuts([QKeySequence("F11"), QKeySequence("Ctrl+Shift+F")])
        slideshow_act.triggered.connect(self._toggle_slideshow)
        self.view_menu.addAction(slideshow_act)

        frameless_act = QAction("macOS Frameless Window", self, checkable=True)
        frameless_act.setShortcut(QKeySequence("Ctrl+Alt+F"))
        frameless_act.setChecked(self.is_frameless)
        frameless_act.toggled.connect(self._toggle_frameless_mode)
        self.view_menu.addAction(frameless_act)

        appearance_menu = self.view_menu.addMenu("Appearance")
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)

        self.theme_auto_act = QAction("Auto (System Default)", self, checkable=True)
        self.theme_auto_act.setChecked(self.appearance_mode == "auto")
        self.theme_auto_act.triggered.connect(lambda: self._set_appearance_mode("auto"))
        self.theme_group.addAction(self.theme_auto_act)
        appearance_menu.addAction(self.theme_auto_act)

        self.theme_dark_act = QAction("Dark", self, checkable=True)
        self.theme_dark_act.setChecked(self.appearance_mode == MacTheme.DARK)
        self.theme_dark_act.triggered.connect(lambda: self._set_appearance_mode(MacTheme.DARK))
        self.theme_group.addAction(self.theme_dark_act)
        appearance_menu.addAction(self.theme_dark_act)

        self.theme_light_act = QAction("Light", self, checkable=True)
        self.theme_light_act.setChecked(self.appearance_mode == MacTheme.LIGHT)
        self.theme_light_act.triggered.connect(lambda: self._set_appearance_mode(MacTheme.LIGHT))
        self.theme_group.addAction(self.theme_light_act)
        appearance_menu.addAction(self.theme_light_act)

        self.view_menu.addSeparator()

        actual_size = QAction("Actual Size", self)
        actual_size.setShortcuts([QKeySequence("Ctrl+1"), QKeySequence("Ctrl+Alt+0")])
        actual_size.triggered.connect(self.canvas.zoom_actual_size)
        self.view_menu.addAction(actual_size)

        zoom_to_fit = QAction("Zoom to Fit", self)
        zoom_to_fit.setShortcuts([QKeySequence("Ctrl+0"), QKeySequence("Ctrl+9")])
        zoom_to_fit.triggered.connect(self.canvas.zoom_to_fit)
        self.view_menu.addAction(zoom_to_fit)

        zoom_to_width = QAction("Zoom to Width", self)
        zoom_to_width.setShortcut(QKeySequence("Ctrl+8"))
        zoom_to_width.triggered.connect(self.canvas.zoom_to_width)
        self.view_menu.addAction(zoom_to_width)

        zoom_in_act = QAction("Zoom In", self)
        zoom_in_act.setShortcuts([QKeySequence("Ctrl+="), QKeySequence("Ctrl++"), QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Plus)])
        zoom_in_act.triggered.connect(self.canvas.zoom_in)
        self.view_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("Zoom Out", self)
        zoom_out_act.setShortcuts([QKeySequence("Ctrl+-"), QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus)])
        zoom_out_act.triggered.connect(self.canvas.zoom_out)
        self.view_menu.addAction(zoom_out_act)

        # 5. Go Menu
        self.go_menu = self.top_menubar.addMenu("Go")
        next_act = QAction("Next Page / Image", self)
        next_act.setShortcuts([QKeySequence(Qt.Key.Key_Right), QKeySequence(Qt.Key.Key_Down), QKeySequence(Qt.Key.Key_PageDown)])
        next_act.triggered.connect(self.next_page)
        self.go_menu.addAction(next_act)

        prev_act = QAction("Previous Page / Image", self)
        prev_act.setShortcuts([QKeySequence(Qt.Key.Key_Left), QKeySequence(Qt.Key.Key_Up), QKeySequence(Qt.Key.Key_PageUp)])
        prev_act.triggered.connect(self.prev_page)
        self.go_menu.addAction(prev_act)

        first_act = QAction("First Page / Image", self)
        first_act.setShortcut(QKeySequence("Home"))
        first_act.triggered.connect(self._first_page)
        self.go_menu.addAction(first_act)

        last_act = QAction("Last Page / Image", self)
        last_act.setShortcut(QKeySequence("End"))
        last_act.triggered.connect(self._last_page)
        self.go_menu.addAction(last_act)

        goto_act = QAction("Go to Page...", self)
        goto_act.setShortcut(QKeySequence("Ctrl+G"))
        goto_act.triggered.connect(self._go_to_page_dialog)
        self.go_menu.addAction(goto_act)

        # 6. Tools Menu
        self.tools_menu = self.top_menubar.addMenu("Tools")
        markup_act = QAction("Show Markup Toolbar", self)
        markup_act.setShortcut(QKeySequence("Ctrl+Shift+A"))
        markup_act.triggered.connect(self._toggle_markup_bar)
        self.tools_menu.addAction(markup_act)

        loupe_act = QAction("Show Magnifier (Loupe)", self)
        loupe_act.setShortcuts([QKeySequence("~"), QKeySequence("`"), QKeySequence("Ctrl+Shift+M")])
        loupe_act.triggered.connect(lambda: self.canvas.toggle_loupe())
        self.tools_menu.addAction(loupe_act)

        crop_act = QAction("Crop", self)
        crop_act.setShortcut(QKeySequence("Ctrl+K"))
        crop_act.triggered.connect(self.canvas.apply_crop)
        self.tools_menu.addAction(crop_act)

        self.tools_menu.addSeparator()

        rot_l_act = QAction("Rotate Left", self)
        rot_l_act.setShortcut(QKeySequence("Ctrl+L"))
        rot_l_act.triggered.connect(self._rotate_left)
        self.tools_menu.addAction(rot_l_act)

        rot_r_act = QAction("Rotate Right", self)
        rot_r_act.setShortcut(QKeySequence("Ctrl+R"))
        rot_r_act.triggered.connect(self._rotate_right)
        self.tools_menu.addAction(rot_r_act)

        self.tools_menu.addSeparator()

        color_act = QAction("Adjust Color...", self)
        color_act.setShortcut(QKeySequence("Ctrl+Alt+C"))
        color_act.triggered.connect(self._open_adjust_color)
        self.tools_menu.addAction(color_act)

        size_act = QAction("Adjust Size...", self)
        size_act.setShortcut(QKeySequence("Ctrl+Alt+S"))
        size_act.triggered.connect(self._open_adjust_size)
        self.tools_menu.addAction(size_act)

        batch_act = QAction("Batch Resize / Convert Images...", self)
        batch_act.triggered.connect(self._open_batch_dialog)
        self.tools_menu.addAction(batch_act)

        overlay_tool_act = QAction("Add Image Overlay...", self)
        overlay_tool_act.triggered.connect(self._add_image_overlay)
        self.tools_menu.addAction(overlay_tool_act)

        insp_act = QAction("Show Inspector", self)
        insp_act.triggered.connect(self._toggle_inspector_panel)
        self.tools_menu.addAction(insp_act)

        # 7. Window Menu
        self.win_menu = self.top_menubar.addMenu("Window")
        min_act = QAction("Minimize", self)
        min_act.setShortcut(QKeySequence("Ctrl+M"))
        min_act.triggered.connect(self.showMinimized)
        self.win_menu.addAction(min_act)

        zoom_win_act = QAction("Zoom / Maximize", self)
        zoom_win_act.triggered.connect(self._toggle_maximize)
        self.win_menu.addAction(zoom_win_act)

        self.win_menu.addSeparator()

        next_tab_act = QAction("Select Next Tab", self)
        next_tab_act.setShortcuts([QKeySequence("Ctrl+Tab"), QKeySequence("Ctrl+PageDown")])
        next_tab_act.triggered.connect(lambda: self.cycle_tab(forward=True))
        self.win_menu.addAction(next_tab_act)

        prev_tab_act = QAction("Select Previous Tab", self)
        prev_tab_act.setShortcuts([QKeySequence("Ctrl+Shift+Tab"), QKeySequence("Ctrl+PageUp")])
        prev_tab_act.triggered.connect(lambda: self.cycle_tab(forward=False))
        self.win_menu.addAction(prev_tab_act)

        # 8. Help Menu
        self.help_menu = self.top_menubar.addMenu("Help")
        preview_help_act = QAction("Preview Help", self)
        preview_help_act.setShortcut(QKeySequence("F1"))
        preview_help_act.triggered.connect(lambda: self._show_help())
        self.help_menu.addAction(preview_help_act)

        shortcuts_guide_act = QAction("Keyboard Shortcuts Guide", self)
        shortcuts_guide_act.triggered.connect(self._show_shortcuts_guide)
        self.help_menu.addAction(shortcuts_guide_act)

        self.help_menu.addSeparator()

        check_up_h_act = QAction("Check for Updates...", self)
        check_up_h_act.triggered.connect(self._check_for_updates_manual)
        self.help_menu.addAction(check_up_h_act)

        self.help_menu.addSeparator()

        about_h_act = QAction("About Document Viewer", self)
        about_h_act.triggered.connect(self._show_about)
        self.help_menu.addAction(about_h_act)

        # Register keyboard shortcuts into window actions
        for a in [new_tab_act, open_act, open_folder_act, self.save_act, self.save_as_act, self.revert_act, export_pdf_act, export_act,
                  print_act, print_prev_act, close_tab_act, close_act, undo_act, redo_act, copy_text_act,
                  extract_all_act, toggle_sb, toggle_mb_act, toggle_sb_bar, self.toggle_tab_bar_act, slideshow_act,
                  frameless_act, actual_size, zoom_to_fit, zoom_in_act, zoom_out_act, next_act,
                  prev_act, first_act, last_act, markup_act, loupe_act, crop_act, rot_l_act,
                  rot_r_act, color_act, size_act, insp_act, min_act, zoom_win_act, next_tab_act, prev_tab_act, theme_act,
                  quit_act, pref_act, hide_act, check_updates_act, check_up_h_act,
                  preview_help_act, shortcuts_guide_act]:
            self.addAction(a)

        # --- Markup toolbar shortcuts ---
        for key_seq, sig in self.markup_bar.shortcut_specs():
            QShortcut(key_seq, self, activated=sig.emit)

        # --- Organize toolbar shortcuts ---
        for key_seq, sig in self.organize_bar.shortcut_specs():
            QShortcut(key_seq, self, activated=sig.emit)

    def _toggle_menu_bar(self, checked: bool):
        self.top_menubar.setVisible(checked)

    def set_primary_toolbar_visible(self, visible: bool):
        self.toolbar_widget.setVisible(visible)
        tip = "Hide Toolbar (Ctrl+Alt+T)" if visible else "Show Toolbar (Ctrl+Alt+T)"
        if hasattr(self, "window_controls") and hasattr(self.window_controls, "btn_toggle_toolbar"):
            self.window_controls.btn_toggle_toolbar.setToolTip(tip)
        if hasattr(self, "toggle_primary_toolbar_act"):
            self.toggle_primary_toolbar_act.setText("Hide Toolbar" if visible else "Show Toolbar")
        self._update_window_chrome_state()

    def _toggle_primary_toolbar(self, *args, **kwargs):
        self.set_primary_toolbar_visible(not self.toolbar_widget.isVisible())

    def _toggle_status_bar(self, checked: bool):
        self.status_bar.setVisible(checked)

    def _add_recent_file(self, file_path: str):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        recents = settings.value("recent_files", [], type=list) or []
        path = os.path.abspath(file_path)
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        recents = recents[:10]
        settings.setValue("recent_files", recents)
        self._update_recent_menu()

    def _update_recent_menu(self):
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        settings = QSettings("TriviLabs", "PreviewMacOS")
        recents = settings.value("recent_files", [], type=list) or []
        valid_recents = [p for p in recents if os.path.exists(p)]
        if not valid_recents:
            no_act = QAction("No Recent Documents", self)
            no_act.setEnabled(False)
            self.recent_menu.addAction(no_act)
            return

        for p in valid_recents:
            act = QAction(os.path.basename(p), self)
            act.setToolTip(p)
            act.triggered.connect(lambda _, path=p: self._open_recent_item(path))
            self.recent_menu.addAction(act)

        self.recent_menu.addSeparator()
        clear_act = QAction("Clear Menu", self)
        clear_act.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_act)

    def _open_recent_item(self, path: str):
        if self.document is not None:
            if os.path.isdir(path):
                self.new_tab()
                self.open_folder(path)
            elif os.path.isfile(path):
                self.new_tab(path)
            return

        if os.path.isdir(path):
            self.open_folder(path)
        elif os.path.isfile(path):
            self.open_file(path)

    def _clear_recent_files(self):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("recent_files", [])
        self._update_recent_menu()

