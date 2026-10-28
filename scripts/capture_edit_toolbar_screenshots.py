"""
Captures screenshots of the improved Edit toolbar in Preview for Linux:
1. Typical window width (1180px) - grouped tools and contextual action strip
2. Compact / minimum window width (780px) - responsive overflow adaptation
3. Active tool with blue accent & context formatting row
4. Light mode Edit toolbar parity
"""

import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor
from PIL import Image

from preview.ui.main_window import MacMainWindow
from preview.core.annotations import AnnotationItem, AnnotationType
from preview.theme import MacTheme

ARTIFACT_DIR = "/home/zoro0x1/.gemini/antigravity-ide/brain/50214f98-c441-4363-88a0-a8f6dec56735"

def capture_screenshots():
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Prepare sample PDF
    import fitz
    pdf_doc = fitz.open()
    page = pdf_doc.new_page(width=612, height=792)
    page.insert_text((54, 72), "Preview for Linux - Professional Edit Toolbar", fontsize=18, fontname="helv")
    page.draw_line((54, 84), (558, 84), color=(0.7, 0.7, 0.7), width=1)
    page.insert_text(
        (54, 120),
        "This sample document demonstrates the upgraded macOS-style Edit toolbar.\n"
        "Editing tools are organized into logical segmented pill groups:\n"
        "• Selection: Pointer, Hand, and Selection dropdown\n"
        "• Text: Text Box, Highlighter, Underline, Strikethrough, Sticky Note\n"
        "• Drawing: Sketch / Freehand Pen\n"
        "• Shapes: Rectangles, Rounded Rectangles, Ovals, Lines, Arrows, Callouts\n"
        "• Privacy & Signing: Redact, Signature\n"
        "• Image Editing: Crop, Rotate Left, Rotate Selection, Adjust Color, Adjust Size\n"
        "• History: Undo, Redo\n\n"
        "Contextual formatting rows surface controls based on active selection without text truncation.",
        fontsize=11,
        fontname="helv"
    )
    pdf_path = "/tmp/preview_toolbar_sample.pdf"
    pdf_doc.save(pdf_path)
    pdf_doc.close()

    # -------------------------------------------------------------
    # 1. Typical window width (1180px) - Full Edit Toolbar & Quick Actions
    # -------------------------------------------------------------
    win = MacMainWindow(initial_file=pdf_path)
    win.resize(1180, 780)
    win.show()
    win.set_workspace_mode("Edit")
    win.set_inspector_visible(False)
    QApplication.processEvents()

    p1 = os.path.join(ARTIFACT_DIR, "edit_toolbar_typical_width.png")
    win.grab().save(p1)
    print(f"Captured: {p1}")

    # -------------------------------------------------------------
    # 2. Compact / Minimum window width (780px) - Responsive Overflow
    # -------------------------------------------------------------
    win.resize(780, 750)
    win.markup_bar.handle_resize(780)
    QApplication.processEvents()

    p2 = os.path.join(ARTIFACT_DIR, "edit_toolbar_compact_width.png")
    win.grab().save(p2)
    print(f"Captured: {p2}")

    # -------------------------------------------------------------
    # 3. Active Tool & Context Formatting (Text Tool Active)
    # -------------------------------------------------------------
    win.resize(1180, 780)
    win.markup_bar.handle_resize(1180)
    win.markup_bar.text_btn.click()
    QApplication.processEvents()

    p3 = os.path.join(ARTIFACT_DIR, "edit_toolbar_contextual_text.png")
    win.grab().save(p3)
    print(f"Captured: {p3}")

    # -------------------------------------------------------------
    # 4. Light Theme Edit Toolbar
    # -------------------------------------------------------------
    win._apply_theme(MacTheme.LIGHT, animate=False)
    win.markup_bar.pointer_btn.click()
    QApplication.processEvents()

    p4 = os.path.join(ARTIFACT_DIR, "edit_toolbar_light_theme.png")
    win.grab().save(p4)
    print(f"Captured: {p4}")

    win.close()
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass

if __name__ == "__main__":
    capture_screenshots()
