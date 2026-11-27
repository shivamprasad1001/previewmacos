"""Window chrome, floating HUDs, and draggable toolbar/menubar widgets."""

from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QLabel, QLineEdit, QAbstractButton,
    QMenuBar, QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QColor, QMouseEvent, QPainter, QBrush, QPen, QFont
)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, QPropertyAnimation, QEasingCurve, QTimer

from preview.icons import MacIconFactory
from preview.theme import MacTheme

if TYPE_CHECKING:
    from preview.ui.main_window import MacMainWindow

class FloatingStatusPill(QWidget):
    """Small floating pill displaying page and zoom info at bottom center of canvas, fading after 2s."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("floatingStatusPill")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 5, 14, 5)
        layout.setSpacing(6)

        self.label = QLabel(self)
        self.label.setObjectName("floatingStatusLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(240)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_fade)

        self.hide()

    def show_status(self, text: str):
        if not text:
            return
        self.label.setText(text)
        self.adjustSize()
        self._reposition()
        self.raise_()
        self.show()

        if self.fade_anim.state() == QPropertyAnimation.State.Running:
            self.fade_anim.stop()

        self.opacity_effect.setOpacity(1.0)
        self.timer.start(2000)

    def _start_fade(self):
        if self.fade_anim.state() == QPropertyAnimation.State.Running:
            self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_fade_finished(self):
        if self.opacity_effect.opacity() == 0.0:
            self.hide()

    def _reposition(self):
        p = self.parentWidget()
        if not p:
            return
        x = (p.width() - self.width()) // 2
        y = p.height() - self.height() - 20
        self.move(max(0, x), max(0, y))

class FloatingSlideshowHUD(QWidget):
    """Floating translucent control bar for Fullscreen Slideshow mode."""

    def __init__(self, main_win: 'MacMainWindow', parent: QWidget):
        super().__init__(parent)
        self.main_win = main_win
        self.setObjectName("floatingSlideshowHUD")
        self.setStyleSheet("""
            #floatingSlideshowHUD {
                background-color: rgba(24, 24, 26, 220);
                border: 1px solid rgba(255, 255, 255, 38);
                border-radius: 18px;
            }
            #floatingSlideshowHUD QToolButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                color: #ffffff;
                font-size: 13px;
                padding: 4px 8px;
            }
            #floatingSlideshowHUD QToolButton:hover {
                background-color: rgba(255, 255, 255, 35);
            }
            #floatingSlideshowHUD QLabel {
                color: #e5e5ea;
                font-size: 12px;
                font-weight: 500;
                padding: 0 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        # Prev
        self.prev_btn = QToolButton()
        self.prev_btn.setText("◀")
        self.prev_btn.setToolTip("Previous Page (Left Arrow)")
        self.prev_btn.clicked.connect(self.main_win.prev_page)
        layout.addWidget(self.prev_btn)

        # Play / Pause
        self.play_btn = QToolButton()
        self.play_btn.setText("⏸")
        self.play_btn.setToolTip("Pause / Resume Auto-advance (Space)")
        self.play_btn.clicked.connect(self.main_win._toggle_slideshow_timer)
        layout.addWidget(self.play_btn)

        # Next
        self.next_btn = QToolButton()
        self.next_btn.setText("▶")
        self.next_btn.setToolTip("Next Page (Right Arrow)")
        self.next_btn.clicked.connect(self.main_win.next_page)
        layout.addWidget(self.next_btn)

        # Counter
        self.counter_label = QLabel("1 / 1")
        layout.addWidget(self.counter_label)

        # Exit
        self.exit_btn = QToolButton()
        self.exit_btn.setText("✕")
        self.exit_btn.setToolTip("Exit Slideshow (Esc)")
        self.exit_btn.clicked.connect(lambda: self.main_win.toggle_fullscreen(auto_advance=False))
        layout.addWidget(self.exit_btn)

        self.adjustSize()
        self.hide()

    def update_page_info(self, current: int, total: int):
        self.counter_label.setText(f"{current} / {total}")
        self.adjustSize()
        self._reposition()

    def set_playing(self, is_playing: bool):
        self.play_btn.setText("⏸" if is_playing else "▶")

    def _reposition(self):
        p = self.parentWidget()
        if not p:
            return
        x = (p.width() - self.width()) // 2
        y = p.height() - self.height() - 28
        self.move(max(0, x), max(0, y))

