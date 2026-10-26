"""
Annotation model supporting markup, sketches, shapes, text, signatures, and crop selections.
Provides interactive hit-testing, resize handles, and rendering over documents.
"""

from enum import Enum, auto
from typing import List, Optional, Tuple
import math

from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont, QPixmap
from PyQt6.QtCore import Qt, QPointF, QRectF, QSizeF

class AnnotationType(Enum):
    NONE = auto()
    PEN = auto()
    HIGHLIGHTER = auto()
    RECTANGLE = auto()
    ROUNDED_RECT = auto()
    ELLIPSE = auto()
    LINE = auto()
    ARROW = auto()
    TEXT = auto()
    NOTE = auto()
    SIGNATURE = auto()
    CROP_BOX = auto()
    CROP_OVAL = auto()
    CROP_LASSO = auto()
    REDACT = auto()
    LOUPE = auto()
    CALLOUT = auto()

class Handle(Enum):
    NONE = 0
    NW = 1
    N = 2
    NE = 3
    E = 4
    SE = 5
    S = 6
    SW = 7
    W = 8
    START = 9
    END = 10
    TAIL = 11
    MAGNIFY = 12

class AnnotationItem:
    """A single markup or annotation element."""
    
    def __init__(self, item_type: AnnotationType):
        self.item_type: AnnotationType = item_type
        self.rect: QRectF = QRectF()
        self.points: List[QPointF] = []
        self.stroke_color: QColor = QColor("#ff3b30")  # Default red markup
        self.stroke_width: float = 3.0
        self.fill_color: QColor = QColor(Qt.GlobalColor.transparent)
        self.text: str = "Text"
        self.font_size: int = 16
        self.font_family: str = "-apple-system"
        self.signature_pixmap: Optional[QPixmap] = None
        self.is_selected: bool = False
        self.is_bold: bool = False
        self.is_italic: bool = False
        self.is_underline: bool = False
        self.alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft
        self.magnification: float = 2.0
        self.tail_point: QPointF = QPointF()

    def draw(self, painter: QPainter, zoom: float = 1.0, page_pixmap: Optional[QPixmap] = None):
        """Draws the annotation item using current zoom transformation."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale coordinates to display zoom
        if self.item_type == AnnotationType.PEN:
            if len(self.points) > 1:
                pen = QPen(self.stroke_color, self.stroke_width * zoom)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                
                path = QPainterPath()
                p0 = self.points[0] * zoom
                path.moveTo(p0)
                for pt in self.points[1:]:
                    path.lineTo(pt * zoom)
                painter.drawPath(path)

        elif self.item_type == AnnotationType.HIGHLIGHTER:
            if len(self.points) > 1:
                # Translucent highlighter
                color = QColor(self.stroke_color)
                color.setAlpha(90)
                pen = QPen(color, max(12.0, self.stroke_width * 4) * zoom)
                pen.setCapStyle(Qt.PenCapStyle.SquareCap)
                pen.setJoinStyle(Qt.PenJoinStyle.BevelJoin)
                painter.setPen(pen)
                
                path = QPainterPath()
                path.moveTo(self.points[0] * zoom)
                for pt in self.points[1:]:
                    path.lineTo(pt * zoom)
                painter.drawPath(path)

        elif self.item_type == AnnotationType.RECTANGLE:
            pen = QPen(self.stroke_color, self.stroke_width * zoom)
            painter.setPen(pen)
            painter.setBrush(QBrush(self.fill_color))
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            painter.drawRect(scaled_rect)

        elif self.item_type == AnnotationType.ROUNDED_RECT:
            pen = QPen(self.stroke_color, self.stroke_width * zoom)
            painter.setPen(pen)
            painter.setBrush(QBrush(self.fill_color))
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            painter.drawRoundedRect(scaled_rect, 10 * zoom, 10 * zoom)

        elif self.item_type == AnnotationType.ELLIPSE:
            pen = QPen(self.stroke_color, self.stroke_width * zoom)
            painter.setPen(pen)
            painter.setBrush(QBrush(self.fill_color))
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            painter.drawEllipse(scaled_rect)

        elif self.item_type == AnnotationType.LINE:
            if len(self.points) >= 2:
                pen = QPen(self.stroke_color, self.stroke_width * zoom)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(self.points[0] * zoom, self.points[1] * zoom)

        elif self.item_type == AnnotationType.ARROW:
            if len(self.points) >= 2:
                p1 = self.points[0] * zoom
                p2 = self.points[1] * zoom
                pen = QPen(self.stroke_color, self.stroke_width * zoom)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(p1, p2)
                # Arrowhead
                angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                head_len = 14.0 * zoom
                arrow_p1 = QPointF(p2.x() - head_len * math.cos(angle - math.pi / 6),
                                   p2.y() - head_len * math.sin(angle - math.pi / 6))
                arrow_p2 = QPointF(p2.x() - head_len * math.cos(angle + math.pi / 6),
                                   p2.y() - head_len * math.sin(angle + math.pi / 6))
                path = QPainterPath()
                path.moveTo(p2)
                path.lineTo(arrow_p1)
                path.lineTo(arrow_p2)
                path.closeSubpath()
                painter.setBrush(QBrush(self.stroke_color))
                painter.drawPath(path)

        elif self.item_type == AnnotationType.TEXT:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            if self.fill_color.alpha() > 0:
                painter.setBrush(QBrush(self.fill_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(scaled_rect, 4, 4)
            
            font = QFont(self.font_family, int(self.font_size * zoom))
            if getattr(self, "is_bold", False):
                font.setBold(True)
            if getattr(self, "is_italic", False):
                font.setItalic(True)
            if getattr(self, "is_underline", False):
                font.setUnderline(True)
            painter.setFont(font)
            painter.setPen(QPen(self.stroke_color))
            align = getattr(self, "alignment", Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignTop
            painter.drawText(scaled_rect, align, self.text)

        elif self.item_type == AnnotationType.NOTE:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 32 * zoom, 32 * zoom)
            # Yellow note square
            painter.setBrush(QBrush(QColor("#ffd60a")))
            painter.setPen(QPen(QColor("#d4ac0d"), 1.2 * zoom))
            painter.drawRoundedRect(scaled_rect, 4 * zoom, 4 * zoom)
            # Fold corner
            painter.setBrush(QBrush(QColor("#f4d03f")))
            f_rect = QRectF(scaled_rect.right() - 8*zoom, scaled_rect.top(), 8*zoom, 8*zoom)
            painter.drawRect(f_rect)

        elif self.item_type == AnnotationType.SIGNATURE and self.signature_pixmap:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            painter.drawPixmap(scaled_rect.toRect(), self.signature_pixmap)

        elif self.item_type == AnnotationType.REDACT:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawRect(scaled_rect)
            # Subtle inner edge
            painter.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(scaled_rect)

        elif self.item_type == AnnotationType.CROP_BOX:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            pen = QPen(QColor("#007aff"), 1.8)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(scaled_rect)
            self._draw_resize_handles(painter, scaled_rect)

        elif self.item_type == AnnotationType.CROP_OVAL:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            pen = QPen(QColor("#007aff"), 1.8)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(scaled_rect)
            self._draw_resize_handles(painter, scaled_rect)

        elif self.item_type == AnnotationType.CROP_LASSO:
            if len(self.points) > 1:
                path = QPainterPath()
                path.moveTo(self.points[0] * zoom)
                for pt in self.points[1:]:
                    path.lineTo(pt * zoom)
                path.closeSubpath()
                pen = QPen(QColor("#007aff"), 1.8)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)

        elif self.item_type == AnnotationType.LOUPE:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            if scaled_rect.width() > 2 and scaled_rect.height() > 2:
                clip_path = QPainterPath()
                clip_path.addEllipse(scaled_rect)
                painter.save()
                painter.setClipPath(clip_path)

                mag = max(1.1, min(5.0, getattr(self, "magnification", 2.0)))
                if page_pixmap:
                    cx = scaled_rect.center().x()
                    cy = scaled_rect.center().y()
                    src_w = scaled_rect.width() / mag
                    src_h = scaled_rect.height() / mag
                    src_rect = QRectF(cx - src_w / 2.0, cy - src_h / 2.0, src_w, src_h)
                    painter.drawPixmap(scaled_rect, page_pixmap, src_rect)
                else:
                    painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(scaled_rect)

                # Inner subtle glass shadow
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(0, 0, 0, 45), 2.5 * zoom))
                painter.drawEllipse(scaled_rect.adjusted(1, 1, -1, -1))
                painter.restore()

                # Bezel ring
                stroke_c = self.stroke_color if self.stroke_color.isValid() else QColor("#007aff")
                pen = QPen(stroke_c, max(2.5, self.stroke_width * zoom))
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(scaled_rect)

                # Specular reflection ring
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0))
                painter.drawEllipse(scaled_rect.adjusted(1.5, 1.5, -1.5, -1.5))

        elif self.item_type == AnnotationType.CALLOUT:
            scaled_rect = QRectF(self.rect.left() * zoom, self.rect.top() * zoom, 
                                 self.rect.width() * zoom, self.rect.height() * zoom)
            tail = self.tail_point * zoom if (self.tail_point and not self.tail_point.isNull()) else QPointF(scaled_rect.left() - 20 * zoom, scaled_rect.bottom() + 25 * zoom)
            
            # Construct speech bubble path
            path = QPainterPath()
            rad = 8.0 * zoom
            path.addRoundedRect(scaled_rect, rad, rad)
            
            tri = QPainterPath()
            cx = scaled_rect.center().x()
            cy = scaled_rect.center().y()
            dx = tail.x() - cx
            dy = tail.y() - cy
            
            if abs(dy) >= abs(dx):
                if dy >= 0:
                    base_y = scaled_rect.bottom()
                    bx = min(max(cx, scaled_rect.left() + 20 * zoom), scaled_rect.right() - 20 * zoom)
                    tri.moveTo(bx - 12 * zoom, base_y)
                    tri.lineTo(tail)
                    tri.lineTo(bx + 12 * zoom, base_y)
                else:
                    base_y = scaled_rect.top()
                    bx = min(max(cx, scaled_rect.left() + 20 * zoom), scaled_rect.right() - 20 * zoom)
                    tri.moveTo(bx - 12 * zoom, base_y)
                    tri.lineTo(tail)
                    tri.lineTo(bx + 12 * zoom, base_y)
            else:
                if dx >= 0:
                    base_x = scaled_rect.right()
                    by = min(max(cy, scaled_rect.top() + 15 * zoom), scaled_rect.bottom() - 15 * zoom)
                    tri.moveTo(base_x, by - 10 * zoom)
                    tri.lineTo(tail)
                    tri.lineTo(base_x, by + 10 * zoom)
                else:
                    base_x = scaled_rect.left()
                    by = min(max(cy, scaled_rect.top() + 15 * zoom), scaled_rect.bottom() - 15 * zoom)
                    tri.moveTo(base_x, by - 10 * zoom)
                    tri.lineTo(tail)
                    tri.lineTo(base_x, by + 10 * zoom)
            tri.closeSubpath()
            combined_path = path.united(tri)

            fill_c = self.fill_color if (self.fill_color.isValid() and self.fill_color.alpha() > 0) else QColor(255, 255, 255, 240)
            painter.setBrush(QBrush(fill_c))
            pen = QPen(self.stroke_color, self.stroke_width * zoom)
            painter.setPen(pen)
            painter.drawPath(combined_path)

            if self.text:
                font = QFont(self.font_family, int(self.font_size * zoom))
                if getattr(self, "is_bold", False):
                    font.setBold(True)
                if getattr(self, "is_italic", False):
                    font.setItalic(True)
                if getattr(self, "is_underline", False):
                    font.setUnderline(True)
                painter.setFont(font)
                painter.setPen(QPen(self.stroke_color))
                text_rect = scaled_rect.adjusted(6 * zoom, 6 * zoom, -6 * zoom, -6 * zoom)
                align = int(getattr(self, "alignment", Qt.AlignmentFlag.AlignCenter)) | int(Qt.TextFlag.TextWordWrap)
                painter.drawText(text_rect, align, self.text)

        # Draw selection border and handles if selected
        if self.is_selected and self.item_type not in (AnnotationType.CROP_BOX, AnnotationType.CROP_OVAL, AnnotationType.CROP_LASSO):
            doc_b = self.get_bounds()
            bounds = QRectF(doc_b.x() * zoom, doc_b.y() * zoom,
                            doc_b.width() * zoom, doc_b.height() * zoom)
            pen = QPen(QColor("#0a84ff"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(bounds.adjusted(-4, -4, 4, 4))
            self._draw_resize_handles(painter, bounds.adjusted(-4, -4, 4, 4), zoom=zoom)

        painter.restore()

    def _draw_resize_handles(self, painter: QPainter, rect: QRectF, zoom: float = 1.0):
        """Draws standard macOS resize handles."""
        h_sz = 8.0
        
        if self.item_type in (AnnotationType.LINE, AnnotationType.ARROW) and len(self.points) >= 2:
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(QPen(QColor("#0a84ff"), 1.5))
            for pt in [rect.topLeft(), rect.bottomRight()]:
                painter.drawRect(QRectF(pt.x() - h_sz/2, pt.y() - h_sz/2, h_sz, h_sz))
            return

        handles = self.get_handles_positions(zoom)
        for h, pt in handles.items():
            if h == Handle.MAGNIFY:
                # Green magnification handle
                painter.setBrush(QBrush(QColor("#34c759")))
                painter.setPen(QPen(QColor("#ffffff"), 1.5))
                painter.drawEllipse(QRectF(pt.x() * zoom - 5, pt.y() * zoom - 5, 10, 10))
            elif h == Handle.TAIL:
                # Green tail handle
                painter.setBrush(QBrush(QColor("#34c759")))
                painter.setPen(QPen(QColor("#ffffff"), 1.5))
                painter.drawEllipse(QRectF(pt.x() * zoom - 5, pt.y() * zoom - 5, 10, 10))
            else:
                painter.setBrush(QBrush(QColor("#ffffff")))
                painter.setPen(QPen(QColor("#0a84ff"), 1.5))
                painter.drawRect(QRectF(pt.x() * zoom - h_sz/2, pt.y() * zoom - h_sz/2, h_sz, h_sz))

    def get_handles_positions(self, zoom: float = 1.0) -> dict:
        """Returns dictionary of {Handle: QPointF} in document coordinates."""
        if self.item_type in (AnnotationType.LINE, AnnotationType.ARROW):
            if len(self.points) >= 2:
                return {
                    Handle.START: self.points[0],
                    Handle.END: self.points[1]
                }
            return {}

        if self.item_type == AnnotationType.LOUPE:
            b = self.rect.normalized()
            cx, cy = b.center().x(), b.center().y()
            rx, ry = b.width() / 2.0, b.height() / 2.0
            # Place magnify handle on perimeter at 45 degrees
            mag_pt = QPointF(cx + rx * 0.707, cy - ry * 0.707)
            return {
                Handle.NW: b.topLeft(),
                Handle.NE: b.topRight(),
                Handle.SE: b.bottomRight(),
                Handle.SW: b.bottomLeft(),
                Handle.MAGNIFY: mag_pt,
            }

        if self.item_type == AnnotationType.CALLOUT:
            b = self.rect.normalized()
            handles = {
                Handle.NW: b.topLeft(),
                Handle.N: QPointF(b.center().x(), b.top()),
                Handle.NE: b.topRight(),
                Handle.E: QPointF(b.right(), b.center().y()),
                Handle.SE: b.bottomRight(),
                Handle.S: QPointF(b.center().x(), b.bottom()),
                Handle.SW: b.bottomLeft(),
                Handle.W: QPointF(b.left(), b.center().y()),
            }
            if self.tail_point and not self.tail_point.isNull():
                handles[Handle.TAIL] = self.tail_point
            return handles

        b = self.get_bounds()
        if not b.isValid() or b.isEmpty():
            return {}
        
        return {
            Handle.NW: b.topLeft(),
            Handle.N: QPointF(b.center().x(), b.top()),
            Handle.NE: b.topRight(),
            Handle.E: QPointF(b.right(), b.center().y()),
            Handle.SE: b.bottomRight(),
            Handle.S: QPointF(b.center().x(), b.bottom()),
            Handle.SW: b.bottomLeft(),
            Handle.W: QPointF(b.left(), b.center().y()),
        }

    def get_handle_at_point(self, doc_pt: QPointF, zoom: float = 1.0) -> Handle:
        """Returns which handle is hit by doc_pt (in doc coords), or Handle.NONE."""
        hit_radius = 10.0 / max(0.1, zoom)
        handles = self.get_handles_positions(zoom)
        for handle, pt in handles.items():
            dx = doc_pt.x() - pt.x()
            dy = doc_pt.y() - pt.y()
            if (dx * dx + dy * dy) <= (hit_radius * hit_radius):
                return handle
        return Handle.NONE

    def resize_by_handle(self, handle: Handle, doc_pt: QPointF, orig_bounds: QRectF, orig_points: Optional[List[QPointF]] = None):
        """Resizes the annotation based on handle dragging."""
        min_sz = 10.0
        if self.item_type in (AnnotationType.LINE, AnnotationType.ARROW):
            if len(self.points) >= 2:
                if handle == Handle.START:
                    self.points[0] = doc_pt
                elif handle == Handle.END:
                    self.points[1] = doc_pt
            return

        if handle == Handle.TAIL and self.item_type == AnnotationType.CALLOUT:
            self.tail_point = doc_pt
            return

        if handle == Handle.MAGNIFY and self.item_type == AnnotationType.LOUPE:
            cx, cy = self.rect.center().x(), self.rect.center().y()
            dx = doc_pt.x() - cx
            dy = doc_pt.y() - cy
            dist = math.sqrt(dx * dx + dy * dy)
            rad = max(10.0, self.rect.width() / 2.0)
            ratio = dist / rad
            self.magnification = max(1.2, min(5.0, round(ratio * 2.0, 1)))
            return

        l = orig_bounds.left()
        r = orig_bounds.right()
        t = orig_bounds.top()
        b = orig_bounds.bottom()

        if handle in (Handle.NW, Handle.W, Handle.SW):
            l = min(doc_pt.x(), r - min_sz)
        if handle in (Handle.NE, Handle.E, Handle.SE):
            r = max(doc_pt.x(), l + min_sz)
        if handle in (Handle.NW, Handle.N, Handle.NE):
            t = min(doc_pt.y(), b - min_sz)
        if handle in (Handle.SW, Handle.S, Handle.SE):
            b = max(doc_pt.y(), t + min_sz)

        new_rect = QRectF(l, t, r - l, b - t)

        if self.item_type in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, 
                              AnnotationType.ELLIPSE, AnnotationType.TEXT, 
                              AnnotationType.NOTE, AnnotationType.SIGNATURE, 
                              AnnotationType.CROP_BOX, AnnotationType.CROP_OVAL, 
                              AnnotationType.REDACT, AnnotationType.LOUPE, AnnotationType.CALLOUT):
            self.rect = new_rect

        elif self.item_type in (AnnotationType.PEN, AnnotationType.HIGHLIGHTER, AnnotationType.CROP_LASSO) and orig_points and orig_bounds.isValid():
            ow = max(1.0, orig_bounds.width())
            oh = max(1.0, orig_bounds.height())
            new_pts = []
            for p in orig_points:
                rel_x = (p.x() - orig_bounds.left()) / ow
                rel_y = (p.y() - orig_bounds.top()) / oh
                new_pts.append(QPointF(new_rect.left() + rel_x * new_rect.width(),
                                       new_rect.top() + rel_y * new_rect.height()))
            self.points = new_pts

    def get_bounds(self) -> QRectF:
        """Calculates bounding box of annotation in document coordinates."""
        if self.item_type in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, 
                              AnnotationType.ELLIPSE, AnnotationType.TEXT, 
                              AnnotationType.NOTE, AnnotationType.SIGNATURE, 
                              AnnotationType.CROP_BOX, AnnotationType.CROP_OVAL, 
                              AnnotationType.REDACT, AnnotationType.LOUPE):
            return self.rect.normalized()
        elif self.item_type == AnnotationType.CALLOUT:
            b = self.rect.normalized()
            if self.tail_point and not self.tail_point.isNull():
                return b.united(QRectF(self.tail_point.x(), self.tail_point.y(), 1, 1))
            return b
        elif self.points:
            min_x = min(p.x() for p in self.points)
            max_x = max(p.x() for p in self.points)
            min_y = min(p.y() for p in self.points)
            max_y = max(p.y() for p in self.points)
            w = max(5.0, max_x - min_x)
            h = max(5.0, max_y - min_y)
            return QRectF(min_x, min_y, w, h)
        return QRectF()

    def contains_point(self, pt: QPointF) -> bool:
        """Hit test for selection."""
        bounds = self.get_bounds().adjusted(-8, -8, 8, 8)
        return bounds.contains(pt)

    def translate(self, dx: float, dy: float):
        """Moves annotation by (dx, dy)."""
        if self.rect.isValid():
            self.rect.translate(dx, dy)
        if self.item_type == AnnotationType.CALLOUT and self.tail_point and not self.tail_point.isNull():
            self.tail_point = QPointF(self.tail_point.x() + dx, self.tail_point.y() + dy)
        if self.points:
            self.points = [QPointF(p.x() + dx, p.y() + dy) for p in self.points]
