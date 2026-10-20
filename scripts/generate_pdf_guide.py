#!/usr/bin/env python3
"""
Generates the PDF User Guide and Shortcut Cheat Sheet using PyMuPDF.
Strict visual style:
- A4 paper size (595.32 x 841.92 pt).
- Plain black text on white.
- Page numbers.
- No color blocks.
- Clean typography and structured tables.
"""

import json
import os
import time
import pymupdf

A4_WIDTH = 595.32
A4_HEIGHT = 841.92
MARGIN_LEFT = 54.0
MARGIN_RIGHT = 54.0
CONTENT_WIDTH = A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

def draw_header_footer(page, page_num: int, total_pages: int, title: str = "Preview for Linux and Windows — User Guide"):
    # Header line
    if page_num > 1:
        page.draw_line(pymupdf.Point(MARGIN_LEFT, 40), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, 40), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text(pymupdf.Point(MARGIN_LEFT, 34), "Preview for Linux and Windows — User Guide", fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))

    # Footer line and page number
    page.draw_line(pymupdf.Point(MARGIN_LEFT, A4_HEIGHT - 40), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, A4_HEIGHT - 40), color=(0.8, 0.8, 0.8), width=0.5)
    page_text = f"Page {page_num} of {total_pages}"
    page.insert_text(pymupdf.Point(A4_WIDTH - MARGIN_RIGHT - 60, A4_HEIGHT - 26), page_text, fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))
    page.insert_text(pymupdf.Point(MARGIN_LEFT, A4_HEIGHT - 26), "Apple Support / macOS User Guide Style", fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))

