"""
macOS-style collapsible left sidebar with page thumbnails and table of contents outline.

Features:
  * Animated segmented control with sliding selection pill
  * Per-item hover cross-fade on thumbnails
  * Selection-ring "breathe" pulse
  * Cross-fade between Thumbnails / Contact Sheet / Outline
  * Animated splitter resizing when switching modes
  * Smooth animated scroll-to-selected-page
  * Fade-in on document load
  * Empty-state view
"""

from typing import Optional
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QLabel, QStackedWidget,
    QStyledItemDelegate, QStyle, QMenu, QMessageBox,
    QSlider, QFileDialog, QSizePolicy, QGraphicsOpacityEffect,
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QAction,
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QRectF, QEvent, QPointF,
    QVariantAnimation, QPropertyAnimation, QEasingCurve, QAbstractAnimation,
)

from preview.core.document import Document
from preview.icons import MacIconFactory
from preview.theme import StudioTheme


class ThemeName(str, Enum):
    DARK = "dark"
    LIGHT = "light"


def _resolve_theme_name(theme) -> str:
    if isinstance(theme, ThemeName):
        return theme.value
    if isinstance(theme, str):
        return theme
    return getattr(theme, "value", "dark")


# =====================================================================
#  ANIMATED SEGMENTED CONTROL
# =====================================================================
class AnimatedSegmentedControl(QWidget):
    """macOS-style segmented control with a smoothly sliding selection pill and animated hover."""

    segmentClicked = pyqtSignal(int)

    _H_PAD = 2
    _V_PAD = 2
    _TRACK_RADIUS = 7
    _PILL_RADIUS = 5
    _ANIM_MS = 220
    _HOVER_ANIM_MS = 120

    def __init__(self, labels, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._labels = list(labels)
        self._current = 0
        self._pill_pos: float = 0.0
        self._hover_idx: int = -1
        self._hover_alpha: float = 0.0
        self._is_dark = True
        self.setMouseTracking(True)
        self.setFixedHeight(28)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Selection sliding animation (interpolates fractional segment position 0.0 .. len-1)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(self._ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_frame)

        # Hover fade animation
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(self._HOVER_ANIM_MS)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.valueChanged.connect(self._on_hover_anim_frame)

    # ---- public API ----
    def minimumSizeHint(self) -> QSize:
        return QSize(120, 28)

    def sizeHint(self) -> QSize:
        return QSize(220, 28)

    def currentIndex(self) -> int:
        return self._current

    @property
    def _indicator(self) -> QRectF:
        """Backward-compatible property returning the instantaneous pill rectangle."""
        return self._pill_rect_for_pos(self._pill_pos)

    def setCurrentIndex(self, idx: int, animate: bool = True) -> None:
        if not (0 <= idx < len(self._labels)):
            return
        if idx == self._current:
            if abs(self._pill_pos - float(idx)) > 1e-4:
                self._pill_pos = float(idx)
                self.update()
            return

        start = self._pill_pos
        self._current = idx
        target = float(idx)

        # If hovering over the newly selected index, fade out hover highlight
        if self._hover_idx == idx:
            self._hover_alpha = 0.0

        if animate and self.isVisible():
            if self._anim.state() == QAbstractAnimation.State.Running:
                self._anim.stop()
            self._anim.setStartValue(start)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            if self._anim.state() == QAbstractAnimation.State.Running:
                self._anim.stop()
            self._pill_pos = target
            self.update()

    def set_dark(self, is_dark: bool) -> None:
        if is_dark == self._is_dark:
            return
        self._is_dark = is_dark
        self.update()

    # ---- internals ----
    def _seg_width(self) -> float:
        return self.width() / max(1, len(self._labels))

    def _seg_rect(self, idx: int) -> QRectF:
        return self._pill_rect_for_pos(float(idx))

    def _pill_rect_for_pos(self, pos: float) -> QRectF:
        w = self._seg_width()
        return QRectF(
            pos * w + self._H_PAD,
            self._V_PAD,
            w - 2 * self._H_PAD,
            self.height() - 2 * self._V_PAD,
        )

    def _on_anim_frame(self, val) -> None:
        self._pill_pos = float(val)
        self.update()

    def _on_hover_anim_frame(self, val) -> None:
        self._hover_alpha = float(val)
        self.update()

    def _animate_hover_to(self, idx: int) -> None:
        if idx == self._hover_idx:
            return
        self._hover_idx = idx
        target_alpha = 1.0 if (0 <= idx < len(self._labels) and idx != self._current) else 0.0

        if self._hover_anim.state() == QAbstractAnimation.State.Running:
            self._hover_anim.stop()

        if self.isVisible():
            self._hover_anim.setStartValue(self._hover_alpha)
            self._hover_anim.setEndValue(target_alpha)
            self._hover_anim.start()
        else:
            self._hover_alpha = target_alpha
            self.update()

    def _hit_test(self, pos: QPointF) -> int:
        if not self.rect().contains(pos.toPoint()) or self.width() <= 0:
            return -1
        w = self._seg_width()
        idx = int(pos.x() / w)
        return idx if 0 <= idx < len(self._labels) else -1

    # ---- events ----
    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        if self._anim.state() != QAbstractAnimation.State.Running:
            self._pill_pos = float(self._current)
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            idx = self._hit_test(e.position())
            if 0 <= idx < len(self._labels):
                if idx != self._current:
                    self.setCurrentIndex(idx)
                self.segmentClicked.emit(idx)

    def mouseMoveEvent(self, e) -> None:
        idx = self._hit_test(e.position())
        if idx != self._hover_idx:
            self._animate_hover_to(idx)

    def leaveEvent(self, e) -> None:
        self._animate_hover_to(-1)

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = StudioTheme
        is_dark = self._is_dark

        bg = QColor(s.DARK_BG_CARD if is_dark else s.LIGHT_BG_CARD)
        border = QColor(s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE)
        sel_bg = QColor(s.DARK_BG_WINDOW if is_dark else "#ffffff")
        sel_border = QColor(s.DARK_BORDER if is_dark else s.LIGHT_BORDER)
        text_active = QColor(s.DARK_TEXT_PRIMARY if is_dark else s.LIGHT_TEXT_PRIMARY)
        text_idle = QColor(s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY)

        # Track
        track = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(track, self._TRACK_RADIUS, self._TRACK_RADIUS)

        # Hover highlight (smooth animated pill on unselected segment)
        if 0 <= self._hover_idx < len(self._labels) and self._hover_idx != self._current and self._hover_alpha > 0.005:
            hover_r = self._seg_rect(self._hover_idx)
            max_alpha = 28 if is_dark else 20
            cur_alpha = int(max_alpha * self._hover_alpha)
            hover_bg = QColor(255, 255, 255, cur_alpha) if is_dark else QColor(0, 0, 0, cur_alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(hover_bg))
            p.drawRoundedRect(hover_r, self._PILL_RADIUS, self._PILL_RADIUS)

        # Sliding selected pill (always computed dynamically from _pill_pos and current width)
        pill_rect = self._pill_rect_for_pos(self._pill_pos)

        # Subtle drop shadow under selected pill for macOS elevation
        shadow_rect = pill_rect.adjusted(0.0, 0.5, 0.0, 1.0)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 35 if is_dark else 20)))
        p.drawRoundedRect(shadow_rect, self._PILL_RADIUS, self._PILL_RADIUS)

        # Selected pill background & border
        p.setPen(QPen(sel_border, 1))
        p.setBrush(QBrush(sel_bg))
        p.drawRoundedRect(pill_rect, self._PILL_RADIUS, self._PILL_RADIUS)

        # Labels
        for i, label in enumerate(self._labels):
            r = self._seg_rect(i)
            dist = abs(self._pill_pos - float(i))
            if dist < 0.35:
                col = text_active
                weight = QFont.Weight.DemiBold
            elif i == self._hover_idx and self._hover_alpha > 0.1:
                col = text_active
                weight = QFont.Weight.Medium
            else:
                col = text_idle
                weight = QFont.Weight.Medium

            seg_w = r.width()
            font = QFont(s.FONT_FAMILY)
            font.setPixelSize(11 if seg_w >= 62 else 10)
            font.setWeight(weight)
            p.setFont(font)
            p.setPen(col)
            avail_w = max(8, int(seg_w - 6))
            text = p.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, avail_w)
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), text)


