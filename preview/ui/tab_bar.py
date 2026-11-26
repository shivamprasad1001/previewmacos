"""
macOS-styled Window Tabs and Document Tab Bar for Preview macOS.

Custom-painted browser-style tab bar:
  * rounded-top tabs, the selected tab joins the content area below it
  * hover highlight, thin separators between inactive tabs
  * close button that appears on the selected / hovered tab
  * dirty indicator: a dot replaces the close button until the tab is hovered
  * middle-click closes a tab, double-click on empty space opens a new tab
  * drag to reorder, scroll buttons when tabs overflow

Dirty state is read from the tab text: a title starting with a bullet
(for example "\u25cf report.pdf") shows the dot and the bullet is not drawn
as text.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any
import re
import uuid

from PyQt6.QtWidgets import QWidget, QTabBar, QHBoxLayout, QToolButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen

from preview.core.document import Document
from preview.core.history import HistoryManager
from preview.theme import StudioTheme


# --- Geometry -----------------------------------------------------------
TAB_BAR_HEIGHT = 34      # full bar height (visual tab starts TAB_TOP_INSET below)
TAB_TOP_INSET = 5        # gap above the tabs
TAB_RADIUS = 8.0         # top corner radius
TAB_MIN_WIDTH = 110
TAB_MAX_WIDTH = 220
TAB_PAD = 12             # left padding before the title
TAB_PAD_RIGHT = 8        # gap between close button and tab edge
CLOSE_SIZE = 16          # close button hit area
DIRTY_BULLET = "\u25cf"

_RGBA_RE = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)"
)


def _qcolor(value: Any) -> QColor:
    """Convert hex names or CSS 'rgba(r, g, b, a)' strings to a QColor."""
    if isinstance(value, QColor):
        return QColor(value)
    text = str(value).strip()
    if text == "transparent":
        return QColor(0, 0, 0, 0)
    m = _RGBA_RE.fullmatch(text)
    if m:
        r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
        raw_alpha = m.group(4)
        if raw_alpha is None:
            alpha = 255
        else:
            a = float(raw_alpha)
            alpha = int(round(a * 255)) if a <= 1.0 else int(a)
        return QColor(r, g, b, max(0, min(255, alpha)))
    color = QColor(text)
    return color if color.isValid() else QColor(0, 0, 0, 0)


class ThemeName(str, Enum):
    """Canonical theme identifiers. Use these instead of raw strings."""
    DARK = "dark"
    LIGHT = "light"


@dataclass
class DocumentTabState:
    """Encapsulates independent document state for a single tab."""
    tab_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document: Optional[Document] = None
    file_path: Optional[str] = None
    title: str = "Untitled"
    current_page: int = 0
    zoom: float = 1.0
    view_mode: str = "Single"
    pan_offset: QPointF = field(default_factory=lambda: QPointF(0, 0))
    annotations: Dict[int, List[Any]] = field(default_factory=dict)
    history: HistoryManager = field(default_factory=HistoryManager)
    is_modified: bool = False


class MacTabBar(QTabBar):
    """Custom-painted browser-style tab bar with reordering and close buttons."""

    empty_area_double_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macTabBar")
        self.setMovable(True)
        # Close buttons are drawn and handled by this class.
        self.setTabsClosable(False)
        self.setExpanding(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideMiddle)
        self.setDrawBase(False)
        self.setMouseTracking(True)
        self.setAccessibleName("Document tabs")
        self._theme: ThemeName = ThemeName.DARK
        self._hover_tab: int = -1
        self._hover_close: int = -1
        self._press_close: int = -1
        self._press_middle: int = -1

    # --- Theme ----------------------------------------------------------
    def update_theme(self, theme_name: ThemeName) -> None:
        """Apply the given theme. No-op if the theme is unchanged."""
        if theme_name == self._theme:
            return
        self._theme = theme_name
        self.update()

    def _colors(self) -> Dict[str, QColor]:
        is_dark = self._theme == ThemeName.DARK
        s = StudioTheme
        raw = {
            "bg_bar": s.DARK_BG_WINDOW if is_dark else s.LIGHT_BG_WINDOW,
            "border": s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE,
            "text": s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY,
            "text_sel": s.DARK_TEXT_PRIMARY if is_dark else s.LIGHT_TEXT_PRIMARY,
            "text_hover": "#ffffff" if is_dark else "#000000",
            "sel_bg": s.DARK_BG_CARD if is_dark else s.LIGHT_BG_CARD,
            "sel_border": s.DARK_BORDER if is_dark else s.LIGHT_BORDER,
            "hover_bg": s.DARK_BG_HOVER if is_dark else s.LIGHT_BG_HOVER,
            "close_hover": s.DARK_DANGER_SUBTLE if is_dark else "rgba(239, 68, 68, 0.15)",
            "accent": s.DARK_ACCENT if is_dark else s.LIGHT_ACCENT,
        }
        colors = {k: _qcolor(v) for k, v in raw.items()}
        sep = QColor(colors["text"])
        sep.setAlpha(70)
        colors["separator"] = sep
        return colors

    # --- Title helpers --------------------------------------------------
    def _split_title(self, index: int):
        """Return (clean_title, is_dirty) for a tab."""
        text = self.tabText(index)
        dirty = text.lstrip().startswith(DIRTY_BULLET)
        if dirty:
            text = text.lstrip().lstrip(DIRTY_BULLET).strip()
        return text, dirty

    def _title_font(self, selected: bool) -> QFont:
        font = QFont(self.font())
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Medium)
        return font

    # --- Geometry -------------------------------------------------------
    def tabSizeHint(self, index: int) -> QSize:
        text, _ = self._split_title(index)
        fm = QFontMetrics(self._title_font(False))
        width = (
            fm.horizontalAdvance(text)
            + TAB_PAD
            + TAB_PAD_RIGHT + CLOSE_SIZE + 4
            + 2
        )
        width = max(TAB_MIN_WIDTH, min(TAB_MAX_WIDTH, width))
        return QSize(width, TAB_BAR_HEIGHT)

    def minimumTabSizeHint(self, index: int) -> QSize:
        return QSize(TAB_MIN_WIDTH, TAB_BAR_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        return QSize(120, TAB_BAR_HEIGHT)

    def _visual_rect(self, index: int) -> QRectF:
        """The drawn tab shape (inset from the full tab rect)."""
        r = QRectF(self.tabRect(index))
        return QRectF(
            r.left() + 1.0,
            r.top() + TAB_TOP_INSET,
            r.width() - 2.0,
            r.height() - TAB_TOP_INSET,
        )

    def _close_rect(self, index: int) -> QRectF:
        vis = self._visual_rect(index)
        x = vis.right() - TAB_PAD_RIGHT - CLOSE_SIZE
        y = vis.top() + (vis.height() - CLOSE_SIZE) / 2.0
        return QRectF(x, y, CLOSE_SIZE, CLOSE_SIZE)

    # --- Painting -------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._colors()

        painter.fillRect(self.rect(), c["bg_bar"])

        # Bottom border of the whole bar (the selected tab covers its part)
        painter.setPen(QPen(c["border"], 1))
        y = self.height() - 0.5
        painter.drawLine(QPointF(0, y), QPointF(self.width(), y))

        count = self.count()
        current = self.currentIndex()
        order = [i for i in range(count) if i != current]
        if 0 <= current < count:
            order.append(current)
        for i in order:
            self._paint_tab(painter, i, c)

    def _tab_path(self, vis: QRectF) -> QPainterPath:
        r = TAB_RADIUS
        path = QPainterPath()
        path.moveTo(vis.left(), vis.bottom() + 1.0)
        path.lineTo(vis.left(), vis.top() + r)
        path.arcTo(QRectF(vis.left(), vis.top(), 2 * r, 2 * r), 180, -90)
        path.lineTo(vis.right() - r, vis.top())
        path.arcTo(QRectF(vis.right() - 2 * r, vis.top(), 2 * r, 2 * r), 90, -90)
        path.lineTo(vis.right(), vis.bottom() + 1.0)
        return path

    def _paint_tab(self, p: QPainter, i: int, c: Dict[str, QColor]) -> None:
        vis = self._visual_rect(i)
        selected = i == self.currentIndex()
        hovered = i == self._hover_tab
        title, dirty = self._split_title(i)

        p.save()
        if selected:
            path = self._tab_path(vis)
            p.setPen(Qt.PenStyle.NoPen)
            p.fillPath(path, c["sel_bg"])
            p.setPen(QPen(c["sel_border"], 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)  # open path: no bottom edge
            # Accent line along the top edge
            p.setPen(QPen(c["accent"], 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.drawLine(
                QPointF(vis.left() + TAB_RADIUS, vis.top() + 1.0),
                QPointF(vis.right() - TAB_RADIUS, vis.top() + 1.0),
            )
        elif hovered:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c["hover_bg"])
            p.drawRoundedRect(vis.adjusted(2, 2, -2, -3), 6, 6)
        else:
            # Separator on the right edge, hidden next to selected/hovered tabs
            nxt = i + 1
            if (
                nxt < self.count()
                and nxt != self.currentIndex()
                and i != self._hover_tab
                and nxt != self._hover_tab
            ):
                p.setPen(QPen(c["separator"], 1))
                top = vis.top() + 6
                bottom = vis.bottom() - 7
                p.drawLine(QPointF(vis.right(), top), QPointF(vis.right(), bottom))
        p.restore()

        # Title
        if selected:
            text_color = c["text_sel"]
        elif hovered:
            text_color = c["text_hover"]
        else:
            text_color = c["text"]
        font = self._title_font(selected)
        p.save()
        p.setFont(font)
        p.setPen(text_color)
        text_rect = QRectF(
            vis.left() + TAB_PAD,
            vis.top(),
            vis.width() - TAB_PAD - TAB_PAD_RIGHT - CLOSE_SIZE - 4,
            vis.height(),
        )
        elided = QFontMetrics(font).elidedText(
            title, Qt.TextElideMode.ElideMiddle, max(0, int(text_rect.width()))
        )
        p.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            elided,
        )
        p.restore()

        # Close button or dirty dot
        close_rect = self._close_rect(i)
        show_close = selected or hovered
        if dirty and not hovered:
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(text_color)
            center = close_rect.center()
            p.drawEllipse(center, 3.5, 3.5)
            p.restore()
        elif show_close:
            p.save()
            if i == self._hover_close:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(c["close_hover"])
                p.drawEllipse(close_rect.adjusted(1, 1, -1, -1))
            glyph = QColor(text_color)
            if i == self._hover_close:
                glyph = c["text_hover"]
            p.setPen(QPen(glyph, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            center = close_rect.center()
            d = 3.2
            p.drawLine(QPointF(center.x() - d, center.y() - d), QPointF(center.x() + d, center.y() + d))
            p.drawLine(QPointF(center.x() - d, center.y() + d), QPointF(center.x() + d, center.y() - d))
            p.restore()

    # --- Mouse handling -------------------------------------------------
    def _close_hit(self, index: int, pos: QPointF) -> bool:
        return index >= 0 and self._close_rect(index).contains(pos)

    def mouseMoveEvent(self, event) -> None:
        if self._press_close >= 0:
            event.accept()
            return
        pos = event.position()
        idx = self.tabAt(pos.toPoint())
        close_idx = idx if self._close_hit(idx, pos) else -1
        if idx != self._hover_tab or close_idx != self._hover_close:
            self._hover_tab = idx
            self._hover_close = close_idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover_tab != -1 or self._hover_close != -1:
            self._hover_tab = -1
            self._hover_close = -1
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        idx = self.tabAt(pos.toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self._close_hit(idx, pos):
            self._press_close = idx
            event.accept()
            return
        if event.button() == Qt.MouseButton.MiddleButton and idx >= 0:
            self._press_middle = idx
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        pos = event.position()
        idx = self.tabAt(pos.toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self._press_close >= 0:
            pressed = self._press_close
            self._press_close = -1
            if idx == pressed and self._close_hit(idx, pos):
                self._hover_tab = -1
                self._hover_close = -1
                self.tabCloseRequested.emit(idx)
            self.update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.MiddleButton and self._press_middle >= 0:
            pressed = self._press_middle
            self._press_middle = -1
            if idx == pressed:
                self._hover_tab = -1
                self._hover_close = -1
                self.tabCloseRequested.emit(idx)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.tabAt(event.position().toPoint()) < 0
        ):
            self.empty_area_double_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def tabRemoved(self, index: int) -> None:
        self._hover_tab = -1
        self._hover_close = -1
        self._press_close = -1
        self._press_middle = -1
        super().tabRemoved(index)
        self.update()


class MacTabBarContainer(QWidget):
    """
    Container holding MacTabBar and the '+' New Tab button.

    Signal notes:
      * tab_moved(from, to): `to` is the *new* index after the move. If you
        keep a parallel list of DocumentTabState, apply
        ``states.insert(to, states.pop(from))`` to keep them in sync.
      * current_changed is suppressed when index == -1 (no tabs remaining).
        React to tab_close_requested or your own model for the empty case.
      * Double-clicking empty space in the bar emits new_tab_clicked.
    """
    new_tab_clicked = pyqtSignal()
    tab_close_requested = pyqtSignal(int)
    current_changed = pyqtSignal(int)
    tab_moved = pyqtSignal(int, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("macTabBarContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(TAB_BAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(4)

        self.tab_bar = MacTabBar(self)
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        self.tab_bar.currentChanged.connect(self._on_current_changed)
        self.tab_bar.tabMoved.connect(self.tab_moved.emit)
        self.tab_bar.empty_area_double_clicked.connect(self.new_tab_clicked.emit)
        layout.addWidget(self.tab_bar, 1)

        self.add_tab_btn = QToolButton(self)
        self.add_tab_btn.setObjectName("newTabBtn")
        self.add_tab_btn.setText("+")
        self.add_tab_btn.setFixedSize(22, 22)
        self.add_tab_btn.setToolTip("New Tab (Ctrl+T)")
        self.add_tab_btn.setAccessibleName("New tab")
        self.add_tab_btn.clicked.connect(self.new_tab_clicked.emit)
        # Center the button in the visual tab area (below the top inset)
        layout.addWidget(self.add_tab_btn, 0, Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 6, (TAB_BAR_HEIGHT - TAB_TOP_INSET - 22) // 2 + 1)

        self._theme: ThemeName = ThemeName.DARK
        self.update_theme(ThemeName.DARK)

    def minimumSizeHint(self) -> QSize:
        return QSize(120, TAB_BAR_HEIGHT)

    def _on_current_changed(self, idx: int) -> None:
        """Forward currentChanged only for valid indices (>= 0)."""
        if idx >= 0:
            self.current_changed.emit(idx)

    def update_theme(self, theme_name: ThemeName) -> None:
        """Apply the given theme to the bar and the '+' button."""
        self._theme = theme_name
        self.tab_bar.update_theme(theme_name)
        is_dark = theme_name == ThemeName.DARK
        s = StudioTheme
        bg_bar = s.DARK_BG_WINDOW if is_dark else s.LIGHT_BG_WINDOW
        border_b = s.DARK_BORDER_SUBTLE if is_dark else s.LIGHT_BORDER_SUBTLE
        btn_hover = s.DARK_BG_HOVER if is_dark else s.LIGHT_BG_HOVER
        btn_col = s.DARK_TEXT_SECONDARY if is_dark else s.LIGHT_TEXT_SECONDARY

        self.setStyleSheet(f"""
            #macTabBarContainer {{
                background-color: {bg_bar};
                border-bottom: 1px solid {border_b};
            }}
            #newTabBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {btn_col};
                font-size: 16px;
                font-weight: 400;
            }}
            #newTabBtn:hover {{
                background-color: {btn_hover};
                color: {"#ffffff" if is_dark else "#000000"};
            }}
        """)