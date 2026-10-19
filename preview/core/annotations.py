"""
Annotation model supporting markup, sketches, shapes, text, signatures, and crop selections.
Provides interactive hit-testing, resize handles, and rendering over documents.
"""

from enum import Enum, auto
from typing import List, Optional, Tuple
import math

from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont, QPixmap
from PyQt6.QtCore import Qt, QPointF, QRectF

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
    REDACT = auto()

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

    def draw(self, painter: QPainter, zoom: float = 1.0):
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
            
            font = QFont(self.font_family, int(self.font_size * zoom), QFont.Weight.Medium)
            painter.setFont(font)
            painter.setPen(QPen(self.stroke_color))
            painter.drawText(scaled_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.text)

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
            # Dim outside region
            # (Outside region dimming is handled in canvas view)
            pen = QPen(QColor("#007aff"), 2.0)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(scaled_rect)
            # Draw handles
            self._draw_resize_handles(painter, scaled_rect)

        # Draw selection border and handles if selected
        if self.is_selected and self.item_type != AnnotationType.CROP_BOX:
            doc_b = self.get_bounds()
            bounds = QRectF(doc_b.x() * zoom, doc_b.y() * zoom,
                            doc_b.width() * zoom, doc_b.height() * zoom)
            pen = QPen(QColor("#0a84ff"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(bounds.adjusted(-4, -4, 4, 4))
            self._draw_resize_handles(painter, bounds.adjusted(-4, -4, 4, 4))

        painter.restore()

    def _draw_resize_handles(self, painter: QPainter, rect: QRectF):
        """Draws standard macOS resize handles."""
        h_sz = 8.0
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#0a84ff"), 1.5))
        
        if self.item_type in (AnnotationType.LINE, AnnotationType.ARROW) and len(self.points) >= 2:
            # Handles on start and end
            for pt in [rect.topLeft(), rect.bottomRight()]:
                painter.drawRect(QRectF(pt.x() - h_sz/2, pt.y() - h_sz/2, h_sz, h_sz))
            return

        handles = [
            rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight(),
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(), rect.center().y()),
            QPointF(rect.right(), rect.center().y())
        ]
        for pt in handles:
            painter.drawRect(QRectF(pt.x() - h_sz/2, pt.y() - h_sz/2, h_sz, h_sz))

    def get_handles_positions(self, zoom: float = 1.0) -> dict:
        """Returns dictionary of {Handle: QPointF} in document coordinates."""
        if self.item_type in (AnnotationType.LINE, AnnotationType.ARROW):
            if len(self.points) >= 2:
                return {
                    Handle.START: self.points[0],
                    Handle.END: self.points[1]
                }
            return {}

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
                              AnnotationType.CROP_BOX, AnnotationType.REDACT):
            self.rect = new_rect

        elif self.item_type in (AnnotationType.PEN, AnnotationType.HIGHLIGHTER) and orig_points and orig_bounds.isValid():
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
                              AnnotationType.CROP_BOX, AnnotationType.REDACT):
            return self.rect.normalized()
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
        if self.points:
            self.points = [QPointF(p.x() + dx, p.y() + dy) for p in self.points]
