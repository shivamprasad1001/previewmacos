import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QRectF, QPointF

def create_guide_screenshots():
    os.makedirs("preview/assets/help", exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)

    # We will generate crisp synthetic UI mockups representing the real app's UI for light & dark themes
    screens = [
        ("guide-sidebar-thumbnails", "Sidebar & Thumbnails", "sidebar"),
        ("guide-toolbar-overview", "Navigation & Main Toolbar", "toolbar"),
        ("guide-markup-tools", "Markup & Annotation Bar", "markup"),
        ("guide-adjust-color", "Adjust Color Dialog", "color_dialog"),
        ("guide-adjust-size", "Adjust Size Dialog", "size_dialog"),
        ("guide-export-options", "Export & Conversion", "export_dialog"),
        ("guide-signature-manager", "Signature Capture", "signature_dialog"),
        ("guide-inspector-panel", "Inspector Panel", "inspector_dialog")
    ]

    for filename, title, mode in screens:
        for theme in ["light", "dark"]:
            w, h = 860, 520
            img = QImage(w, h, QImage.Format.Format_ARGB32)
            is_dark = (theme == "dark")
            bg_col = QColor("#1e1e1e") if is_dark else QColor("#f6f6f6")
            panel_col = QColor("#2d2d2d") if is_dark else QColor("#ffffff")
            text_col = QColor("#f0f0f0") if is_dark else QColor("#1c1c1e")
            sub_col = QColor("#999999") if is_dark else QColor("#666666")
            border_col = QColor("#3e3e3e") if is_dark else QColor("#e0e0e0")
            accent_col = QColor("#0a84ff")

            img.fill(bg_col)
            p = QPainter(img)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Window frame border
            p.setPen(QPen(border_col, 1))
            p.setBrush(QBrush(panel_col))
            p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 10, 10)

            # Title bar
            p.setPen(Qt.PenStyle.NoPen)
            tb_bg = QColor("#262626") if is_dark else QColor("#ececec")
            p.setBrush(QBrush(tb_bg))
            p.drawRoundedRect(QRectF(1, 1, w - 2, 42), 10, 10)
            p.drawRect(QRectF(1, 30, w - 2, 12))

            # Traffic lights
            p.setBrush(QBrush(QColor("#ff5f56")))
            p.drawEllipse(QRectF(16, 14, 12, 12))
            p.setBrush(QBrush(QColor("#ffbd2e")))
            p.drawEllipse(QRectF(36, 14, 12, 12))
            p.setBrush(QBrush(QColor("#27c93f")))
            p.drawEllipse(QRectF(56, 14, 12, 12))

            # Title text
            p.setFont(QFont("Inter, sans-serif", 11, QFont.Weight.Medium))
            p.setPen(text_col)
            p.drawText(QRectF(0, 0, w, 42), Qt.AlignmentFlag.AlignCenter, f"Document Viewer — {title}")

            # Specific screen contents
            if mode == "sidebar":
                # Sidebar left panel
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(QColor("#252526") if is_dark else QColor("#f0f0f2")))
                p.drawRect(QRectF(1, 43, 200, h - 44))
                # Dropdown
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(12, 54, 176, 26), 5, 5)
                p.setFont(QFont("Inter, sans-serif", 9))
                p.setPen(text_col)
                p.drawText(QRectF(22, 54, 150, 26), Qt.AlignmentFlag.AlignVCenter, "Thumbnails ▼")
                # Thumbs cards
                for i in range(3):
                    card_y = 92 + i * 115
                    p.setPen(QPen(accent_col if i == 0 else border_col, 2 if i == 0 else 1))
                    p.setBrush(QBrush(panel_col))
                    p.drawRoundedRect(QRectF(40, card_y, 120, 85), 6, 6)
                    p.setPen(sub_col)
                    p.drawText(QRectF(40, card_y + 90, 120, 18), Qt.AlignmentFlag.AlignCenter, f"{i+1}")
                # Main canvas preview
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(QColor("#ffffff") if is_dark else QColor("#ffffff")))
                p.drawRoundedRect(QRectF(240, 65, 580, 425), 4, 4)
                p.setPen(QColor("#333333"))
                p.drawText(QRectF(270, 95, 520, 30), Qt.AlignmentFlag.AlignLeft, "Quarterly Report Overview")

            elif mode == "toolbar":
                # Top toolbar items
                tb_y = 50
                p.setBrush(QBrush(QColor("#333333") if is_dark else QColor("#e8e8e8")))
                p.setPen(QPen(border_col, 1))
                p.drawRoundedRect(QRectF(16, tb_y, 80, 28), 6, 6)
                p.setPen(text_col)
                p.setFont(QFont("Inter, sans-serif", 9))
                p.drawText(QRectF(16, tb_y, 80, 28), Qt.AlignmentFlag.AlignCenter, "Sidebar")

                p.drawRoundedRect(QRectF(106, tb_y, 85, 28), 6, 6)
                p.drawText(QRectF(106, tb_y, 85, 28), Qt.AlignmentFlag.AlignCenter, "Open ▼")

                p.drawRoundedRect(QRectF(w - 230, tb_y, 110, 28), 14, 14)
                p.setPen(sub_col)
                p.drawText(QRectF(w - 220, tb_y, 90, 28), Qt.AlignmentFlag.AlignVCenter, "🔍 Search...")

                p.setPen(text_col)
                p.drawRoundedRect(QRectF(w - 110, tb_y, 85, 28), 6, 6)
                p.drawText(QRectF(w - 110, tb_y, 85, 28), Qt.AlignmentFlag.AlignCenter, "Markup")

                # Canvas
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(60, 100, 740, 390), 6, 6)

            elif mode == "markup":
                # Markup toolbar
                p.setBrush(QBrush(QColor("#252526") if is_dark else QColor("#eaeaea")))
                p.setPen(QPen(border_col, 1))
                p.drawRect(QRectF(1, 43, w - 2, 38))
                tools = ["Select ▼", "Shapes ▼", "Pen", "Highlighter", "Text", "Note", "Redact", "Sign", "Color", "Rotate", "Crop"]
                cur_x = 16
                p.setFont(QFont("Inter, sans-serif", 9))
                for idx, t in enumerate(tools):
                    btn_w = 64 if "▼" in t else (50 if len(t) < 6 else 60)
                    is_active = (idx == 0)
                    p.setBrush(QBrush(accent_col if is_active else panel_col))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawRoundedRect(QRectF(cur_x, 48, btn_w, 28), 5, 5)
                    p.setPen(QColor("#ffffff") if is_active else text_col)
                    p.drawText(QRectF(cur_x, 48, btn_w, 28), Qt.AlignmentFlag.AlignCenter, t)
                    cur_x += btn_w + 6

                # Document with sample highlight & shape
                p.setBrush(QBrush(panel_col))
                p.setPen(QPen(border_col, 1))
                p.drawRoundedRect(QRectF(100, 100, 660, 390), 4, 4)
                # Sample highlight
                p.setBrush(QBrush(QColor(255, 235, 59, 120)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(140, 150, 240, 24))
                # Sample red rectangle
                p.setPen(QPen(QColor("#ff3b30"), 3))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(QRectF(140, 200, 280, 120), 4, 4)

            elif mode == "color_dialog":
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(220, 70, 420, 410), 10, 10)
                p.setFont(QFont("Inter, sans-serif", 12, QFont.Weight.Bold))
                p.setPen(text_col)
                p.drawText(QRectF(240, 90, 380, 30), Qt.AlignmentFlag.AlignLeft, "Adjust Color")
                sliders = ["Exposure", "Contrast", "Highlights", "Shadows", "Saturation", "Temperature", "Tint", "Sepia", "Sharpness"]
                p.setFont(QFont("Inter, sans-serif", 9))
                for idx, s in enumerate(sliders):
                    sy = 130 + idx * 32
                    p.setPen(sub_col)
                    p.drawText(QRectF(240, sy, 90, 20), Qt.AlignmentFlag.AlignVCenter, s)
                    p.setPen(QPen(border_col, 3))
                    p.drawLine(QPointF(340, sy + 10), QPointF(580, sy + 10))
                    # Handle
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(accent_col))
                    p.drawEllipse(QRectF(460, sy + 4, 12, 12))

            elif mode == "size_dialog":
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(220, 80, 420, 380), 10, 10)
                p.setFont(QFont("Inter, sans-serif", 12, QFont.Weight.Bold))
                p.setPen(text_col)
                p.drawText(QRectF(240, 100, 380, 30), Qt.AlignmentFlag.AlignLeft, "Adjust Size")
                p.setFont(QFont("Inter, sans-serif", 9))
                fields = [("Width:", "1920 pixels"), ("Height:", "1080 pixels"), ("Resolution:", "72 pixels/inch")]
                for idx, (lbl, val) in enumerate(fields):
                    fy = 150 + idx * 45
                    p.setPen(sub_col)
                    p.drawText(QRectF(240, fy, 100, 28), Qt.AlignmentFlag.AlignVCenter, lbl)
                    p.setBrush(QBrush(QColor("#333333") if is_dark else QColor("#ececec")))
                    p.setPen(QPen(border_col, 1))
                    p.drawRoundedRect(QRectF(350, fy, 180, 28), 5, 5)
                    p.setPen(text_col)
                    p.drawText(QRectF(360, fy, 160, 28), Qt.AlignmentFlag.AlignVCenter, val)

            elif mode == "export_dialog":
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(200, 75, 460, 390), 10, 10)
                p.setFont(QFont("Inter, sans-serif", 12, QFont.Weight.Bold))
                p.setPen(text_col)
                p.drawText(QRectF(230, 95, 400, 30), Qt.AlignmentFlag.AlignLeft, "Export Image")
                p.setFont(QFont("Inter, sans-serif", 9))
                rows = [("Format:", "PNG (Portable Network Graphics)"), ("Quality:", "Best (100%)"), ("Color Space:", "sRGB"), ("Embed Profile:", "[x] Preserve Color Profile")]
                for idx, (lbl, val) in enumerate(rows):
                    ry = 145 + idx * 45
                    p.setPen(sub_col)
                    p.drawText(QRectF(230, ry, 100, 28), Qt.AlignmentFlag.AlignVCenter, lbl)
                    p.setBrush(QBrush(QColor("#333333") if is_dark else QColor("#ececec")))
                    p.setPen(QPen(border_col, 1))
                    p.drawRoundedRect(QRectF(340, ry, 260, 28), 5, 5)
                    p.setPen(text_col)
                    p.drawText(QRectF(350, ry, 240, 28), Qt.AlignmentFlag.AlignVCenter, val)

            elif mode == "signature_dialog":
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(200, 80, 460, 380), 10, 10)
                p.setFont(QFont("Inter, sans-serif", 12, QFont.Weight.Bold))
                p.setPen(text_col)
                p.drawText(QRectF(230, 100, 400, 30), Qt.AlignmentFlag.AlignLeft, "Create Signature")
                # Drawing canvas box
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(QColor("#222222") if is_dark else QColor("#f9f9f9")))
                p.drawRoundedRect(QRectF(230, 140, 400, 200), 6, 6)
                # Guide baseline
                p.setPen(QPen(QColor("#444444") if is_dark else QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(250, 280), QPointF(610, 280))
                # Signature sample
                p.setPen(QPen(QColor("#007aff"), 2))
                p.drawPolyline([QPointF(260, 270), QPointF(280, 250), QPointF(300, 275), QPointF(320, 230), QPointF(340, 280), QPointF(370, 260)])

            elif mode == "inspector_dialog":
                p.setPen(QPen(border_col, 1))
                p.setBrush(QBrush(panel_col))
                p.drawRoundedRect(QRectF(240, 70, 380, 410), 10, 10)
                p.setFont(QFont("Inter, sans-serif", 12, QFont.Weight.Bold))
                p.setPen(text_col)
                p.drawText(QRectF(265, 95, 330, 30), Qt.AlignmentFlag.AlignLeft, "Document Inspector")
                p.setFont(QFont("Inter, sans-serif", 9))
                info = [
                    ("File Name:", "annual_summary_2026.pdf"),
                    ("File Size:", "2.4 MB (2,516,582 bytes)"),
                    ("Document Format:", "PDF 1.7"),
                    ("Page Count:", "18 Pages"),
                    ("Dimensions:", "612 x 792 pt (Letter)"),
                    ("Security:", "Password Encrypted (AES-256)"),
                    ("Color Space:", "DeviceRGB (8-bit)")
                ]
                for idx, (k, v) in enumerate(info):
                    iy = 140 + idx * 36
                    p.setPen(sub_col)
                    p.drawText(QRectF(265, iy, 110, 20), Qt.AlignmentFlag.AlignVCenter, k)
                    p.setPen(text_col)
                    p.drawText(QRectF(380, iy, 215, 20), Qt.AlignmentFlag.AlignVCenter, v)

            p.end()
            out_path = f"preview/assets/help/{filename}-{theme}.png"
            img.save(out_path)
            print(f"Generated {out_path}")

if __name__ == "__main__":
    create_guide_screenshots()
