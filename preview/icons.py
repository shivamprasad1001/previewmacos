"""
High-definition vector icon renderer for macOS Preview tools.
Generates razor-sharp, resolution-independent SF Symbols styled icons.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF

class MacIconFactory:
    """Creates crisp macOS SF Symbols style icons using QPainter vector paths."""

    @staticmethod
    def create_icon(name: str, color_hex: str = "#f5f5f7", size: int = 24) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(color_hex)
        pen = QPen(color)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        s = float(size)
        pad = s * 0.15
        rect = QRectF(pad, pad, s - 2 * pad, s - 2 * pad)

        try:
            method = getattr(MacIconFactory, f"_draw_{name}", None)
            if method:
                method(painter, rect, color, pen)
            else:
                MacIconFactory._draw_default(painter, rect, color, pen)
        finally:
            painter.end()

        return QIcon(pixmap)

    @staticmethod
    def _draw_sidebar(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Window rectangle with left sidebar divider
        painter.drawRoundedRect(r, 3, 3)
        sidebar_x = r.left() + r.width() * 0.35
        painter.drawLine(QPointF(sidebar_x, r.top()), QPointF(sidebar_x, r.bottom()))

    @staticmethod
    def _draw_thumbnails(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # 4 small squares
        hw = (r.width() - 3) / 2
        hh = (r.height() - 3) / 2
        painter.drawRoundedRect(QRectF(r.left(), r.top(), hw, hh), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(r.left() + hw + 3, r.top(), hw, hh), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(r.left(), r.top() + hh + 3, hw, hh), 1.5, 1.5)
        painter.drawRoundedRect(QRectF(r.left() + hw + 3, r.top() + hh + 3, hw, hh), 1.5, 1.5)

    @staticmethod
    def _draw_zoom_in(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Magnifying glass with +
        cx = r.left() + r.width() * 0.42
        cy = r.top() + r.height() * 0.42
        rad = r.width() * 0.35
        painter.drawEllipse(QPointF(cx, cy), rad, rad)
        # Handle
        hx1 = cx + rad * 0.707
        hy1 = cy + rad * 0.707
        hx2 = r.right()
        hy2 = r.bottom()
        pen_thick = QPen(color)
        pen_thick.setWidthF(2.4)
        pen_thick.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_thick)
        painter.drawLine(QPointF(hx1, hy1), QPointF(hx2, hy2))
        painter.setPen(pen)
        # Plus inside
        plus_sz = rad * 0.55
        painter.drawLine(QPointF(cx - plus_sz, cy), QPointF(cx + plus_sz, cy))
        painter.drawLine(QPointF(cx, cy - plus_sz), QPointF(cx, cy + plus_sz))

    @staticmethod
    def _draw_zoom_out(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        cx = r.left() + r.width() * 0.42
        cy = r.top() + r.height() * 0.42
        rad = r.width() * 0.35
        painter.drawEllipse(QPointF(cx, cy), rad, rad)
        # Handle
        hx1 = cx + rad * 0.707
        hy1 = cy + rad * 0.707
        hx2 = r.right()
        hy2 = r.bottom()
        pen_thick = QPen(color)
        pen_thick.setWidthF(2.4)
        pen_thick.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_thick)
        painter.drawLine(QPointF(hx1, hy1), QPointF(hx2, hy2))
        painter.setPen(pen)
        # Minus inside
        minus_sz = rad * 0.55
        painter.drawLine(QPointF(cx - minus_sz, cy), QPointF(cx + minus_sz, cy))

    @staticmethod
    def _draw_zoom_fit(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # 4 corners pointing inward/outward
        m = 3
        # Top-left
        painter.drawLine(QPointF(r.left(), r.top() + m), QPointF(r.left(), r.top()))
        painter.drawLine(QPointF(r.left(), r.top()), QPointF(r.left() + m, r.top()))
        # Top-right
        painter.drawLine(QPointF(r.right() - m, r.top()), QPointF(r.right(), r.top()))
        painter.drawLine(QPointF(r.right(), r.top()), QPointF(r.right(), r.top() + m))
        # Bottom-left
        painter.drawLine(QPointF(r.left(), r.bottom() - m), QPointF(r.left(), r.bottom()))
        painter.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.left() + m, r.bottom()))
        # Bottom-right
        painter.drawLine(QPointF(r.right() - m, r.bottom()), QPointF(r.right(), r.bottom()))
        painter.drawLine(QPointF(r.right(), r.bottom()), QPointF(r.right(), r.bottom() - m))
        # Center square
        cr = QRectF(r.left() + r.width()*0.25, r.top() + r.height()*0.25, r.width()*0.5, r.height()*0.5)
        painter.drawRect(cr)

    @staticmethod
    def _draw_rotate_left(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Counter-clockwise rotation arc + arrow
        path = QPainterPath()
        path.arcMoveTo(r, 45)
        path.arcTo(r, 45, 230)
        painter.drawPath(path)
        # Arrowhead at top
        p = path.currentPosition()
        painter.drawLine(p, QPointF(p.x() - 4, p.y() - 1))
        painter.drawLine(p, QPointF(p.x() - 1, p.y() + 4))

    @staticmethod
    def _draw_rotate_right(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Clockwise rotation arc + arrow
        path = QPainterPath()
        path.arcMoveTo(r, 135)
        path.arcTo(r, 135, -230)
        painter.drawPath(path)
        p = path.currentPosition()
        painter.drawLine(p, QPointF(p.x() + 4, p.y() - 1))
        painter.drawLine(p, QPointF(p.x() + 1, p.y() + 4))

    @staticmethod
    def _draw_markup(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # macOS classic pencil in circle
        painter.drawEllipse(r)
        # Angled pencil
        p1 = QPointF(r.left() + r.width() * 0.3, r.bottom() - r.height() * 0.3)
        p2 = QPointF(r.right() - r.width() * 0.3, r.top() + r.height() * 0.3)
        painter.drawLine(p1, p2)
        # Tip
        p_tip = QPointF(r.left() + r.width() * 0.24, r.bottom() - r.height() * 0.24)
        painter.drawLine(p1, p_tip)

    @staticmethod
    def _draw_select(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Dashed marquee box
        dash_pen = QPen(pen)
        dash_pen.setStyle(Qt.PenStyle.DashLine)
        dash_pen.setDashPattern([3, 2])
        painter.setPen(dash_pen)
        painter.drawRect(r)

    @staticmethod
    def _draw_pen(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Pen nib angled
        path = QPainterPath()
        top_pt = QPointF(r.right() - 2, r.top() + 2)
        tip_pt = QPointF(r.left() + 2, r.bottom() - 2)
        path.moveTo(top_pt)
        path.lineTo(r.right() - 6, r.top() + 2)
        path.lineTo(tip_pt)
        path.lineTo(r.right() - 2, r.top() + 6)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(tip_pt, QPointF(r.left() + 7, r.bottom() - 7))

    @staticmethod
    def _draw_highlighter(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Marker / Highlighter angled with chisel tip
        path = QPainterPath()
        path.moveTo(r.left() + 3, r.bottom() - 3)
        path.lineTo(r.left() + 8, r.bottom() - 3)
        path.lineTo(r.right() - 3, r.top() + 8)
        path.lineTo(r.right() - 8, r.top() + 3)
        path.closeSubpath()
        painter.drawPath(path)

    @staticmethod
    def _draw_shapes(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Overlapping square and circle
        r_box = QRectF(r.left(), r.top() + r.height()*0.25, r.width()*0.55, r.height()*0.55)
        painter.drawRoundedRect(r_box, 2, 2)
        r_circ = QRectF(r.left() + r.width()*0.35, r.top(), r.width()*0.55, r.height()*0.55)
        painter.drawEllipse(r_circ)

    @staticmethod
    def _draw_text(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Capital 'A' or 'T' symbol
        font = QFont("-apple-system", int(r.height() * 0.9), QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, "A")

    @staticmethod
    def _draw_note(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Sticky note with folded corner
        path = QPainterPath()
        fold = r.width() * 0.3
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right() - fold, r.top())
        path.lineTo(r.right(), r.top() + fold)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        painter.drawPath(path)
        # Fold lines
        painter.drawLine(QPointF(r.right() - fold, r.top()), QPointF(r.right() - fold, r.top() + fold))
        painter.drawLine(QPointF(r.right() - fold, r.top() + fold), QPointF(r.right(), r.top() + fold))

    @staticmethod
    def _draw_sign(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Cursive signature stroke line
        path = QPainterPath()
        path.moveTo(r.left(), r.top() + r.height() * 0.6)
        path.quadTo(r.left() + r.width()*0.2, r.top(), r.left() + r.width()*0.4, r.top() + r.height()*0.5)
        path.quadTo(r.left() + r.width()*0.6, r.bottom(), r.left() + r.width()*0.8, r.top() + r.height()*0.4)
        path.lineTo(r.right(), r.bottom() - 2)
        painter.drawPath(path)

    @staticmethod
    def _draw_crop(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Intersecting crop angle marks
        painter.drawLine(QPointF(r.left() + 4, r.top()), QPointF(r.left() + 4, r.bottom() - 4))
        painter.drawLine(QPointF(r.left(), r.top() + 4), QPointF(r.right() - 4, r.top() + 4))
        painter.drawLine(QPointF(r.right() - 4, r.top() + 4), QPointF(r.right() - 4, r.bottom()))
        painter.drawLine(QPointF(r.left() + 4, r.bottom() - 4), QPointF(r.right(), r.bottom() - 4))

    @staticmethod
    def _draw_color_adjust(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Sliders or aperture
        y1 = r.top() + r.height() * 0.25
        y2 = r.top() + r.height() * 0.75
        painter.drawLine(QPointF(r.left(), y1), QPointF(r.right(), y1))
        painter.drawLine(QPointF(r.left(), y2), QPointF(r.right(), y2))
        # Knobs
        painter.drawEllipse(QPointF(r.left() + r.width()*0.35, y1), 2.5, 2.5)
        painter.drawEllipse(QPointF(r.left() + r.width()*0.65, y2), 2.5, 2.5)

    @staticmethod
    def _draw_size_adjust(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Aspect frame with arrows
        painter.drawRoundedRect(r, 2, 2)
        painter.drawLine(QPointF(r.left() + 4, r.bottom() - 4), QPointF(r.right() - 4, r.top() + 4))

    @staticmethod
    def _draw_inspector(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Circle with 'i'
        painter.drawEllipse(r)
        font = QFont("-apple-system", int(r.height() * 0.65), QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, "i")

    @staticmethod
    def _draw_search(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Magnifying glass
        cx = r.left() + r.width() * 0.42
        cy = r.top() + r.height() * 0.42
        rad = r.width() * 0.35
        painter.drawEllipse(QPointF(cx, cy), rad, rad)
        hx1 = cx + rad * 0.707
        hy1 = cy + rad * 0.707
        hx2 = r.right()
        hy2 = r.bottom()
        pen_thick = QPen(color)
        pen_thick.setWidthF(2.2)
        pen_thick.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_thick)
        painter.drawLine(QPointF(hx1, hy1), QPointF(hx2, hy2))

    @staticmethod
    def _draw_export(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Box with arrow pointing up (Share / Export)
        br = QRectF(r.left(), r.top() + r.height()*0.35, r.width(), r.height()*0.65)
        painter.drawRoundedRect(br, 2, 2)
        # Arrow
        cx = r.center().x()
        painter.drawLine(QPointF(cx, r.top()), QPointF(cx, r.top() + r.height()*0.55))
        painter.drawLine(QPointF(cx, r.top()), QPointF(cx - 3.5, r.top() + 3.5))
        painter.drawLine(QPointF(cx, r.top()), QPointF(cx + 3.5, r.top() + 3.5))

    @staticmethod
    def _draw_open(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Folder open icon
        path = QPainterPath()
        tab_w = r.width() * 0.4
        tab_h = r.height() * 0.25
        path.moveTo(r.left(), r.top() + tab_h)
        path.lineTo(r.left() + tab_w, r.top() + tab_h)
        path.lineTo(r.left() + tab_w + 3, r.top())
        path.lineTo(r.right() - 2, r.top())
        path.lineTo(r.right() - 2, r.bottom() - 2)
        path.lineTo(r.left(), r.bottom() - 2)
        path.closeSubpath()
        painter.drawPath(path)
        # Front flap angled
        flap = QPainterPath()
        flap.moveTo(r.left(), r.bottom() - 2)
        flap.lineTo(r.left() + 3, r.top() + tab_h + 3)
        flap.lineTo(r.right(), r.top() + tab_h + 3)
        flap.lineTo(r.right() - 3, r.bottom() - 2)
        flap.closeSubpath()
        painter.drawPath(flap)

    @staticmethod
    def _draw_folder(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Classic macOS Folder icon
        path = QPainterPath()
        tab_w = r.width() * 0.38
        tab_h = r.height() * 0.22
        path.moveTo(r.left(), r.top() + tab_h)
        path.lineTo(r.left(), r.top())
        path.lineTo(r.left() + tab_w, r.top())
        path.lineTo(r.left() + tab_w + 2.5, r.top() + tab_h)
        path.lineTo(r.right(), r.top() + tab_h)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        painter.drawPath(path)

    @staticmethod
    def _draw_pointer(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # macOS Arrow cursor
        path = QPainterPath()
        p_top = QPointF(r.left() + 1, r.top() + 1)
        path.moveTo(p_top)
        path.lineTo(r.left() + 1, r.bottom() - 3)
        path.lineTo(r.left() + r.width()*0.4, r.top() + r.height()*0.65)
        path.lineTo(r.right() - 2, r.bottom() - 1)
        path.lineTo(r.right() - 1, r.bottom() - 3)
        path.lineTo(r.left() + r.width()*0.55, r.top() + r.height()*0.5)
        path.lineTo(r.right() - 2, r.top() + r.height()*0.5)
        path.closeSubpath()
        painter.drawPath(path)

    @staticmethod
    def _draw_arrow_left(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Chevron left
        path = QPainterPath()
        cx = r.center().x()
        cy = r.center().y()
        path.moveTo(cx + 3, cy - 6)
        path.lineTo(cx - 3, cy)
        path.lineTo(cx + 3, cy + 6)
        painter.drawPath(path)

    @staticmethod
    def _draw_arrow_right(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Chevron right
        path = QPainterPath()
        cx = r.center().x()
        cy = r.center().y()
        path.moveTo(cx - 3, cy - 6)
        path.lineTo(cx + 3, cy)
        path.lineTo(cx - 3, cy + 6)
        painter.drawPath(path)

    @staticmethod
    def _draw_doc_proxy(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Small document sheet with folded corner
        path = QPainterPath()
        fold = r.width() * 0.35
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right() - fold, r.top())
        path.lineTo(r.right(), r.top() + fold)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(r.right() - fold, r.top()), QPointF(r.right() - fold, r.top() + fold))
        painter.drawLine(QPointF(r.right() - fold, r.top() + fold), QPointF(r.right(), r.top() + fold))

    @staticmethod
    def _draw_line_style(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # 3 horizontal lines of varying weights (open-source line style icon)
        y1 = r.top() + r.height() * 0.22
        y2 = r.top() + r.height() * 0.50
        y3 = r.top() + r.height() * 0.78
        
        p1 = QPen(color)
        p1.setWidthF(1.2)
        p1.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(p1)
        painter.drawLine(QPointF(r.left() + 2, y1), QPointF(r.right() - 2, y1))

        p2 = QPen(color)
        p2.setWidthF(2.2)
        p2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(p2)
        painter.drawLine(QPointF(r.left() + 2, y2), QPointF(r.right() - 2, y2))

        p3 = QPen(color)
        p3.setWidthF(3.4)
        p3.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(p3)
        painter.drawLine(QPointF(r.left() + 2, y3), QPointF(r.right() - 2, y3))

    @staticmethod
    def _draw_redact(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # macOS Redaction blackout icon
        painter.setPen(pen)
        painter.drawRoundedRect(r, 2.5, 2.5)
        painter.setBrush(QBrush(color))
        inner = r.adjusted(2.5, 3.5, -2.5, -3.5)
        painter.drawRoundedRect(inner, 1.5, 1.5)

    @staticmethod
    def _draw_loupe(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Loupe / Magnifier circular lens
        cx = r.center().x()
        cy = r.center().y()
        rad = min(r.width(), r.height()) * 0.44
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), rad, rad)
        # Inner lens ring
        p_inner = QPen(color)
        p_inner.setWidthF(1.0)
        painter.setPen(p_inner)
        painter.drawEllipse(QPointF(cx, cy), rad * 0.65, rad * 0.65)
        # Reticle crosshair
        ch = rad * 0.3
        painter.drawLine(QPointF(cx - ch, cy), QPointF(cx + ch, cy))
        painter.drawLine(QPointF(cx, cy - ch), QPointF(cx, cy + ch))

    @staticmethod
    def _draw_print(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Printer body and paper
        painter.setPen(pen)
        # Body
        body = QRectF(r.left(), r.top() + r.height() * 0.35, r.width(), r.height() * 0.45)
        painter.drawRoundedRect(body, 2, 2)
        # Top sheet
        top_sheet = QRectF(r.left() + r.width() * 0.2, r.top(), r.width() * 0.6, r.height() * 0.38)
        painter.drawRect(top_sheet)
        # Bottom paper tray
        bot_sheet = QRectF(r.left() + r.width() * 0.22, r.top() + r.height() * 0.65, r.width() * 0.56, r.height() * 0.35)
        painter.drawRect(bot_sheet)

    @staticmethod
    def _draw_slideshow(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Presentation screen with play button
        painter.setPen(pen)
        painter.drawRoundedRect(r, 3, 3)
        # Play triangle
        play_path = QPainterPath()
        cx, cy = r.center().x(), r.center().y()
        sz = r.width() * 0.2
        play_path.moveTo(cx - sz * 0.7, cy - sz)
        play_path.lineTo(cx + sz * 1.0, cy)
        play_path.lineTo(cx - sz * 0.7, cy + sz)
        play_path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.drawPath(play_path)

    @staticmethod
    def _draw_default(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        painter.drawRect(r)
