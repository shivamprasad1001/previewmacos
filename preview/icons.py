"""
High-definition vector icon renderer for macOS Preview tools.
Generates razor-sharp, resolution-independent SF Symbols styled icons.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF

class MacIconFactory:
    """Creates crisp macOS SF Symbols style icons using QPainter vector paths."""

    @staticmethod
    def create_icon(name: str, color_hex: str = "#f5f5f7", size: int = 24, with_dropdown: bool = False) -> QIcon:
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

            if with_dropdown:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                tri = QPolygonF([
                    QPointF(s - 5.5, s - 4.5),
                    QPointF(s - 1.5, s - 4.5),
                    QPointF(s - 3.5, s - 1.5)
                ])
                painter.drawPolygon(tri)
        finally:
            painter.end()

        return QIcon(pixmap)

    @staticmethod
    def create_dropdown_tool_icon(name: str, color_hex: str = "#f5f5f7", width: int = 28, height: int = 16) -> QIcon:
        """Creates a segmented tool icon with main symbol on the left and dropdown triangle on the right."""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(color_hex)
        pen = QPen(color)
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Draw left tool icon
        icon_rect = QRectF(1.0, 1.0, 14.0, 14.0)
        try:
            method = getattr(MacIconFactory, f"_draw_{name}", None)
            if method:
                method(painter, icon_rect, color, pen)
            else:
                MacIconFactory._draw_default(painter, icon_rect, color, pen)

            # Subtle vertical separator line between tool icon and dropdown arrow
            sep_col = QColor(color.red(), color.green(), color.blue(), 70)
            painter.setPen(QPen(sep_col, 1.0))
            painter.drawLine(QPointF(17.5, 2.5), QPointF(17.5, float(height) - 2.5))

            # Dropdown arrow triangle on the right
            cx = float(width) - 4.5
            cy = float(height) / 2.0
            tri = QPolygonF([
                QPointF(cx - 2.8, cy - 1.8),
                QPointF(cx + 2.8, cy - 1.8),
                QPointF(cx, cy + 2.0)
            ])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawPolygon(tri)
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
        # macOS SF Symbol 'pencil.tip.crop.circle': Authentic Apple Pencil tip inside circle
        painter.setBrush(Qt.BrushStyle.NoBrush)
        p_circ = QPen(color, 1.2, Qt.PenStyle.SolidLine)
        painter.setPen(p_circ)
        painter.drawEllipse(r)

        cx, cy = r.center().x(), r.center().y()
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-45)

        pencil = QPainterPath()
        pencil.moveTo(-1.8, -4.0)
        pencil.lineTo(1.8, -4.0)
        pencil.lineTo(1.8, 1.0)
        pencil.lineTo(0.0, 4.2)
        pencil.lineTo(-1.8, 1.0)
        pencil.closeSubpath()

        painter.setPen(QPen(color, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(pencil)
        painter.drawLine(QPointF(-1.8, 1.0), QPointF(1.8, 1.0))

        # Nib fill
        nib = QPainterPath()
        nib.moveTo(-0.9, 2.7)
        nib.lineTo(0.0, 4.2)
        nib.lineTo(0.9, 2.7)
        nib.closeSubpath()
        painter.fillPath(nib, QBrush(color))

        painter.restore()

    @staticmethod
    def _draw_select(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Marquee selection box with 4 corner anchor handles
        dash_pen = QPen(color, 1.2, Qt.PenStyle.CustomDashLine, Qt.PenCapStyle.FlatCap)
        dash_pen.setDashPattern([2.5, 2.0])
        painter.setPen(dash_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner = r.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.drawRect(inner)
        
        # 4 solid corner grab handles
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        hs = 2.5
        for pt in [inner.topLeft(), inner.topRight(), inner.bottomLeft(), inner.bottomRight()]:
            painter.drawRect(QRectF(pt.x() - hs/2, pt.y() - hs/2, hs, hs))

    @staticmethod
    def _draw_select_oval(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Dashed elliptical selection outline with corner handles
        dash_pen = QPen(color, 1.2, Qt.PenStyle.CustomDashLine, Qt.PenCapStyle.FlatCap)
        dash_pen.setDashPattern([2.5, 2.0])
        painter.setPen(dash_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner = r.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.drawEllipse(inner)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        hs = 2.5
        for pt in [QPointF(inner.center().x(), inner.top()),
                   QPointF(inner.center().x(), inner.bottom()),
                   QPointF(inner.left(), inner.center().y()),
                   QPointF(inner.right(), inner.center().y())]:
            painter.drawRect(QRectF(pt.x() - hs/2, pt.y() - hs/2, hs, hs))

    @staticmethod
    def _draw_select_lasso(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Dashed freehand lasso loop selection outline
        dash_pen = QPen(color, 1.2, Qt.PenStyle.CustomDashLine, Qt.PenCapStyle.FlatCap)
        dash_pen.setDashPattern([2.5, 2.0])
        painter.setPen(dash_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.35, r.bottom() - 1)
        path.cubicTo(r.left(), r.top() + r.height() * 0.5,
                     r.left() + r.width() * 0.35, r.top() + 1,
                     r.right() - 1, r.top() + r.height() * 0.3)
        path.cubicTo(r.right() + 1, r.bottom() - 2,
                     r.center().x(), r.bottom(),
                     r.left() + r.width() * 0.35, r.bottom() - 1)
        painter.drawPath(path)

    @staticmethod
    def _draw_pen(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Apple Pencil / Stylus angled with drawing stroke
        p = QPen(color, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        path = QPainterPath()
        tip = QPointF(r.left() + r.width() * 0.25, r.bottom() - r.height() * 0.25)
        path.moveTo(tip)
        path.lineTo(r.left() + r.width() * 0.15, r.bottom() - r.height() * 0.40)
        path.lineTo(r.right() - 4, r.top() + 1)
        path.lineTo(r.right() - 1, r.top() + 4)
        path.lineTo(r.left() + r.width() * 0.40, r.bottom() - r.height() * 0.15)
        path.closeSubpath()
        painter.drawPath(path)
        
        # Scribble wave under tip
        wave = QPainterPath()
        wave.moveTo(r.left(), r.bottom())
        wave.quadTo(r.left() + r.width() * 0.2, r.bottom() - 4, r.left() + r.width() * 0.45, r.bottom() - 1)
        painter.drawPath(wave)

    @staticmethod
    def _draw_highlighter(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Chisel-tip marker with broad highlight bar
        p = QPen(color, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        w, h = r.width(), r.height()
        path = QPainterPath()
        path.moveTo(r.left() + w * 0.15, r.bottom() - h * 0.35)
        path.lineTo(r.left() + w * 0.35, r.bottom() - h * 0.15)
        path.lineTo(r.right() - 1, r.top() + h * 0.35)
        path.lineTo(r.right() - w * 0.35, r.top() + 1)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(r.left() + w * 0.25, r.bottom() - h * 0.45), QPointF(r.left() + w * 0.45, r.bottom() - h * 0.25))
        
        # Wide highlight stripe at bottom
        hl_pen = QPen(color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(hl_pen)
        painter.drawLine(QPointF(r.left() + 1, r.bottom() - 1), QPointF(r.right() - 1, r.bottom() - 1))

    @staticmethod
    def _draw_shapes(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Crisp distinct circle overlapping a sharp square
        painter.setBrush(Qt.BrushStyle.NoBrush)
        p = QPen(color, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p)
        # Circle top-left
        c_sz = r.width() * 0.56
        painter.drawEllipse(QRectF(r.left(), r.top(), c_sz, c_sz))
        # Square bottom-right
        s_sz = r.width() * 0.52
        painter.drawRect(QRectF(r.right() - s_sz, r.bottom() - s_sz, s_sz, s_sz))

    @staticmethod
    def _draw_text(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Universal 'T' in a subtle dashed text frame
        p = QPen(color, 1.0, Qt.PenStyle.DashLine)
        p.setDashPattern([2, 2])
        painter.setPen(p)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(r, 2, 2)
        
        font = QFont("-apple-system", int(r.height() * 0.72), QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, "T")

    @staticmethod
    def _draw_note(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Square Post-It Note with curled bottom corner & ruled lines
        p = QPen(color, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        fold = r.width() * 0.28
        path = QPainterPath()
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right(), r.top())
        path.lineTo(r.right(), r.bottom() - fold)
        path.lineTo(r.right() - fold, r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        painter.drawPath(path)
        
        painter.drawLine(QPointF(r.right() - fold, r.bottom()), QPointF(r.right() - fold, r.bottom() - fold))
        painter.drawLine(QPointF(r.right() - fold, r.bottom() - fold), QPointF(r.right(), r.bottom() - fold))
        
        line_pen = QPen(color, 1.0)
        painter.setPen(line_pen)
        y1 = r.top() + r.height() * 0.32
        y2 = r.top() + r.height() * 0.58
        painter.drawLine(QPointF(r.left() + 3, y1), QPointF(r.right() - 3, y1))
        painter.drawLine(QPointF(r.left() + 3, y2), QPointF(r.right() - fold - 1, y2))

    @staticmethod
    def _draw_sign(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Fountain pen writing a signature on a baseline
        w, h = r.width(), r.height()
        p_base = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p_base)
        painter.drawLine(QPointF(r.left(), r.bottom() - 1), QPointF(r.right(), r.bottom() - 1))
        
        sig = QPainterPath()
        sig.moveTo(r.left() + 2, r.bottom() - 3)
        sig.quadTo(r.left() + w * 0.25, r.top() + h * 0.35, r.left() + w * 0.45, r.bottom() - 4)
        sig.quadTo(r.left() + w * 0.62, r.top() + h * 0.55, r.left() + w * 0.72, r.top() + h * 0.42)
        p_sig = QPen(color, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p_sig)
        painter.drawPath(sig)
        
        tip = QPointF(r.left() + w * 0.72, r.top() + h * 0.42)
        nib = QPainterPath()
        nib.moveTo(tip)
        nib.lineTo(tip.x() - 1.5, tip.y() - 4.5)
        nib.lineTo(tip.x() + 2.5, tip.y() - 8.5)
        nib.lineTo(tip.x() + 5.5, tip.y() - 5.5)
        nib.lineTo(tip.x() + 1.5, tip.y() - 1.5)
        nib.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(nib)

    @staticmethod
    def _draw_crop(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Photography framing crop blades
        m = r.width() * 0.22
        p = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
        painter.setPen(p)
        painter.drawLine(QPointF(r.left() + m, r.top()), QPointF(r.left() + m, r.bottom() - m))
        painter.drawLine(QPointF(r.left(), r.top() + m), QPointF(r.right() - m, r.top() + m))
        painter.drawLine(QPointF(r.right() - m, r.top() + m), QPointF(r.right() - m, r.bottom()))
        painter.drawLine(QPointF(r.left() + m, r.bottom() - m), QPointF(r.right(), r.bottom() - m))

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
        # Clean macOS SF Symbol folder icon
        path = QPainterPath()
        w = r.width()
        h = r.height() * 0.88
        x = r.left()
        y = r.top() + (r.height() - h) / 2

        tab_w = w * 0.42
        tab_h = h * 0.22

        path.moveTo(x + 1.5, y + tab_h)
        path.lineTo(x + tab_w, y + tab_h)
        path.lineTo(x + tab_w + 1.8, y)
        path.lineTo(x + w - 1.5, y)
        path.quadTo(x + w, y, x + w, y + 1.5)
        path.lineTo(x + w, y + h - 1.5)
        path.quadTo(x + w, y + h, x + w - 1.5, y + h)
        path.lineTo(x + 1.5, y + h)
        path.quadTo(x, y + h, x, y + h - 1.5)
        path.lineTo(x, y + tab_h + 1.5)
        path.quadTo(x, y + tab_h, x + 1.5, y + tab_h)
        path.closeSubpath()

        f_pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(f_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

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
        # Solid classic macOS arrow cursor
        path = QPainterPath()
        x0, y0 = r.left(), r.top()
        w, h = r.width(), r.height()
        path.moveTo(x0, y0)
        path.lineTo(x0, y0 + h * 0.95)
        path.lineTo(x0 + w * 0.28, y0 + h * 0.68)
        path.lineTo(x0 + w * 0.58, y0 + h * 0.98)
        path.lineTo(x0 + w * 0.74, y0 + h * 0.84)
        path.lineTo(x0 + w * 0.44, y0 + h * 0.54)
        path.lineTo(x0 + w * 0.88, y0 + h * 0.54)
        path.closeSubpath()
        painter.setBrush(QBrush(color))
        p_pen = QPen(color, 0.8)
        painter.setPen(p_pen)
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
    def _draw_arrow_down(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Crisp solid dropdown arrow triangle (matching macOS / attached photo)
        path = QPainterPath()
        cx = r.center().x()
        cy = r.center().y()
        path.moveTo(cx - 3.5, cy - 2.0)
        path.lineTo(cx + 3.5, cy - 2.0)
        path.lineTo(cx, cy + 2.5)
        path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
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
        # Stepped thickness lines: thin, medium, thick with graduated lengths
        w, h = r.width(), r.height()
        p1 = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p1)
        painter.drawLine(QPointF(r.left() + w * 0.25, r.top() + h * 0.2), QPointF(r.right() - w * 0.25, r.top() + h * 0.2))
        
        p2 = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p2)
        painter.drawLine(QPointF(r.left() + w * 0.12, r.top() + h * 0.5), QPointF(r.right() - w * 0.12, r.top() + h * 0.5))
        
        p3 = QPen(color, 3.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p3)
        painter.drawLine(QPointF(r.left() + 1, r.top() + h * 0.8), QPointF(r.right() - 1, r.top() + h * 0.8))

    @staticmethod
    def _draw_redact(painter: QPainter, r: QRectF, color: QColor, pen: QPen):
        # Simulated text lines with solid BLACKOUT CENSOR BAR across middle
        line_pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(line_pen)
        painter.drawLine(QPointF(r.left() + 1, r.top() + 2), QPointF(r.right() - 1, r.top() + 2))
        painter.drawLine(QPointF(r.left() + 1, r.bottom() - 2), QPointF(r.right() - 3, r.bottom() - 2))
        
        bar = QRectF(r.left(), r.top() + r.height() * 0.30, r.width(), r.height() * 0.40)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar, 1.5, 1.5)

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
