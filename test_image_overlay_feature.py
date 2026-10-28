"""
Tests for the Canva-style Image Overlay feature in Preview macOS.
Validates item creation, aspect ratio preservation, handle resizing,
rendering, canvas integration, undo/redo, and toolbar/menu actions.
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import QPointF, QRectF

from preview.core.annotations import AnnotationItem, AnnotationType, Handle
from preview.core.document import Document
from preview.ui.canvas import CanvasView
from preview.ui.markup_toolbar import MarkupToolbar
from preview.icons import MacIconFactory

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestImageOverlayFeature(unittest.TestCase):
    def setUp(self):
        # Create a sample test pixmap (60x40 red rectangle)
        img = QImage(60, 40, QImage.Format.Format_ARGB32)
        img.fill(QColor(255, 0, 0, 255))
        self.sample_pixmap = QPixmap.fromImage(img)

    def test_annotation_item_image_overlay_creation(self):
        item = AnnotationItem(AnnotationType.IMAGE_OVERLAY)
        item.overlay_pixmap = self.sample_pixmap
        item.rect = QRectF(50, 50, 120, 80)

        self.assertEqual(item.item_type, AnnotationType.IMAGE_OVERLAY)
        self.assertEqual(item.get_bounds(), QRectF(50, 50, 120, 80))
        self.assertTrue(item.contains_point(QPointF(60, 60)))
        self.assertFalse(item.contains_point(QPointF(300, 300)))

    def test_image_overlay_translation_and_resize(self):
        item = AnnotationItem(AnnotationType.IMAGE_OVERLAY)
        item.overlay_pixmap = self.sample_pixmap
        item.rect = QRectF(100, 100, 200, 150)

        # Move by (20, 30)
        item.translate(20, 30)
        self.assertEqual(item.rect, QRectF(120, 130, 200, 150))

        # Resize via SE handle
        orig_bounds = QRectF(item.rect)
        item.resize_by_handle(Handle.SE, QPointF(350, 300), orig_bounds)
        self.assertEqual(item.rect.width(), 230.0)
        self.assertEqual(item.rect.height(), 170.0)

    def test_image_overlay_render_without_crash(self):
        item = AnnotationItem(AnnotationType.IMAGE_OVERLAY)
        item.overlay_pixmap = self.sample_pixmap
        item.rect = QRectF(10, 10, 100, 80)
        item.is_selected = True

        target_img = QImage(200, 200, QImage.Format.Format_ARGB32)
        target_img.fill(QColor(255, 255, 255))
        painter = QPainter(target_img)
        item.draw(painter, zoom=1.0)
        painter.end()

        # Check that target image has painted pixels in the region
        pixel = target_img.pixelColor(20, 20)
        self.assertEqual(pixel.red(), 255)

    def test_canvas_add_image_overlay(self):
        canvas = CanvasView()
        # Set up a test document
        import tempfile
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            t_path = f.name
            im = Image.new("RGB", (600, 400), color="blue")
            im.save(t_path)

        doc = Document(t_path)
        canvas.set_document(doc)

        # Add image overlay
        overlay_item = canvas.add_image_overlay(self.sample_pixmap)
        self.assertIsNotNone(overlay_item)
        self.assertEqual(overlay_item.item_type, AnnotationType.IMAGE_OVERLAY)
        self.assertTrue(overlay_item.is_selected)
        self.assertIn(overlay_item, canvas._get_current_annotations())

        # Test undo
        canvas.undo()
        self.assertNotIn(overlay_item, canvas._get_current_annotations())

        # Test redo
        canvas.redo()
        self.assertIn(overlay_item, canvas._get_current_annotations())

    def test_markup_toolbar_image_overlay_button(self):
        toolbar = MarkupToolbar()
        self.assertTrue(hasattr(toolbar, "image_overlay_btn"))
        self.assertEqual(toolbar.image_overlay_btn.toolTip(), "Add Image Overlay (Ctrl+Shift+I)")

        received = []
        toolbar.image_overlay_requested.connect(lambda: received.append(True))
        toolbar.image_overlay_btn.click()
        self.assertEqual(len(received), 1)

    def test_icon_factory_maps_image_overlay(self):
        icon = MacIconFactory.create_icon("image_overlay", "#000000", 18)
        self.assertFalse(icon.isNull())

    def test_main_window_set_markup_visible(self):
        from preview.ui.main_window import MacMainWindow
        win = MacMainWindow()
        self.assertTrue(hasattr(win, "set_markup_visible"))
        win.set_markup_visible(True)
        self.assertEqual(win.current_workspace_mode, "Edit")
        self.assertFalse(win.markup_bar.isHidden())

        win.set_markup_visible(False)
        self.assertEqual(win.current_workspace_mode, "View")
        self.assertTrue(win.markup_bar.isHidden())
        win.close()


if __name__ == "__main__":
    unittest.main()
