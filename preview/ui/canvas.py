"""
Interactive document canvas widget supporting High-DPI rendering, zoom, pan, 
markup drawing, handle manipulation, search highlight, and cropping.
"""

from typing import List, Optional, Tuple, Dict
from PIL import Image

from PyQt6.QtWidgets import QWidget, QInputDialog, QMenu, QDialog
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QCursor, QMouseEvent, 
    QWheelEvent, QKeyEvent, QPaintEvent, QNativeGestureEvent, QPainterPath
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer, QEvent, QVariantAnimation, QEasingCurve

from preview.core.document import Document, SearchResult
from preview.core.annotations import AnnotationItem, AnnotationType, Handle
from preview.core.history import HistoryManager, ActionCommand
from preview.ui.sticky_note_dialog import StickyNoteDialog

class CanvasView(QWidget):
    """Interactive canvas rendering document pages and annotations."""

    zoom_changed = pyqtSignal(float)
    status_message = pyqtSignal(str)
    crop_available = pyqtSignal(bool)
    tool_deselected = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("documentCanvas")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.document: Optional[Document] = None
        self.history: HistoryManager = HistoryManager()
        self.current_page: int = 0
        self.zoom: float = 1.0

        # Annotations per page: page_idx -> List[AnnotationItem]
        self.annotations: Dict[int, List[AnnotationItem]] = {}
        
        # Current active tool
        self.active_tool: AnnotationType = AnnotationType.NONE
        self.stroke_color: QColor = QColor("#ff3b30")
        self.stroke_width: float = 3.0
        self.fill_color: QColor = QColor(Qt.GlobalColor.transparent)
        self.font_size: int = 16
        self.font_family: str = "-apple-system"
        self.active_signature_pixmap: Optional[QPixmap] = None

        # Interaction state
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF()
        self._pan_offset: QPointF = QPointF(0, 0)
        self._space_held: bool = False

        self._active_annotation: Optional[AnnotationItem] = None
        self._selected_annotation: Optional[AnnotationItem] = None
        self._is_dragging_item: bool = False
        self._drag_start_doc_pt: QPointF = QPointF()
        self._item_dragged_total_dx: float = 0.0
        self._item_dragged_total_dy: float = 0.0

        # Handle Resizing State
        self._active_handle: Handle = Handle.NONE
        self._resize_orig_bounds: QRectF = QRectF()
        self._resize_orig_points: List[QPointF] = []

        # Selection / Crop box
        self.crop_box: Optional[AnnotationItem] = None
        self._resizing_handle: int = -1  # 0 to 7

        # Search highlights
        self.search_results: List[SearchResult] = []
        self.current_search_idx: int = -1
        self._auto_fit: bool = True

        # Rubber-band edge spring physics
        self._spring_anim: Optional[QVariantAnimation] = None
        self._spring_timer: QTimer = QTimer(self)
        self._spring_timer.setSingleShot(True)
        self._spring_timer.timeout.connect(self._spring_to_bounds)
        self.floating_pill = None

        # Loupe / Magnifier
        self.loupe_enabled: bool = False
        self._loupe_pos: QPointF = QPointF(-1000, -1000)
        self._loupe_radius: float = 80.0
        self._loupe_zoom: float = 2.5

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._auto_fit and self.document:
            self.zoom_to_fit()
        if hasattr(self, "floating_pill") and self.floating_pill:
            self.floating_pill._reposition()

    def set_document(self, doc: Document):
        self.document = doc
        self.current_page = 0
        self.annotations.clear()
        self.crop_box = None
        self._pan_offset = QPointF(0, 0)
        self._auto_fit = True
        self.zoom_to_fit()
        self.update()

    def set_page(self, page_idx: int):
        if self.document and 0 <= page_idx < self.document.page_count:
            self.current_page = page_idx
            self.crop_box = None
            self.crop_available.emit(False)
            if self._auto_fit:
                self.zoom_to_fit()
            self.update()

    def set_zoom(self, zoom: float):
        self.zoom = max(0.05, min(10.0, zoom))
        self.zoom_changed.emit(self.zoom)
        self.update()

    def _get_resting_bounds(self) -> Tuple[float, float, float, float]:
        """Calculates (min_x, max_x, min_y, max_y) for page resting positions."""
        if not self.document:
            return (0.0, 0.0, 0.0, 0.0)
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        pw = w_doc * self.zoom
        ph = h_doc * self.zoom
        vw = float(self.width())
        vh = float(self.height())
        padding = 24.0

        if pw + 2 * padding <= vw:
            min_x = max_x = (vw - pw) / 2.0
        else:
            min_x = vw - padding - pw
            max_x = padding

        if ph + 2 * padding <= vh:
            min_y = max_y = (vh - ph) / 2.0
        else:
            min_y = vh - padding - ph
            max_y = padding

        return (min_x, max_x, min_y, max_y)

    def _clamp_offset(self, offset: QPointF) -> QPointF:
        min_x, max_x, min_y, max_y = self._get_resting_bounds()
        cx = min(max_x, max(min_x, offset.x()))
        cy = min(max_y, max(min_y, offset.y()))
        return QPointF(cx, cy)

    def _apply_pan_delta(self, delta: QPointF):
        if self._spring_anim and self._spring_anim.state() == QVariantAnimation.State.Running:
            self._spring_anim.stop()
        min_x, max_x, min_y, max_y = self._get_resting_bounds()
        cur_x = self._pan_offset.x()
        cur_y = self._pan_offset.y()
        dx = delta.x()
        dy = delta.y()

        # Rubber-band edge resistance factor: 0.35 when dragging beyond resting boundaries
        if (cur_x < min_x and dx < 0) or (cur_x > max_x and dx > 0):
            dx *= 0.35
        if (cur_y < min_y and dy < 0) or (cur_y > max_y and dy > 0):
            dy *= 0.35

        self._pan_offset += QPointF(dx, dy)
        self.update()

    def _spring_to_bounds(self):
        target = self._clamp_offset(self._pan_offset)
        diff = target - self._pan_offset
        if abs(diff.x()) > 0.5 or abs(diff.y()) > 0.5:
            if self._spring_anim and self._spring_anim.state() == QVariantAnimation.State.Running:
                self._spring_anim.stop()
            self._spring_anim = QVariantAnimation(self)
            self._spring_anim.setDuration(160)
            self._spring_anim.setStartValue(self._pan_offset)
            self._spring_anim.setEndValue(target)
            self._spring_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._spring_anim.valueChanged.connect(self._on_spring_tick)
            self._spring_anim.start()

    def _on_spring_tick(self, val):
        self._pan_offset = val
        self.update()

    def zoom_at(self, anchor_pos: QPointF, factor: float):
        self._auto_fit = False
        old_zoom = self.zoom
        new_zoom = max(0.05, min(10.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-4:
            return

        doc_x = (anchor_pos.x() - self._pan_offset.x()) / old_zoom
        doc_y = (anchor_pos.y() - self._pan_offset.y()) / old_zoom

        self.zoom = new_zoom
        self.zoom_changed.emit(self.zoom)
        self._pan_offset = QPointF(
            anchor_pos.x() - doc_x * new_zoom,
            anchor_pos.y() - doc_y * new_zoom
        )
        self.update()
        self._spring_to_bounds()

    def zoom_in(self):
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        self.zoom_at(center, 1.25)

    def zoom_out(self):
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        self.zoom_at(center, 1.0 / 1.25)

    def zoom_actual_size(self):
        self._auto_fit = False
        self.set_zoom(1.0)
        if self.document:
            w_doc, h_doc = self.document.get_page_size(self.current_page)
            self._pan_offset = QPointF(
                (self.width() - w_doc) / 2,
                (self.height() - h_doc) / 2
            )
        self.update()

    def zoom_to_fit(self):
        self._auto_fit = True
        if not self.document:
            return
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        padding = 24.0
        vw = max(50.0, float(self.width()) - 2.0 * padding)
        vh = max(50.0, float(self.height()) - 2.0 * padding)
        if w_doc > 0 and h_doc > 0:
            scale = min(vw / w_doc, vh / h_doc)
            self.set_zoom(scale)
            # Center offset with 24px padding bounds
            self._pan_offset = QPointF(
                (float(self.width()) - w_doc * self.zoom) / 2.0,
                (float(self.height()) - h_doc * self.zoom) / 2.0
            )
            self.update()

    def toggle_loupe(self, enable: Optional[bool] = None):
        """Toggles macOS Loupe / Magnifier lens inspection tool."""
        if enable is None:
            self.loupe_enabled = not self.loupe_enabled
        else:
            self.loupe_enabled = enable

        if self.loupe_enabled:
            self.set_active_tool(AnnotationType.NONE)
            center = QPointF(self.width() / 2.0, self.height() / 2.0)
            self._loupe_pos = center
            self.status_message.emit("Magnifier active — Move cursor to inspect, Esc to close")
        else:
            self._loupe_pos = QPointF(-1000, -1000)
            self.status_message.emit("Magnifier closed")
        
        self._update_cursor()
        self.update()

    def set_active_tool(self, tool: AnnotationType):
        self.active_tool = tool
        if tool != AnnotationType.NONE and self.loupe_enabled:
            self.loupe_enabled = False
        if tool != AnnotationType.CROP_BOX and self.crop_box:
            self.crop_box = None
            self.crop_available.emit(False)
        self._update_cursor()
        self.update()

    def _update_cursor(self):
        if self._space_held or self._is_panning:
            self.setCursor(Qt.CursorShape.OpenHandCursor if not self._is_panning else Qt.CursorShape.ClosedHandCursor)
        elif self.loupe_enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.active_tool in (AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.active_tool in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, 
                                  AnnotationType.ELLIPSE, AnnotationType.LINE, 
                                  AnnotationType.ARROW, AnnotationType.CROP_BOX,
                                  AnnotationType.REDACT):
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self.active_tool == AnnotationType.TEXT:
            self.setCursor(Qt.CursorShape.IBeamCursor)
        elif self.active_tool in (AnnotationType.NOTE, AnnotationType.SIGNATURE):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_font_size(self, size: int):
        self.font_size = size
        if self._selected_annotation and self._selected_annotation.item_type == AnnotationType.TEXT:
            self._selected_annotation.font_size = size
            self.update()

    def set_font_family(self, family: str):
        self.font_family = family
        if self._selected_annotation and self._selected_annotation.item_type == AnnotationType.TEXT:
            self._selected_annotation.font_family = family
            self.update()

    def clamp_to_doc_bounds(self, pt: QPointF) -> QPointF:
        if not self.document:
            return pt
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        return QPointF(max(0.0, min(float(w_doc), float(pt.x()))),
                       max(0.0, min(float(h_doc), float(pt.y()))))

    def is_inside_doc_bounds(self, pt: QPointF) -> bool:
        if not self.document:
            return False
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        return (0.0 <= pt.x() <= w_doc) and (0.0 <= pt.y() <= h_doc)

    def get_document_page_rect(self) -> QRectF:
        """Returns the page rectangle in canvas view coordinates."""
        if not self.document:
            return QRectF()
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        return QRectF(self._pan_offset.x(), self._pan_offset.y(), w_doc * self.zoom, h_doc * self.zoom)

    def view_to_doc_coords(self, pt: QPointF) -> QPointF:
        """Transforms canvas pixel coordinates to document point coordinates."""
        return QPointF((pt.x() - self._pan_offset.x()) / self.zoom, 
                       (pt.y() - self._pan_offset.y()) / self.zoom)

    def doc_to_view_coords(self, pt: QPointF) -> QPointF:
        """Transforms document coordinates to canvas coordinates."""
        return QPointF(pt.x() * self.zoom + self._pan_offset.x(),
                       pt.y() * self.zoom + self._pan_offset.y())

    # --- Mouse Events ---
    def mousePressEvent(self, event: QMouseEvent):
        if self._spring_anim and self._spring_anim.state() == QVariantAnimation.State.Running:
            self._spring_anim.stop()

        if event.button() == Qt.MouseButton.RightButton:
            self._show_canvas_context_menu(event.position())
            return

        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self._space_held):
            self._is_panning = True
            self._pan_start = event.position()
            self._update_cursor()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            doc_pt = self.view_to_doc_coords(event.position())

            # 0. Check if clicking on a resize handle of the currently selected annotation
            if self._selected_annotation and self.active_tool == AnnotationType.NONE:
                hit_h = self._selected_annotation.get_handle_at_point(doc_pt, self.zoom)
                if hit_h != Handle.NONE:
                    self._active_handle = hit_h
                    self._resize_orig_bounds = QRectF(self._selected_annotation.get_bounds())
                    self._resize_orig_points = [QPointF(p) for p in self._selected_annotation.points]
                    return

            # If drawing tool active, ignore clicks outside document page bounds
            if self.active_tool != AnnotationType.NONE:
                if not self.is_inside_doc_bounds(doc_pt):
                    return
                doc_pt = self.clamp_to_doc_bounds(doc_pt)

            # 1. Handle Crop Tool
            if self.active_tool == AnnotationType.CROP_BOX:
                self.crop_box = AnnotationItem(AnnotationType.CROP_BOX)
                self.crop_box.rect = QRectF(doc_pt, doc_pt)
                self.crop_available.emit(True)
                self.update()
                return

            # 2. Handle Pen / Highlighter
            if self.active_tool in (AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                item = AnnotationItem(self.active_tool)
                item.stroke_color = QColor(self.stroke_color)
                item.stroke_width = self.stroke_width
                item.points = [doc_pt]
                self._active_annotation = item
                self._get_current_annotations().append(item)
                self.update()
                return

            # 3. Handle Shapes & Redaction
            if self.active_tool in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT, 
                                    AnnotationType.ELLIPSE, AnnotationType.LINE, 
                                    AnnotationType.ARROW, AnnotationType.REDACT):
                item = AnnotationItem(self.active_tool)
                item.stroke_color = QColor(self.stroke_color)
                item.stroke_width = self.stroke_width
                item.fill_color = QColor(self.fill_color)
                item.rect = QRectF(doc_pt, doc_pt)
                item.points = [doc_pt, doc_pt]
                self._active_annotation = item
                self._get_current_annotations().append(item)
                self.update()
                return

            # 4. Handle Text tool
            if self.active_tool == AnnotationType.TEXT:
                text, ok = QInputDialog.getText(self, "Add Text", "Enter annotation text:", text="Text")
                if ok and text.strip():
                    item = AnnotationItem(AnnotationType.TEXT)
                    item.text = text
                    item.stroke_color = QColor(self.stroke_color)
                    item.font_size = self.font_size
                    item.font_family = self.font_family
                    item.rect = QRectF(doc_pt.x(), doc_pt.y(), 180, 36)
                    self._get_current_annotations().append(item)
                    page = self.current_page
                    self._push_add_command(item, page)
                    self.update()
                return

            # 5. Handle Note tool
            if self.active_tool == AnnotationType.NOTE:
                dlg = StickyNoteDialog(initial_text="", parent=self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    note_text = dlg.get_text()
                    if note_text.strip():
                        item = AnnotationItem(AnnotationType.NOTE)
                        item.text = note_text
                        item.rect = QRectF(doc_pt.x(), doc_pt.y(), 32, 32)
                        self._get_current_annotations().append(item)
                        page = self.current_page
                        self._push_add_command(item, page)
                        self.update()
                return

            # 6. Handle Signature tool
            if self.active_tool == AnnotationType.SIGNATURE and self.active_signature_pixmap:
                item = AnnotationItem(AnnotationType.SIGNATURE)
                item.signature_pixmap = self.active_signature_pixmap
                sw = self.active_signature_pixmap.width() / 2
                sh = self.active_signature_pixmap.height() / 2
                item.rect = QRectF(doc_pt.x(), doc_pt.y(), sw, sh)
                self._get_current_annotations().append(item)
                page = self.current_page
                self._push_add_command(item, page)
                self.update()
                return

            # 7. Selection / Moving existing annotations
            clicked_item = None
            for item in reversed(self._get_current_annotations()):
                if item.contains_point(doc_pt):
                    clicked_item = item
                    break
            
            for item in self._get_current_annotations():
                item.is_selected = (item is clicked_item)
            
            self._selected_annotation = clicked_item
            if clicked_item:
                self._is_dragging_item = True
                self._drag_start_doc_pt = doc_pt
                self._item_dragged_total_dx = 0.0
                self._item_dragged_total_dy = 0.0
            
            self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            doc_pt = self.view_to_doc_coords(event.position())
            for item in reversed(self._get_current_annotations()):
                if item.contains_point(doc_pt):
                    if item.item_type == AnnotationType.TEXT:
                        self._edit_text_annotation(item)
                        return
                    elif item.item_type == AnnotationType.NOTE:
                        self._open_sticky_note_dialog(item)
                        return

    def _edit_text_annotation(self, item: AnnotationItem):
        text, ok = QInputDialog.getMultiLineText(
            self, "Edit Text Box", "Text content:", item.text
        )
        if ok and text is not None:
            old_text = item.text
            new_text = text
            page = self.current_page
            def undo_txt():
                if self.current_page != page:
                    self.set_page(page)
                item.text = old_text
                self.update()
            def redo_txt():
                if self.current_page != page:
                    self.set_page(page)
                item.text = new_text
                self.update()
            item.text = new_text
            self.history.push(ActionCommand("Edit Text", undo_txt, redo_txt))
            self.update()

    def _open_sticky_note_dialog(self, item: AnnotationItem):
        dlg = StickyNoteDialog(initial_text=item.text, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_text = dlg.get_text()
            if new_text != item.text:
                old_text = item.text
                page = self.current_page
                def undo_note():
                    if self.current_page != page:
                        self.set_page(page)
                    item.text = old_text
                    self.update()
                def redo_note():
                    if self.current_page != page:
                        self.set_page(page)
                    item.text = new_text
                    self.update()
                item.text = new_text
                self.history.push(ActionCommand("Edit Sticky Note", undo_note, redo_note))
                self.update()

    def _push_add_command(self, item: AnnotationItem, page: int):
        def undo_fn():
            if self.current_page != page:
                self.set_page(page)
            if item in self.annotations.get(page, []):
                self.annotations[page].remove(item)
                if self._selected_annotation is item:
                    self._selected_annotation = None
                self.update()
        def redo_fn():
            if self.current_page != page:
                self.set_page(page)
            if page not in self.annotations:
                self.annotations[page] = []
            self.annotations[page].append(item)
            self.update()
        self.history.push(ActionCommand("Add Annotation", undo_fn, redo_fn))

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._apply_pan_delta(delta)
            self._pan_start = event.position()
            return

        if self.loupe_enabled:
            self._loupe_pos = event.position()
            self.update()

        doc_pt = self.view_to_doc_coords(event.position())

        # 0. Handle Active Resize Handle Dragging
        if self._active_handle != Handle.NONE and self._selected_annotation and (event.buttons() & Qt.MouseButton.LeftButton):
            doc_pt_clamped = self.clamp_to_doc_bounds(doc_pt)
            self._selected_annotation.resize_by_handle(
                self._active_handle, doc_pt_clamped, self._resize_orig_bounds, self._resize_orig_points
            )
            self.update()
            return

        # 1. Update Crop Box (clamped to page bounds)
        if self.crop_box and (event.buttons() & Qt.MouseButton.LeftButton):
            doc_pt_clamped = self.clamp_to_doc_bounds(doc_pt)
            p1 = self.crop_box.rect.topLeft()
            self.crop_box.rect = QRectF(p1, doc_pt_clamped).normalized()
            self.update()
            return

        # 2. Update Active Drawing Annotation (clamped to page bounds)
        if self._active_annotation and (event.buttons() & Qt.MouseButton.LeftButton):
            doc_pt_clamped = self.clamp_to_doc_bounds(doc_pt)
            if self._active_annotation.item_type in (AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                self._active_annotation.points.append(doc_pt_clamped)
            elif self._active_annotation.item_type in (AnnotationType.RECTANGLE, 
                                                        AnnotationType.ROUNDED_RECT, 
                                                        AnnotationType.ELLIPSE,
                                                        AnnotationType.REDACT):
                p1 = self._active_annotation.rect.topLeft()
                self._active_annotation.rect = QRectF(p1, doc_pt_clamped).normalized()
            elif self._active_annotation.item_type in (AnnotationType.LINE, AnnotationType.ARROW):
                if len(self._active_annotation.points) >= 2:
                    self._active_annotation.points[1] = doc_pt_clamped
            self.update()
            return

        # 3. Dragging Selected Annotation
        if self._is_dragging_item and self._selected_annotation and (event.buttons() & Qt.MouseButton.LeftButton):
            dx = doc_pt.x() - self._drag_start_doc_pt.x()
            dy = doc_pt.y() - self._drag_start_doc_pt.y()
            self._selected_annotation.translate(dx, dy)
            self._item_dragged_total_dx += dx
            self._item_dragged_total_dy += dy
            self._drag_start_doc_pt = doc_pt
            self.update()
            return

        # 4. Hover cursor update over resize handles
        if self.active_tool == AnnotationType.NONE and self._selected_annotation and not event.buttons():
            handle = self._selected_annotation.get_handle_at_point(doc_pt, self.zoom)
            if handle in (Handle.NW, Handle.SE):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif handle in (Handle.NE, Handle.SW):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif handle in (Handle.N, Handle.S):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif handle in (Handle.E, Handle.W):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif handle in (Handle.START, Handle.END):
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self._selected_annotation.contains_point(doc_pt):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self._update_cursor()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self._update_cursor()
            self._spring_to_bounds()
            return

        # Commit resize handle drag
        if self._active_handle != Handle.NONE:
            self._active_handle = Handle.NONE
            if self._selected_annotation:
                item = self._selected_annotation
                old_b = QRectF(self._resize_orig_bounds)
                old_pts = [QPointF(p) for p in self._resize_orig_points]
                new_b = QRectF(item.get_bounds())
                new_pts = [QPointF(p) for p in item.points]
                page = self.current_page
                def undo_resize():
                    if self.current_page != page:
                        self.set_page(page)
                    if item.item_type in (AnnotationType.LINE, AnnotationType.ARROW, AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                        item.points = [QPointF(p) for p in old_pts]
                    else:
                        item.rect = QRectF(old_b)
                    self.update()
                def redo_resize():
                    if self.current_page != page:
                        self.set_page(page)
                    if item.item_type in (AnnotationType.LINE, AnnotationType.ARROW, AnnotationType.PEN, AnnotationType.HIGHLIGHTER):
                        item.points = [QPointF(p) for p in new_pts]
                    else:
                        item.rect = QRectF(new_b)
                    self.update()
                self.history.push(ActionCommand("Resize Annotation", undo_resize, redo_resize))
            self.update()
            return

        if self._active_annotation:
            item = self._active_annotation
            page = self.current_page
            self._push_add_command(item, page)
            self._active_annotation = None

        if self._is_dragging_item:
            self._is_dragging_item = False
            if self._selected_annotation and (abs(self._item_dragged_total_dx) > 1 or abs(self._item_dragged_total_dy) > 1):
                item = self._selected_annotation
                tdx = self._item_dragged_total_dx
                tdy = self._item_dragged_total_dy
                page = self.current_page
                def undo_move():
                    if self.current_page != page:
                        self.set_page(page)
                    item.translate(-tdx, -tdy)
                    self.update()
                def redo_move():
                    if self.current_page != page:
                        self.set_page(page)
                    item.translate(tdx, tdy)
                    self.update()
                self.history.push(ActionCommand("Move Annotation", undo_move, redo_move))

        self.update()

    def undo(self):
        if self.history.undo():
            self.status_message.emit("Undo")
            self.update()
        else:
            self.status_message.emit("Nothing to undo")

    def redo(self):
        if self.history.redo():
            self.status_message.emit("Redo")
            self.update()
        else:
            self.status_message.emit("Nothing to redo")

    def unselect_tools(self):
        """Resets active drawing/crop tools to standard pointer mode."""
        self.set_active_tool(AnnotationType.NONE)
        if self.crop_box:
            self.crop_box = None
            self.crop_available.emit(False)
        if self._selected_annotation:
            self._selected_annotation.is_selected = False
            self._selected_annotation = None
        self._update_cursor()
        self.update()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture:
            if hasattr(event, "gestureType") and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                factor = 1.0 + event.value()
                self.zoom_at(event.position(), factor)
                return True
        return super().event(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta != 0:
                factor = 1.0015 ** delta
                self.zoom_at(event.position(), factor)
            event.accept()
        else:
            dy = event.angleDelta().y() / 2.0
            dx = event.angleDelta().x() / 2.0
            self._apply_pan_delta(QPointF(dx, dy))
            self._spring_timer.start(100)
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.unselect_tools()
            self.tool_deselected.emit()
            event.accept()
            return

        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if event.key() == Qt.Key.Key_Z:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.redo()
                else:
                    self.undo()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Y:
                self.redo()
                event.accept()
                return

        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_held = True
            self._update_cursor()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self._selected_annotation and self._selected_annotation in self._get_current_annotations():
                item = self._selected_annotation
                page = self.current_page
                idx = self._get_current_annotations().index(item)
                def undo_del():
                    if self.current_page != page:
                        self.set_page(page)
                    if page not in self.annotations:
                        self.annotations[page] = []
                    self.annotations[page].insert(idx, item)
                    self._selected_annotation = item
                    item.is_selected = True
                    self.update()
                def redo_del():
                    if self.current_page != page:
                        self.set_page(page)
                    if item in self.annotations.get(page, []):
                        self.annotations[page].remove(item)
                    if self._selected_annotation is item:
                        self._selected_annotation = None
                    self.update()
                self.history.push(ActionCommand("Delete Annotation", undo_del, redo_del))
                self._get_current_annotations().remove(item)
                self._selected_annotation = None
                self.update()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_held = False
            self._update_cursor()
        super().keyReleaseEvent(event)

    # --- Actions ---
    def apply_crop(self):
        """Applies active crop selection to the current document image."""
        if not self.crop_box or not self.document:
            return

        r = self.crop_box.rect.normalized()
        if r.width() < 10 or r.height() < 10:
            return

        # If document is an image, crop PIL image
        if not self.document.is_pdf and self.document._pil_image:
            old_img = self.document._pil_image.copy()
            crop_rect = (int(r.left()), int(r.top()), int(r.right()), int(r.bottom()))
            cropped = old_img.crop(crop_rect)
            page = self.current_page
            self.document.update_image(cropped, page)
            self.crop_box = None
            self.crop_available.emit(False)
            self.zoom_to_fit()
            self.status_message.emit("Image cropped successfully.")

            def undo_crop():
                self.document.update_image(old_img, page)
                self.zoom_to_fit()
            def redo_crop():
                self.document.update_image(cropped, page)
                self.zoom_to_fit()
            self.history.push(ActionCommand("Crop Image", undo_crop, redo_crop))

    def _get_current_annotations(self) -> List[AnnotationItem]:
        if self.current_page not in self.annotations:
            self.annotations[self.current_page] = []
        return self.annotations[self.current_page]

    # --- Paint Event ---
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if not self.document:
            # Draw placeholder when no file is open
            painter.setPen(QPen(QColor("#8e8e93")))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                             "Drag and drop a PDF or image here,\nor click Open File")
            return

        # 1. Render Document Page
        page_pix = self.document.render_page(self.current_page, zoom=self.zoom)
        page_rect = self.get_document_page_rect()

        # Draw subtle macOS paper drop shadow
        painter.setPen(Qt.PenStyle.NoPen)
        shadow_outer = page_rect.adjusted(-4, 2, 4, 8)
        painter.setBrush(QBrush(QColor(0, 0, 0, 16)))
        painter.drawRoundedRect(shadow_outer, 6, 6)

        shadow_mid = page_rect.adjusted(-2, 1, 2, 4)
        painter.setBrush(QBrush(QColor(0, 0, 0, 28)))
        painter.drawRoundedRect(shadow_mid, 4, 4)

        shadow_inner = page_rect.adjusted(-1, 0, 1, 2)
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        painter.drawRoundedRect(shadow_inner, 2, 2)

        # Draw page pixmap
        painter.drawPixmap(int(page_rect.left()), int(page_rect.top()), page_pix)

        # Subtle crisp page outline
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(page_rect)

        # 2. Draw Search Results Highlights
        if self.search_results:
            for s in self.search_results:
                if s.page_num == self.current_page:
                    sr_view = QRectF(
                        page_rect.left() + s.rect.left() * self.zoom,
                        page_rect.top() + s.rect.top() * self.zoom,
                        s.rect.width() * self.zoom,
                        s.rect.height() * self.zoom
                    )
                    painter.setBrush(QBrush(QColor(255, 230, 0, 110)))
                    painter.setPen(QPen(QColor(255, 170, 0, 180), 1.0))
                    painter.drawRect(sr_view)

        # 3. Draw Annotations on this page
        painter.save()
        painter.translate(page_rect.topLeft())
        w_doc, h_doc = self.document.get_page_size(self.current_page)
        painter.setClipRect(QRectF(0, 0, w_doc * self.zoom, h_doc * self.zoom))
        for item in self._get_current_annotations():
            item.draw(painter, zoom=self.zoom)
        
        # 4. Draw Crop Box
        if self.crop_box:
            self.crop_box.draw(painter, zoom=self.zoom)
        painter.restore()

        # 5. Draw Loupe / Magnifier Lens if active
        pos_pt = self._loupe_pos.toPoint() if hasattr(self._loupe_pos, "toPoint") else self._loupe_pos
        if self.loupe_enabled and self.document and self.rect().contains(pos_pt):
            painter.save()
            cx, cy = float(self._loupe_pos.x()), float(self._loupe_pos.y())
            r = self._loupe_radius
            lens_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

            # Drop shadow under lens
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
            painter.drawEllipse(lens_rect.adjusted(-2, 3, 2, 7))

            # Magnified document coordinates
            doc_center = self.view_to_doc_coords(QPointF(cx, cy))
            mag_zoom = max(0.2, self.zoom * self._loupe_zoom)
            
            # Render magnified page
            mag_pix = self.document.render_page(self.current_page, zoom=mag_zoom)
            mag_page_x = cx - doc_center.x() * mag_zoom
            mag_page_y = cy - doc_center.y() * mag_zoom

            # Circular clipping path for lens
            clip = QPainterPath()
            clip.addEllipse(lens_rect)
            painter.setClipPath(clip)

            # White page backing
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(lens_rect)

            # Draw magnified document
            painter.drawPixmap(int(mag_page_x), int(mag_page_y), mag_pix)

            # Draw magnified annotations inside loupe
            painter.save()
            painter.translate(mag_page_x, mag_page_y)
            for item in self._get_current_annotations():
                item.draw(painter, zoom=mag_zoom)
            painter.restore()

            # Glass reticle & bezel
            painter.setClipping(False)
            pen_cross = QPen(QColor(10, 132, 255, 120), 1.0)
            painter.setPen(pen_cross)
            painter.drawLine(QPointF(cx - 8, cy), QPointF(cx + 8, cy))
            painter.drawLine(QPointF(cx, cy - 8), QPointF(cx, cy + 8))

            # macOS silver-titanium bezel
            rim_outer = QPen(QColor(50, 50, 55, 230), 3.5)
            painter.setPen(rim_outer)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(lens_rect)

            rim_inner = QPen(QColor(255, 255, 255, 160), 1.0)
            painter.setPen(rim_inner)
            painter.drawEllipse(lens_rect.adjusted(1.5, 1.5, -1.5, -1.5))

            painter.restore()

    def _show_canvas_context_menu(self, pos: QPointF):
        if not self.document:
            return
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        menu.setObjectName("canvasContextMenu")
        
        # Copy page text
        if self.document.is_pdf:
            act_copy = QAction("Copy Page Text", self)
            act_copy.triggered.connect(self._copy_page_text)
            menu.addAction(act_copy)
            menu.addSeparator()

        # Loupe
        act_loupe = QAction("Hide Magnifier" if self.loupe_enabled else "Show Magnifier", self)
        act_loupe.setShortcut("~")
        act_loupe.triggered.connect(lambda: self.toggle_loupe())
        menu.addAction(act_loupe)
        menu.addSeparator()

        # Zoom
        act_fit = QAction("Zoom to Fit", self)
        act_fit.triggered.connect(self.zoom_to_fit)
        menu.addAction(act_fit)

        act_actual = QAction("Actual Size", self)
        act_actual.triggered.connect(self.zoom_actual_size)
        menu.addAction(act_actual)
        menu.addSeparator()

        # Rotate
        act_rot = QAction("Rotate 90° Clockwise", self)
        act_rot.triggered.connect(lambda: self.document.rotate_page(self.current_page, 90))
        menu.addAction(act_rot)

        menu.exec(self.mapToGlobal(pos.toPoint()))

    def _copy_page_text(self):
        if self.document and self.document.is_pdf:
            txt = self.document.extract_text(self.current_page)
            if txt:
                from PyQt6.QtWidgets import QApplication
                QApplication.clipboard().setText(txt)
                self.status_message.emit(f"Copied {len(txt)} characters to clipboard")
            else:
                self.status_message.emit("No selectable text on this page")
