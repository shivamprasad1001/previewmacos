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
from PyQt6.QtCore import QPointF, QRectF, Qt

# Initialize Qt App in offscreen mode
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PREVIEW_TESTING"] = "1"
app = QApplication(sys.argv)

import pymupdf
from preview.core.document import Document, PasswordRequiredError
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
        win.set_modified(False)
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

    def test_26_annotation_handle_resizing(self):
        from preview.core.annotations import Handle
        rect = AnnotationItem(AnnotationType.RECTANGLE)
        rect.rect = QRectF(100, 100, 200, 150)
        
        # Test handle detection
        handle = rect.get_handle_at_point(QPointF(300, 250), zoom=1.0)
        self.assertEqual(handle, Handle.SE)
        
        # Test resizing SE handle
        orig_bounds = rect.get_bounds()
        orig_pts = list(rect.points)
        rect.resize_by_handle(Handle.SE, QPointF(350, 280), orig_bounds, orig_pts)
        self.assertEqual(rect.rect.width(), 250.0)
        self.assertEqual(rect.rect.height(), 180.0)

        # Test line resizing
        line = AnnotationItem(AnnotationType.LINE)
        line.points = [QPointF(50, 50), QPointF(150, 150)]
        handle_end = line.get_handle_at_point(QPointF(150, 150), zoom=1.0)
        self.assertEqual(handle_end, Handle.END)
        line.resize_by_handle(Handle.END, QPointF(180, 200), line.get_bounds(), list(line.points))
        self.assertEqual(line.points[1], QPointF(180, 200))

    def test_27_sticky_note_dialog(self):
        from preview.ui.sticky_note_dialog import StickyNoteDialog
        note = AnnotationItem(AnnotationType.NOTE)
        note.text = "Initial note text"
        dlg = StickyNoteDialog(initial_text=note.text)
        self.assertEqual(dlg.editor.toPlainText(), "Initial note text")
        dlg.editor.setPlainText("Updated text")
        dlg.text_saved.connect(lambda txt: setattr(note, "text", txt))
        dlg.accept()
        self.assertEqual(note.text, "Updated text")
        dlg.close()

    def test_28_markup_toolbar_font_and_actions(self):
        from preview.ui.markup_toolbar import MarkupToolbar
        tb = MarkupToolbar()
        self.assertIsNotNone(tb.font_combo)
        self.assertIsNotNone(tb.color_adjust_btn)
        self.assertIsNotNone(tb.size_adjust_btn)
        self.assertIsNotNone(tb.rotate_btn)
        
        # Verify signals
        captured = []
        tb.adjust_color_requested.connect(lambda: captured.append("color"))
        tb.color_adjust_btn.click()
        self.assertIn("color", captured)
        tb.close()

    def test_29_sidebar_and_thumbnail_slider(self):
        win = MacMainWindow(initial_file=self.test_img_path)
        self.assertTrue(win.sidebar.view_btn.isEnabled())
        
        # Test slider adjustment
        initial_w = win.sidebar.thumbnail_width
        win.sidebar.size_slider.setValue(160)
        self.assertEqual(win.sidebar.thumbnail_width, 160)
        win.close()

    def test_30_pdf_links_and_words(self):
        pdf_path = "/tmp/test_pdf_links_words.pdf"
        pdf = pymupdf.open()
        p1 = pdf.new_page(width=612, height=792)
        p1.insert_text(pymupdf.Point(72, 72), "Hello macOS Preview PDF Engine")
        p2 = pdf.new_page(width=612, height=792)
        p2.insert_text(pymupdf.Point(72, 72), "Target Page")
        p1_ref = pdf[0]
        p1_ref.insert_link({"kind": pymupdf.LINK_URI, "from": pymupdf.Rect(72, 60, 150, 80), "uri": "https://apple.com"})
        p1_ref.insert_link({"kind": pymupdf.LINK_GOTO, "from": pymupdf.Rect(72, 90, 150, 110), "page": 1})
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        self.assertTrue(doc.is_pdf)
        self.assertEqual(doc.page_count, 2)
        
        # Test word extraction
        words = doc.get_page_words(0)
        self.assertGreaterEqual(len(words), 4)
        word_texts = [w[1] for w in words]
        self.assertIn("Hello", word_texts)
        self.assertIn("macOS", word_texts)
        self.assertIn("Preview", word_texts)

        # Test link extraction
        links = doc.get_page_links(0)
        self.assertGreaterEqual(len(links), 2)
        uri_links = [lk for lk in links if lk.get("uri")]
        goto_links = [lk for lk in links if lk.get("page") is not None]
        self.assertEqual(len(uri_links), 1)
        self.assertEqual(uri_links[0]["uri"], "https://apple.com")
        self.assertEqual(len(goto_links), 1)
        self.assertEqual(goto_links[0]["page"], 1)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    def test_31_pdf_page_reordering_and_insertion(self):
        pdf_path = "/tmp/test_pdf_reorder.pdf"
        pdf = pymupdf.open()
        p0 = pdf.new_page()
        p0.insert_text(pymupdf.Point(72, 72), "Page Zero")
        p1 = pdf.new_page()
        p1.insert_text(pymupdf.Point(72, 72), "Page One")
        p2 = pdf.new_page()
        p2.insert_text(pymupdf.Point(72, 72), "Page Two")
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        self.assertEqual(doc.page_count, 3)

        # Reorder: move page 0 to index 2
        moved = doc.move_page(0, 2)
        self.assertTrue(moved)
        self.assertEqual(doc.page_count, 3)
        self.assertIn("Page Zero", doc.extract_text(2))
        self.assertIn("Page One", doc.extract_text(0))

        # Insert page from an image or pdf
        insert_path = "/tmp/test_pdf_to_insert.pdf"
        p_ins = pymupdf.open()
        p_new = p_ins.new_page()
        p_new.insert_text(pymupdf.Point(72, 72), "Inserted Fresh Page")
        p_ins.save(insert_path)
        p_ins.close()

        ins_ok = doc.insert_file(insert_path, after_page_idx=0)
        self.assertTrue(ins_ok)
        self.assertEqual(doc.page_count, 4)
        self.assertIn("Inserted Fresh Page", doc.extract_text(1))

        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(insert_path):
            os.remove(insert_path)

    def test_32_pdf_merge_and_split(self):
        pdf1 = "/tmp/test_merge_1.pdf"
        pdf2 = "/tmp/test_merge_2.pdf"
        merged = "/tmp/test_merged_out.pdf"
        split_out = "/tmp/test_split_out.pdf"

        # Create two test PDFs
        d1 = pymupdf.open()
        d1.new_page()
        d1.new_page()
        d1.save(pdf1)
        d1.close()

        d2 = pymupdf.open()
        d2.new_page()
        d2.new_page()
        d2.new_page()
        d2.save(pdf2)
        d2.close()

        # Test merge
        ok_merge = Document.merge_pdfs([pdf1, pdf2], merged)
        self.assertTrue(ok_merge)
        merged_doc = Document(merged)
        self.assertEqual(merged_doc.page_count, 5)

        # Test split: extract pages 0, 2, 4
        ok_split = merged_doc.split_pdf(split_out, [0, 2, 4])
        self.assertTrue(ok_split)
        split_doc = Document(split_out)
        self.assertEqual(split_doc.page_count, 3)

        for p in [pdf1, pdf2, merged, split_out]:
            if os.path.exists(p):
                os.remove(p)

    def test_33_pdf_password_protection(self):
        pdf_path = "/tmp/test_pdf_plain.pdf"
        enc_path = "/tmp/test_pdf_encrypted.pdf"

        pdf = pymupdf.open()
        p = pdf.new_page()
        p.insert_text(pymupdf.Point(72, 72), "Super Secret Information")
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        doc.set_pdf_password("Apple12345")
        doc.save_with_annotations(enc_path, {})

        # Opening without password should raise PasswordRequiredError
        with self.assertRaises(PasswordRequiredError):
            Document(enc_path)

        # Opening with correct password in init should succeed
        doc_authed = Document(enc_path, password="Apple12345")
        self.assertEqual(doc_authed.page_count, 1)
        self.assertIn("Super Secret", doc_authed.extract_text(0))

        for p in [pdf_path, enc_path]:
            if os.path.exists(p):
                os.remove(p)

    def test_34_pdf_save_with_annotations(self):
        pdf_path = "/tmp/test_pdf_annot.pdf"
        annot_out = "/tmp/test_pdf_annot_baked.pdf"

        pdf = pymupdf.open()
        p = pdf.new_page(width=600, height=800)
        p.insert_text(pymupdf.Point(50, 50), "Document content before annotation")
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        
        # Build annotations
        pen = AnnotationItem(AnnotationType.PEN)
        pen.points = [QPointF(50, 100), QPointF(100, 150), QPointF(150, 100)]
        pen.stroke_color = QColor(255, 0, 0)
        pen.stroke_width = 3.0

        rect = AnnotationItem(AnnotationType.RECTANGLE)
        rect.rect = QRectF(50, 200, 100, 60)
        rect.stroke_color = QColor(0, 122, 255)
        rect.stroke_width = 2.0

        txt = AnnotationItem(AnnotationType.TEXT)
        txt.rect = QRectF(50, 300, 200, 40)
        txt.text = "Native Preview Text Annot"
        txt.stroke_color = QColor(0, 0, 0)

        note = AnnotationItem(AnnotationType.NOTE)
        note.rect = QRectF(50, 400, 32, 32)
        note.text = "Mac Note popup content"

        ok_save = doc.save_with_annotations(annot_out, {0: [pen, rect, txt, note]})
        self.assertTrue(ok_save)

        # Inspect baked annotations using PyMuPDF directly
        baked = pymupdf.open(annot_out)
        baked_page = baked[0]
        annots = list(baked_page.annots())
        self.assertGreaterEqual(len(annots), 3)
        baked.close()

        for p in [pdf_path, annot_out]:
            if os.path.exists(p):
                os.remove(p)

    def test_35_canvas_pdf_text_selection_and_view_mode(self):
        from preview.ui.canvas import CanvasView
        canvas = CanvasView()
        
        # Test view mode switching
        canvas.set_view_mode("Two-Up")
        self.assertEqual(canvas.view_mode, "Two-Up")
        canvas.set_view_mode("Single")
        self.assertEqual(canvas.view_mode, "Single")

        # Test text selection structures
        canvas._is_selecting_text = False
        canvas._selected_text = "Selected Parity Text"
        canvas._copy_selected_text()
        
        # Test clipboard content
        clipboard = QApplication.clipboard()
        self.assertEqual(clipboard.text(), "Selected Parity Text")

        canvas._clear_text_selection()
        self.assertEqual(canvas._selected_text, "")
        self.assertEqual(len(canvas._text_sel_rects), 0)
        canvas.close()

    def test_36_permanent_redactions_and_form_fields(self):
        pdf_path = "/tmp/test_pdf_redact_form.pdf"
        pdf = pymupdf.open()
        page = pdf.new_page(width=600, height=800)
        page.insert_text(pymupdf.Point(50, 100), "Sensitive Secret Token XYZ")
        
        # Add a text form widget
        widget = pymupdf.Widget()
        widget.rect = pymupdf.Rect(50, 200, 250, 240)
        widget.field_name = "UserEmail"
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        widget.field_value = "default@apple.com"
        page.add_widget(widget)

        # Add a redaction annotation over "Sensitive Secret Token XYZ"
        page.add_redact_annot(pymupdf.Rect(45, 80, 300, 120))
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        
        # 1. Test form field inspection and update
        fields = doc.get_form_fields(0)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["name"], "UserEmail")
        self.assertEqual(fields[0]["value"], "default@apple.com")
        
        set_ok = doc.set_form_field_value(0, "UserEmail", "steve@apple.com")
        self.assertTrue(set_ok)
        updated_fields = doc.get_form_fields(0)
        self.assertEqual(updated_fields[0]["value"], "steve@apple.com")

        # 2. Test permanent redaction
        self.assertIn("Sensitive Secret Token XYZ", doc.extract_text(0))
        redact_ok = doc.apply_permanent_redactions(0)
        self.assertTrue(redact_ok)
        self.assertNotIn("Sensitive Secret Token XYZ", doc.extract_text(0))

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    def test_35_pdf_render_scale_and_scroll_parity(self):
        pdf_path = "/tmp/test_pdf_scale_scroll.pdf"
        pdf = pymupdf.open()
        p1 = pdf.new_page(width=612, height=792)
        p1.insert_text(pymupdf.Point(72, 72), "Page 1 Content")
        p2 = pdf.new_page(width=612, height=792)
        p2.insert_text(pymupdf.Point(72, 72), "Page 2 Content")
        pdf.save(pdf_path)
        pdf.close()

        doc = Document(pdf_path)
        w, h = doc.get_page_size(0)
        self.assertEqual((w, h), (612.0, 792.0))

        # Ensure render_page at 1.0 zoom has 1:1 parity with get_page_size
        pix_1 = doc.render_page(0, zoom=1.0)
        self.assertEqual(pix_1.width(), 612)
        self.assertEqual(pix_1.height(), 792)

        # Ensure render_page at 0.5 zoom scales linearly
        pix_half = doc.render_page(0, zoom=0.5)
        self.assertEqual(pix_half.width(), 306)
        self.assertEqual(pix_half.height(), 396)

        # Test Canvas navigation signals on wheel scroll
        from preview.ui.canvas import CanvasView
        from PyQt6.QtCore import Qt, QPoint
        from PyQt6.QtGui import QWheelEvent
        canvas = CanvasView()
        canvas.resize(800, 600)
        canvas.set_document(doc)

        next_called = []
        prev_called = []
        canvas.page_next_requested.connect(lambda: next_called.append(True))
        canvas.page_prev_requested.connect(lambda: prev_called.append(True))

        # Simulate wheel down event when page fits
        ev_down = QWheelEvent(QPointF(400, 300), QPointF(400, 300), QPoint(0, 0), QPoint(0, -120),
                              Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                              Qt.ScrollPhase.NoScrollPhase, False)
        canvas.wheelEvent(ev_down)
        self.assertTrue(len(next_called) > 0)

        # Simulate wheel up event
        ev_up = QWheelEvent(QPointF(400, 300), QPointF(400, 300), QPoint(0, 0), QPoint(0, 120),
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                            Qt.ScrollPhase.NoScrollPhase, False)
        canvas.wheelEvent(ev_up)
        self.assertTrue(len(prev_called) > 0)

        # Test converting rendered PDF page to PIL Image for Adjust Color without TypeError
        from PyQt6.QtCore import QBuffer, QIODevice
        import io
        from PIL import Image
        qbuf = QBuffer()
        qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
        pix_1.save(qbuf, "PNG")
        pil_from_pdf = Image.open(io.BytesIO(qbuf.data().data()))
        qbuf.close()
        self.assertEqual(pil_from_pdf.size, (612, 792))

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    def test_36_color_adjust_dialog_full_resolution_and_validation(self):
        from preview.ui.adjust_color_dialog import AdjustColorDialog
        from preview.ui.main_window import MacMainWindow
        from unittest.mock import patch, MagicMock

        # 1. Test that AdjustColorDialog preserves full resolution (no downscaling/proxy zoom-out)
        large_img = Image.new("RGB", (2500, 1800), color=(100, 150, 200))
        dlg = AdjustColorDialog(large_img)
        self.assertEqual(dlg.original_image.size, (2500, 1800))
        self.assertEqual(dlg.current_preview.size, (2500, 1800))

        dlg.exposure_slider.setValue(25)
        dlg._do_apply_changes()
        self.assertEqual(dlg.current_preview.size, (2500, 1800))

        dlg._on_slider_released()
        self.assertEqual(dlg.current_preview.size, (2500, 1800))

        # Test set_image
        new_img = Image.new("RGB", (3000, 2000), color=(50, 60, 70))
        dlg.set_image(new_img)
        self.assertEqual(dlg.original_image.size, (3000, 2000))
        self.assertEqual(dlg.current_preview.size, (3000, 2000))
        dlg.close()

        # 2. Test PDF document validation showing informative notice
        win = MacMainWindow()
        mock_doc = MagicMock()
        mock_doc.is_pdf = True
        mock_doc._pil_image = None
        win.document = mock_doc

        with patch("PyQt6.QtWidgets.QMessageBox.information") as mock_info:
            win._open_adjust_color()
            mock_info.assert_called_once()
            self.assertIn("image documents", mock_info.call_args[0][2])

        with patch("PyQt6.QtWidgets.QMessageBox.information") as mock_info:
            win._open_adjust_size()
            mock_info.assert_called_once()
            self.assertIn("image documents", mock_info.call_args[0][2])
        win.close()

    def test_39_open_segmented_and_dropdown_markup_controls(self):
        """Verifies Open segmented button [ 📂 Open | ▼ ] and dropdown menus for selection, color, font."""
        win = MacMainWindow(initial_file=self.test_img_path)
        
        # 1. Open Segmented Control
        self.assertTrue(hasattr(win, "open_segmented"))
        self.assertTrue(hasattr(win, "open_btn"))
        self.assertTrue(hasattr(win, "open_arrow_btn"))
        self.assertEqual(win.open_btn.text(), "Open")
        self.assertIsNotNone(win.open_arrow_btn.menu())
        self.assertEqual(len(win.open_arrow_btn.menu().actions()), 2)
        self.assertEqual(win.open_arrow_btn.menu().actions()[0].text(), "Open File(s)...")
        self.assertEqual(win.open_arrow_btn.menu().actions()[1].text(), "Open Folder of Images...")

        # 2. Markup Toolbar Dropdown Tools
        mb = win.markup_bar
        # Selection dropdown
        self.assertIsNotNone(mb.select_btn.menu())
        select_actions = mb.select_btn.menu().actions()
        self.assertGreaterEqual(len(select_actions), 3)
        self.assertIn("Rectangular Selection", select_actions[0].text())
        self.assertIn("Oval", select_actions[1].text())
        self.assertIn("Lasso", select_actions[2].text())
        
        # Trigger selection tool change
        select_actions[0].trigger()
        self.assertEqual(mb.current_tool, AnnotationType.CROP_BOX)
        self.assertEqual(win.canvas.active_tool, AnnotationType.CROP_BOX)

        # 3. Stroke and Fill Color Dropdowns
        self.assertIsNotNone(mb.color_btn.menu())
        stroke_actions = mb.color_btn.menu().actions()
        self.assertGreaterEqual(len(stroke_actions), 10)
        # Choose Blue from palette
        blue_action = [a for a in stroke_actions if "Blue" in a.text()][0]
        blue_action.trigger()
        self.assertEqual(mb.stroke_color.name(), "#007aff")
        self.assertEqual(win.canvas.stroke_color.name(), "#007aff")

        self.assertIsNotNone(mb.fill_btn.menu())
        fill_actions = mb.fill_btn.menu().actions()
        self.assertGreaterEqual(len(fill_actions), 10)
        green_action = [a for a in fill_actions if "Green" in a.text()][0]
        green_action.trigger()
        self.assertEqual(mb.fill_color.name(), "#34c759")
        self.assertEqual(win.canvas.fill_color.name(), "#34c759")

        # 4. Font Controls: Spin, Family, Bold, Italic, Underline, Alignment
        mb.font_spin.setValue(24)
        self.assertEqual(win.canvas.font_size, 24)

        mb.bold_btn.setChecked(True)
        self.assertTrue(getattr(win.canvas, "font_bold", False))

        mb.italic_btn.setChecked(True)
        self.assertTrue(getattr(win.canvas, "font_italic", False))

        mb.underline_btn.setChecked(True)
        self.assertTrue(getattr(win.canvas, "font_underline", False))

        # Text options menu (alignment & sizes)
        self.assertIsNotNone(mb.text_options_btn.menu())
        text_menu_actions = mb.text_options_btn.menu().actions()
        align_center = [a for a in text_menu_actions if "Align Center" in a.text()][0]
        align_center.trigger()
        self.assertEqual(win.canvas.text_alignment, Qt.AlignmentFlag.AlignHCenter)

        win.close()

    def test_40_oval_and_lasso_crop_cut_delete(self):
        """Verifies oval and lasso selections crop with alpha transparency, cut, copy, and delete."""
        win = MacMainWindow(initial_file=self.test_img_path)
        canvas = win.canvas

        # 1. Test Oval Crop
        canvas.set_active_tool(AnnotationType.CROP_OVAL)
        self.assertEqual(canvas.active_tool, AnnotationType.CROP_OVAL)
        
        canvas.crop_box = AnnotationItem(AnnotationType.CROP_OVAL)
        canvas.crop_box.rect = QRectF(10, 10, 80, 80)
        canvas.apply_crop()
        
        # Image should be 80x80 RGBA with transparent corners and opaque center
        img = canvas.document._pil_image
        self.assertEqual(img.size, (80, 80))
        self.assertEqual(img.mode, "RGBA")
        corner_alpha = img.getpixel((1, 1))[3]
        center_alpha = img.getpixel((40, 40))[3]
        self.assertEqual(corner_alpha, 0, "Corner outside ellipse should be transparent")
        self.assertGreater(center_alpha, 200, "Center inside ellipse should be opaque")

        # 2. Test Lasso Crop
        canvas.set_active_tool(AnnotationType.CROP_LASSO)
        self.assertEqual(canvas.active_tool, AnnotationType.CROP_LASSO)

        canvas.crop_box = AnnotationItem(AnnotationType.CROP_LASSO)
        canvas.crop_box.points = [
            QPointF(10, 10),
            QPointF(50, 10),
            QPointF(50, 50),
            QPointF(10, 50),
            QPointF(10, 10)
        ]
        canvas.apply_crop()
        img2 = canvas.document._pil_image
        self.assertEqual(img2.size, (40, 40))
        self.assertEqual(img2.mode, "RGBA")

        # 3. Test Delete Selection (clears selection to transparent)
        canvas.crop_box = AnnotationItem(AnnotationType.CROP_OVAL)
        canvas.crop_box.rect = QRectF(5, 5, 20, 20)
        canvas.delete_selection()
        cleared_img = canvas.document._pil_image
        self.assertEqual(cleared_img.getpixel((15, 15))[3], 0, "Pixels inside deleted oval should be cleared/transparent")

        win.set_modified(False)
        win.close()

    def test_41_history_dirty_tracking(self):
        """Verifies HistoryManager correctly tracks modified state through undo/redo/save cycles."""
        changes = []
        hist = HistoryManager(on_changed=lambda m: changes.append(m))
        self.assertFalse(hist.is_modified)

        # 1. Push a command -> becomes modified
        hist.push(ActionCommand("Edit", lambda: None, lambda: None))
        self.assertTrue(hist.is_modified)
        self.assertEqual(changes[-1], True)

        # 2. Undo -> returns to clean state
        hist.undo()
        self.assertFalse(hist.is_modified)
        self.assertEqual(changes[-1], False)

        # 3. Redo -> modified again
        hist.redo()
        self.assertTrue(hist.is_modified)

        # 4. Mark saved -> current position is now clean
        hist.mark_saved()
        self.assertFalse(hist.is_modified)

        # 5. Another change -> modified
        hist.push(ActionCommand("Edit 2", lambda: None, lambda: None))
        self.assertTrue(hist.is_modified)

        # 6. Undo back to save checkpoint -> clean again
        hist.undo()
        self.assertFalse(hist.is_modified)

        # 7. Clear -> clean
        hist.clear()
        self.assertFalse(hist.is_modified)

    def test_42_save_confirmation_dialog_and_traffic_light(self):
        """Verifies TrafficLightButton dirty dot and MacSaveConfirmationDialog choices."""
        from preview.ui.save_dialog import MacSaveConfirmationDialog
        from preview.ui.main_window import TrafficLightButton

        # 1. Traffic light button modified dot
        btn = TrafficLightButton("#ff5f56", "#e0443e", "✕", "#4d0000")
        self.assertFalse(btn._modified)
        btn.set_modified(True)
        self.assertTrue(btn._modified)
        btn.set_modified(False)
        self.assertFalse(btn._modified)

        # 2. Dialog choices: Save, Don't Save, Cancel (Replace Original removed)
        dlg = MacSaveConfirmationDialog("document.pdf", has_file_path=True)
        self.assertIsNotNone(dlg.btn_dont_save)
        self.assertIsNotNone(dlg.btn_cancel)
        self.assertIsNotNone(dlg.btn_save)
        self.assertEqual(dlg.btn_save.text(), "Save")
        self.assertEqual(dlg.btn_dont_save.text(), "Don't Save")
        self.assertEqual(dlg.btn_cancel.text(), "Cancel")

        # Test button action return codes
        dlg._on_save()
        self.assertEqual(dlg.result_code, MacSaveConfirmationDialog.SAVE)

        dlg._on_dont_save()
        self.assertEqual(dlg.result_code, MacSaveConfirmationDialog.DONT_SAVE)

        dlg._on_cancel()
        self.assertEqual(dlg.result_code, MacSaveConfirmationDialog.CANCEL)

    def test_43_unsaved_changes_prompt_and_save_options(self):
        """Verifies full window dirty detection, window title '— Edited', replace, copy, and revert workflows."""
        import tempfile
        import shutil

        # Create isolated temporary copy of test image
        temp_dir = tempfile.mkdtemp()
        orig_img = os.path.join(temp_dir, "work_photo.png")
        shutil.copyfile(self.test_img_path, orig_img)

        try:
            win = MacMainWindow(initial_file=orig_img)
            self.assertFalse(win.is_document_modified())
            self.assertNotIn("— Edited", win.windowTitle())
            self.assertFalse(win.traffic_cluster.btn_close._modified)

            # 1. Modify document by adding an annotation
            pen = AnnotationItem(AnnotationType.PEN)
            pen.points = [QPointF(5, 5), QPointF(50, 50)]
            win.canvas.annotations[0] = [pen]
            win.canvas.history.push(ActionCommand("Draw Pen", lambda: None, lambda: None))

            # Verify dirty state is detected and displayed
            self.assertTrue(win.is_document_modified())
            self.assertIn("— Edited", win.windowTitle())
            self.assertTrue(win.traffic_cluster.btn_close._modified)
            self.assertTrue(win.revert_act.isEnabled())

            # 2. Test 'Save As New Copy'
            copy_path = os.path.join(temp_dir, "work_photo_new_copy.png")
            # Directly test save_as_new_copy logic:
            win.document.save_with_annotations(copy_path, win.canvas.annotations)
            self.assertTrue(os.path.exists(copy_path))
            # Verify original file was preserved
            self.assertTrue(os.path.exists(orig_img))

            # 3. Test 'Revert to Original'
            # Reset canvas with mock user confirmation
            win.set_modified(False)
            win.open_file(orig_img)
            self.assertFalse(win.is_document_modified())
            self.assertNotIn("— Edited", win.windowTitle())
            self.assertFalse(win.traffic_cluster.btn_close._modified)

            # 4. Modify again and test 'Replace Original'
            win.set_modified(True)
            self.assertTrue(win.is_document_modified())
            self.assertIn("— Edited", win.windowTitle())

            save_ok = win._save_file_direct()
            self.assertTrue(save_ok)
            self.assertFalse(win.is_document_modified())
            self.assertNotIn("— Edited", win.windowTitle())
            self.assertFalse(win.traffic_cluster.btn_close._modified)

            # 5. Test closeEvent ignoring when cancelled
            from PyQt6.QtGui import QCloseEvent
            close_evt = QCloseEvent()
            win.set_modified(True)
            # Monkey-patch maybe_save_changes to simulate user clicking Cancel
            win.maybe_save_changes = lambda: False
            win.closeEvent(close_evt)
            self.assertFalse(close_evt.isAccepted(), "closeEvent should be ignored when cancelled")

            # Monkey-patch maybe_save_changes to simulate user clicking Don't Save
            close_evt2 = QCloseEvent()
            win.maybe_save_changes = lambda: True
            win.closeEvent(close_evt2)
            self.assertTrue(close_evt2.isAccepted(), "closeEvent should be accepted when Don't Save or Saved")

            win.set_modified(False)
            win.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_44_markup_disabled_blocks_edits(self):
        """Verifies that when markup is disabled (toolbar closed), no annotations/selections can be created or edited."""
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF, QEvent
        win = MacMainWindow(initial_file=self.test_img_path)
        win.show()
        canvas = win.canvas

        # By default markup bar is hidden -> canvas.markup_enabled is False
        self.assertTrue(win.markup_bar.isHidden())
        self.assertFalse(canvas.markup_enabled)

        # 1. Attempt mouse click with active tool while markup_enabled is False
        canvas.set_active_tool(AnnotationType.RECTANGLE)
        # Simulate click
        click_pt = canvas.doc_to_view_coords(QPointF(50, 50))
        evt = QMouseEvent(QEvent.Type.MouseButtonPress, click_pt, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        canvas.mousePressEvent(evt)
        # No annotation should have been added
        self.assertEqual(len(canvas._get_current_annotations()), 0)

        # 2. Toggle markup toolbar open -> canvas.markup_enabled becomes True
        win._toggle_markup_bar()
        self.assertFalse(win.markup_bar.isHidden())
        self.assertTrue(canvas.markup_enabled)

        # 3. Now drawing an annotation works
        canvas.set_active_tool(AnnotationType.RECTANGLE)
        canvas.mousePressEvent(evt)
        self.assertIsNotNone(canvas._active_annotation)

        # 4. Toggle markup toolbar closed -> resets active tool and disables editing
        win._toggle_markup_bar()
        self.assertTrue(win.markup_bar.isHidden())
        self.assertFalse(canvas.markup_enabled)
        self.assertEqual(canvas.active_tool, AnnotationType.NONE)
        self.assertIsNone(canvas.crop_box)

        win.set_modified(False)
        win.close()

    def test_45_rotate_selection_all_types(self):
        """Verifies rotating selections of all types: Rectangular, Oval, and Lasso, plus annotations."""
        win = MacMainWindow(initial_file=self.test_img_path)
        canvas = win.canvas
        win._toggle_markup_bar() # enable markup

        # Create an asymmetrical test image (80x80)
        from PIL import Image
        test_img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        # Draw a colored red patch at top-left quadrant (10, 10) to (30, 30)
        for y in range(10, 30):
            for x in range(10, 30):
                test_img.putpixel((x, y), (255, 0, 0, 255))
        canvas.document.update_image(test_img)

        # 1. Test Rectangular Selection Rotation
        canvas.crop_box = AnnotationItem(AnnotationType.CROP_BOX)
        canvas.crop_box.rect = QRectF(10, 10, 40, 40)
        canvas.crop_available.emit(True)

        canvas.rotate_selection(90)
        # Bounding box should stay 40x40 centered at same place
        self.assertEqual(int(canvas.crop_box.rect.width()), 40)
        self.assertEqual(int(canvas.crop_box.rect.height()), 40)
        # Red patch originally at top-left (10-30, 10-30) should now be rotated 90° clockwise
        # Verify history was pushed
        self.assertTrue(canvas.history.can_undo)

        # 2. Test Oval Selection Rotation
        canvas.crop_box = AnnotationItem(AnnotationType.CROP_OVAL)
        canvas.crop_box.rect = QRectF(20, 20, 40, 40)
        canvas.crop_available.emit(True)
        canvas.rotate_selection(90)
        self.assertIsNotNone(canvas.crop_box)

        # 3. Test Lasso Selection Rotation
        canvas.crop_box = AnnotationItem(AnnotationType.CROP_LASSO)
        canvas.crop_box.points = [QPointF(20, 20), QPointF(60, 20), QPointF(60, 60), QPointF(20, 60)]
        canvas.crop_available.emit(True)
        canvas.rotate_selection(90)
        self.assertEqual(len(canvas.crop_box.points), 4)

        # 4. Test Annotation Item Rotation
        canvas.crop_box = None
        rect_annot = AnnotationItem(AnnotationType.RECTANGLE)
        rect_annot.rect = QRectF(10, 20, 80, 40) # w=80, h=40
        canvas._selected_annotation = rect_annot
        canvas.rotate_selection(90)
        # Width and height should swap to 40x80
        self.assertEqual((int(rect_annot.rect.width()), int(rect_annot.rect.height())), (40, 80))

        win.set_modified(False)
        win.close()

    def test_46_help_window_initialization_and_theme(self):
        """Test 46: Verify HelpWindow initializes, applies light/dark themes, and sets title."""
        from preview.ui.help_window import HelpWindow
        from preview.theme import MacTheme

        # Light theme
        help_win_light = HelpWindow(theme=MacTheme.LIGHT)
        self.assertEqual(help_win_light.windowTitle(), "Preview Help")
        self.assertIn("Get Started", [help_win_light.nav_tree.topLevelItem(i).text(0) for i in range(help_win_light.nav_tree.topLevelItemCount())])
        help_win_light.close()

        # Dark theme
        help_win_dark = HelpWindow(theme=MacTheme.DARK)
        self.assertEqual(help_win_dark.current_theme, MacTheme.DARK)
        help_win_dark.close()

    def test_47_help_content_and_dictionary_coverage(self):
        """Test 47: Verify help content files exist, and dictionary achieves 100% code coverage."""
        import json
        dict_path = os.path.abspath("help/content/dictionary.json")
        self.assertTrue(os.path.exists(dict_path))
        with open(dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", [])
        self.assertGreaterEqual(len(entries), 100)

        # Run verify_help_dictionary.py
        import subprocess
        res = subprocess.run(["python3", "scripts/verify_help_dictionary.py"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Dictionary verification failed:\n{res.stdout}\n{res.stderr}")
        self.assertIn("100% documented", res.stdout)

    def test_48_help_window_search_and_navigation(self):
        """Test 48: Verify HelpWindow navigation to tasks, dictionary filtering, and shortcuts."""
        from preview.ui.help_window import HelpWindow
        help_win = HelpWindow()

        # Navigate to a task
        help_win.navigate_to("adjust-color")
        self.assertEqual(help_win.current_page_id, "adjust-color")
        self.assertIn("Adjust color", help_win.browser.toPlainText())

        # Test dictionary search filter
        help_win._on_search_changed("crop")
        self.assertEqual(help_win.current_page_id, "dictionary")
        self.assertIn("Crop", help_win.browser.toPlainText())

        # Test shortcuts guide direct navigation
        help_win.open_shortcuts()
        self.assertEqual(help_win.current_page_id, "shortcuts")
        self.assertIn("Keyboard Shortcuts", help_win.browser.toPlainText())

        help_win.close()

    def test_49_image_guide_and_annotated_screenshots(self):
        """Test 49: Verify Image Guide specs and generated annotated screenshots exist."""
        import glob
        specs = glob.glob("help/content/image_guide/*.json")
        self.assertEqual(len(specs), 13, f"Expected 13 task image specs, found {len(specs)}")

        rendered_pngs = glob.glob("help/generated/guide-*.png")
        self.assertEqual(len(rendered_pngs), 13, f"Expected 13 rendered task screenshots, found {len(rendered_pngs)}")

    def test_50_pdf_guide_and_cheatsheet(self):
        """Test 50: Verify PDF Guide and 1-page Cheat Sheet exist and have valid pages."""
        import pymupdf

        guide_pdf = "help/generated/preview_user_guide.pdf"
        self.assertTrue(os.path.exists(guide_pdf))
        doc_guide = pymupdf.open(guide_pdf)
        self.assertGreaterEqual(doc_guide.page_count, 4)
        doc_guide.close()

        cheatsheet_pdf = "help/generated/preview_shortcuts_cheatsheet.pdf"
        self.assertTrue(os.path.exists(cheatsheet_pdf))
        doc_sheet = pymupdf.open(cheatsheet_pdf)
        self.assertEqual(doc_sheet.page_count, 1)
    def test_51_theme_manager_and_auto_detection(self):
        """Test 51: Verify ThemeManager and Auto System Theme detection (Issue #6)."""
        from preview.theme import ThemeManager, MacTheme
        # Check follow_system_theme
        theme = ThemeManager.follow_system_theme()
        self.assertIn(theme, [MacTheme.DARK, MacTheme.LIGHT])

        # Check ThemeManager instance modes
        tm = ThemeManager(default_mode="auto")
        self.assertEqual(tm.mode, "auto")
        self.assertIn(tm.get_resolved_theme(), [MacTheme.DARK, MacTheme.LIGHT])

        tm.set_mode(MacTheme.LIGHT)
        self.assertEqual(tm.mode, MacTheme.LIGHT)
        self.assertEqual(tm.get_resolved_theme(), MacTheme.LIGHT)

        tm.set_mode(MacTheme.DARK)
        self.assertEqual(tm.mode, MacTheme.DARK)
        self.assertEqual(tm.get_resolved_theme(), MacTheme.DARK)

        # Check MacMainWindow actions
        win = MacMainWindow(initial_file=self.test_img_path)
        self.assertTrue(hasattr(win, "theme_auto_act"))
        self.assertTrue(hasattr(win, "theme_dark_act"))
        self.assertTrue(hasattr(win, "theme_light_act"))

        win._set_appearance_mode(MacTheme.LIGHT)
        self.assertEqual(win.current_theme, MacTheme.LIGHT)
        self.assertTrue(win.theme_light_act.isChecked())

        win._set_appearance_mode(MacTheme.DARK)
        self.assertEqual(win.current_theme, MacTheme.DARK)
        self.assertTrue(win.theme_dark_act.isChecked())

        win._set_appearance_mode("auto")
        self.assertEqual(win.appearance_mode, "auto")
        self.assertTrue(win.theme_auto_act.isChecked())
        win.close()

if __name__ == "__main__":
    unittest.main()



