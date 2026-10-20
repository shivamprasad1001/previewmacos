import os
import json
import fitz  # PyMuPDF

def generate_pdf_guides(data_path="preview/data/help_data.json", output_dir="preview/data"):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    full_guide_path = os.path.join(output_dir, "preview_macos_user_guide.pdf")
    cheatsheet_path = os.path.join(output_dir, "preview_macos_cheatsheet.pdf")

    # A4 Dimensions: 595.28 x 841.89 points
    page_w, page_h = 595.28, 841.89

    # 1. Full Multi-Page Guide
    doc = fitz.open()

    # --- Cover & Quick Start Page ---
    page1 = doc.new_page(width=page_w, height=page_h)
    # Background & Header Band
    header_rect = fitz.Rect(0, 0, page_w, 140)
    page1.draw_rect(header_rect, color=None, fill=(0.04, 0.52, 1.0)) # #0a84ff

    # Title & Subtitle
    page1.insert_text(fitz.Point(40, 60), "Document Viewer for Linux", fontsize=24, color=(1, 1, 1), fontname="helv", fontfile=None)
    page1.insert_text(fitz.Point(40, 90), "Complete User Guide & Feature Manual (macOS Preview Clone)", fontsize=13, color=(0.9, 0.95, 1), fontname="helv")
    page1.insert_text(fitz.Point(40, 115), f"Version {data.get('version', '1.4.0')}  |  Updated: {data.get('updated_at', '2026-10-20')}", fontsize=10, color=(0.85, 0.9, 1), fontname="helv")

    # Section 1: Quick Start (5 steps)
    page1.insert_text(fitz.Point(40, 175), "Quick Start Guide (5 Simple Steps)", fontsize=15, color=(0.1, 0.1, 0.1), fontname="helv")
    page1.draw_line(fitz.Point(40, 185), fitz.Point(page_w - 40, 185), color=(0.8, 0.8, 0.8), width=1)

    steps = [
        ("1. Open File or Folder", "Click Open (Ctrl+O) to load PDFs or images. Click the arrow to open photo folders."),
        ("2. Navigate Pages", "Open the sidebar (Ctrl+B) to browse thumbnails. Use arrow keys or Page Down to scroll."),
        ("3. Markup & Annotate", "Click Markup (Ctrl+Shift+A) to access pens, highlighters, shapes, text, and signatures."),
        ("4. Adjust & Crop", "Use Rectangular, Oval, or Lasso selection to crop (Ctrl+K). Press Ctrl+Alt+C for color grading."),
        ("5. Save & Export", "Press Ctrl+S to save edits. Choose File > Export (Ctrl+E) or Export as PDF (Ctrl+Shift+E).")
    ]

    y_cur = 215
    for title, desc in steps:
        # Step number badge
        badge_rect = fitz.Rect(40, y_cur - 12, 60, y_cur + 8)
        page1.draw_rect(badge_rect, color=None, fill=(0.04, 0.52, 1.0))
        page1.insert_text(fitz.Point(45, y_cur + 2), title[:2].strip(), fontsize=11, color=(1, 1, 1), fontname="helv")

        page1.insert_text(fitz.Point(70, y_cur), title, fontsize=11, color=(0.1, 0.1, 0.1), fontname="helv")
        page1.insert_text(fitz.Point(70, y_cur + 16), desc, fontsize=9.5, color=(0.35, 0.35, 0.35), fontname="helv")
        y_cur += 42

    # Section 2: Essential Shortcut Keys
    y_cur += 15
    page1.insert_text(fitz.Point(40, y_cur), "Essential Keyboard Shortcuts", fontsize=15, color=(0.1, 0.1, 0.1), fontname="helv")
    page1.draw_line(fitz.Point(40, y_cur + 10), fitz.Point(page_w - 40, y_cur + 10), color=(0.8, 0.8, 0.8), width=1)
    y_cur += 30

    shortcuts = [
        ("Ctrl + O", "Open Document / Images", "Ctrl + S", "Save Edits"),
        ("Ctrl + Shift + S", "Duplicate / Save As", "Ctrl + E", "Export File"),
        ("Ctrl + Shift + E", "Export as PDF", "Ctrl + P", "Print Document"),
        ("Ctrl + B", "Toggle Sidebar", "Ctrl + Shift + A", "Toggle Markup Toolbar"),
        ("Ctrl + K", "Crop Selection", "Ctrl + R / Ctrl + L", "Rotate 90° Clockwise / CCW"),
        ("Ctrl + Alt + C", "Adjust Color Dialog", "Ctrl + Alt + S", "Adjust Size Dialog"),
        ("Ctrl + I", "Show Inspector", "Ctrl + T", "Toggle Dark / Light Theme"),
        ("Ctrl + F", "Find in Document", "Ctrl + Shift + F", "Fullscreen Slideshow")
    ]

    col1_x, col2_x = 40, 305
    for k1, desc1, k2, desc2 in shortcuts:
        page1.insert_text(fitz.Point(col1_x, y_cur), f"[{k1}]", fontsize=9.5, color=(0.04, 0.52, 1.0), fontname="helv")
        page1.insert_text(fitz.Point(col1_x + 85, y_cur), desc1, fontsize=9.5, color=(0.2, 0.2, 0.2), fontname="helv")

        page1.insert_text(fitz.Point(col2_x, y_cur), f"[{k2}]", fontsize=9.5, color=(0.04, 0.52, 1.0), fontname="helv")
        page1.insert_text(fitz.Point(col2_x + 95, y_cur), desc2, fontsize=9.5, color=(0.2, 0.2, 0.2), fontname="helv")
        y_cur += 22

    # Footer
    page1.insert_text(fitz.Point(40, page_h - 30), "Page 1 of 3  •  Document Viewer Help & Documentation", fontsize=8.5, color=(0.6, 0.6, 0.6), fontname="helv")

    # --- Page 2: Feature Cheat Sheet Table ---
    page2 = doc.new_page(width=page_w, height=page_h)
    page2.insert_text(fitz.Point(40, 45), "Feature & Tool Directory Cheat Sheet", fontsize=16, color=(0.1, 0.1, 0.1), fontname="helv")
    page2.insert_text(fitz.Point(40, 62), "Comprehensive reference of tools, actions, and menu paths.", fontsize=9.5, color=(0.5, 0.5, 0.5), fontname="helv")
    page2.draw_line(fitz.Point(40, 72), fitz.Point(page_w - 40, 72), color=(0.8, 0.8, 0.8), width=1)

    # Table Header
    th_rect = fitz.Rect(40, 80, page_w - 40, 102)
    page2.draw_rect(th_rect, color=None, fill=(0.94, 0.94, 0.96))
    page2.insert_text(fitz.Point(46, 95), "Tool / Feature", fontsize=9.5, color=(0.1, 0.1, 0.1), fontname="helv")
    page2.insert_text(fitz.Point(180, 95), "Menu Path / Location", fontsize=9.5, color=(0.1, 0.1, 0.1), fontname="helv")
    page2.insert_text(fitz.Point(360, 95), "Purpose & Action", fontsize=9.5, color=(0.1, 0.1, 0.1), fontname="helv")
    page2.insert_text(fitz.Point(510, 95), "Shortcut", fontsize=9.5, color=(0.1, 0.1, 0.1), fontname="helv")

    ty = 118
    # Print first 24 entries
    for item in data.get("dictionary", [])[:24]:
        name = item.get("name", "")
        where = item.get("where", "")[:35]
        meaning = item.get("meaning", "")[:42] + ("..." if len(item.get("meaning", "")) > 42 else "")
        sc = item.get("shortcut", "—") or "—"

        page2.insert_text(fitz.Point(46, ty), name[:22], fontsize=8.5, color=(0.04, 0.52, 1.0), fontname="helv")
        page2.insert_text(fitz.Point(180, ty), where, fontsize=8, color=(0.3, 0.3, 0.3), fontname="helv")
        page2.insert_text(fitz.Point(360, ty), meaning, fontsize=8, color=(0.2, 0.2, 0.2), fontname="helv")
        page2.insert_text(fitz.Point(510, ty), sc, fontsize=8, color=(0.4, 0.4, 0.4), fontname="helv")
        ty += 28

    page2.insert_text(fitz.Point(40, page_h - 30), "Page 2 of 3  •  Feature Directory Cheat Sheet", fontsize=8.5, color=(0.6, 0.6, 0.6), fontname="helv")

    # --- Page 3: Troubleshooting, Errors, Contact & Support ---
    page3 = doc.new_page(width=page_w, height=page_h)
    page3.insert_text(fitz.Point(40, 45), "Troubleshooting, Common Errors & Support", fontsize=16, color=(0.1, 0.1, 0.1), fontname="helv")
    page3.draw_line(fitz.Point(40, 58), fitz.Point(page_w - 40, 58), color=(0.8, 0.8, 0.8), width=1)

    ey = 85
    page3.insert_text(fitz.Point(40, ey), "Common Error Messages & Quick Fixes", fontsize=13, color=(0.1, 0.1, 0.1), fontname="helv")
    ey += 20

    for err in data.get("troubleshooting", []):
        err_box = fitz.Rect(40, ey - 10, page_w - 40, ey + 42)
        page3.draw_rect(err_box, color=(0.9, 0.9, 0.9), fill=(0.98, 0.98, 0.99))
        page3.insert_text(fitz.Point(50, ey + 4), f"Error: {err.get('error')}", fontsize=9.5, color=(0.85, 0.2, 0.2), fontname="helv")
        page3.insert_text(fitz.Point(50, ey + 18), f"Cause: {err.get('cause')}", fontsize=8.5, color=(0.4, 0.4, 0.4), fontname="helv")
        page3.insert_text(fitz.Point(50, ey + 32), f"Fix: {err.get('fix')}", fontsize=8.5, color=(0.1, 0.6, 0.2), fontname="helv")
        ey += 60

    # FAQ Highlights
    ey += 15
    page3.insert_text(fitz.Point(40, ey), "Frequently Asked Questions", fontsize=13, color=(0.1, 0.1, 0.1), fontname="helv")
    ey += 20
    for faq in data.get("faq", [])[:4]:
        page3.insert_text(fitz.Point(40, ey), f"Q: {faq.get('q')}", fontsize=9, color=(0.1, 0.1, 0.1), fontname="helv")
        page3.insert_text(fitz.Point(40, ey + 13), f"A: {faq.get('a')}", fontsize=8.5, color=(0.35, 0.35, 0.35), fontname="helv")
        ey += 32

    # Support & Contact Box
    ey += 20
    contact_box = fitz.Rect(40, ey, page_w - 40, ey + 100)
    page3.draw_rect(contact_box, color=None, fill=(0.95, 0.97, 1.0))
    page3.draw_rect(contact_box, color=(0.7, 0.85, 1.0), width=1)
    page3.insert_text(fitz.Point(55, ey + 25), "Contact & Technical Support", fontsize=12, color=(0.04, 0.52, 1.0), fontname="helv")
    page3.insert_text(fitz.Point(55, ey + 48), "GitHub Project: https://github.com/shivamprasad1001/previewmacos", fontsize=9, color=(0.2, 0.2, 0.2), fontname="helv")
    page3.insert_text(fitz.Point(55, ey + 66), "Report Issues & Request Features: https://github.com/shivamprasad1001/previewmacos/issues", fontsize=9, color=(0.2, 0.2, 0.2), fontname="helv")
    page3.insert_text(fitz.Point(55, ey + 84), "Built with Python, PyQt6, and PyMuPDF for Linux Desktop.", fontsize=8.5, color=(0.5, 0.5, 0.5), fontname="helv")

    page3.insert_text(fitz.Point(40, page_h - 30), "Page 3 of 3  •  Troubleshooting & Support", fontsize=8.5, color=(0.6, 0.6, 0.6), fontname="helv")

    doc.save(full_guide_path)
    print("Generated full guide:", full_guide_path)

    # 2. One-Page Cheat Sheet PDF
    doc_single = fitz.open()
    sp = doc_single.new_page(width=page_w, height=page_h)
    # Header
    sp.draw_rect(fitz.Rect(0, 0, page_w, 65), color=None, fill=(0.04, 0.52, 1.0))
    sp.insert_text(fitz.Point(40, 35), "Document Viewer — 1-Page Cheat Sheet", fontsize=18, color=(1, 1, 1), fontname="helv")
    sp.insert_text(fitz.Point(40, 52), f"Version {data.get('version')}  |  Complete Quick Reference", fontsize=9, color=(0.9, 0.95, 1), fontname="helv")

    sy = 90
    sp.insert_text(fitz.Point(40, sy), "Keyboard Shortcuts", fontsize=12, color=(0.1, 0.1, 0.1), fontname="helv")
    sp.draw_line(fitz.Point(40, sy + 6), fitz.Point(page_w - 40, sy + 6), color=(0.85, 0.85, 0.85), width=1)
    sy += 22

    for k1, d1, k2, d2 in shortcuts:
        sp.insert_text(fitz.Point(40, sy), f"[{k1}]", fontsize=8.5, color=(0.04, 0.52, 1.0), fontname="helv")
        sp.insert_text(fitz.Point(120, sy), d1, fontsize=8.5, color=(0.2, 0.2, 0.2), fontname="helv")
        sp.insert_text(fitz.Point(305, sy), f"[{k2}]", fontsize=8.5, color=(0.04, 0.52, 1.0), fontname="helv")
        sp.insert_text(fitz.Point(395, sy), d2, fontsize=8.5, color=(0.2, 0.2, 0.2), fontname="helv")
        sy += 18

    sy += 16
    sp.insert_text(fitz.Point(40, sy), "Core Tools & Features", fontsize=12, color=(0.1, 0.1, 0.1), fontname="helv")
    sp.draw_line(fitz.Point(40, sy + 6), fitz.Point(page_w - 40, sy + 6), color=(0.85, 0.85, 0.85), width=1)
    sy += 22

    for item in data.get("dictionary", [])[:18]:
        sp.insert_text(fitz.Point(40, sy), item["name"][:20], fontsize=8.5, color=(0.04, 0.52, 1.0), fontname="helv")
        sp.insert_text(fitz.Point(170, sy), item["where"][:32], fontsize=8, color=(0.4, 0.4, 0.4), fontname="helv")
        sp.insert_text(fitz.Point(340, sy), item["meaning"][:45], fontsize=8, color=(0.2, 0.2, 0.2), fontname="helv")
        sy += 18

    sy += 16
    sp.insert_text(fitz.Point(40, sy), "Quick 5-Step Workflow", fontsize=12, color=(0.1, 0.1, 0.1), fontname="helv")
    sp.draw_line(fitz.Point(40, sy + 6), fitz.Point(page_w - 40, sy + 6), color=(0.85, 0.85, 0.85), width=1)
    sy += 20
    for title, desc in steps:
        sp.insert_text(fitz.Point(40, sy), f"• {title}:", fontsize=8.5, color=(0.1, 0.1, 0.1), fontname="helv")
        sp.insert_text(fitz.Point(170, sy), desc, fontsize=8, color=(0.4, 0.4, 0.4), fontname="helv")
        sy += 16

    sp.insert_text(fitz.Point(40, page_h - 20), "Preview macOS Linux Edition  •  1-Page Cheat Sheet", fontsize=8, color=(0.6, 0.6, 0.6), fontname="helv")

    doc_single.save(cheatsheet_path)
    print("Generated 1-page cheatsheet:", cheatsheet_path)

if __name__ == "__main__":
    generate_pdf_guides()