class TrafficLightButton(QToolButton):
    """Traffic light button (12px circle) displaying hover glyphs (✕, −, +) when active, grey when window is inactive, and modified dot when dirty."""

    def __init__(self, color_bg: str, border_col: str, symbol: str, glyph_col: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.color_bg = color_bg
        self.border_col = border_col
        self.glyph_col = glyph_col
        self._hovered = False
        self._active = True
        self._modified = False
        self.setFixedSize(12, 12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_modified(self, modified: bool):
        if self._modified != modified:
            self._modified = modified
            self.update()

    def set_cluster_hovered(self, hovered: bool):
        self._hovered = hovered
        self.update()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_active = self._active
        if self.window():
            is_active = is_active and self.window().isActiveWindow()

        is_dark = True
        win = self.window()
        if win and hasattr(win, "current_theme"):
            is_dark = (win.current_theme == MacTheme.DARK)

        if not is_active:
            # Subtle inactive studio controls
            fill_col = "#22242a" if is_dark else "#e5e7eb"
            stroke_col = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.10)"
            p.setBrush(QBrush(QColor(fill_col)))
            p.setPen(QPen(QColor(stroke_col), 0.75))
            p.drawRoundedRect(QRectF(0.5, 0.5, 11.0, 11.0), 3.0, 3.0)
            if self._modified and not self._hovered:
                p.setBrush(QBrush(QColor("#4b5563" if is_dark else "#9ca3af")))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(QRectF(3.5, 3.5, 5.0, 5.0), 1.5, 1.5)
        else:
            if self._hovered:
                if self.symbol == "✕":
                    bg = "#ef4444"
                    border = "#dc2626"
                elif self.symbol == "−":
                    bg = "#f59e0b"
                    border = "#d97706"
                else:
                    bg = "#10b981"
                    border = "#059669"
                p.setBrush(QBrush(QColor(bg)))
                p.setPen(QPen(QColor(border), 0.75))
                p.drawRoundedRect(QRectF(0.5, 0.5, 11.0, 11.0), 3.0, 3.0)
                p.setPen(QColor("#ffffff"))
                font = QFont("Inter", 7, QFont.Weight.Bold)
                p.setFont(font)
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.symbol)
            else:
                fill = "#282a32" if is_dark else "#f3f4f6"
                stroke = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.14)"
                p.setBrush(QBrush(QColor(fill)))
                p.setPen(QPen(QColor(stroke), 0.75))
                p.drawRoundedRect(QRectF(0.5, 0.5, 11.0, 11.0), 3.0, 3.0)
                if self._modified:
                    # Dirty indicator dot in crimson
                    p.setBrush(QBrush(QColor("#ef4444")))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawRoundedRect(QRectF(3.5, 3.5, 5.0, 5.0), 1.5, 1.5)
        p.end()

class StudioCloseButton(QToolButton):
    """
    Modern Studio window close button (30x30) with dirty dot indicator
    and high-contrast crimson hover state.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("windowCloseBtn")
        self.setFixedSize(30, 30)
        self.setIconSize(QSize(14, 14))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._modified = False
        self._active = True
        self._hovered = False

    def set_modified(self, modified: bool):
        if self._modified != modified:
            self._modified = modified
            self.update()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.setIcon(MacIconFactory.create_icon("window_close", "#ffffff", 14))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        win = self.window()
        is_dark = getattr(win, "current_theme", MacTheme.DARK) == MacTheme.DARK
        col = "#f5f5f7" if is_dark else "#2c2c2e"
        self.setIcon(MacIconFactory.create_icon("window_close", col, 14))
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._modified and not self._hovered:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QBrush(QColor("#ef4444")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(self.width() - 8, 3, 5, 5))
            p.end()


class StudioWindowControls(QWidget):
    """
    Standard modern window controls: Minimize, Maximize/Restore, Close.
    Cleanly positioned on the right side of the window header bar
    without macOS traffic-light imitation.
    """

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        self.setObjectName("studioWindowControls")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 16, 5)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.setSpacing(5)

        self.btn_min = QToolButton(self)
        self.btn_min.setObjectName("windowMinBtn")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setIconSize(QSize(14, 14))
        self.btn_min.setToolTip("Minimize (Ctrl+M)")
        self.btn_min.setAccessibleName("Minimize Window")
        self.btn_min.clicked.connect(main_win.showMinimized)

        self.btn_max = QToolButton(self)
        self.btn_max.setObjectName("windowMaxBtn")
        self.btn_max.setFixedSize(30, 30)
        self.btn_max.setIconSize(QSize(14, 14))
        self.btn_max.setToolTip("Zoom / Maximize")
        self.btn_max.setAccessibleName("Maximize Window")
        self.btn_max.clicked.connect(main_win._toggle_maximize)

        self.btn_close = StudioCloseButton(self)
        self.btn_close.setObjectName("windowCloseBtn")
        self.btn_close.setToolTip("Close (Ctrl+W)")
        self.btn_close.setAccessibleName("Close Window")
        self.btn_close.clicked.connect(main_win.close)

        self.btn_toggle_toolbar = QToolButton(self)
        self.btn_toggle_toolbar.setObjectName("windowToolbarToggleBtn")
        self.btn_toggle_toolbar.setFixedSize(30, 30)
        self.btn_toggle_toolbar.setIconSize(QSize(12, 12))
        self.btn_toggle_toolbar.setToolTip("Hide Toolbar (Ctrl+Alt+T)")
        self.btn_toggle_toolbar.setAccessibleName("Toggle Primary Toolbar")
        self.btn_toggle_toolbar.clicked.connect(main_win._toggle_primary_toolbar)

        layout.addWidget(self.btn_toggle_toolbar)
        layout.addSpacing(6)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def set_active_state(self, active: bool):
        self.btn_close.set_active(active)
        self.update()

    def update_icons(self, col: str):
        if hasattr(self, "btn_toggle_toolbar"):
            self.btn_toggle_toolbar.setIcon(MacIconFactory.create_icon("panel-top", col, 12))
        self.btn_min.setIcon(MacIconFactory.create_icon("window_minimize", col, 14))
        is_max = self.main_win.isMaximized()
        max_icon = "window_restore" if is_max else "window_maximize"
        self.btn_max.setIcon(MacIconFactory.create_icon(max_icon, col, 14))
        self.btn_max.setToolTip("Zoom / Maximize")
        if not self.btn_close._hovered:
            self.btn_close.setIcon(MacIconFactory.create_icon("window_close", col, 14))


class TrafficLightCluster(QWidget):
    """Container for traffic lights spaced 8px apart (retained for backward compatibility)."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_close = TrafficLightButton("#ef4444", "#dc2626", "✕", "#ffffff", self)
        self.btn_close.setObjectName("trafficClose")
        self.btn_close.setToolTip("Close (Ctrl+W)")
        self.btn_close.clicked.connect(main_win.close)

        self.btn_min = TrafficLightButton("#f59e0b", "#d97706", "−", "#ffffff", self)
        self.btn_min.setObjectName("trafficMinimize")
        self.btn_min.setToolTip("Minimize (Ctrl+M)")
        self.btn_min.clicked.connect(main_win.showMinimized)

        self.btn_max = TrafficLightButton("#10b981", "#059669", "+", "#ffffff", self)
        self.btn_max.setObjectName("trafficMaximize")
        self.btn_max.setToolTip("Zoom / Maximize")
        self.btn_max.clicked.connect(main_win._toggle_maximize)

        layout.addWidget(self.btn_close)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)

    def set_active_state(self, active: bool):
        self.btn_close.set_active(active)
        self.btn_min.set_active(active)
        self.btn_max.set_active(active)

    def enterEvent(self, event):
        self.btn_close.set_cluster_hovered(True)
        self.btn_min.set_cluster_hovered(True)
        self.btn_max.set_cluster_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_close.set_cluster_hovered(False)
        self.btn_min.set_cluster_hovered(False)
        self.btn_max.set_cluster_hovered(False)
        super().leaveEvent(event)