def generate_pdf_guide(output_pdf: str = "help/generated/preview_user_guide.pdf"):
    doc = pymupdf.open()
    date_str = time.strftime("%B %Y")
    version_str = "1.5.0"

    # --- Page 1: Cover ---
    p1 = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    p1.insert_text(pymupdf.Point(MARGIN_LEFT, 240), "Preview for Linux and Windows", fontname="hebo", fontsize=28, color=(0, 0, 0))
    p1.insert_text(pymupdf.Point(MARGIN_LEFT, 275), "User Guide & Reference Manual", fontname="helv", fontsize=16, color=(0.3, 0.3, 0.3))
    p1.draw_line(pymupdf.Point(MARGIN_LEFT, 295), pymupdf.Point(MARGIN_LEFT + 200, 295), color=(0, 0, 0), width=1.5)

    p1.insert_text(pymupdf.Point(MARGIN_LEFT, 330), f"Version {version_str} (Multiplatform Edition)", fontname="helv", fontsize=11, color=(0.2, 0.2, 0.2))
    p1.insert_text(pymupdf.Point(MARGIN_LEFT, 350), f"Published: {date_str}", fontname="helv", fontsize=11, color=(0.2, 0.2, 0.2))
    p1.insert_text(pymupdf.Point(MARGIN_LEFT, 370), "Developer: Shivam Prasad | Powered by TriviLabs.in", fontname="helv", fontsize=11, color=(0.2, 0.2, 0.2))

    summary_text = (
        "A calm, readable, and comprehensive user guide for Preview on Linux and Windows.\n"
        "Covers document viewing, PDF navigation, annotation tools, image adjustments,\n"
        "signatures, redactions, and keyboard shortcuts."
    )
    p1.insert_textbox(pymupdf.Rect(MARGIN_LEFT, 430, A4_WIDTH - MARGIN_RIGHT, 530), summary_text, fontname="helv", fontsize=11, color=(0.2, 0.2, 0.2), lineheight=1.5)

    # --- Page 2: Quick Start & Window Overview ---
    p2 = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    y = 65.0
    p2.insert_text(pymupdf.Point(MARGIN_LEFT, y), "1. Quick Start", fontname="hebo", fontsize=18, color=(0, 0, 0))
    y += 10
    p2.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.8, 0.8, 0.8), width=0.75)
    y += 24

    quick_steps = [
        "1. Open a Document: Click Open on the toolbar or press Ctrl + O to choose any PDF or image.",
        "2. Navigate Pages: Use Right Arrow and Left Arrow, or click the Sidebar button (Ctrl + B).",
        "3. Zoom and Pan: Press Ctrl + 9 to fit window, or hold Spacebar and drag mouse to pan.",
        "4. Annotate: Click the Markup button (Ctrl + Shift + A) to sketch, highlight, add text or notes.",
        "5. Save or Export: Press Ctrl + S to save, or select File > Export... (Ctrl + E) to convert formats."
    ]
    for step in quick_steps:
        p2.insert_text(pymupdf.Point(MARGIN_LEFT + 10, y), step, fontname="helv", fontsize=10.5, color=(0.1, 0.1, 0.1))
        y += 22

    y += 18
    p2.insert_text(pymupdf.Point(MARGIN_LEFT, y), "2. Window Overview", fontname="hebo", fontsize=18, color=(0, 0, 0))
    y += 10
    p2.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.8, 0.8, 0.8), width=0.75)
    y += 22

    overview_items = [
        ("Menubar & Top Toolbar", "Contains traffic lights, page navigation, segmented Open control, zoom, rotate, markup toggle, search box, and inspector button."),
        ("Left Sidebar", "Displays vertical Thumbnails, multi-column Contact Sheet, or the Table of Contents outline tree. Includes a thumbnail size slider."),
        ("Canvas Viewport", "Smooth high-DPI rendering surface for PDFs and images with loupe magnifier and selection marquee interaction."),
        ("Markup Toolbar", "Secondary 38px utility bar providing sketch pen, highlighter, shapes, text box, sticky notes, redaction, signatures, and color swatches.")
    ]
    for title, desc in overview_items:
        p2.insert_text(pymupdf.Point(MARGIN_LEFT + 10, y), f"• {title}:", fontname="hebo", fontsize=11, color=(0, 0, 0))
        y += 16
        rect = pymupdf.Rect(MARGIN_LEFT + 22, y - 10, A4_WIDTH - MARGIN_RIGHT, y + 25)
        p2.insert_textbox(rect, desc, fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2), lineheight=1.4)
        y += 34

    # --- Page 3: Feature Table ---
    p3 = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    y = 65.0
    p3.insert_text(pymupdf.Point(MARGIN_LEFT, y), "3. Feature Reference Table", fontname="hebo", fontsize=18, color=(0, 0, 0))
    y += 10
    p3.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.8, 0.8, 0.8), width=0.75)
    y += 24

    features = [
        ("Open & Recent", "File > Open... (Ctrl+O)", "Opens single PDF/image or multi-page image folders with recent history."),
        ("Sidebar & Outline", "View > Toggle Sidebar (Ctrl+B)", "Thumbnails, contact sheets, and chapter bookmarks with drag reordering."),
        ("Annotation & Markup", "Tools > Show Markup Toolbar", "Pen, highlighter, shapes, text, sticky notes, and line formatting."),
        ("Selection & Crop", "Tools > Crop (Ctrl+K)", "Rectangular, oval, and lasso cropping with 90° selection rotation."),
        ("Signature Pad", "Markup Toolbar > Signatures", "Smooth trackpad vector drawing pad with transparent PNG placement."),
        ("Redaction", "Edit > Apply All Redactions", "Permanent blackout sanitization destroying covered text and imagery."),
        ("Adjust Color", "Tools > Adjust Color... (Ctrl+Alt+C)", "Live RGB histogram with exposure, contrast, saturation, and tint sliders."),
        ("Adjust Size", "Tools > Adjust Size... (Ctrl+Alt+S)", "Pixel resampling and DPI resolution scaling with aspect ratio lock."),
        ("PDF Security", "File > Set PDF Password...", "AES-256 standard password encryption for confidential documents."),
        ("Export & Print", "File > Export... (Ctrl+E)", "Converts to PDF, PNG, JPEG, WebP, TIFF with quality and DPI options.")
    ]

    # Draw table headers
    p3.insert_text(pymupdf.Point(MARGIN_LEFT, y), "Feature", fontname="hebo", fontsize=10, color=(0, 0, 0))
    p3.insert_text(pymupdf.Point(MARGIN_LEFT + 120, y), "Location / Shortcut", fontname="hebo", fontsize=10, color=(0, 0, 0))
    p3.insert_text(pymupdf.Point(MARGIN_LEFT + 260, y), "Description", fontname="hebo", fontsize=10, color=(0, 0, 0))
    y += 6
    p3.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.5, 0.5, 0.5), width=1.0)
    y += 16

    for name, where, desc in features:
        p3.insert_text(pymupdf.Point(MARGIN_LEFT, y), name, fontname="hebo", fontsize=9.5, color=(0.1, 0.1, 0.1))
        p3.insert_text(pymupdf.Point(MARGIN_LEFT + 120, y), where, fontname="helv", fontsize=8.5, color=(0.3, 0.3, 0.3))
        rect = pymupdf.Rect(MARGIN_LEFT + 260, y - 9, A4_WIDTH - MARGIN_RIGHT, y + 22)
        p3.insert_textbox(rect, desc, fontname="helv", fontsize=8.5, color=(0.2, 0.2, 0.2), lineheight=1.3)
        y += 24
        p3.draw_line(pymupdf.Point(MARGIN_LEFT, y - 4), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y - 4), color=(0.9, 0.9, 0.9), width=0.5)

    # --- Page 4: Shortcuts Table ---
    p4 = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    y = 65.0
    p4.insert_text(pymupdf.Point(MARGIN_LEFT, y), "4. Keyboard Shortcuts Reference", fontname="hebo", fontsize=18, color=(0, 0, 0))
    y += 10
    p4.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.8, 0.8, 0.8), width=0.75)
    y += 20

    shortcut_sections = [
        ("File Operations", [
            ("Open File", "Ctrl + O"),
            ("Open Folder of Images", "Ctrl + Shift + O"),
            ("Save Changes", "Ctrl + S"),
            ("Duplicate / Save As New Copy", "Ctrl + Shift + S"),
            ("Export as PDF", "Ctrl + Shift + E"),
            ("Export Dialog", "Ctrl + E"),
            ("Print Document", "Ctrl + P"),
            ("Close Window", "Ctrl + W")
        ]),
        ("Navigation & View", [
            ("Next / Previous Page", "Right Arrow / Left Arrow"),
            ("First / Last Page", "Home / End"),
            ("Go to Page Dialog", "Ctrl + G"),
            ("Toggle Sidebar", "Ctrl + B"),
            ("Actual Size (100%)", "Ctrl + 0"),
            ("Zoom to Fit Window", "Ctrl + 9"),
            ("Zoom In / Zoom Out", "Ctrl + = / Ctrl + -"),
            ("Magnifier Loupe", "` (backtick) or ~")
        ]),
        ("Tools & Editing", [
            ("Toggle Markup Toolbar", "Ctrl + Shift + A"),
            ("Crop Selection", "Ctrl + K"),
            ("Rotate Page Right", "Ctrl + R"),
            ("Rotate Selection 90°", "Ctrl + R (with marquee)"),
            ("Rotate Page Left", "Ctrl + L"),
            ("Adjust Color Panel", "Ctrl + Alt + C"),
            ("Adjust Size Panel", "Ctrl + Alt + S"),
            ("Show Inspector", "Ctrl + I")
        ])
    ]

    for sec_title, s_list in shortcut_sections:
        p4.insert_text(pymupdf.Point(MARGIN_LEFT, y), sec_title, fontname="hebo", fontsize=12, color=(0, 0, 0))
        y += 6
        p4.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.7, 0.7, 0.7), width=0.75)
        y += 16
        for action, key in s_list:
            p4.insert_text(pymupdf.Point(MARGIN_LEFT + 10, y), action, fontname="helv", fontsize=9.5, color=(0.2, 0.2, 0.2))
            p4.insert_text(pymupdf.Point(MARGIN_LEFT + 280, y), key, fontname="hebo", fontsize=9.5, color=(0, 0, 0))
            y += 15
        y += 10

    # --- Page 5: Common Problems & Fixes (Troubleshooting) ---
    p5 = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    y = 65.0
    p5.insert_text(pymupdf.Point(MARGIN_LEFT, y), "5. Common Problems and Fixes", fontname="hebo", fontsize=18, color=(0, 0, 0))
    y += 10
    p5.draw_line(pymupdf.Point(MARGIN_LEFT, y), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y), color=(0.8, 0.8, 0.8), width=0.75)
    y += 24

    troubles = [
        ("Tools are disabled or not responding",
         "Cause: The secondary Markup Toolbar is hidden.\n"
         "Fix: Click the Markup button on the top toolbar or press Ctrl + Shift + A to reveal tools."),
        ("Crop and Rotate Selection buttons stay grayed out",
         "Cause: An active rectangular, oval, or lasso marquee has not been drawn.\n"
         "Fix: Select a selection tool from the Markup Toolbar and drag across canvas first."),
        ("Unsaved document modifications are lost",
         "Cause: The document was closed and Don't Save was clicked in the alert sheet.\n"
         "Fix: Always click Save or press Enter. Use Ctrl + S frequently while editing."),
        ("Adjust Color does not change PDF vector text",
         "Cause: Adjust Color operates on raster image pixels and photographic data.\n"
         "Fix: Use the Highlighter tool or font formatting controls for text pages."),
        ("Password-protected PDF will not open",
         "Cause: AES-256 encrypted documents require the security password to decrypt.\n"
         "Fix: Enter the password provided by the document creator.")
    ]

    for title, text in troubles:
        p5.insert_text(pymupdf.Point(MARGIN_LEFT, y), f"Problem: {title}", fontname="hebo", fontsize=11, color=(0.8, 0.1, 0.1))
        y += 16
        rect = pymupdf.Rect(MARGIN_LEFT + 12, y - 8, A4_WIDTH - MARGIN_RIGHT, y + 36)
        p5.insert_textbox(rect, text, fontname="helv", fontsize=9.5, color=(0.2, 0.2, 0.2), lineheight=1.4)
        y += 44
        p5.draw_line(pymupdf.Point(MARGIN_LEFT, y - 6), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, y - 6), color=(0.9, 0.9, 0.9), width=0.5)

    # Add header/footer to all pages
    total_pages = doc.page_count
    for i in range(total_pages):
        draw_header_footer(doc[i], i + 1, total_pages)

    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    doc.save(output_pdf)
    print(f"Generated PDF Guide: {output_pdf} ({total_pages} pages)")

