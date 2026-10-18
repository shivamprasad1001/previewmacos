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
from PyQt6.QtWidgets import QApplication, QLabel
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
        from preview import __version__
        about = AboutDialog()
        # Verify developer, powered by mentions, and dynamic version
        found_developer = False
        found_trivilabs = False
        found_version = False
        for child in about.findChildren(object):
            text = getattr(child, "text", lambda: "")()
            if "Shivam Prasad" in text:
                found_developer = True
            if "TriviLabs.in" in text or "trivilabs.in" in text:
                found_trivilabs = True
            if f"Version {__version__}" in text:
                found_version = True
        self.assertTrue(found_developer, "Developer 'Shivam Prasad' must be present in About dialog")
        self.assertTrue(found_trivilabs, "Powered by 'TriviLabs.in' must be present in About dialog")
        self.assertTrue(found_version, f"Version {__version__} must be present in About dialog")

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

    def test_13_pdf_and_image_page_deletion(self):
        import tempfile
        # Test image collection page deletion
        tf1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf1.close()
        tf2.close()
        Image.new("RGB", (100, 100), "red").save(tf1.name)
        Image.new("RGB", (100, 100), "blue").save(tf2.name)

        doc = Document([tf1.name, tf2.name])
        self.assertEqual(doc.page_count, 2)
        # Delete first page
        success = doc.delete_page(0)
        self.assertTrue(success)
        self.assertEqual(doc.page_count, 1)
        # Cannot delete the only remaining page
        fail = doc.delete_page(0)
        self.assertFalse(fail)
        self.assertEqual(doc.page_count, 1)

        os.remove(tf1.name)
        os.remove(tf2.name)

    def test_14_page_duplication_and_blank_insert(self):
        import pymupdf
        # Test with a PDF document
        test_pdf = "/tmp/test_dup.pdf"
        pdoc = pymupdf.open()
        pdoc.new_page(width=300, height=300)
        pdoc.save(test_pdf)
        pdoc.close()

        doc = Document(test_pdf)
        self.assertEqual(doc.page_count, 1)
        # Duplicate page
        dup_ok = doc.duplicate_page(0)
        self.assertTrue(dup_ok)
        self.assertEqual(doc.page_count, 2)
        # Insert blank page
        insert_ok = doc.insert_blank_page(0)
        self.assertTrue(insert_ok)
        self.assertEqual(doc.page_count, 3)

        if os.path.exists(test_pdf):
            os.remove(test_pdf)

    def test_15_text_extraction(self):
        import pymupdf
        test_pdf = "/tmp/test_extract.pdf"
        pdoc = pymupdf.open()
        p = pdoc.new_page(width=400, height=400)
        p.insert_text((50, 50), "Hello Preview macOS")
        pdoc.save(test_pdf)
        pdoc.close()

        doc = Document(test_pdf)
        txt = doc.extract_text(0)
        self.assertIn("Hello Preview macOS", txt)
        full_txt = doc.extract_text(None)
        self.assertIn("Hello Preview macOS", full_txt)

        if os.path.exists(test_pdf):
            os.remove(test_pdf)

    def test_16_export_all_to_pdf(self):
        import tempfile
        tf1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf1.close()
        tf2.close()
        Image.new("RGB", (150, 150), "green").save(tf1.name)
        Image.new("RGB", (150, 150), "yellow").save(tf2.name)

        doc = Document([tf1.name, tf2.name])
        out_pdf = "/tmp/test_exported_collection.pdf"
        doc.export_all_to_pdf(out_pdf)
        self.assertTrue(os.path.exists(out_pdf))

        import pymupdf
        check_doc = pymupdf.open(out_pdf)
        self.assertEqual(len(check_doc), 2)
        check_doc.close()

        os.remove(tf1.name)
        os.remove(tf2.name)
        os.remove(out_pdf)

    def test_17_redact_annotation(self):
        item = AnnotationItem(AnnotationType.REDACT)
        item.rect = QRectF(20, 20, 150, 40)
        self.assertEqual(item.item_type, AnnotationType.REDACT)
        bounds = item.get_bounds()
        self.assertEqual(bounds.width(), 150.0)
        self.assertEqual(bounds.height(), 40.0)
        self.assertTrue(item.contains_point(QPointF(50, 30)))

    def test_18_loupe_magnifier(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        canvas = win.canvas
        self.assertFalse(canvas.loupe_enabled)
        # Enable loupe
        canvas.toggle_loupe(True)
        self.assertTrue(canvas.loupe_enabled)
        self.assertEqual(canvas.active_tool, AnnotationType.NONE)
        canvas._loupe_pos = canvas.rect().center()

        # Test paint with loupe active
        pix = QPixmap(canvas.size())
        from PyQt6.QtGui import QPainter
        painter = QPainter(pix)
        canvas.render(painter)
        painter.end()

        # Disable loupe
        canvas.toggle_loupe(False)
        self.assertFalse(canvas.loupe_enabled)
        win.close()

    def test_19_mac_export_dialog(self):
        from preview.ui.export_dialog import MacExportDialog
        dlg = MacExportDialog(
            current_file_path=self.test_img_path,
            page_count=3,
            current_page=1
        )
        self.assertEqual(dlg.selected_format, "PDF")
        self.assertEqual(dlg.page_count, 3)
        self.assertEqual(dlg.current_page, 1)
        self.assertTrue(hasattr(dlg, "quality_slider"))
        self.assertTrue(hasattr(dlg, "dpi_combo"))
        dlg.close()

    def test_20_recent_files_settings(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        win._add_recent_file(self.test_img_path)
        from PyQt6.QtCore import QSettings
        settings = QSettings("TriviLabs", "PreviewMacOS")
        recents = settings.value("recent_files", [], type=list)
        self.assertIn(os.path.abspath(self.test_img_path), recents)
        win._clear_recent_files()
        cleared = settings.value("recent_files", [], type=list)
        self.assertEqual(len(cleared), 0)
        win.close()

    def test_21_slideshow_mode_and_hud(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        self.assertTrue(hasattr(win, "slideshow_hud"))
        self.assertFalse(getattr(win, "_is_slideshow", False))
        # Start slideshow
        win._toggle_slideshow()
        self.assertTrue(getattr(win, "_is_slideshow", True))
        self.assertTrue(win.slideshow_hud.isVisible())
        # Exit slideshow
        win._toggle_slideshow()
        self.assertFalse(getattr(win, "_is_slideshow", False))
        self.assertFalse(win.slideshow_hud.isVisible())
        win.close()

    def test_22_updater_version_parsing(self):
        from preview.core.updater import parse_version
        self.assertEqual(parse_version("1.1.1"), (1, 1, 1))
        self.assertEqual(parse_version("v1.2.0"), (1, 2, 0))
        self.assertGreater(parse_version("v1.2.0"), parse_version("v1.1.1"))
        self.assertGreater(parse_version("2.0.0"), parse_version("1.9.9"))
        self.assertEqual(parse_version("invalid"), (0,))

    def test_23_update_dialog_and_banner_ui(self):
        from preview.core.updater import UpdateInfo
        from preview.ui.update_dialog import UpdateDialog, UpdateBanner
        info = UpdateInfo(
            version="1.2.0",
            tag_name="v1.2.0",
            title="Preview 1.2.0",
            body="### What's New\n- Awesome new feature\n- Bug fixes",
            html_url="https://github.com/shivamprasad1001/previewmacos/releases/tag/v1.2.0",
            deb_url="https://example.com/preview.deb",
            exe_url="https://example.com/preview.exe"
        )
        self.assertEqual(info.version, "1.2.0")
        
        # Test Dialog instantiation
        dlg = UpdateDialog(info, current_version="1.1.1")
        self.assertIsNotNone(dlg.notes_browser)
        self.assertTrue(dlg.auto_check_cb.isChecked())
        dlg.close()

        # Test Banner instantiation
        banner = UpdateBanner(info)
        labels_text = " ".join(lbl.text() for lbl in banner.findChildren(QLabel))
        self.assertIn("1.2.0", labels_text)
        banner.close()

    def test_24_main_window_update_integration(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        self.assertTrue(hasattr(win, "_check_for_updates_manual"))
        self.assertTrue(hasattr(win, "_check_for_updates_startup"))
        self.assertTrue(hasattr(win, "_start_update_check"))
        win.close()

    def test_25_downloader_and_auto_install(self):
        from preview.core.updater import UpdateDownloadWorker, install_update
        worker = UpdateDownloadWorker("https://example.com/test.deb", "/tmp/test.deb")
        self.assertEqual(worker.download_url, "https://example.com/test.deb")
        self.assertFalse(worker._is_cancelled)
        worker.cancel()
        self.assertTrue(worker._is_cancelled)

if __name__ == "__main__":
    unittest.main()

