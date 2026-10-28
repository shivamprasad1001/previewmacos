"""
Test Suite for Preview for Linux Redesign:
- Workspace Modes (View, Edit, Organize)
- Two-Tier Markup Toolbar & Dynamic Context Formatting Bar
- Pro Inspector Panel (Properties, Layers, Adjustments)
- Organize Action Bar & Document Management
- Responsive Window Behavior & Prototypeless Integration
"""

import os
import unittest
import tempfile
import pymupdf
from PIL import Image

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize
from PyQt6.QtGui import QColor, QResizeEvent

from preview.ui.main_window import MacMainWindow
from preview.core.document import Document
from preview.core.annotations import AnnotationItem, AnnotationType

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestRedesignWorkspaceAndModes(unittest.TestCase):

    def setUp(self):
        # Create a sample multi-page PDF for testing
        self.tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.pdf_path = self.tmp_pdf.name
        self.tmp_pdf.close()

        doc = pymupdf.open()
        for i in range(3):
            page = doc.new_page(width=612, height=792)
            page.insert_text(pymupdf.Point(72, 72), f"Page {i + 1} Content")
        doc.save(self.pdf_path)
        doc.close()

        # Create a sample image for testing
        self.tmp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        self.img_path = self.tmp_img.name
        self.tmp_img.close()
        img = Image.new("RGB", (300, 200), color=(50, 120, 200))
        img.save(self.img_path)

    def tearDown(self):
        for p in [self.pdf_path, self.img_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def test_01_workspace_mode_transitions(self):
        """Verifies clean switching between View, Edit, and Organize workspace modes."""
        win = MacMainWindow(initial_file=self.pdf_path)
        win.show()

        # 1. Mode A: View mode by default
        self.assertEqual(win.current_workspace_mode, "View")
        self.assertTrue(win.markup_bar.isHidden())
        self.assertTrue(win.organize_bar.isHidden())
        self.assertTrue(win.inspector_panel.isHidden())
        self.assertFalse(win.canvas.markup_enabled)
        self.assertTrue(win.mode_view_btn.isChecked())
        self.assertFalse(win.mode_edit_btn.isChecked())
        self.assertFalse(win.mode_organize_btn.isChecked())

        # 2. Mode B: Edit mode
        win.set_workspace_mode("Edit")
        self.assertEqual(win.current_workspace_mode, "Edit")
        self.assertFalse(win.markup_bar.isHidden())
        self.assertTrue(win.organize_bar.isHidden())
        self.assertFalse(win.inspector_panel.isHidden())
        self.assertTrue(win.canvas.markup_enabled)
        self.assertTrue(win.markup_toggle_btn.isChecked())
        self.assertTrue(win.mode_edit_btn.isChecked())
        self.assertFalse(win.mode_view_btn.isChecked())
        self.assertFalse(win.mode_organize_btn.isChecked())

        # 3. Mode C: Organize mode
        win.set_workspace_mode("Organize")
        self.assertEqual(win.current_workspace_mode, "Organize")
        self.assertTrue(win.markup_bar.isHidden())
        self.assertFalse(win.organize_bar.isHidden())
        self.assertTrue(win.inspector_panel.isHidden())
        self.assertFalse(win.canvas.markup_enabled)
        self.assertTrue(win.mode_organize_btn.isChecked())
        self.assertFalse(win.mode_edit_btn.isChecked())
        self.assertFalse(win.mode_view_btn.isChecked())

        # 4. Return to View mode
        win.set_workspace_mode("View")
        self.assertEqual(win.current_workspace_mode, "View")
        self.assertTrue(win.markup_bar.isHidden())
        self.assertTrue(win.organize_bar.isHidden())
        self.assertTrue(win.inspector_panel.isHidden())
        self.assertFalse(win.canvas.markup_enabled)
        self.assertTrue(win.mode_view_btn.isChecked())

        win.close()

    def test_02_context_aware_formatting_bar(self):
        """Verifies that the 2-tier markup toolbar dynamically updates its context formatting row."""
        win = MacMainWindow(initial_file=self.pdf_path)
        win.show()
        win.set_workspace_mode("Edit")
        mb = win.markup_bar

        # Tier 1 tools exist and are grouped
        self.assertIsNotNone(mb.select_btn)
        self.assertIsNotNone(mb.hand_btn)
        self.assertIsNotNone(mb.text_btn)
        self.assertIsNotNone(mb.pen_btn)
        self.assertIsNotNone(mb.highlighter_btn)
        self.assertIsNotNone(mb.underline_btn)
        self.assertIsNotNone(mb.strikethrough_btn)
        self.assertIsNotNone(mb.redact_btn)
        self.assertIsNotNone(mb.sign_btn)
        self.assertIsNotNone(mb.shapes_btn)

        # Dynamic context bar exists
        self.assertIsNotNone(mb.context_bar)

        # 1. Select Pen -> Shape format row active (index 0)
        mb.pen_btn.click()
        self.assertEqual(mb.context_stack.currentIndex(), 0)  # Shape formatting

        # 2. Select Text -> Text typography format row active (index 1)
        mb.text_btn.click()
        self.assertEqual(mb.context_stack.currentIndex(), 1)  # Text formatting

        # 3. Select Redact -> Redaction warning format row active (index 3)
        mb.redact_btn.click()
        self.assertEqual(mb.context_stack.currentIndex(), 3)  # Redaction pending

        # 4. Context bar with selected shape annotation
        shape_annot = AnnotationItem(AnnotationType.RECTANGLE)
        shape_annot.points = [QPointF(20, 20), QPointF(100, 80)]
        shape_annot.stroke_color = QColor("#007aff")
        shape_annot.stroke_width = 2.5
        shape_annot.fill_color = QColor(0, 0, 0, 0)
        win.canvas.selected_annotation = shape_annot
        mb.set_selected_annotation(shape_annot)
        self.assertEqual(mb.context_stack.currentIndex(), 0)

        # 5. Context bar with selected text annotation
        text_annot = AnnotationItem(AnnotationType.TEXT)
        text_annot.rect = QRectF(50, 50, 150, 40)
        text_annot.text = "Hello Context"
        text_annot.font_family = "Inter"
        text_annot.font_size = 16
        text_annot.stroke_color = QColor("#ff3b30")
        win.canvas.selected_annotation = text_annot
        mb.set_selected_annotation(text_annot)
        self.assertEqual(mb.context_stack.currentIndex(), 1)
        self.assertEqual(mb.font_spin.value(), 16)

        win.close()

    def test_03_mac_inspector_panel_properties_and_layers(self):
        """Verifies Inspector panel's 3 tabs (Properties, Layers, Adjust), metadata card, and live annotation editing."""
        win = MacMainWindow(initial_file=self.pdf_path)
        win.show()
        win.set_inspector_visible(True)
        insp = win.inspector_panel

        self.assertFalse(insp.isHidden())
        self.assertEqual(insp.width(), 280)
        self.assertEqual(insp.stack.count(), 3)

        # Tab 0: Document metadata overview when nothing is selected
        insp.set_active_tab(0)
        self.assertIsNone(insp.selected_annotation)
        # Tab 1: Layers / Annotations list
        insp.set_active_tab(1)
        self.assertEqual(insp.stack.currentIndex(), 1)

        # Add an annotation to active page
        annot = AnnotationItem(AnnotationType.RECTANGLE)
        annot.points = [QPointF(10, 10), QPointF(120, 90)]
        annot.stroke_color = QColor("#34c759")
        annot.stroke_width = 3.0
        annot.fill_color = QColor(255, 255, 0, 100)

        win.canvas.annotations.setdefault(win.canvas.current_page, []).append(annot)
        win.canvas.selected_annotation = annot
        insp.set_selected_annotation(annot)

        # Tab 0 now shows live Annotation Properties
        insp.set_active_tab(0)
        self.assertIsNotNone(insp.style_card)
        self.assertFalse(insp.style_card.isHidden())

        # Test live property changes
        insp.width_spin.setValue(5.0)
        self.assertEqual(annot.stroke_width, 5.0)

        # Delete annotation via inspector
        insp.annot_del_btn.click()
        self.assertNotIn(annot, win.canvas.annotations.get(win.canvas.current_page, []))

        # Close button collapses inspector
        insp.close_btn.click()
        self.assertTrue(insp.isHidden())

        win.close()

    def test_04_organize_action_bar_integration(self):
        """Verifies that the Organize mode action bar is connected to actual document and page operations."""
        win = MacMainWindow(initial_file=self.pdf_path)
        win.show()
        win.set_workspace_mode("Organize")
        bar = win.organize_bar

        self.assertFalse(bar.isHidden())
        self.assertIsNotNone(bar.rot_left_btn)
        self.assertIsNotNone(bar.rot_right_btn)
        self.assertIsNotNone(bar.dup_btn)
        self.assertIsNotNone(bar.insert_blank_btn)
        self.assertIsNotNone(bar.del_btn)
        self.assertIsNotNone(bar.merge_btn)
        self.assertIsNotNone(bar.split_btn)
        self.assertIsNotNone(bar.export_btn)

        # Rotate action rotates active page in document
        initial_rot = win.document.rotations.get(win.canvas.current_page, 0)
        bar.rot_right_btn.click()
        self.assertEqual(win.document.rotations.get(win.canvas.current_page, 0), (initial_rot + 90) % 360)

        # Duplicate page duplicates active page
        initial_count = win.document.page_count
        bar.dup_btn.click()
        self.assertEqual(win.document.page_count, initial_count + 1)

        # Insert blank page
        bar.insert_blank_btn.click()
        self.assertEqual(win.document.page_count, initial_count + 2)

        win.close()

    def test_05_responsive_inspector_auto_collapse(self):
        """Verifies that the inspector automatically collapses on narrow display viewports to prevent UI overlap."""
        win = MacMainWindow(initial_file=self.pdf_path)
        win.show()
        win.resize(1150, 780)
        win.set_inspector_visible(True)
        self.assertFalse(win.inspector_panel.isHidden())

        # Send resize event for narrow window (< 860px)
        evt = QResizeEvent(QSize(780, 700), QSize(1150, 780))
        win.resizeEvent(evt)
        self.assertTrue(win.inspector_panel.isHidden())
        self.assertFalse(win.inspector_btn.isChecked())

        win.close()

    def test_06_image_color_adjustment_tab_in_inspector(self):
        """Verifies that the Adjust tab in the inspector displays live histogram and color controls for image files."""
        win = MacMainWindow(initial_file=self.img_path)
        win.show()
        win.set_inspector_visible(True)
        insp = win.inspector_panel

        insp.set_active_tab(2)
        self.assertEqual(insp.stack.currentIndex(), 2)
        self.assertIsNotNone(insp.hist_widget)
        self.assertIn("exposure", insp.sliders)
        self.assertIn("contrast", insp.sliders)
        self.assertIn("saturation", insp.sliders)

        # Change exposure
        insp.sliders["exposure"].setValue(15)
        # Document image was updated
        self.assertIsNotNone(win.document._pil_image)

        # Reset button restores original image
        insp.reset_btn.click()
        self.assertEqual(insp.sliders["exposure"].value(), 0)

        win.close()


if __name__ == "__main__":
    unittest.main()