def generate_shortcut_cheatsheet(output_pdf: str = "help/generated/preview_shortcuts_cheatsheet.pdf"):
    """Generates a crisp single-page A4 shortcut cheat sheet."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)

    # Header
    page.insert_text(pymupdf.Point(MARGIN_LEFT, 50), "Preview for Linux and Windows — Keyboard Shortcut Cheat Sheet", fontname="hebo", fontsize=16, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(MARGIN_LEFT, 68), "Essential productivity hotkeys for document navigation, editing, and markup", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
    page.draw_line(pymupdf.Point(MARGIN_LEFT, 78), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, 78), color=(0, 0, 0), width=1.0)

    # Two-column layout
    col1_x = MARGIN_LEFT
    col2_x = MARGIN_LEFT + 250.0

    groups = [
        # Col 1
        (col1_x, 100, "Document & File", [
            ("Open File", "Ctrl + O"),
            ("Open Folder", "Ctrl + Shift + O"),
            ("Save Changes", "Ctrl + S"),
            ("Duplicate / Save As", "Ctrl + Shift + S"),
            ("Export as PDF", "Ctrl + Shift + E"),
            ("Export Dialog", "Ctrl + E"),
            ("Print Document", "Ctrl + P"),
            ("Close Window", "Ctrl + W"),
            ("Quit Application", "Ctrl + Q")
        ]),
        (col1_x, 305, "Navigation & Display", [
            ("Next Page", "Right Arrow / Down Arrow"),
            ("Previous Page", "Left Arrow / Up Arrow"),
            ("First Page / Last Page", "Home / End"),
            ("Go to Page Dialog", "Ctrl + G"),
            ("Toggle Sidebar", "Ctrl + B"),
            ("Actual Size (100%)", "Ctrl + 0"),
            ("Zoom to Fit Window", "Ctrl + 9"),
            ("Zoom In / Zoom Out", "Ctrl + = / Ctrl + -"),
            ("Magnifier Loupe", "` (backtick) or ~"),
            ("Slideshow Mode", "F5"),
            ("Frameless Mode", "F11")
        ]),
        # Col 2
        (col2_x, 100, "Annotation & Markup", [
            ("Toggle Markup Bar", "Ctrl + Shift + A"),
            ("Pointer / Select Mode", "Esc"),
            ("Crop Selection", "Ctrl + K"),
            ("Rotate Selection 90°", "Ctrl + R"),
            ("Rotate Page Left", "Ctrl + L"),
            ("Rotate Page Right", "Ctrl + R"),
            ("Undo Last Action", "Ctrl + Z"),
            ("Redo Action", "Ctrl + Shift + Z"),
            ("Delete Item / Page", "Delete"),
            ("Insert Blank Page", "Ctrl + Shift + N")
        ]),
        (col2_x, 320, "Tools & Preferences", [
            ("Adjust Color Panel", "Ctrl + Alt + C"),
            ("Adjust Size Panel", "Ctrl + Alt + S"),
            ("Show Inspector", "Ctrl + I"),
            ("Dark / Light Theme", "Ctrl + T"),
            ("Preferences", "Ctrl + ,"),
            ("Search Document", "Ctrl + F"),
            ("Preview Help", "F1")
        ])
    ]

    for col_x, start_y, heading, items in groups:
        page.insert_text(pymupdf.Point(col_x, start_y), heading, fontname="hebo", fontsize=12, color=(0, 0, 0))
        page.draw_line(pymupdf.Point(col_x, start_y + 4), pymupdf.Point(col_x + 230, start_y + 4), color=(0.8, 0.8, 0.8), width=0.5)
        y = start_y + 18
        for act, key in items:
            page.insert_text(pymupdf.Point(col_x, y), act, fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
            page.insert_text(pymupdf.Point(col_x + 130, y), key, fontname="hebo", fontsize=9, color=(0, 0, 0))
            y += 16

    # Bottom tips box
    page.draw_line(pymupdf.Point(MARGIN_LEFT, A4_HEIGHT - 80), pymupdf.Point(A4_WIDTH - MARGIN_RIGHT, A4_HEIGHT - 80), color=(0.8, 0.8, 0.8), width=0.5)
    page.insert_text(pymupdf.Point(MARGIN_LEFT, A4_HEIGHT - 62), "Tips: Shortcuts use Ctrl on Linux and Windows, or Cmd on macOS. Press F1 inside any window to open Preview Help.", fontname="helv", fontsize=8.5, color=(0.4, 0.4, 0.4))
    page.insert_text(pymupdf.Point(MARGIN_LEFT, A4_HEIGHT - 48), "Preview for Linux and Windows — Generated with PyMuPDF | Calm, readable software documentation.", fontname="helv", fontsize=8.5, color=(0.4, 0.4, 0.4))

    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    doc.save(output_pdf)
    print(f"Generated Shortcut Cheat Sheet: {output_pdf} (1 page)")

if __name__ == "__main__":
    generate_pdf_guide()
    generate_shortcut_cheatsheet()
