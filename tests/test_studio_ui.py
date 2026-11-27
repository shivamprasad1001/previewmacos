"""
Unit and integration tests for Studio Pro UI components:
- SettingsDialog tabs, controls, settings persistence, legacy migration, defaults reset, cache purge.
- Studio titlebar modern window controls (min, max, close), dirty indicator, maximize/restore toggling.
- Action ribbon physical tool icons (chisel highlighter, fountain pen, rubber stamp, crop shears, loupe).
- Right-side Inspector panel smooth toggle, shortcut keybindings, and toolbar responsiveness.
"""

import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence

from preview.ui.settings_dialog import (
    SettingsDialog, StudioSettingsManager, DEFAULT_STUDIO_SETTINGS, SHORTCUTS_CATALOG
)
from preview.ui.main_window import MacMainWindow, StudioWindowControls

# Single QApplication offscreen instance
app = QApplication.instance()
if not app:
    app = QApplication([])


class TestStudioSettingsDialog(unittest.TestCase):
    """Validates SettingsDialog tabs, persistence, and legacy synchronization."""

    def setUp(self):
        # Clear test QSettings
        self.studio_settings = QSettings("TriviLabs", "PreviewStudio")
        self.studio_settings.clear()
        self.legacy_settings = QSettings("TriviLabs", "PreviewMacOS")
        self.legacy_settings.clear()

    def tearDown(self):
        self.studio_settings.clear()
        self.legacy_settings.clear()

    def test_01_dialog_tabs_initialization(self):
        """Verifies all 5 tabs and their key controls exist in SettingsDialog."""
        dlg = SettingsDialog()
        self.assertEqual(dlg.tab_widget.count(), 5)
        self.assertEqual(dlg.tab_widget.tabText(0), "General")
        self.assertEqual(dlg.tab_widget.tabText(1), "Canvas & Display")
        self.assertEqual(dlg.tab_widget.tabText(2), "Annotations & Tools")
        self.assertEqual(dlg.tab_widget.tabText(3), "Performance & Cache")
        self.assertEqual(dlg.tab_widget.tabText(4), "Keyboard Shortcuts")

        # General Tab controls
        self.assertIsNotNone(dlg.combo_startup_mode)
        self.assertEqual(dlg.combo_startup_mode.count(), 3)
        self.assertIsNotNone(dlg.combo_default_zoom)
        self.assertIsNotNone(dlg.combo_theme)
        self.assertIsNotNone(dlg.chk_auto_updates)

        # Canvas Tab controls
        self.assertIsNotNone(dlg.chk_hw_accel)
        self.assertIsNotNone(dlg.combo_dpi_scaling)
        self.assertIsNotNone(dlg.combo_interpolation)
        self.assertIsNotNone(dlg.combo_canvas_tone)
        self.assertIsNotNone(dlg.btn_custom_color)

        # Annotations Tab controls
        self.assertIsNotNone(dlg.btn_highlight_color)
        self.assertIsNotNone(dlg.spin_pen_width)
        self.assertIsNotNone(dlg.combo_stamp_text)
        self.assertIsNotNone(dlg.combo_redaction_style)

        # Performance Tab controls
        self.assertIsNotNone(dlg.spin_prefetch)
        self.assertIsNotNone(dlg.spin_disk_cache)
        self.assertIsNotNone(dlg.btn_purge_cache)

        # Shortcuts Tab controls
        self.assertIsNotNone(dlg.shortcut_filter)
        self.assertIsNotNone(dlg.shortcuts_table)
        self.assertEqual(dlg.shortcuts_table.columnCount(), 3)
        self.assertGreaterEqual(dlg.shortcuts_table.rowCount(), len(SHORTCUTS_CATALOG))
        dlg.close()

    def test_02_settings_persistence_and_apply(self):
        """Verifies saving settings writes to PreviewStudio and synchronizes with legacy PreviewMacOS."""
        dlg = SettingsDialog()

        # Modify values
        dlg.combo_startup_mode.setCurrentText("Organize")
        dlg.combo_default_zoom.setCurrentText("100%")
        dlg.combo_theme.setCurrentText("Light")
        dlg.chk_auto_updates.setChecked(False)
        dlg.spin_pen_width.setValue(5.5)
        dlg.combo_stamp_text.setCurrentText("CONFIDENTIAL")
        dlg.combo_canvas_tone.setCurrentText("Charcoal")
        dlg.spin_prefetch.setValue(4)
        dlg.spin_disk_cache.setValue(512)

        # Click Apply
        dlg._on_apply_clicked()

        # Check PreviewStudio QSettings
        saved = StudioSettingsManager.load_all()
        self.assertEqual(saved["startup_mode"], "Organize")
        self.assertEqual(saved["default_zoom"], "100%")
        self.assertEqual(saved["theme"], "Light")
        self.assertFalse(saved["auto_check_updates"])
        self.assertEqual(saved["default_pen_width"], 5.5)
        self.assertEqual(saved["default_stamp_text"], "CONFIDENTIAL")
        self.assertEqual(saved["canvas_background_tone"], "Charcoal")
        self.assertEqual(saved["page_prefetch_distance"], 4)
        self.assertEqual(saved["disk_cache_limit"], 512)

        # Check synchronized legacy PreviewMacOS settings
        self.assertFalse(self.legacy_settings.value("check_updates_on_startup", True, type=bool))
        self.assertEqual(self.legacy_settings.value("appearance_mode", "dark", type=str), "light")
        dlg.close()

    def test_03_legacy_settings_migration(self):
        """Verifies seamless migration from existing PreviewMacOS configuration."""
        # Pre-seed legacy settings
        self.legacy_settings.setValue("check_updates_on_startup", False)
        self.legacy_settings.setValue("appearance_mode", "light")
        self.legacy_settings.setValue("recent_files", ["/tmp/test.png"])

        loaded = StudioSettingsManager.load_all()
        self.assertFalse(loaded["auto_check_updates"])
        self.assertEqual(loaded["theme"], "Light")

        # Verify migrated value is now saved in Studio settings
        self.assertFalse(self.studio_settings.value("auto_check_updates", True, type=bool))
        self.assertEqual(self.studio_settings.value("recent_files", [], type=list), ["/tmp/test.png"])

    def test_04_reset_to_defaults(self):
        """Verifies the Reset Defaults button restores factory configuration."""
        dlg = SettingsDialog()

        # Mutate controls
        dlg.combo_startup_mode.setCurrentText("Edit")
        dlg.spin_pen_width.setValue(12.0)
        dlg.chk_auto_updates.setChecked(False)

        # Reset
        dlg._on_reset_defaults()

        # Verify UI controls reflect defaults
        self.assertEqual(dlg.combo_startup_mode.currentText(), DEFAULT_STUDIO_SETTINGS["startup_mode"])
        self.assertEqual(dlg.spin_pen_width.value(), DEFAULT_STUDIO_SETTINGS["default_pen_width"])
        self.assertEqual(dlg.chk_auto_updates.isChecked(), DEFAULT_STUDIO_SETTINGS["auto_check_updates"])
        dlg.close()

    def test_05_shortcuts_filtering(self):
        """Verifies interactive search filter on the keybindings table."""
        dlg = SettingsDialog()
        table = dlg.shortcuts_table

        # Initially all rows visible
        visible_initial = sum(1 for row in range(table.rowCount()) if not table.isRowHidden(row))
        self.assertEqual(visible_initial, table.rowCount())

        # Filter by 'Loupe'
        dlg.shortcut_filter.setText("Loupe")
        visible_filtered = sum(1 for row in range(table.rowCount()) if not table.isRowHidden(row))
        self.assertGreater(visible_filtered, 0)
        self.assertLess(visible_filtered, visible_initial)

        # Clear filter
        dlg.shortcut_filter.setText("")
        visible_cleared = sum(1 for row in range(table.rowCount()) if not table.isRowHidden(row))
        self.assertEqual(visible_cleared, visible_initial)
        dlg.close()

    def test_06_cache_purge_maintenance(self):
        """Verifies memory cache purge trigger updates maintenance status."""
        dlg = SettingsDialog()
        self.assertEqual(dlg.lbl_cache_status.text(), "Memory Cache: Ready")
        dlg.btn_purge_cache.click()
        self.assertIn("freed successfully", dlg.lbl_cache_status.text())
        dlg.close()


