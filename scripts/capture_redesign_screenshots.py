"""
Script to capture verification screenshots of the redesigned UI in both Light and Dark modes at 1280px and 1024px.
"""

import os
import sys
import tempfile
import pymupdf
from PIL import Image

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from preview.ui.main_window import MacMainWindow
from preview.theme import MacTheme

def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    out_dir = os.path.abspath("docs/screenshots")
    os.makedirs(out_dir, exist_ok=True)
    
    artifact_dir = "/home/zoro0x1/.gemini/antigravity-ide/brain/27848777-99d0-48da-97ed-dec47f27ed9b"

    # Create a nice sample PDF document with multiple pages
    tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf_path = tmp_pdf.name
    tmp_pdf.close()

    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page(width=612, height=792)
        # Add heading and paragraph
        page.insert_text(pymupdf.Point(72, 100), f"TriviLabs Preview - Sample Page {i + 1}", fontsize=18, fontname="helv", color=(0.1, 0.2, 0.4))
        page.insert_text(pymupdf.Point(72, 140), "Authentic macOS Preview experience engineered natively for Linux.", fontsize=12, fontname="helv", color=(0.3, 0.3, 0.3))
        page.insert_text(pymupdf.Point(72, 170), "This document verifies layout geometry, typography, Lucide icons, and zero-clipping toolbars.", fontsize=11, fontname="helv", color=(0.4, 0.4, 0.4))
        page.draw_rect(pymupdf.Rect(72, 210, 540, 450), color=(0.2, 0.5, 0.9), width=1.5, fill=(0.95, 0.97, 1.0))
        page.insert_text(pymupdf.Point(90, 250), "• Single unified Lucide icon set with stroke-width 1.75", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(90, 280), "• Fixed 48px Header bar with grouped window controls and mode switcher", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(90, 310), "• Fixed 44px Tool bar with 32x32 buttons and 6px border radii", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(90, 340), "• Segmented sidebar tabs [ Thumbnails | Outline | Contact Sheet ]", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(90, 370), "• 280px Pro Inspector Panel with 16px padding and wrapping text", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        page.insert_text(pymupdf.Point(90, 400), "• Responsive layout with icon-only fallback for narrow viewports", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
    doc.save(pdf_path)
    doc.close()

    screenshots = []

    # 1. Dark Mode - Empty State (1280x800)
    win_empty_dark = MacMainWindow()
    win_empty_dark.apply_theme(MacTheme.DARK)
    win_empty_dark.resize(1280, 800)
    win_empty_dark.show()
    for _ in range(10):
        app.processEvents()
    pix = win_empty_dark.grab()
    p1 = os.path.join(out_dir, "redesign_dark_empty_1280.png")
    pix.save(p1)
    screenshots.append(p1)
    win_empty_dark.close()

    # 2. Light Mode - Empty State (1280x800)
    win_empty_light = MacMainWindow()
    win_empty_light.apply_theme(MacTheme.LIGHT)
    win_empty_light.resize(1280, 800)
    win_empty_light.show()
    for _ in range(10):
        app.processEvents()
    pix = win_empty_light.grab()
    p2 = os.path.join(out_dir, "redesign_light_empty_1280.png")
    pix.save(p2)
    screenshots.append(p2)
    win_empty_light.close()

    # 3. Dark Mode - Edit Mode with Inspector (1280x800)
    win_edit_dark = MacMainWindow(initial_file=pdf_path)
    win_edit_dark.apply_theme(MacTheme.DARK)
    win_edit_dark.resize(1280, 800)
    win_edit_dark.set_workspace_mode("Edit")
    win_edit_dark.show()
    for _ in range(10):
        app.processEvents()
    pix = win_edit_dark.grab()
    p3 = os.path.join(out_dir, "redesign_dark_edit_1280.png")
    pix.save(p3)
    screenshots.append(p3)
    win_edit_dark.close()

    # 4. Light Mode - Edit Mode with Inspector (1280x800)
    win_edit_light = MacMainWindow(initial_file=pdf_path)
    win_edit_light.apply_theme(MacTheme.LIGHT)
    win_edit_light.resize(1280, 800)
    win_edit_light.set_workspace_mode("Edit")
    win_edit_light.show()
    for _ in range(10):
        app.processEvents()
    pix = win_edit_light.grab()
    p4 = os.path.join(out_dir, "redesign_light_edit_1280.png")
    pix.save(p4)
    screenshots.append(p4)
    win_edit_light.close()

    # 5. Dark Mode - Responsive Narrow (1024x720)
    win_resp_dark = MacMainWindow(initial_file=pdf_path)
    win_resp_dark.apply_theme(MacTheme.DARK)
    win_resp_dark.resize(1024, 720)
    win_resp_dark.set_workspace_mode("Edit")
    win_resp_dark.show()
    for _ in range(10):
        app.processEvents()
    pix = win_resp_dark.grab()
    p5 = os.path.join(out_dir, "redesign_dark_responsive_1024.png")
    pix.save(p5)
    screenshots.append(p5)
    win_resp_dark.close()

    # 6. Light Mode - Responsive Narrow (1024x720)
    win_resp_light = MacMainWindow(initial_file=pdf_path)
    win_resp_light.apply_theme(MacTheme.LIGHT)
    win_resp_light.resize(1024, 720)
    win_resp_light.set_workspace_mode("Edit")
    win_resp_light.show()
    for _ in range(10):
        app.processEvents()
    pix = win_resp_light.grab()
    p6 = os.path.join(out_dir, "redesign_light_responsive_1024.png")
    pix.save(p6)
    screenshots.append(p6)
    win_resp_light.close()

    # Copy all to artifact dir
    import shutil
    for path in screenshots:
        dest = os.path.join(artifact_dir, os.path.basename(path))
        shutil.copyfile(path, dest)
        print(f"Captured: {path} -> {dest}")

    # Clean up temp file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    main()
