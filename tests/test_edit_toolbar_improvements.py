"""
Unit and integration tests for the improved Edit toolbar in Preview for Linux:
- Logical grouping into segmented pill containers
- Consistent button dimensions, icons, and styling
- Subtle dividers between groups
- Responsive overflow adaptation for small/compact window sizes (<940px)
- Contextual formatting row without text label truncation
- Signal wiring and tool switching
"""

import os
import tempfile
import unittest
from PyQt6.QtWidgets import QApplication, QFrame
from PIL import Image

from preview.core.annotations import AnnotationType
from preview.ui.main_window import MacMainWindow
from preview.theme import MacTheme


class TestEditToolbarImprovements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

        # Create temporary test image
        cls._tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.test_img_path = os.path.join(cls._tmp_dir.name, "test_edit_toolbar.png")
        img = Image.new("RGB", (600, 400), color=(120, 160, 220))
        img.save(cls.test_img_path)

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()

    def test_01_logical_tool_grouping_and_containers(self):
        """Verifies editing tools are organized into logical groups with consistent dimensions."""
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # Check that all logical group containers exist
        self.assertIsNotNone(mb.group_select)
        self.assertIsNotNone(mb.group_image)
        groups = [g for g in mb.findChildren(QFrame) if g.objectName() == "markupGroup"]
        self.assertGreaterEqual(len(groups), 7)

        # Verify consistent button sizing across all standard tools
        standard_btns = [
            mb.pointer_btn, mb.hand_btn, mb.text_btn, mb.highlighter_btn,
            mb.underline_tool_btn, mb.strikethrough_tool_btn, mb.note_btn,
            mb.pen_btn, mb.sign_btn, mb.crop_btn, mb.rotate_btn,
            mb.color_adjust_btn, mb.size_adjust_btn, mb.undo_btn, mb.redo_btn
        ]
        base_w = standard_btns[0].width()
        base_h = standard_btns[0].height()
        for btn in standard_btns:
            self.assertEqual(btn.width(), base_w)
            self.assertEqual(btn.height(), base_h)

        # Dropdown tools have room for disclosure triangle
        self.assertEqual(mb.select_btn.height(), base_h)
        self.assertEqual(mb.shapes_btn.height(), base_h)
        self.assertGreaterEqual(mb.select_btn.width(), base_w)
        self.assertGreaterEqual(mb.shapes_btn.width(), base_w)

        win.close()

    def test_02_helpful_tooltips_and_shortcuts(self):
        """Verifies every tool button has an informative tooltip with keyboard shortcuts."""
        win = MacMainWindow(initial_file=self.test_img_path)
        mb = win.markup_bar

        self.assertIn("Esc", mb.pointer_btn.toolTip())
        self.assertIn("Space", mb.hand_btn.toolTip())
        self.assertIn("Selection", mb.select_btn.toolTip())
        self.assertIn("T", mb.text_btn.toolTip())
        self.assertIn("H", mb.highlighter_btn.toolTip())
        self.assertIn("U", mb.underline_tool_btn.toolTip())
        self.assertIn("S", mb.strikethrough_tool_btn.toolTip())
        self.assertIn("N", mb.note_btn.toolTip())
        self.assertIn("P", mb.pen_btn.toolTip())
        self.assertIn("S", mb.shapes_btn.toolTip())
        self.assertIn("R", mb.redact_btn.toolTip())
        self.assertIn("K", mb.sign_btn.toolTip())
        self.assertIn("Ctrl+K", mb.crop_btn.toolTip())
        self.assertIn("Ctrl+L", mb.rotate_btn.toolTip())
        self.assertIn("Ctrl+Alt+C", mb.color_adjust_btn.toolTip())
        self.assertIn("Ctrl+Alt+S", mb.size_adjust_btn.toolTip())
        self.assertIn("Ctrl+Z", mb.undo_btn.toolTip())
        self.assertIn("Ctrl+Shift+Z", mb.redo_btn.toolTip())

        win.close()

    def test_03_responsive_overflow_adaptation(self):
        """Verifies secondary image tools collapse into overflow menu on compact window widths (<940px)."""
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # Wide window (1180px): image group visible, overflow button hidden
        win.resize(1180, 750)
        mb.handle_resize(1180)
        self.assertTrue(mb.group_image.isVisible())
        self.assertFalse(mb.overflow_btn.isVisible())

        # Narrow / compact window (780px): image group collapsed, overflow button visible
        win.resize(780, 750)
        mb.handle_resize(780)
        self.assertFalse(mb.group_image.isVisible())
        self.assertTrue(mb.overflow_btn.isVisible())

        # Check overflow menu items exist
        self.assertIsNotNone(mb.overflow_btn.menu())
        overflow_actions = mb.overflow_btn.menu().actions()
        action_texts = [a.text() for a in overflow_actions]
        self.assertIn("Crop Selection", action_texts)
        self.assertIn("Rotate Left 90°", action_texts)
        self.assertIn("Rotate Selection 90°", action_texts)
        self.assertIn("Adjust Color...", action_texts)
        self.assertIn("Adjust Size...", action_texts)

        win.close()

    def test_04_contextual_quick_actions_never_truncate(self):
        """Verifies the Tier 2 contextual action strip has proper sizing and does not truncate labels."""
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # Default context (index 4)
        mb.update_context_row()
        self.assertFalse(mb._context_views[4].isHidden())

        # Buttons have full labels
        self.assertEqual(mb.btn_adj_col.text(), "Adjust Color...")
        self.assertEqual(mb.btn_adj_sz.text(), "Adjust Size...")
        self.assertEqual(mb.btn_rot.text(), "Rotate Left 90°")

        # Buttons have valid icons
        self.assertFalse(mb.btn_adj_col.icon().isNull())
        self.assertFalse(mb.btn_adj_sz.icon().isNull())
        self.assertFalse(mb.btn_rot.icon().isNull())

        win.close()

    def test_05_all_toolbar_action_signal_dispatches(self):
        """Verifies every toolbar action triggers the proper signals and canvas modifications."""
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # Pen tool
        mb.pen_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.PEN)
        self.assertFalse(mb._context_views[0].isHidden())

        # Text tool
        mb.text_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.TEXT)
        self.assertFalse(mb._context_views[1].isHidden())

        # Redact tool
        mb.redact_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.REDACT)
        self.assertFalse(mb._context_views[3].isHidden())

        # Pointer tool / Esc
        mb.pointer_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.NONE)
        self.assertFalse(mb._context_views[4].isHidden())

        win.close()

    def test_06_theme_switching_preserves_toolbar_integrity(self):
        """Verifies switching between Dark and Light themes updates toolbar styling without error."""
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win.set_workspace_mode("Edit")

        # Light theme
        win._apply_theme(MacTheme.LIGHT, animate=False)
        self.assertEqual(win.current_theme, MacTheme.LIGHT)
        self.assertIsNotNone(win.markup_bar.pointer_btn.icon())

        # Dark theme
        win._apply_theme(MacTheme.DARK, animate=False)
        self.assertEqual(win.current_theme, MacTheme.DARK)
        self.assertIsNotNone(win.markup_bar.pointer_btn.icon())

        win.close()


if __name__ == "__main__":
    unittest.main()