class TestStudioWindowControlsAndHeader(unittest.TestCase):
    """Validates the modern Studio titlebar controls, dirty state, and header integration."""

    @classmethod
    def setUpClass(cls):
        # Create a sample test image
        import tempfile
        from PIL import Image
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_img = os.path.join(cls.temp_dir, "studio_test.png")
        img = Image.new("RGBA", (400, 300), (45, 45, 55, 255))
        img.save(cls.test_img)

    def test_07_window_controls_right_side_integration(self):
        """Verifies window controls are placed on the right side and have modern controls."""
        win = MacMainWindow(initial_file=self.test_img)
        self.assertTrue(hasattr(win, "window_controls"))
        wc = win.window_controls
        self.assertIsInstance(wc, StudioWindowControls)

        # Backward compatibility alias
        self.assertIs(win.traffic_cluster, wc)

        # Check buttons
        self.assertIsNotNone(wc.btn_min)
        self.assertIsNotNone(wc.btn_max)
        self.assertIsNotNone(wc.btn_close)

        self.assertEqual(wc.btn_min.objectName(), "windowMinBtn")
        self.assertEqual(wc.btn_max.objectName(), "windowMaxBtn")
        self.assertEqual(wc.btn_close.objectName(), "windowCloseBtn")

        # Verify button sizing
        self.assertGreater(wc.btn_min.width(), 0)
        self.assertGreater(wc.btn_max.width(), 0)
        self.assertGreater(wc.btn_close.width(), 0)


        # Verify placement: window controls in top-right menubar corner, settings after sidebar in toolbar
        layout = win.toolbar_widget.layout()
        idx_settings = layout.indexOf(win.settings_btn)
        idx_sidebar = layout.indexOf(win.sidebar_btn)

        # Sidebar is on the left (first control)
        self.assertEqual(idx_sidebar, 0)
        # Settings is placed towards the end (right side)
        self.assertGreater(idx_settings, idx_sidebar)
        # Window controls sit in the top-right corner of the menubar
        self.assertIs(win.top_menubar.cornerWidget(Qt.Corner.TopRightCorner), wc)

        win.close()

    def test_08_close_button_dirty_indicator(self):
        """Verifies StudioCloseButton dirty dot modification state."""
        win = MacMainWindow(initial_file=self.test_img)
        wc = win.window_controls

        self.assertFalse(wc.btn_close._modified)
        self.assertFalse(win.traffic_cluster.btn_close._modified)

        # Set modified
        win.set_modified(True)
        self.assertTrue(wc.btn_close._modified)
        self.assertTrue(win.traffic_cluster.btn_close._modified)

        # Clear modified
        win.set_modified(False)
        self.assertFalse(wc.btn_close._modified)
        self.assertFalse(win.traffic_cluster.btn_close._modified)

        win.close()

    def test_09_settings_gear_button_and_shortcut(self):
        """Verifies settings gear button and Preferences action open SettingsDialog."""
        win = MacMainWindow(initial_file=self.test_img)
        self.assertTrue(hasattr(win, "settings_btn"))
        self.assertEqual(win.settings_btn.objectName(), "settingsBtn")
        self.assertFalse(win.settings_btn.icon().isNull())

        # Check shortcut Ctrl+, is wired
        found_shortcut = False
        for act in win.findChildren(QApplication.instance().allWidgets()[0].__class__):
            pass
        # Check action in menu
        menu_actions = win.logo_menu.actions()
        for act in menu_actions:
            if act.shortcut() == QKeySequence("Ctrl+,"):
                found_shortcut = True
                self.assertEqual(act.text(), "Preferences...")
                break
        self.assertTrue(found_shortcut, "Preferences (Ctrl+,) action not found in logo menu")

        win.close()

    def test_10_maximize_restore_toggle(self):
        """Verifies window maximization and icon toggling."""
        win = MacMainWindow(initial_file=self.test_img)
        wc = win.window_controls

        self.assertFalse(win.isMaximized())
        self.assertFalse(wc.btn_max.icon().isNull())

        # Toggle maximize
        win._toggle_maximize()
        self.assertTrue(win.isMaximized())
        self.assertFalse(wc.btn_max.icon().isNull())

        # Restore
        win._toggle_maximize()
        self.assertFalse(win.isMaximized())

        win.close()


