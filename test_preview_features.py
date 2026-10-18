"""
Comprehensive verification test suite for Preview macOS Linux clone.
Validates parity with macOS Preview functionality.
"""

import sys
import os
import unittest

# Ensure path is included
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import QPointF, QRectF

# Initialize Qt App in offscreen mode
os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QApplication(sys.argv)

from preview.core.document import Document
from preview.core.annotations import AnnotationItem, AnnotationType
from preview.core.color_adjust import ColorAdjustEngine
from preview.core.history import HistoryManager, ActionCommand
from preview.ui.main_window import MacMainWindow
from preview.ui.about_dialog import AboutDialog

class TestPreviewParity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create temporary test image
        cls.test_img_path = "/tmp/test_preview_photo.png"
        img = Image.new("RGBA", (800, 600), color=(100, 150, 200, 255))
        img.save(cls.test_img_path)

        # Path to sample PDF in user downloads if available
        cls.sample_pdf = os.path.expanduser("~/Downloads/Invoice.pdf")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_img_path):
            os.remove(cls.test_img_path)

    def test_01_image_loading_and_metadata(self):
        doc = Document(self.test_img_path)
        self.assertFalse(doc.is_pdf)
        self.assertEqual(doc.page_count, 1)
        w, h = doc.get_page_size(0)
        self.assertEqual((w, h), (800.0, 600.0))
        self.assertIn("dimensions", doc.metadata)

    def test_02_pdf_loading_and_search(self):
        if os.path.exists(self.sample_pdf):
            doc = Document(self.sample_pdf)
            self.assertTrue(doc.is_pdf)
            self.assertGreaterEqual(doc.page_count, 1)
            # Test search
            results = doc.search_text("Invoice")
            self.assertIsInstance(results, list)
            # Test thumbnail caching
            thumb = doc.get_thumbnail(0, width=120)
            self.assertFalse(thumb.isNull())

    def test_03_page_rotation(self):
        doc = Document(self.test_img_path)
        doc.rotate_page(0, 90)
        w, h = doc.get_page_size(0)
        self.assertEqual((w, h), (600.0, 800.0))
        doc.rotate_page(0, -90)
        w, h = doc.get_page_size(0)
        self.assertEqual((w, h), (800.0, 600.0))

    def test_04_annotations_model(self):
        pen = AnnotationItem(AnnotationType.PEN)
        pen.points = [QPointF(10, 10), QPointF(50, 50)]
        self.assertTrue(pen.contains_point(QPointF(30, 30)))

        rect = AnnotationItem(AnnotationType.RECTANGLE)
        rect.rect = QRectF(100, 100, 200, 150)
        self.assertTrue(rect.contains_point(QPointF(150, 150)))

        # Verify drawing with selection and zoom doesn't raise TypeError
        from PyQt6.QtGui import QPainter, QPixmap
        pix = QPixmap(300, 300)
        p = QPainter(pix)
        rect.is_selected = True
        rect.draw(p, zoom=1.5)
        p.end()

    def test_05_color_adjust_engine(self):
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        
        # Test adjustments
        adj = ColorAdjustEngine.adjust(img, exposure=0.5, contrast=0.2, saturation=0.3, temperature=0.2, tint=0.1)
        self.assertEqual(adj.size, img.size)

        # Test Auto Levels
        auto_img = ColorAdjustEngine.auto_levels(img)
        self.assertEqual(auto_img.size, img.size)

        # Test Histogram
        r, g, b = ColorAdjustEngine.get_histogram(img)
        self.assertEqual(len(r), 256)
        self.assertEqual(len(g), 256)
        self.assertEqual(len(b), 256)

    def test_06_history_undo_redo(self):
        hist = HistoryManager()
        val = [0]
        cmd = ActionCommand("Add", lambda: val.clear(), lambda: val.append(1))
        hist.push(cmd)
        self.assertTrue(hist.can_undo)
        hist.undo()
        self.assertEqual(val, [])
        self.assertTrue(hist.can_redo)
        hist.redo()
        self.assertEqual(val, [1])

    def test_07_about_dialog_attribution(self):
        about = AboutDialog()
        # Verify developer and powered by mentions
        found_developer = False
        found_trivilabs = False
        for child in about.findChildren(object):
            text = getattr(child, "text", lambda: "")()
            if "Shivam Prasad" in text:
                found_developer = True
            if "TriviLabs.in" in text or "trivilabs.in" in text:
                found_trivilabs = True
        self.assertTrue(found_developer, "Developer 'Shivam Prasad' must be present in About dialog")
        self.assertTrue(found_trivilabs, "Powered by 'TriviLabs.in' must be present in About dialog")

    def test_08_main_window_layout_and_toolbar_height(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        self.assertEqual(win.toolbar_widget.height(), 52)
        self.assertFalse(win.toolbar_widget.height() > 60)
        self.assertEqual(win.sidebar.thumb_list.count(), 1)
        win.close()

    def test_09_folder_and_multi_image_loading(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 3 images
            p1 = os.path.join(tmpdir, "img1.png")
            p2 = os.path.join(tmpdir, "img2.jpg")
            p3 = os.path.join(tmpdir, "img10.png")
            Image.new("RGB", (100, 100), "red").save(p1)
            Image.new("RGB", (100, 100), "green").save(p2)
            Image.new("RGB", (100, 100), "blue").save(p3)

            doc = Document()
            self.assertTrue(doc.load_folder(tmpdir))
            self.assertEqual(doc.page_count, 3)
            self.assertIn("img1.png", doc.image_paths[0])
            self.assertIn("img2.jpg", doc.image_paths[1])
            self.assertIn("img10.png", doc.image_paths[2])

            win = MacMainWindow(initial_target=tmpdir)
            self.assertEqual(win.document.page_count, 3)
            self.assertEqual(win.sidebar.thumb_list.count(), 3)
            win.next_page()
            self.assertEqual(win.canvas.current_page, 1)
            win.prev_page()
            self.assertEqual(win.canvas.current_page, 0)
            win.close()

    def test_10_markup_tool_selection_and_deselection(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        win._toggle_markup_bar()
        self.assertFalse(win.markup_bar.isHidden())

        # Select Pen tool
        win.markup_bar.pen_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.PEN)
        self.assertTrue(win.markup_bar.pen_btn.isChecked())

        # Click Pen again -> should DESELECT to NONE / pointer
        win.markup_bar.pen_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.NONE)
        self.assertFalse(win.markup_bar.pen_btn.isChecked())
        self.assertTrue(win.markup_bar.pointer_btn.isChecked())

        # Select Highlighter, then click Pointer button
        win.markup_bar.highlighter_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.HIGHLIGHTER)
        win.markup_bar.pointer_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.NONE)

        # Select Pen, then hide markup bar -> should unselect automatically
        win.markup_bar.pen_btn.click()
        self.assertEqual(win.canvas.active_tool, AnnotationType.PEN)
        win._toggle_markup_bar()
        self.assertFalse(win.markup_bar.isVisible())
        self.assertEqual(win.canvas.active_tool, AnnotationType.NONE)
        win.close()

    def test_11_undo_redo_annotation_and_drag(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        canvas = win.canvas
        initial_count = len(canvas._get_current_annotations())

        item = AnnotationItem(AnnotationType.RECTANGLE)
        item.rect = QRectF(50, 50, 100, 100)
        canvas._get_current_annotations().append(item)
        canvas._push_add_command(item, 0)

        self.assertEqual(len(canvas._get_current_annotations()), initial_count + 1)
        self.assertTrue(canvas.history.can_undo)

        # Undo addition
        canvas.undo()
        self.assertEqual(len(canvas._get_current_annotations()), initial_count)
        self.assertTrue(canvas.history.can_redo)

        # Redo addition
        canvas.redo()
        self.assertEqual(len(canvas._get_current_annotations()), initial_count + 1)
        win.close()

    def test_12_theme_colors(self):
        from preview.theme import MacTheme
        self.assertEqual(MacTheme.LIGHT_BG_CANVAS, "#ececf0")
        self.assertNotEqual(MacTheme.LIGHT_BG_CANVAS, "#525257")
        qss_light = MacTheme.get_stylesheet(MacTheme.LIGHT)
        self.assertIn("#ececf0", qss_light)

if __name__ == "__main__":
    unittest.main()