class DraggableToolbar(QWidget):
    """Unified header bar (52px) with centered title, native window dragging on empty space, and double-click maximize."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        self._drag_start_pos: Optional[QPoint] = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_title_geometry()

    def minimumSizeHint(self) -> QSize:
        return QSize(360, 48)

    def update_title_geometry(self):
        """Header bar layout with stretch items automatically centers the title container."""
        pass

    def _is_draggable_target(self, pos: QPoint) -> bool:
        child = self.childAt(pos)
        title_w = getattr(self.main_win, 'title_widget', None)
        center_c = getattr(self.main_win, 'center_container', None)
        is_empty_or_title = (
            child is None or
            child is self or
            child is title_w or
            child is center_c or
            isinstance(child, QLabel) or
            (title_w is not None and title_w.isAncestorOf(child))
        )
        if is_empty_or_title and not isinstance(child, (QAbstractButton, QLineEdit)):
            return True
        return False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_draggable_target(event.position().toPoint()):
            if self.main_win.start_window_drag(event):
                event.accept()
                return
            self._drag_start_pos = event.globalPosition().toPoint() - self.main_win.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            if not self.main_win.isMaximized():
                self.main_win.move(event.globalPosition().toPoint() - self._drag_start_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        self.unsetCursor()
        self.main_win.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_draggable_target(event.position().toPoint()):
            self.main_win._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class DraggableMenuBar(QMenuBar):
    """Sleek macOS-styled top menu bar supporting native window dragging outside menus."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        self._drag_start_pos: Optional[QPoint] = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            action = self.actionAt(event.position().toPoint())
            corner_w = self.cornerWidget(Qt.Corner.TopRightCorner)
            pos = event.position().toPoint()
            is_in_corner = corner_w is not None and corner_w.geometry().contains(pos)
            if action is None and not is_in_corner:
                if self.main_win.start_window_drag(event):
                    event.accept()
                    return
                self._drag_start_pos = event.globalPosition().toPoint() - self.main_win.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            if not self.main_win.isMaximized():
                self.main_win.move(event.globalPosition().toPoint() - self._drag_start_pos)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        self.unsetCursor()
        self.main_win.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            action = self.actionAt(event.position().toPoint())
            corner_w = self.cornerWidget(Qt.Corner.TopRightCorner)
            pos = event.position().toPoint()
            is_in_corner = corner_w is not None and corner_w.geometry().contains(pos)
            if action is None and not is_in_corner:
                self.main_win._toggle_maximize()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