class TestStudioActionRibbonAndInspector(unittest.TestCase):
    """Validates realistic physical tool icons and smooth Inspector panel toggling."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from PIL import Image
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_img = os.path.join(cls.temp_dir, "ribbon_test.png")
        img = Image.new("RGBA", (500, 400), (20, 20, 25, 255))
        img.save(cls.test_img)

    def test_11_physical_tool_icons_wiring(self):
        """Verifies the 5 realistic physical tool icons are wired up on the action ribbon."""
        win = MacMainWindow(initial_file=self.test_img)
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # 1. Chisel Highlighter
        self.assertIsNotNone(mb.highlighter_btn)
        self.assertFalse(mb.highlighter_btn.icon().isNull())

        # 2. Fountain Pen
        self.assertIsNotNone(mb.pen_btn)
        self.assertFalse(mb.pen_btn.icon().isNull())

        # 3. Rubber Stamp
        self.assertIsNotNone(mb.sign_btn)
        self.assertFalse(mb.sign_btn.icon().isNull())
        self.assertTrue(hasattr(mb, "stamp_btn"))
        self.assertFalse(mb.stamp_btn.icon().isNull())

        # 4. Crop Shears
        self.assertIsNotNone(mb.crop_btn)
        self.assertFalse(mb.crop_btn.icon().isNull())

        # 5. Magnifying Loupe (in Shapes dropdown menu)
        loupe_actions = [a for a in mb.shapes_btn.menu().actions() if a.data() == "loupe"]
        self.assertEqual(len(loupe_actions), 1)
        self.assertFalse(loupe_actions[0].icon().isNull())

        win.close()

    def test_12_inspector_panel_toggle_and_shortcut(self):
        """Verifies right-side Inspector panel toggles smoothly via button and shortcut."""
        win = MacMainWindow(initial_file=self.test_img)
        win.show()

        # Initially hidden
        self.assertFalse(win.inspector_panel.isVisible())
        self.assertFalse(win.inspector_btn.isChecked())

        # Toggle on via set_inspector_visible / header button
        win.set_inspector_visible(True, animated=False)
        self.assertTrue(win.inspector_panel.isVisible())
        self.assertTrue(win.inspector_btn.isChecked())

        # Toggle off
        win.set_inspector_visible(False, animated=False)
        self.assertFalse(win.inspector_panel.isVisible())
        self.assertFalse(win.inspector_btn.isChecked())

        # Check view menu action has Ctrl+I shortcut
        view_actions = win.view_menu.actions()
        insp_act = next((a for a in view_actions if "Inspector" in a.text()), None)
        self.assertIsNotNone(insp_act)
        shortcuts = insp_act.shortcuts()
        shortcut_strings = [s.toString() for s in shortcuts]
        self.assertTrue("Ctrl+I" in shortcut_strings or "Ctrl+I" == insp_act.shortcut().toString())

        win.close()

    def test_13_toolbar_responsiveness(self):
        """Verifies toolbar handles narrow and wide windows cleanly without overflow crashes."""
        win = MacMainWindow(initial_file=self.test_img)
        win.show()
        win.set_workspace_mode("Edit")

        # Wide width (1200px)
        win.resize(1200, 700)
        win.markup_bar.handle_resize(1200)
        self.assertTrue(win.markup_bar.group_image.isVisible())

        # Compact width (750px)
        win.resize(750, 700)
        win.markup_bar.handle_resize(750)
        self.assertFalse(win.markup_bar.group_image.isVisible())
        self.assertTrue(win.markup_bar.overflow_btn.isVisible())

        win.close()

    def test_14_sidebar_and_tabbar_minimum_size_and_thumbnail_selection(self):
        """Verifies window does not expand or lock minimum width when clicking thumbnails or switching tabs."""
        win = MacMainWindow(initial_file=self.test_img)
        win.show()

        # Check constrained minimum size hints
        self.assertLessEqual(win.minimumSizeHint().width(), 500)
        self.assertLessEqual(win.tab_container.minimumSizeHint().width(), 150)
        self.assertLessEqual(win.sidebar.minimumSizeHint().width(), 160)

        # Resizing to a compact 700x500 window should work smoothly
        win.resize(700, 500)
        self.assertLessEqual(win.width(), 750)

        # Add second tab and switch
        win.new_tab(self.test_img)
        self.assertEqual(win.tab_container.tab_bar.count(), 2)
        self.assertLessEqual(win.minimumSizeHint().width(), 500)

        # Selecting thumbnails should not inflate window width
        win.sidebar.thumb_list.setCurrentRow(0)
        self.assertLessEqual(win.width(), 750)

        # Switch to Contact Sheet mode
        win.sidebar.set_view_mode("Contact Sheet")
        self.assertLessEqual(win.width(), 750)

        # Segmented header control must never overflow sidebar width even at minimum width
        win.sidebar.resize(140, 500)
        QApplication.processEvents()
        self.assertLessEqual(win.sidebar.seg_control.width(), win.sidebar.width())

        win.close()


if __name__ == "__main__":
    unittest.main()