# =====================================================================
#  ANIMATED THUMBNAIL DELEGATE
# =====================================================================
class MacThumbnailDelegate(QStyledItemDelegate):
    """Apple-Preview-style thumbnail cards with animated hover & selection pulse."""

    def __init__(self, sidebar: "MacSidebar"):
        super().__init__(sidebar)
        self.sidebar = sidebar

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        doc = self.sidebar.document
        if not doc:
            painter.restore()
            return

        page_idx = index.row()
        if page_idx < 0 or page_idx >= doc.page_count:
            painter.restore()
            return

        is_dark = self.sidebar._theme == "dark"
        s = StudioTheme
        accent = QColor(s.DARK_ACCENT if is_dark else s.LIGHT_ACCENT)
        text_secondary = QColor(s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY)

        thumb_w = float(getattr(self.sidebar, "thumbnail_width", 110))
        try:
            pix = doc.get_thumbnail(page_idx, width=int(thumb_w))
        except Exception:
            pix = None

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        r = option.rect

        # --- 1. Picture rect ---
        if pix is None or pix.isNull():
            draw_w, draw_h = float(thumb_w), float(thumb_w) * 1.3
            max_ph = draw_h
        else:
            pw, ph = pix.width(), pix.height()
            max_pw = float(thumb_w)
            max_ph = float(thumb_w) * 1.3
            scale = min(max_pw / max(1, pw), max_ph / max(1, ph))
            draw_w = pw * scale
            draw_h = ph * scale

        badge_h = 17.0
        group_h = draw_h + 6.0 + badge_h
        pic_x = r.left() + (r.width() - draw_w) / 2.0
        pic_y = r.top() + max(6.0, (r.height() - group_h) / 2.0)
        pic_rect = QRectF(pic_x, pic_y, draw_w, draw_h)

        badge_text = str(page_idx + 1)
        badge_w = max(24.0, len(badge_text) * 7.5 + 14.0)
        badge_x = r.left() + (r.width() - badge_w) / 2.0
        badge_y = pic_rect.bottom() + 6.0
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        # --- 2. Animated hover card ---
        hover_progress = self.sidebar._hover_progress.get(page_idx, 0.0)
        if hover_progress > 0.001 and not is_selected:
            card_w = max(draw_w + 16.0, 56.0)
            card_x = r.left() + (r.width() - card_w) / 2.0
            card_top = pic_rect.top() - 5.0
            card_h = (badge_rect.bottom() + 5.0) - card_top
            base_alpha = 26 if is_dark else 18
            a = int(base_alpha * hover_progress)
            hover_bg = QColor(255, 255, 255, a) if is_dark else QColor(0, 0, 0, a)
            border_a = int((18 if is_dark else 14) * hover_progress)
            hover_border = QColor(255, 255, 255, border_a) if is_dark else QColor(0, 0, 0, border_a)
            painter.setBrush(QBrush(hover_bg))
            painter.setPen(QPen(hover_border, 1.0))
            painter.drawRoundedRect(QRectF(card_x, card_top, card_w, card_h), 6.0, 6.0)

        # --- 3. Drop shadow ---
        shadow_rect = pic_rect.adjusted(-1.0, 1.0, 1.0, 3.0)
        painter.setBrush(QBrush(QColor(0, 0, 0, 45)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 4.0, 4.0)

        # --- 4. Thumbnail (clipped) ---
        clip = QPainterPath()
        clip.addRoundedRect(pic_rect, 4.0, 4.0)
        painter.save()
        painter.setClipPath(clip)
        if pix is not None and not pix.isNull():
            painter.drawPixmap(pic_rect.toRect(), pix)
        else:
            placeholder = QColor(255, 255, 255, 10) if is_dark else QColor(0, 0, 0, 8)
            painter.fillRect(pic_rect, placeholder)
        painter.restore()

        # --- 5. Selection ring (animated pulse) or subtle border ---
        if is_selected:
            pulse = self.sidebar._pulse_progress if self.sidebar._pulse_page == page_idx else 0.0
            ring_alpha = int(255 * (1.0 - 0.55 * pulse))
            ring_width = 3.0 + 3.0 * (1.0 - pulse)
            extra = 2.5 + 1.5 * (1.0 - pulse)
            sel_ring = pic_rect.adjusted(-extra, -extra, extra, extra)
            ring_col = QColor(accent)
            ring_col.setAlpha(ring_alpha)
            painter.setPen(QPen(ring_col, ring_width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(sel_ring, 5.0, 5.0)
        else:
            border_col = QColor(255, 255, 255, 30) if is_dark else QColor(0, 0, 0, 35)
            painter.setPen(QPen(border_col, 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(pic_rect, 4.0, 4.0)

        # --- 6. Page number pill ---
        font = QFont(s.FONT_FAMILY)
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.Bold if is_selected else QFont.Weight.Medium)
        painter.setFont(font)

        if is_selected:
            painter.setBrush(QBrush(accent))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 8.5, 8.5)
            painter.setPen(QColor("#ffffff"))
        else:
            pill_bg = QColor(255, 255, 255, 20) if is_dark else QColor(0, 0, 0, 16)
            painter.setBrush(QBrush(pill_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 8.5, 8.5)
            painter.setPen(text_secondary)

        painter.drawText(badge_rect, int(Qt.AlignmentFlag.AlignCenter), badge_text)
        painter.restore()

    def sizeHint(self, option, index):
        return self.sidebar._thumbnail_item_size(index.row())


# =====================================================================
#  SIDEBAR
# =====================================================================
class MacSidebar(QWidget):
    """Collapsible macOS sidebar providing Thumbnails, Contact Sheet, and Table of Contents."""

    page_selected = pyqtSignal(int)

    _SEG_LABELS = ["Thumbnails", "Contact", "Outline"]
    _SEG_MODES = ["Thumbnails", "Contact Sheet", "Table of Contents"]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macSidebar")
        self.setMinimumWidth(140)
        self.setMaximumWidth(850)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.document: Optional[Document] = None
        self.current_view_mode = "Thumbnails"
        self.thumbnail_width: int = 110
        self._last_thumbnail_sidebar_width: int = 220
        self._theme: str = "dark"

        # Animation state
        self._hover_progress: dict = {}
        self._hover_page: int = -1
        self._hover_anim = None
        self._pulse_page: int = -1
        self._pulse_progress: float = 0.0
        self._pulse_anim = None
        self._splitter_anim = None
        self._scroll_anim = None
        self._stack_fade = None
        self._list_fade = None

        self._setup_ui()
        self._apply_style()
        self.set_view_mode("Thumbnails", animate=False)

    def minimumSizeHint(self) -> QSize:
        return QSize(140, 200)

    # =================================================================
    #  SETUP
    # =================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Header ----
        header = QWidget()
        header.setFixedHeight(40)
        header.setObjectName("sidebarHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(6)

        self.seg_control = AnimatedSegmentedControl(self._SEG_LABELS, self)
        self.seg_control.segmentClicked.connect(self._on_segment_clicked)
        header_layout.addWidget(self.seg_control, 1)
        layout.addWidget(header)

        # Backward-compat aliases
        self.view_dropdown = self.seg_control
        self.view_btn = self.seg_control
        self.view_menu = QMenu(self)
        self.act_thumbs = QAction("Thumbnails", self)
        self.act_thumbs.triggered.connect(lambda: self.set_view_mode("Thumbnails"))
        self.act_contact = QAction("Contact Sheet", self)
        self.act_contact.triggered.connect(lambda: self.set_view_mode("Contact Sheet"))
        self.act_toc = QAction("Table of Contents", self)
        self.act_toc.triggered.connect(lambda: self.set_view_mode("Table of Contents"))
        self.view_menu.addAction(self.act_thumbs)
        self.view_menu.addAction(self.act_contact)
        self.view_menu.addAction(self.act_toc)

        # ---- Stack ----
        self.stack = QStackedWidget()

        self.thumb_list = QListWidget()
        self.thumb_list.setObjectName("thumbList")
        self.thumb_list.setItemDelegate(MacThumbnailDelegate(self))
        self.thumb_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumb_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.thumb_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.thumb_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.thumb_list.setMouseTracking(True)
        self.thumb_list.viewport().setMouseTracking(True)
        self.thumb_list.currentRowChanged.connect(self._on_row_changed)
        self.thumb_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.thumb_list.customContextMenuRequested.connect(self._show_thumb_context_menu)
        self.thumb_list.installEventFilter(self)
        self.thumb_list.viewport().installEventFilter(self)
        if self.thumb_list.model():
            self.thumb_list.model().rowsMoved.connect(self._on_rows_moved)
        self.stack.addWidget(self.thumb_list)

        self.outline_tree = QTreeWidget()
        self.outline_tree.setObjectName("outlineTree")
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.setIndentation(14)
        self.outline_tree.itemClicked.connect(self._on_outline_item_clicked)
        self.stack.addWidget(self.outline_tree)

        # Empty state page
        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_label = QLabel("No document open")
        empty_label.setObjectName("emptyStateLabel")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.stack.addWidget(self.empty_page)

        layout.addWidget(self.stack, 1)

        # ---- Footer ----
        self.footer = QWidget()
        self.footer.setFixedHeight(30)
        self.footer.setObjectName("sidebarFooter")
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(10, 3, 10, 3)
        footer_layout.setSpacing(8)

        lbl_s = QLabel()
        lbl_s.setObjectName("footerIconSmall")
        lbl_s.setPixmap(MacIconFactory.create_icon("thumbnails", "#8e8e93", 10).pixmap(10, 10))
        footer_layout.addWidget(lbl_s)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setObjectName("thumbSizeSlider")
        self.size_slider.setRange(70, 220)
        self.size_slider.setValue(110)
        self.size_slider.setToolTip("Thumbnail Size")
        self.size_slider.setFixedHeight(16)
        self.size_slider.valueChanged.connect(self._on_thumbnail_size_changed)
        footer_layout.addWidget(self.size_slider, 1)

        lbl_l = QLabel()
        lbl_l.setObjectName("footerIconLarge")
        lbl_l.setPixmap(MacIconFactory.create_icon("thumbnails", "#8e8e93", 16).pixmap(16, 16))
        footer_layout.addWidget(lbl_l)

        self.page_count_label = QLabel("")
        self.page_count_label.setObjectName("pageCountLabel")
        self.page_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(self.page_count_label)

        layout.addWidget(self.footer)

    # =================================================================
    #  THEME
    # =================================================================
    def _apply_style(self):
        is_dark = self._theme == "dark"
        s = StudioTheme

        bg = s.DARK_BG_WINDOW if is_dark else s.LIGHT_BG_WINDOW
        bg_card = s.DARK_BG_CARD if is_dark else s.LIGHT_BG_CARD
        bg_hover = s.DARK_BG_HOVER if is_dark else s.LIGHT_BG_HOVER
        border = s.DARK_BORDER if is_dark else s.LIGHT_BORDER
        border_subtle = s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE
        text_primary = s.DARK_TEXT_PRIMARY if is_dark else s.LIGHT_TEXT_PRIMARY
        text_secondary = s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY
        accent = s.DARK_ACCENT if is_dark else s.LIGHT_ACCENT

        self.seg_control.set_dark(is_dark)

        self.setStyleSheet(f"""
            #macSidebar {{
                background-color: {bg};
                border-right: 1px solid {border};
            }}
            #sidebarHeader {{
                background-color: {bg};
                border-bottom: 1px solid {border_subtle};
            }}
            #thumbList {{
                background-color: {bg};
                border: none;
                outline: 0;
            }}
            #thumbList::item, #thumbList::item:selected,
            #thumbList::item:hover, #thumbList::item:selected:hover {{
                background: transparent;
                border: none;
            }}
            #outlineTree {{
                background-color: {bg};
                border: none;
                outline: 0;
                color: {text_primary};
                font-family: {s.FONT_FAMILY};
                font-size: 12px;
            }}
            #outlineTree::item {{
                padding: 4px 6px;
                border-radius: 4px;
                margin: 1px 6px;
            }}
            #outlineTree::item:hover {{
                background-color: {bg_hover};
            }}
            #outlineTree::item:selected {{
                background-color: {accent};
                color: #ffffff;
            }}
            #sidebarFooter {{
                background-color: {bg};
                border-top: 1px solid {border_subtle};
            }}
            #thumbSizeSlider::groove:horizontal {{
                background: {border};
                height: 3px;
                border-radius: 1px;
            }}
            #thumbSizeSlider::handle:horizontal {{
                background: {text_secondary};
                width: 11px; height: 11px;
                margin: -4px 0;
                border-radius: 5px;
            }}
            #thumbSizeSlider::handle:horizontal:hover {{
                background: {text_primary};
            }}
            #pageCountLabel {{
                color: {text_secondary};
                font-family: {s.FONT_FAMILY};
                font-size: 10px;
            }}
            #emptyStateLabel {{
                color: {text_secondary};
                font-family: {s.FONT_FAMILY};
                font-size: 13px;
            }}
            QMenu#thumbContextMenu {{
                background-color: {bg_card};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px;
                color: {text_primary};
                font-family: {s.FONT_FAMILY};
                font-size: 12px;
            }}
            QMenu#thumbContextMenu::item {{
                padding: 5px 20px 5px 12px;
                border-radius: 4px;
            }}
            QMenu#thumbContextMenu::item:selected {{
                background-color: {accent};
                color: #ffffff;
            }}
            QMenu#thumbContextMenu::separator {{
                height: 1px;
                background: {border_subtle};
                margin: 4px 6px;
            }}
        """)
        self.thumb_list.viewport().update()

    def update_theme(self, theme_name):
        new_theme = _resolve_theme_name(theme_name)
        if new_theme == self._theme:
            return
        self._theme = new_theme
        self._apply_style()
        self.thumb_list.viewport().update()
        self.outline_tree.viewport().update()

    # =================================================================
    #  ANIMATION HELPERS
    # =================================================================
    def _stop_anim(self, attr_name: str) -> None:
        """Safely stop and forget an animation, tolerating an already-deleted C++ object."""
        anim = getattr(self, attr_name, None)
        if anim is None:
            return
        try:
            if anim.state() == QAbstractAnimation.State.Running:
                anim.stop()
        except RuntimeError:
            pass  # C++ side already gone
        finally:
            setattr(self, attr_name, None)

    def _forget_anim(self, attr_name: str, anim: QAbstractAnimation) -> None:
        if getattr(self, attr_name, None) is anim:
            setattr(self, attr_name, None)

    def _track_anim(self, attr_name: str, anim: QAbstractAnimation,
                    on_finished=None) -> None:
        """Replace the animation in `attr_name`, auto-clear on finish, and start it.

        Uses the default KeepWhenStopped policy — do NOT delete on stop,
        or the C++ object is deleted while we still hold a Python reference.
        """
        self._stop_anim(attr_name)
        setattr(self, attr_name, anim)
        if on_finished is not None:
            anim.finished.connect(on_finished)
        anim.finished.connect(lambda a=anim, n=attr_name: self._forget_anim(n, a))
        anim.start()

    # =================================================================
    #  THUMBNAIL LAYOUT
    # =================================================================
    def _thumbnail_item_size(self, page_idx: int) -> QSize:
        size = float(self.thumbnail_width)
        item_w = int(size + 24)
        max_ph = size * 1.3
        default_h = int(max_ph) + 38

        doc = self.document
        if self.current_view_mode == "Contact Sheet" or not doc or doc.page_count > 100:
            return QSize(item_w, default_h)

        if not (0 <= page_idx < doc.page_count):
            return QSize(item_w, default_h)

        if doc.is_pdf or page_idx < 50:
            try:
                pw, ph = doc.get_page_size(page_idx)
                scale = min(size / max(1.0, pw), max_ph / max(1.0, ph))
                draw_h = max(24.0, ph * scale)
                return QSize(item_w, int(draw_h) + 36)
            except Exception:
                return QSize(item_w, default_h)
        return QSize(item_w, default_h)

    def _apply_thumbnail_layout(self):
        size = self.thumbnail_width
        item_w = int(size + 24)
        item_h = int(size * 1.3) + 38
        uniform_size = QSize(item_w, item_h)

        if self.current_view_mode == "Contact Sheet":
            self.thumb_list.setViewMode(QListWidget.ViewMode.IconMode)
            self.thumb_list.setFlow(QListWidget.Flow.LeftToRight)
            self.thumb_list.setWrapping(True)
            self.thumb_list.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.thumb_list.setMovement(QListWidget.Movement.Static)
            self.thumb_list.setSpacing(8)
            self.thumb_list.setGridSize(QSize(item_w + 10, item_h + 8))
        else:
            self.thumb_list.setViewMode(QListWidget.ViewMode.ListMode)
            self.thumb_list.setFlow(QListWidget.Flow.TopToBottom)
            self.thumb_list.setWrapping(False)
            self.thumb_list.setResizeMode(QListWidget.ResizeMode.Fixed)
            self.thumb_list.setSpacing(4)
            self.thumb_list.setGridSize(QSize())

        is_contact = self.current_view_mode == "Contact Sheet"
        for i in range(self.thumb_list.count()):
            it = self.thumb_list.item(i)
            if it:
                it.setSizeHint(uniform_size if is_contact else self._thumbnail_item_size(i))

        self.thumb_list.doItemsLayout()
        self.thumb_list.viewport().update()

    def _on_thumbnail_size_changed(self, size: int):
        self.thumbnail_width = size
        if self.current_view_mode == "Thumbnails":
            needed_w = int(size + 48)
            if needed_w > self.width() and self.window():
                splitter = getattr(self.window(), "splitter", None)
                if splitter:
                    sizes = splitter.sizes()
                    total_w = sum(sizes)
                    if len(sizes) >= 2:
                        max_sidebar = max(140, total_w - 250)
                        target_w = min(max_sidebar, needed_w)
                        if target_w > sizes[0]:
                            diff = target_w - sizes[0]
                            self._animate_splitter(
                                target_w, max(200, sizes[1] - diff), duration=120
                            )
        self._apply_thumbnail_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_view_mode == "Thumbnails":
            w = self.width()
            if 140 <= w <= 260:
                self._last_thumbnail_sidebar_width = w
        elif self.current_view_mode == "Contact Sheet":
            self.thumb_list.doItemsLayout()

    # =================================================================
    #  DOCUMENT
    # =================================================================
    def set_document(self, doc: Optional[Document]):
        self.document = doc
        if doc is None:
            self.thumb_list.clear()
            self.outline_tree.clear()
            self.page_count_label.setText("")
            self._hover_progress.clear()
            self._hover_page = -1
            self._show_empty_state()
            return

        self.reload_thumbnails()
        self.reload_outline()

        # Restore last non-empty view
        if self.stack.currentIndex() == 2:
            self.set_view_mode(self.current_view_mode, animate=False)
        else:
            self._apply_thumbnail_layout()

        self._fade_in_list()

    def clear(self):
        self.set_document(None)

    def _show_empty_state(self):
        self.stack.setGraphicsEffect(None)
        self.stack.setCurrentIndex(2)
        if hasattr(self, "footer"):
            self.footer.setVisible(False)

    def _fade_in_list(self) -> None:
        if not self.thumb_list.isVisible():
            return
        effect = QGraphicsOpacityEffect(self.thumb_list)
        effect.setOpacity(0.0)
        self.thumb_list.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)   # parented to sidebar
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.thumb_list.setGraphicsEffect(None))
        self._track_anim("_list_fade", anim)

    def reload_thumbnails(self):
        self.thumb_list.blockSignals(True)
        try:
            self._hover_progress.clear()
            self._hover_page = -1
            self.thumb_list.clear()

            if not self.document:
                self.page_count_label.setText("")
                return

            count = self.document.page_count
            self.page_count_label.setText(f"{count} page{'s' if count != 1 else ''}")

            item_w = int(self.thumbnail_width + 24)
            item_h = int(self.thumbnail_width * 1.3) + 38
            item_size = QSize(item_w, item_h)
            for _ in range(count):
                item = QListWidgetItem()
                item.setSizeHint(item_size)
                self.thumb_list.addItem(item)

            self._apply_thumbnail_layout()

            if count > 0:
                current = max(0, min(self.document.current_page, count - 1))
                self.thumb_list.setCurrentRow(current)
        finally:
            self.thumb_list.blockSignals(False)

    def reload_outline(self):
        self.outline_tree.clear()
        if not self.document:
            return

        outline = self.document.get_outline()
        if hasattr(self, "act_toc"):
            self.act_toc.setEnabled(bool(outline))

        if not outline:
            if self.stack.currentIndex() == 1:
                self.set_view_mode("Thumbnails", animate=False)
            return

        parents = {0: self.outline_tree}
        for level, title, page_num in outline:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, page_num)
            parent = parents.get(level - 1, self.outline_tree)
            if parent is self.outline_tree:
                self.outline_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            parents[level] = item
        self.outline_tree.expandAll()

    # =================================================================
    #  SELECTION / SCROLL / PULSE
    # =================================================================
    def select_page(self, page_idx: int, animate: bool = True):
        if not (0 <= page_idx < self.thumb_list.count()):
            return
        self.thumb_list.blockSignals(True)
        try:
            self.thumb_list.setCurrentRow(page_idx)
            item = self.thumb_list.item(page_idx)
            if item:
                if animate:
                    self._animate_scroll_to(item)
                else:
                    self.thumb_list.scrollToItem(item)
        finally:
            self.thumb_list.blockSignals(False)

    def _animate_scroll_to(self, item) -> None:
        sb = self.thumb_list.verticalScrollBar()
        if not sb:
            return
        rect = self.thumb_list.visualItemRect(item)
        target = (sb.value() + rect.top()
                  - self.thumb_list.viewport().height() // 2
                  + rect.height() // 2)
        target = max(sb.minimum(), min(sb.maximum(), target))
        if target == sb.value():
            return

        anim = QPropertyAnimation(sb, b"value", self)   # parented to sidebar
        anim.setDuration(220)
        anim.setStartValue(sb.value())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._track_anim("_scroll_anim", anim)

    def _pulse(self, idx: int) -> None:
        if idx < 0:
            return
        self._pulse_page = idx

        anim = QVariantAnimation(self)
        anim.setDuration(320)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def on_frame(v):
            self._pulse_progress = float(v)
            self.thumb_list.viewport().update()

        anim.valueChanged.connect(on_frame)
        self._track_anim("_pulse_anim", anim)

    def _on_row_changed(self, row: int):
        if row >= 0:
            self.page_selected.emit(row)
            self._pulse(row)

    def _on_outline_item_clicked(self, item, column):
        page_num = item.data(0, Qt.ItemDataRole.UserRole)
        if page_num is not None:
            self.page_selected.emit(page_num)

    # =================================================================
    #  HOVER ANIMATION
    # =================================================================
    def _on_thumb_hover_move(self, pos: QPointF):
        if not self.thumb_list.isEnabled():
            return
        item = self.thumb_list.itemAt(pos.toPoint())
        new_idx = self.thumb_list.row(item) if item else -1
        if new_idx == self._hover_page:
            return
        old_idx = self._hover_page
        self._hover_page = new_idx
        self._animate_hover(old_idx, new_idx)

    def _animate_hover(self, old_idx: int, new_idx: int) -> None:
        anim = QVariantAnimation(self)
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def on_frame(v):
            f = float(v)
            if old_idx >= 0:
                self._hover_progress[old_idx] = max(0.0, 1.0 - f)
            if new_idx >= 0:
                self._hover_progress[new_idx] = f
            self.thumb_list.viewport().update()

        anim.valueChanged.connect(on_frame)
        self._track_anim(
            "_hover_anim", anim,
            on_finished=lambda: self._prune_hover(old_idx, new_idx),
        )

    def _prune_hover(self, old_idx: int, new_idx: int):
        for idx in (old_idx, new_idx):
            if idx >= 0 and self._hover_progress.get(idx, 1.0) < 0.01:
                self._hover_progress.pop(idx, None)

    def _clear_hover(self):
        if self._hover_page >= 0:
            self._animate_hover(self._hover_page, -1)
            self._hover_page = -1

    # =================================================================
    #  VIEW MODE
    # =================================================================
    def _on_segment_clicked(self, idx: int):
        if 0 <= idx < len(self._SEG_MODES):
            self.set_view_mode(self._SEG_MODES[idx])

    def set_view_mode(self, mode_name: str, animate: bool = True):
        prev_mode = self.current_view_mode
        self.current_view_mode = mode_name

        is_toc = mode_name in ("Table of Contents", "Outline")

        # Sync the segmented control (no recursive emit — setCurrentIndex is silent)
        seg_idx = 2 if is_toc else (1 if mode_name == "Contact Sheet" else 0)
        self.seg_control.setCurrentIndex(seg_idx, animate=animate and self.isVisible())

        target_stack_idx = 1 if is_toc else 0

        if animate and self.isVisible() and self.stack.currentIndex() != target_stack_idx:
            self._cross_fade_to(target_stack_idx)
        else:
            self.stack.setGraphicsEffect(None)
            self.stack.setCurrentIndex(target_stack_idx)

        self.footer.setVisible(not is_toc)
        self._adjust_splitter_for_mode(prev_mode, mode_name, animate=animate)

        if not is_toc:
            self._apply_thumbnail_layout()

    def _cross_fade_to(self, idx: int, duration_out: int = 120,
                       duration_in: int = 160) -> None:
        if idx == self.stack.currentIndex():
            return

        self._stop_anim("_stack_fade")

        effect = QGraphicsOpacityEffect(self.stack)
        effect.setOpacity(1.0)
        self.stack.setGraphicsEffect(effect)

        out_anim = QPropertyAnimation(effect, b"opacity", self)
        out_anim.setDuration(duration_out)
        out_anim.setStartValue(1.0)
        out_anim.setEndValue(0.0)
        out_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def on_out_done():
            self.stack.setCurrentIndex(idx)
            in_anim = QPropertyAnimation(effect, b"opacity", self)
            in_anim.setDuration(duration_in)
            in_anim.setStartValue(0.0)
            in_anim.setEndValue(1.0)
            in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            in_anim.finished.connect(
                lambda: self.stack.setGraphicsEffect(None)
            )
            self._track_anim("_stack_fade", in_anim)

        out_anim.finished.connect(on_out_done)
        self._track_anim("_stack_fade", out_anim)

    def _adjust_splitter_for_mode(self, prev_mode: str, mode_name: str, animate: bool = True):
        window = self.window()
        if not window:
            return
        splitter = getattr(window, "splitter", None)
        if not splitter:
            return
        sizes = splitter.sizes()
        if len(sizes) < 2:
            return

        duration = 220 if animate else 0
        is_toc = mode_name in ("Table of Contents", "Outline")

        if mode_name == "Thumbnails":
            total_w = sum(sizes)
            saved_w = getattr(self, "_last_thumbnail_sidebar_width", 220)
            target_w = max(216, min(saved_w, int(self.thumbnail_width + 110)))
            target_w = max(140, min(target_w, max(140, total_w - 250)))
            if sizes[0] > target_w:
                diff = sizes[0] - target_w
                self._animate_splitter(target_w, sizes[1] + diff, duration=duration)
        elif mode_name == "Contact Sheet":
            if prev_mode == "Thumbnails" and sizes[0] > 0:
                self._last_thumbnail_sidebar_width = sizes[0]
            total_w = sum(sizes)
            grid_w = int(self.thumbnail_width + 38)
            needed_w = max(300, (grid_w * 2) + 40)
            max_sidebar = max(140, total_w - 250)
            target_w = min(max_sidebar, needed_w)
            if target_w > sizes[0]:
                diff = target_w - sizes[0]
                self._animate_splitter(target_w, max(200, sizes[1] - diff), duration=duration)
        elif is_toc:
            if sizes[0] > 260:
                saved_w = getattr(self, "_last_thumbnail_sidebar_width", 220)
                target_w = min(saved_w, 240)
                diff = sizes[0] - target_w
                self._animate_splitter(target_w, sizes[1] + diff, duration=duration)

    def _animate_splitter(self, target_left: int, target_right: int,
                          duration: int = 220) -> None:
        window = self.window()
        if not window:
            return
        splitter = getattr(window, "splitter", None)
        if not splitter:
            return
        sizes = splitter.sizes()
        if len(sizes) < 2:
            return
        start_l, start_r = sizes[0], sizes[1]
        if start_l == target_left:
            return
        if duration <= 0:
            splitter.setSizes([target_left, target_right])
            return

        anim = QVariantAnimation(self)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def on_frame(v):
            f = float(v)
            left_w = int(start_l + (target_left - start_l) * f)
            right_w = int(start_r + (target_right - start_r) * f)
            splitter.setSizes([left_w, max(0, right_w)])

        anim.valueChanged.connect(on_frame)
        self._track_anim("_splitter_anim", anim)

    def _toggle_view_mode(self):
        if self.current_view_mode == "Thumbnails":
            self.set_view_mode("Table of Contents")
        else:
            self.set_view_mode("Thumbnails")

    # =================================================================
    #  CONTEXT MENU
    # =================================================================
    def _show_thumb_context_menu(self, pos):
        if not self.document:
            return
        item = self.thumb_list.itemAt(pos)
        if not item:
            return
        idx = self.thumb_list.row(item)

        menu = QMenu(self)
        menu.setObjectName("thumbContextMenu")

        act_rot_cw = QAction("Rotate 90° Clockwise", self)
        act_rot_cw.triggered.connect(lambda: self._rotate_page(idx, 90))
        menu.addAction(act_rot_cw)

        act_rot_ccw = QAction("Rotate 90° Counter-Clockwise", self)
        act_rot_ccw.triggered.connect(lambda: self._rotate_page(idx, -90))
        menu.addAction(act_rot_ccw)

        menu.addSeparator()

        act_dup = QAction("Duplicate Page", self)
        act_dup.triggered.connect(lambda: self._duplicate_page(idx))
        menu.addAction(act_dup)

        act_insert = QAction("Insert Blank Page After", self)
        act_insert.triggered.connect(lambda: self._insert_blank_page(idx))
        menu.addAction(act_insert)

        act_insert_file = QAction("Insert Page from File…", self)
        act_insert_file.triggered.connect(lambda: self._insert_page_from_file(idx))
        menu.addAction(act_insert_file)

        menu.addSeparator()

        act_del = QAction("Delete Page", self)
        act_del.setShortcut("Delete")
        act_del.setEnabled(self.document.page_count > 1)
        act_del.triggered.connect(lambda: self._confirm_and_delete_page(idx))
        menu.addAction(act_del)

        menu.exec(self.thumb_list.mapToGlobal(pos))

    # =================================================================
    #  PAGE OPERATIONS
    # =================================================================
    def _rotate_page(self, idx: int, degrees: int):
        if not self.document:
            return
        self.document.rotate_page(idx, degrees)
        self.thumb_list.viewport().update()

    def _on_rows_moved(self, parent, start, end, destination, row):
        if not self.document:
            return
        to_idx = row - 1 if row > start else row
        if (0 <= start < self.document.page_count
                and 0 <= to_idx < self.document.page_count
                and start != to_idx):
            self.thumb_list.blockSignals(True)
            try:
                self.document.move_page(start, to_idx)
                self.thumb_list.setCurrentRow(to_idx)
            finally:
                self.thumb_list.blockSignals(False)
            self.thumb_list.viewport().update()
            self.page_selected.emit(to_idx)

    def _insert_page_from_file(self, idx: int):
        if not self.document:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert Page from File", "",
            "Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tiff);;"
            "PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*.*)"
        )
        if path and self.document.insert_file(path, idx):
            self._after_page_insert(idx + 1)

    def _duplicate_page(self, idx: int):
        if self.document and self.document.duplicate_page(idx):
            self._after_page_insert(idx + 1)

    def _insert_blank_page(self, idx: int):
        if self.document and self.document.insert_blank_page(idx):
            self._after_page_insert(idx + 1)

    def _after_page_insert(self, new_page_idx: int):
        self.reload_thumbnails()
        self.reload_outline()
        count = self.document.page_count if self.document else 0
        target = max(0, min(new_page_idx, count - 1))
        self.select_page(target)
        self.page_selected.emit(target)

    def _confirm_and_delete_page(self, idx: int):
        if not self.document:
            return
        if self.document.page_count <= 1:
            QMessageBox.information(self, "Delete Page",
                                    "Cannot delete the only page in the document.")
            return

        reply = QMessageBox.question(
            self, "Delete Page",
            f"Are you sure you want to delete page {idx + 1}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.document.delete_page(idx)
            self.reload_thumbnails()
            self.reload_outline()
            new_count = self.document.page_count
            new_current = max(0, min(self.document.current_page, new_count - 1))
            self.select_page(new_current)
            self.page_selected.emit(new_current)

    # =================================================================
    #  EVENTS
    # =================================================================
    def eventFilter(self, source, event):
        if source is self.thumb_list:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                    row = self.thumb_list.currentRow()
                    if row >= 0:
                        self._confirm_and_delete_page(row)
                        return True
            elif event.type() == QEvent.Type.Leave:
                self._clear_hover()
        elif source is self.thumb_list.viewport():
            if event.type() == QEvent.Type.MouseMove:
                self._on_thumb_hover_move(event.position())
            elif event.type() == QEvent.Type.Leave:
                self._clear_hover()
        return super().eventFilter(source, event)
