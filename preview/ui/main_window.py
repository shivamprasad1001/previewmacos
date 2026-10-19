"""
Main Window for Preview macOS Linux clone.
Implements unified macOS toolbar, authentic traffic light controls, collapsible sidebar, 
markup bar, canvas, menus, keyboard shortcuts, multi-image & folder support, and file drag-and-drop.
"""

import os
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QToolButton, QLineEdit, QLabel, QFileDialog, QMessageBox, 
    QApplication, QMenu, QMenuBar, QStatusBar, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QFrame, QDialog
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent, QColor, 
    QMouseEvent, QPainter, QBrush, QPen, QFont, QKeyEvent, QPixmap
)
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QRectF, QEvent, QPropertyAnimation, QVariantAnimation, QEasingCurve, QSettings

from preview.theme import MacTheme
from preview.icons import MacIconFactory
from preview.core.document import Document
from preview.core.annotations import AnnotationType
from preview.core.history import HistoryManager, ActionCommand
from preview.ui.mac_sidebar import MacSidebar
from preview.ui.canvas import CanvasView
from preview.ui.markup_toolbar import MarkupToolbar
from preview.ui.adjust_color_dialog import AdjustColorDialog
from preview.ui.adjust_size_dialog import AdjustSizeDialog
from preview.ui.signature_dialog import SignatureDialog
from preview.ui.inspector_dialog import InspectorDialog
from preview.ui.about_dialog import AboutDialog
from preview.ui.export_dialog import MacExportDialog
from preview.core.updater import UpdateCheckWorker, UpdateInfo
from preview.ui.update_dialog import UpdateDialog, UpdateBanner

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
        self.exit_btn.clicked.connect(self.main_win._toggle_slideshow)
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
    """Traffic light button (12px circle) displaying hover glyphs (✕, −, +) when active, grey when window is inactive."""

    def __init__(self, color_bg: str, border_col: str, symbol: str, glyph_col: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.color_bg = color_bg
        self.border_col = border_col
        self.glyph_col = glyph_col
        self._hovered = False
        self._active = True
        self.setFixedSize(12, 12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

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
            # Grey circles when window is inactive
            fill_col = "#727277" if is_dark else "#bcbcc2"
            stroke_col = "#5a5a5e" if is_dark else "#9e9ea4"
            p.setBrush(QBrush(QColor(fill_col)))
            p.setPen(QPen(QColor(stroke_col), 0.75))
            p.drawEllipse(QRectF(0.5, 0.5, 11.0, 11.0))
        else:
            p.setBrush(QBrush(QColor(self.color_bg)))
            p.setPen(QPen(QColor(self.border_col), 0.75))
            p.drawEllipse(QRectF(0.5, 0.5, 11.0, 11.0))
            if self._hovered:
                p.setPen(QColor(self.glyph_col))
                font = QFont("Inter", 7, QFont.Weight.Bold)
                p.setFont(font)
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.symbol)
        p.end()

class TrafficLightCluster(QWidget):
    """Container for traffic lights spaced 8px apart."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_close = TrafficLightButton("#ff5f56", "#e0443e", "✕", "#4d0000", self)
        self.btn_close.setToolTip("Close (Ctrl+W)")
        self.btn_close.clicked.connect(main_win.close)

        self.btn_min = TrafficLightButton("#ffbd2e", "#dea123", "−", "#613b00", self)
        self.btn_min.setToolTip("Minimize (Ctrl+M)")
        self.btn_min.clicked.connect(main_win.showMinimized)

        self.btn_max = TrafficLightButton("#27c93f", "#1aab29", "+", "#004707", self)
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
    """Unified header bar (52px) supporting window dragging, double-click maximize, and centered title."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        self._drag_start_pos: Optional[QPoint] = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_title_geometry()

    def update_title_geometry(self):
        title_w = getattr(self.main_win, 'title_widget', None)
        if title_w:
            hint = title_w.sizeHint()
            w = self.width()
            h = self.height()
            tw = min(hint.width(), max(120, w - 380))
            th = max(24, hint.height())
            x = (w - tw) // 2
            y = (h - th) // 2
            title_w.setGeometry(x, y, tw, th)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            title_w = getattr(self.main_win, 'title_widget', None)
            if (child is None or child is self or isinstance(child, QLabel) or
                child is title_w or (title_w and title_w.isAncestorOf(child))):
                win_handle = self.main_win.windowHandle()
                if win_handle and hasattr(win_handle, "startSystemMove"):
                    win_handle.startSystemMove()
                else:
                    self._drag_start_pos = event.globalPosition().toPoint() - self.main_win.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            if not self.main_win.isMaximized():
                self.main_win.move(event.globalPosition().toPoint() - self._drag_start_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            title_w = getattr(self.main_win, 'title_widget', None)
            if (child is None or child is self or isinstance(child, QLabel) or
                child is title_w or (title_w and title_w.isAncestorOf(child))):
                self.main_win._toggle_maximize()
        super().mouseDoubleClickEvent(event)

class DraggableMenuBar(QMenuBar):
    """Sleek macOS-styled top menu bar supporting window dragging when clicked outside menus."""

    def __init__(self, main_win: 'MacMainWindow'):
        super().__init__(main_win)
        self.main_win = main_win
        self._drag_start_pos: Optional[QPoint] = None

    def mousePressEvent(self, event: QMouseEvent):
        action = self.actionAt(event.position().toPoint())
        if action is None and event.button() == Qt.MouseButton.LeftButton:
            win_handle = self.main_win.windowHandle()
            if win_handle and hasattr(win_handle, "startSystemMove"):
                win_handle.startSystemMove()
            else:
                self._drag_start_pos = event.globalPosition().toPoint() - self.main_win.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start_pos and (event.buttons() & Qt.MouseButton.LeftButton):
            if not self.main_win.isMaximized():
                self.main_win.move(event.globalPosition().toPoint() - self._drag_start_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        action = self.actionAt(event.position().toPoint())
        if action is None and event.button() == Qt.MouseButton.LeftButton:
            self.main_win._toggle_maximize()
        super().mouseDoubleClickEvent(event)

class MacMainWindow(QMainWindow):
    """The central macOS Preview application window."""

    def __init__(self, initial_target: Optional[str] = None, initial_file: Optional[str] = None, **kwargs):
        super().__init__()
        self.setObjectName("DocumentViewer")
        self.setWindowTitle("Document Viewer")
        self.resize(1150, 780)
        self.setAcceptDrops(True)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.current_theme: str = self._detect_system_theme()
        self.document: Optional[Document] = None
        self.inspector_dialog: Optional[InspectorDialog] = None
        self.color_dialog: Optional[AdjustColorDialog] = None
        self.is_frameless: bool = True
        self._last_sidebar_width: int = 190
        self._sidebar_anim: Optional[QVariantAnimation] = None
        self._update_worker: Optional[UpdateCheckWorker] = None
        self.update_banner: Optional[UpdateBanner] = None

        # Listen for system theme changes
        app = QApplication.instance()
        if app and hasattr(app, "styleHints"):
            try:
                app.styleHints().colorSchemeChanged.connect(self._on_system_color_scheme_changed)
            except Exception:
                pass

        # Window chrome flags for rounded corners and shadow
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self._setup_ui()
        self._setup_menus()
        self._apply_theme(self.current_theme, animate=False)

        # Background update check on startup (delayed 2.5s)
        QTimer.singleShot(2500, self._check_for_updates_startup)

        target = initial_target or initial_file
        if target:
            if os.path.isdir(target):
                self.open_folder(target)
            elif os.path.isfile(target):
                self.open_file(target)

    def _setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.root_widget = QWidget()
        self.root_widget.setObjectName("rootContainer")
        self.root_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.root_widget.setMouseTracking(True)
        self.setCentralWidget(self.root_widget)

        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(0)

        # Window Frame with 10px rounded corners & soft drop shadow
        self.window_frame = QWidget()
        self.window_frame.setObjectName("windowFrame")
        self.root_layout.addWidget(self.window_frame)

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(24)
        self.shadow_effect.setColor(QColor(0, 0, 0, 95))
        self.shadow_effect.setOffset(0, 4)
        self.window_frame.setGraphicsEffect(self.shadow_effect)

        self.main_layout = QVBoxLayout(self.window_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 0. Topbar Menu Bar (Logo, File, Edit, View, Go, Tools, Window, Help)
        self.top_menubar = DraggableMenuBar(self)
        self.top_menubar.setObjectName("macMenubar")
        self.main_layout.addWidget(self.top_menubar)

        # 1. Canvas & Sidebar instantiation
        self.sidebar = MacSidebar(self)
        self.sidebar.page_selected.connect(self._on_sidebar_page_selected)

        self.canvas = CanvasView(self)
        self.canvas.zoom_changed.connect(self._on_canvas_zoom_changed)
        self.canvas.status_message.connect(self._show_status)

        # 2. Secondary Markup Toolbar (collapsible 38px)
        self.markup_bar = MarkupToolbar(self)
        self.markup_bar.setVisible(False)
        self._connect_markup_bar()
        self.canvas.crop_available.connect(self.markup_bar.set_crop_enabled)

        # 3. Unified macOS Toolbar (fixed 52px tall, 1px bottom border)
        self._setup_toolbar()
        self.main_layout.addWidget(self.toolbar_widget)
        self.main_layout.addWidget(self.markup_bar)

        # 4. Central Splitter (Sidebar + Canvas) takes 100% remaining space
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([190, 960])
        self.main_layout.addWidget(self.splitter, 1)

        # 5. Footer Status Bar
        self.status_bar = QStatusBar(self)
        self.status_bar.setObjectName("macStatusBar")
        self.status_bar.setSizeGripEnabled(False)
        self.page_status_label = QLabel("No document")
        self.zoom_status_label = QLabel("100%")
        self.status_bar.addWidget(self.page_status_label)
        self.status_bar.addPermanentWidget(self.zoom_status_label)
        self.status_bar.setVisible(True)
        self.main_layout.addWidget(self.status_bar)

        # 6. Small floating pill at bottom center of canvas
        self.floating_pill = FloatingStatusPill(self.canvas)
        self.canvas.floating_pill = self.floating_pill

        # 7. Floating Slideshow HUD
        self.slideshow_hud = FloatingSlideshowHUD(self, self.canvas)

    def _setup_toolbar(self):
        self.toolbar_widget = DraggableToolbar(self)
        self.toolbar_widget.setObjectName("macToolbar")
        self.toolbar_widget.setFixedHeight(52)
        self.toolbar_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(14, 0, 14, 0)
        toolbar_layout.setSpacing(6)

        # 1. Traffic lights cluster (Close, Minimize, Maximize) spaced 8px apart
        self.traffic_cluster = TrafficLightCluster(self)
        toolbar_layout.addWidget(self.traffic_cluster)
        self.traffic_cluster.setVisible(self.is_frameless)

        toolbar_layout.addSpacing(12)

        # 2. Sidebar toggle (icon-only, 28px high, 6px radius)
        self.sidebar_btn = QToolButton()
        self.sidebar_btn.setObjectName("sidebarBtn")
        self.sidebar_btn.setFixedSize(28, 28)
        self.sidebar_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.sidebar_btn.clicked.connect(self._toggle_sidebar)
        toolbar_layout.addWidget(self.sidebar_btn)

        toolbar_layout.addSpacing(6)

        # 3. Previous / Next Joined Segmented Pair
        self.nav_segmented = QWidget()
        self.nav_segmented.setObjectName("navSegmented")
        self.nav_segmented.setFixedSize(56, 28)
        nav_layout = QHBoxLayout(self.nav_segmented)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.prev_btn = QToolButton()
        self.prev_btn.setObjectName("prevBtn")
        self.prev_btn.setFixedSize(28, 28)
        self.prev_btn.setToolTip("Previous Page / Image (Left Arrow)")
        self.prev_btn.clicked.connect(self.prev_page)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QToolButton()
        self.next_btn.setObjectName("nextBtn")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setToolTip("Next Page / Image (Right Arrow)")
        self.next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_btn)

        toolbar_layout.addWidget(self.nav_segmented)

        toolbar_layout.addSpacing(6)

        # 4. Open Button (icon-only, 28px high, 6px radius with Dropdown)
        self.open_btn = QToolButton()
        self.open_btn.setObjectName("openBtn")
        self.open_btn.setFixedSize(28, 28)
        self.open_btn.setToolTip("Open Document or Images (Ctrl+O)")
        self.open_btn.clicked.connect(self._open_file_dialog)
        
        open_menu = QMenu(self)
        open_files_action = QAction("Open File(s)...", self)
        open_files_action.setShortcut(QKeySequence("Ctrl+O"))
        open_files_action.triggered.connect(self._open_file_dialog)
        open_menu.addAction(open_files_action)

        open_folder_action = QAction("Open Folder of Images...", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self._open_folder_dialog)
        open_menu.addAction(open_folder_action)

        self.open_btn.setMenu(open_menu)
        self.open_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar_layout.addWidget(self.open_btn)

        # Spacer to allow centering of title
        toolbar_layout.addStretch(1)

        # 5. Centered Title Widget with Lucide file icon, medium weight 13px Inter title
        self.title_widget = QWidget(self.toolbar_widget)
        self.title_widget.setObjectName("titleWidget")
        title_box = QHBoxLayout(self.title_widget)
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(6)
        title_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.proxy_icon_label = QLabel()
        self.proxy_icon_label.setFixedSize(16, 16)
        self.title_label = QLabel("Document Viewer")
        self.title_label.setObjectName("windowTitleLabel")
        self.page_badge = QLabel("")
        self.page_badge.setObjectName("pageBadge")
        self.page_badge.setVisible(False)

        title_box.addWidget(self.proxy_icon_label)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.page_badge)

        # 6. Zoom Out / In Joined Segmented Pair
        self.zoom_segmented = QWidget()
        self.zoom_segmented.setObjectName("zoomSegmented")
        self.zoom_segmented.setFixedSize(56, 28)
        zoom_layout = QHBoxLayout(self.zoom_segmented)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(0)

        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setObjectName("zoomOutBtn")
        self.zoom_out_btn.setFixedSize(28, 28)
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setObjectName("zoomInBtn")
        self.zoom_in_btn.setFixedSize(28, 28)
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)

        toolbar_layout.addWidget(self.zoom_segmented)

        toolbar_layout.addSpacing(6)

        # 7. Rotate as a single button
        self.rotate_btn = QToolButton()
        self.rotate_btn.setObjectName("rotateBtn")
        self.rotate_btn.setFixedSize(28, 28)
        self.rotate_btn.setToolTip("Rotate (Ctrl+R)")
        self.rotate_btn.clicked.connect(self._rotate_right)
        self.rotate_right_btn = self.rotate_btn
        self.rotate_left_btn = self.rotate_btn
        toolbar_layout.addWidget(self.rotate_btn)

        toolbar_layout.addSpacing(6)

        # 8. Markup as a pill button
        self.markup_toggle_btn = QToolButton()
        self.markup_toggle_btn.setObjectName("markupPillBtn")
        self.markup_toggle_btn.setCheckable(True)
        self.markup_toggle_btn.setText("Markup")
        self.markup_toggle_btn.setFixedHeight(28)
        self.markup_toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.markup_toggle_btn.setToolTip("Show/Hide Markup Toolbar (Ctrl+Shift+A)")
        self.markup_toggle_btn.clicked.connect(self._toggle_markup_bar)
        toolbar_layout.addWidget(self.markup_toggle_btn)

        toolbar_layout.addSpacing(6)

        # 9. Search Bar (rounded with magnifier inside and accent focus ring)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("macSearchField")
        self.search_edit.setPlaceholderText("Search")
        self.search_edit.setFixedHeight(28)
        self.search_edit.setFixedWidth(130)
        self.search_edit.returnPressed.connect(self._on_search)
        self.search_action = self.search_edit.addAction(
            MacIconFactory.create_icon("search", "#8e8e93", 14),
            QLineEdit.ActionPosition.LeadingPosition
        )
        toolbar_layout.addWidget(self.search_edit)

        toolbar_layout.addSpacing(4)

        # 10. Inspector button (icon-only, 28px high, 6px radius)
        self.inspector_btn = QToolButton()
        self.inspector_btn.setObjectName("inspectorBtn")
        self.inspector_btn.setFixedSize(28, 28)
        self.inspector_btn.setToolTip("Show Inspector (Ctrl+I)")
        self.inspector_btn.clicked.connect(self._show_inspector)
        toolbar_layout.addWidget(self.inspector_btn)

        # 11. Theme toggle (Dark / Light, icon-only 28px)
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
        self.theme_btn.setToolTip("Toggle Dark/Light Mode (Ctrl+T)")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar_layout.addWidget(self.theme_btn)

        self._update_all_icons()

    def _get_icon_color(self) -> str:
        return "#f5f5f7" if self.current_theme == MacTheme.DARK else "#2c2c2e"

    def _update_all_icons(self):
        col = self._get_icon_color()
        self.sidebar_btn.setIcon(MacIconFactory.create_icon("sidebar", col, 16))
        self.prev_btn.setIcon(MacIconFactory.create_icon("arrow_left", col, 14))
        self.next_btn.setIcon(MacIconFactory.create_icon("arrow_right", col, 14))
        self.open_btn.setIcon(MacIconFactory.create_icon("open", col, 16))
        self.proxy_icon_label.setPixmap(MacIconFactory.create_icon("doc_proxy", col, 16).pixmap(16, 16))
        self.zoom_out_btn.setIcon(MacIconFactory.create_icon("zoom_out", col, 15))
        self.zoom_in_btn.setIcon(MacIconFactory.create_icon("zoom_in", col, 15))
        self.rotate_btn.setIcon(MacIconFactory.create_icon("rotate_right", col, 16))
        self.markup_toggle_btn.setIcon(MacIconFactory.create_icon("markup", "#ffffff" if self.markup_toggle_btn.isChecked() else col, 15))
        self.inspector_btn.setIcon(MacIconFactory.create_icon("inspector", col, 16))

        # Search field inside magnifier
        if hasattr(self, "search_action"):
            search_col = "#98989d" if self.current_theme == MacTheme.DARK else "#6e6e73"
            self.search_action.setIcon(MacIconFactory.create_icon("search", search_col, 14))

        self.markup_bar.update_icons(col)

    def _connect_markup_bar(self):
        self.markup_bar.tool_changed.connect(self.canvas.set_active_tool)
        self.markup_bar.stroke_color_changed.connect(lambda c: setattr(self.canvas, 'stroke_color', c))
        self.markup_bar.stroke_width_changed.connect(lambda w: setattr(self.canvas, 'stroke_width', w))
        self.markup_bar.fill_color_changed.connect(lambda f: setattr(self.canvas, 'fill_color', f))
        self.markup_bar.font_size_changed.connect(self.canvas.set_font_size)
        self.markup_bar.font_family_changed.connect(self.canvas.set_font_family)
        self.markup_bar.adjust_color_requested.connect(self._open_adjust_color)
        self.markup_bar.adjust_size_requested.connect(self._open_adjust_size)
        self.markup_bar.rotate_requested.connect(self._rotate_left)
        self.markup_bar.crop_requested.connect(self.canvas.apply_crop)
        self.markup_bar.signature_requested.connect(self._open_signature_dialog)
        self.canvas.tool_deselected.connect(self.markup_bar.unselect_all)

    def _setup_menus(self):
        # Ensure QMainWindow's native outer menubar is hidden
        native_mb = self.menuBar()
        if native_mb:
            native_mb.setVisible(False)
            native_mb.setFixedHeight(0)

        # 1. Application / Logo Menu
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            logo_icon = QIcon(icon_path)
        else:
            logo_icon = MacIconFactory.create_icon("doc_proxy", self._get_icon_color(), 16)

        self.logo_menu = self.top_menubar.addMenu(logo_icon, "")
        self.logo_menu.setTitle("")

        about_act = QAction("About Document Viewer", self)
        about_act.triggered.connect(self._show_about)
        self.logo_menu.addAction(about_act)

        check_updates_act = QAction("Check for Updates...", self)
        check_updates_act.triggered.connect(self._check_for_updates_manual)
        self.logo_menu.addAction(check_updates_act)

        self.logo_menu.addSeparator()

        theme_act = QAction("Toggle Dark/Light Mode", self)
        theme_act.setShortcut(QKeySequence("Ctrl+T"))
        theme_act.triggered.connect(self._toggle_theme)
        self.logo_menu.addAction(theme_act)

        pref_act = QAction("Preferences...", self)
        pref_act.setShortcut(QKeySequence("Ctrl+,"))
        pref_act.triggered.connect(self._show_about)
        self.logo_menu.addAction(pref_act)

        self.logo_menu.addSeparator()

        hide_act = QAction("Hide Window", self)
        hide_act.setShortcut(QKeySequence("Ctrl+H"))
        hide_act.triggered.connect(self.showMinimized)
        self.logo_menu.addAction(hide_act)

        quit_act = QAction("Quit Document Viewer", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        self.logo_menu.addAction(quit_act)

        # 2. File Menu
        self.file_menu = self.top_menubar.addMenu("File")
        open_act = QAction("Open...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open_file_dialog)
        self.file_menu.addAction(open_act)

        open_folder_act = QAction("Open Folder...", self)
        open_folder_act.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_act.triggered.connect(self._open_folder_dialog)
        self.file_menu.addAction(open_folder_act)

        self.recent_menu = self.file_menu.addMenu("Open Recent")
        self._update_recent_menu()

        self.file_menu.addSeparator()

        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self._save_file)
        self.file_menu.addAction(save_act)

        save_as_act = QAction("Save As...", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self._save_as_file)
        self.file_menu.addAction(save_as_act)

        export_pdf_act = QAction("Export as PDF...", self)
        export_pdf_act.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_pdf_act.triggered.connect(self._export_as_pdf)
        self.file_menu.addAction(export_pdf_act)

        export_act = QAction("Export...", self)
        export_act.setShortcut(QKeySequence("Ctrl+E"))
        export_act.triggered.connect(self._export_file)
        self.file_menu.addAction(export_act)

        self.file_menu.addSeparator()

        print_act = QAction("Print...", self)
        print_act.setShortcut(QKeySequence.StandardKey.Print)
        print_act.triggered.connect(self._print_file)
        self.file_menu.addAction(print_act)

        print_prev_act = QAction("Print Preview...", self)
        print_prev_act.setShortcut(QKeySequence("Ctrl+Shift+P"))
        print_prev_act.triggered.connect(self._print_preview_file)
        self.file_menu.addAction(print_prev_act)

        self.file_menu.addSeparator()

        close_act = QAction("Close Window", self)
        close_act.setShortcut(QKeySequence("Ctrl+W"))
        close_act.triggered.connect(self.close)
        self.file_menu.addAction(close_act)

        # 3. Edit Menu
        self.edit_menu = self.top_menubar.addMenu("Edit")
        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(self.canvas.undo)
        self.edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcuts([QKeySequence("Ctrl+Shift+Z"), QKeySequence("Ctrl+Y"), QKeySequence.StandardKey.Redo])
        redo_act.triggered.connect(self.canvas.redo)
        self.edit_menu.addAction(redo_act)

        self.edit_menu.addSeparator()

        copy_text_act = QAction("Copy Current Page Text", self)
        copy_text_act.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_text_act.triggered.connect(self._copy_current_page_text)
        self.edit_menu.addAction(copy_text_act)

        extract_all_act = QAction("Extract All Text to Clipboard", self)
        extract_all_act.triggered.connect(self._extract_all_text)
        self.edit_menu.addAction(extract_all_act)

        # 4. View Menu
        self.view_menu = self.top_menubar.addMenu("View")
        toggle_sb = QAction("Toggle Sidebar", self)
        toggle_sb.setShortcut(QKeySequence("Ctrl+B"))
        toggle_sb.triggered.connect(self._toggle_sidebar)
        self.view_menu.addAction(toggle_sb)

        toggle_mb_act = QAction("Show Menu Bar", self, checkable=True)
        toggle_mb_act.setShortcut(QKeySequence("Ctrl+Alt+M"))
        toggle_mb_act.setChecked(True)
        toggle_mb_act.toggled.connect(self._toggle_menu_bar)
        self.view_menu.addAction(toggle_mb_act)

        toggle_sb_bar = QAction("Show Status Bar", self, checkable=True)
        toggle_sb_bar.setShortcut(QKeySequence("Ctrl+/"))
        toggle_sb_bar.setChecked(True)
        toggle_sb_bar.toggled.connect(self._toggle_status_bar)
        self.view_menu.addAction(toggle_sb_bar)

        slideshow_act = QAction("Start Slideshow", self)
        slideshow_act.setShortcuts([QKeySequence("F11"), QKeySequence("Ctrl+Shift+F")])
        slideshow_act.triggered.connect(self._toggle_slideshow)
        self.view_menu.addAction(slideshow_act)

        frameless_act = QAction("macOS Frameless Window", self, checkable=True)
        frameless_act.setShortcut(QKeySequence("Ctrl+Alt+F"))
        frameless_act.setChecked(self.is_frameless)
        frameless_act.toggled.connect(self._toggle_frameless_mode)
        self.view_menu.addAction(frameless_act)

        self.view_menu.addSeparator()

        actual_size = QAction("Actual Size", self)
        actual_size.setShortcuts([QKeySequence("Ctrl+1"), QKeySequence("Ctrl+Alt+0")])
        actual_size.triggered.connect(self.canvas.zoom_actual_size)
        self.view_menu.addAction(actual_size)

        zoom_to_fit = QAction("Zoom to Fit", self)
        zoom_to_fit.setShortcuts([QKeySequence("Ctrl+0"), QKeySequence("Ctrl+9")])
        zoom_to_fit.triggered.connect(self.canvas.zoom_to_fit)
        self.view_menu.addAction(zoom_to_fit)

        zoom_in_act = QAction("Zoom In", self)
        zoom_in_act.setShortcuts([QKeySequence("Ctrl+="), QKeySequence("Ctrl++"), QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Plus)])
        zoom_in_act.triggered.connect(self.canvas.zoom_in)
        self.view_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("Zoom Out", self)
        zoom_out_act.setShortcuts([QKeySequence("Ctrl+-"), QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus)])
        zoom_out_act.triggered.connect(self.canvas.zoom_out)
        self.view_menu.addAction(zoom_out_act)

        # 5. Go Menu
        self.go_menu = self.top_menubar.addMenu("Go")
        next_act = QAction("Next Page / Image", self)
        next_act.setShortcuts([QKeySequence(Qt.Key.Key_Right), QKeySequence(Qt.Key.Key_Down), QKeySequence(Qt.Key.Key_PageDown)])
        next_act.triggered.connect(self.next_page)
        self.go_menu.addAction(next_act)

        prev_act = QAction("Previous Page / Image", self)
        prev_act.setShortcuts([QKeySequence(Qt.Key.Key_Left), QKeySequence(Qt.Key.Key_Up), QKeySequence(Qt.Key.Key_PageUp)])
        prev_act.triggered.connect(self.prev_page)
        self.go_menu.addAction(prev_act)

        first_act = QAction("First Page / Image", self)
        first_act.setShortcut(QKeySequence("Home"))
        first_act.triggered.connect(self._first_page)
        self.go_menu.addAction(first_act)

        last_act = QAction("Last Page / Image", self)
        last_act.setShortcut(QKeySequence("End"))
        last_act.triggered.connect(self._last_page)
        self.go_menu.addAction(last_act)

        # 6. Tools Menu
        self.tools_menu = self.top_menubar.addMenu("Tools")
        markup_act = QAction("Show Markup Toolbar", self)
        markup_act.setShortcut(QKeySequence("Ctrl+Shift+A"))
        markup_act.triggered.connect(self._toggle_markup_bar)
        self.tools_menu.addAction(markup_act)

        loupe_act = QAction("Show Magnifier (Loupe)", self)
        loupe_act.setShortcuts([QKeySequence("~"), QKeySequence("`"), QKeySequence("Ctrl+Shift+M")])
        loupe_act.triggered.connect(lambda: self.canvas.toggle_loupe())
        self.tools_menu.addAction(loupe_act)

        crop_act = QAction("Crop", self)
        crop_act.setShortcut(QKeySequence("Ctrl+K"))
        crop_act.triggered.connect(self.canvas.apply_crop)
        self.tools_menu.addAction(crop_act)

        self.tools_menu.addSeparator()

        rot_l_act = QAction("Rotate Left", self)
        rot_l_act.setShortcut(QKeySequence("Ctrl+L"))
        rot_l_act.triggered.connect(self._rotate_left)
        self.tools_menu.addAction(rot_l_act)

        rot_r_act = QAction("Rotate Right", self)
        rot_r_act.setShortcut(QKeySequence("Ctrl+R"))
        rot_r_act.triggered.connect(self._rotate_right)
        self.tools_menu.addAction(rot_r_act)

        self.tools_menu.addSeparator()

        color_act = QAction("Adjust Color...", self)
        color_act.setShortcut(QKeySequence("Ctrl+Alt+C"))
        color_act.triggered.connect(self._open_adjust_color)
        self.tools_menu.addAction(color_act)

        size_act = QAction("Adjust Size...", self)
        size_act.setShortcut(QKeySequence("Ctrl+Alt+S"))
        size_act.triggered.connect(self._open_adjust_size)
        self.tools_menu.addAction(size_act)

        insp_act = QAction("Show Inspector", self)
        insp_act.setShortcut(QKeySequence("Ctrl+I"))
        insp_act.triggered.connect(self._show_inspector)
        self.tools_menu.addAction(insp_act)

        # 7. Window Menu
        self.win_menu = self.top_menubar.addMenu("Window")
        min_act = QAction("Minimize", self)
        min_act.setShortcut(QKeySequence("Ctrl+M"))
        min_act.triggered.connect(self.showMinimized)
        self.win_menu.addAction(min_act)

        zoom_win_act = QAction("Zoom / Maximize", self)
        zoom_win_act.triggered.connect(self._toggle_maximize)
        self.win_menu.addAction(zoom_win_act)

        # 8. Help Menu
        self.help_menu = self.top_menubar.addMenu("Help")
        check_up_h_act = QAction("Check for Updates...", self)
        check_up_h_act.triggered.connect(self._check_for_updates_manual)
        self.help_menu.addAction(check_up_h_act)

        self.help_menu.addSeparator()

        about_h_act = QAction("About Document Viewer", self)
        about_h_act.triggered.connect(self._show_about)
        self.help_menu.addAction(about_h_act)

        # Register keyboard shortcuts into window actions
        for a in [open_act, open_folder_act, save_act, save_as_act, export_pdf_act, export_act,
                  print_act, print_prev_act, close_act, undo_act, redo_act, copy_text_act,
                  extract_all_act, toggle_sb, toggle_mb_act, toggle_sb_bar, slideshow_act,
                  frameless_act, actual_size, zoom_to_fit, zoom_in_act, zoom_out_act, next_act,
                  prev_act, first_act, last_act, markup_act, loupe_act, crop_act, rot_l_act,
                  rot_r_act, color_act, size_act, insp_act, min_act, zoom_win_act, theme_act,
                  quit_act, pref_act, hide_act, check_updates_act, check_up_h_act]:
            self.addAction(a)

    def _toggle_menu_bar(self, checked: bool):
        self.top_menubar.setVisible(checked)

    def _toggle_status_bar(self, checked: bool):
        self.status_bar.setVisible(checked)

    def _first_page(self):
        if self.document and self.document.page_count > 0:
            self.canvas.set_page(0)
            self.document.set_current_page(0)
            self.sidebar.select_page(0)
            self._update_status()

    def _last_page(self):
        if self.document and self.document.page_count > 0:
            last = self.document.page_count - 1
            self.canvas.set_page(last)
            self.document.set_current_page(last)
            self.sidebar.select_page(last)
            self._update_status()

    def open_file(self, file_path: str):
        try:
            self.document = Document(file_path)
            self._bind_document()
            self._add_recent_file(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", f"Could not open {file_path}:\n{str(e)}")

    def open_files(self, file_paths: List[str]):
        try:
            self.document = Document()
            self.document.load_files(file_paths)
            self._bind_document()
            if file_paths:
                self._add_recent_file(file_paths[0])
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Images", f"Could not open images:\n{str(e)}")

    def open_folder(self, folder_path: str):
        try:
            self.document = Document()
            self.document.load_folder(folder_path)
            self._bind_document()
            self._add_recent_file(folder_path)
            self._show_status(f"Loaded folder with {self.document.page_count} images.")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Folder", f"Could not open folder {folder_path}:\n{str(e)}")

    def _bind_document(self):
        if not self.document:
            return
        self.document.document_changed.connect(self._on_doc_changed)
        self.document.page_changed.connect(self._on_doc_page_changed)
        
        self.sidebar.set_document(self.document)
        self.canvas.set_document(self.document)
        
        self.title_label.setText(self.document.file_name)
        self.setWindowTitle(self.document.file_name)
        self.toolbar_widget.update_title_geometry()
        self._update_status()

        # Re-fit image/page to canvas after layout is settled
        QTimer.singleShot(60, self.canvas.zoom_to_fit)

    def next_page(self):
        if self.document and self.canvas.current_page < self.document.page_count - 1:
            nxt = self.canvas.current_page + 1
            self.canvas.set_page(nxt)
            self.document.set_current_page(nxt)
            self.sidebar.select_page(nxt)
            self._update_status()

    def prev_page(self):
        if self.document and self.canvas.current_page > 0:
            prv = self.canvas.current_page - 1
            self.canvas.set_page(prv)
            self.document.set_current_page(prv)
            self.sidebar.select_page(prv)
            self._update_status()

    def _open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Document or Images", "", 
            "Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tiff);;PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*.*)"
        )
        if paths:
            if len(paths) == 1:
                self.open_file(paths[0])
            else:
                self.open_files(paths)

    def _open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder of Images")
        if folder:
            self.open_folder(folder)

    def _save_file(self):
        if not self.document:
            return
        if self.document.file_path:
            try:
                self.document.export_document(self.document.file_path)
                self._show_status("Document saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
        else:
            self._save_as_file()

    def _save_as_file(self):
        if not self.document:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Document As", self.document.file_name,
            "PDF Document (*.pdf);;PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        if path:
            try:
                self.document.export_document(path)
                self.open_file(path)
                self._show_status(f"Saved to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save As Error", str(e))

    # --- Open Recent Documents ---
    def _add_recent_file(self, file_path: str):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        recents = settings.value("recent_files", [], type=list) or []
        path = os.path.abspath(file_path)
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        recents = recents[:10]
        settings.setValue("recent_files", recents)
        self._update_recent_menu()

    def _update_recent_menu(self):
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        settings = QSettings("TriviLabs", "PreviewMacOS")
        recents = settings.value("recent_files", [], type=list) or []
        valid_recents = [p for p in recents if os.path.exists(p)]
        if not valid_recents:
            no_act = QAction("No Recent Documents", self)
            no_act.setEnabled(False)
            self.recent_menu.addAction(no_act)
            return

        for p in valid_recents:
            act = QAction(os.path.basename(p), self)
            act.setToolTip(p)
            act.triggered.connect(lambda _, path=p: self._open_recent_item(path))
            self.recent_menu.addAction(act)

        self.recent_menu.addSeparator()
        clear_act = QAction("Clear Menu", self)
        clear_act.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_act)

    def _open_recent_item(self, path: str):
        if os.path.isdir(path):
            self.open_folder(path)
        elif os.path.isfile(path):
            self.open_file(path)

    def _clear_recent_files(self):
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("recent_files", [])
        self._update_recent_menu()

    # --- Export & Print ---
    def _export_as_pdf(self):
        if not self.document:
            return
        default_dir = os.path.dirname(self.document.file_path) if self.document.file_path else os.path.expanduser("~/Documents")
        base = os.path.splitext(self.document.file_name)[0]
        initial_path = os.path.join(default_dir, f"{base}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Export as PDF", initial_path, "PDF Document (*.pdf)")
        if path:
            try:
                self.document.export_all_to_pdf(path)
                self._show_status(f"Exported to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _export_file(self):
        if not self.document:
            return
        dlg = MacExportDialog(
            current_file_path=self.document.file_path,
            page_count=self.document.page_count,
            current_page=self.canvas.current_page,
            parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_path:
            try:
                target_page = None if dlg.export_all_pages else self.canvas.current_page
                if dlg.selected_format == "PDF" and dlg.export_all_pages:
                    self.document.export_all_to_pdf(dlg.selected_path)
                else:
                    self.document.export_document(
                        dlg.selected_path, 
                        format_name=dlg.selected_format,
                        quality=dlg.selected_quality,
                        page_idx=target_page
                    )
                self._show_status(f"Exported to {os.path.basename(dlg.selected_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _print_file(self):
        if not self.document:
            return
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Document")
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self._render_to_printer(printer)
                self._show_status("Document sent to printer.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _print_preview_file(self):
        if not self.document:
            return
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_dialog.setWindowTitle("Print Preview")
            preview_dialog.resize(900, 700)
            preview_dialog.paintRequested.connect(self._render_to_printer)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Print Preview Error", str(e))

    def _render_to_printer(self, printer):
        if not self.document:
            return
        from PyQt6.QtGui import QPainter
        painter = QPainter(printer)
        try:
            page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            for p_idx in range(self.document.page_count):
                if p_idx > 0:
                    printer.newPage()
                pix = self.document.render_page(p_idx, zoom=2.0)
                scaled = pix.scaled(
                    page_rect.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                x = page_rect.left() + (page_rect.width() - scaled.width()) / 2
                y = page_rect.top() + (page_rect.height() - scaled.height()) / 2
                painter.drawPixmap(int(x), int(y), scaled)
        finally:
            painter.end()

    # --- Live Text Extraction ---
    def _copy_current_page_text(self):
        if not self.document:
            return
        txt = self.document.extract_text(self.canvas.current_page)
        if txt.strip():
            QApplication.clipboard().setText(txt)
            self._show_status(f"Copied {len(txt)} characters to clipboard.")
        else:
            self._show_status("No selectable text on this page.")

    def _extract_all_text(self):
        if not self.document:
            return
        txt = self.document.extract_text(None)
        if txt.strip():
            QApplication.clipboard().setText(txt)
            self._show_status(f"Copied full document text ({len(txt)} chars) to clipboard.")
        else:
            self._show_status("No selectable text in document.")

    # --- Fullscreen Slideshow / Presentation Mode ---
    def _toggle_slideshow(self):
        if not hasattr(self, "_is_slideshow"):
            self._is_slideshow = False
            self._slideshow_timer = QTimer(self)
            self._slideshow_timer.setInterval(3500)
            self._slideshow_timer.timeout.connect(self._slideshow_advance)

        self._is_slideshow = not self._is_slideshow

        if self._is_slideshow:
            self._saved_maximized = self.isMaximized()
            self._saved_menubar_vis = self.top_menubar.isVisible()
            self._saved_sidebar_vis = self.sidebar.isVisible()
            self._saved_statusbar_vis = self.status_bar.isVisible()
            self._saved_toolbar_vis = self.toolbar_widget.isVisible()

            self.top_menubar.hide()
            self.sidebar.hide()
            self.status_bar.hide()
            self.toolbar_widget.hide()
            self.showFullScreen()
            self.canvas.zoom_to_fit()
            self._show_slideshow_controls(True)
            self._slideshow_timer.start()
            self.slideshow_hud.set_playing(True)
            self._show_status("Slideshow started (Press Esc to exit, Space to pause/resume)")
        else:
            if hasattr(self, "_slideshow_timer"):
                self._slideshow_timer.stop()
            self._show_slideshow_controls(False)
            self.showNormal()
            if getattr(self, "_saved_maximized", False):
                self.showMaximized()
            if getattr(self, "_saved_menubar_vis", True):
                self.top_menubar.show()
            if getattr(self, "_saved_sidebar_vis", True):
                self.sidebar.show()
            if getattr(self, "_saved_statusbar_vis", True):
                self.status_bar.show()
            if getattr(self, "_saved_toolbar_vis", True):
                self.toolbar_widget.show()
            self.canvas.zoom_to_fit()
            self._show_status("Exited slideshow mode.")

    def _toggle_slideshow_timer(self):
        if not hasattr(self, "_slideshow_timer"):
            return
        if self._slideshow_timer.isActive():
            self._slideshow_timer.stop()
            self.slideshow_hud.set_playing(False)
            self._show_status("Slideshow paused")
        else:
            self._slideshow_timer.start()
            self.slideshow_hud.set_playing(True)
            self._show_status("Slideshow playing")

    def _slideshow_advance(self):
        if not self.document:
            return
        if self.canvas.current_page < self.document.page_count - 1:
            self.next_page()
        else:
            self.canvas.set_page(0)
            self.sidebar.select_page(0)
            self._update_status()

    def _show_slideshow_controls(self, show: bool):
        if hasattr(self, "slideshow_hud") and self.slideshow_hud:
            if show and self.document:
                self.slideshow_hud.update_page_info(self.canvas.current_page + 1, self.document.page_count)
                self.slideshow_hud.show()
                self.slideshow_hud.raise_()
            else:
                self.slideshow_hud.hide()

    def _on_sidebar_page_selected(self, page_idx: int):
        self.canvas.set_page(page_idx)
        if self.document:
            self.document.set_current_page(page_idx)
        self._update_status()

    def _on_canvas_zoom_changed(self, zoom: float):
        zoom_str = "Fit" if getattr(self.canvas, '_auto_fit', False) else f"{int(zoom * 100)}%"
        self.zoom_status_label.setText(zoom_str)
        if hasattr(self, "floating_pill") and self.floating_pill:
            if self.document:
                curr = self.canvas.current_page + 1
                tot = self.document.page_count
                if tot > 1:
                    self.floating_pill.show_status(f"Page {curr} of {tot}  •  {zoom_str}")
                else:
                    self.floating_pill.show_status(zoom_str)
            else:
                self.floating_pill.show_status(zoom_str)

    def _on_doc_changed(self):
        self.sidebar.reload_thumbnails()
        self.sidebar.reload_outline()
        self.canvas.update()
        self._update_status()

    def _on_doc_page_changed(self, page_idx: int):
        self.sidebar.reload_thumbnails()
        self.canvas.update()

    def _toggle_sidebar(self):
        if hasattr(self, "_sidebar_anim") and self._sidebar_anim and self._sidebar_anim.state() == QVariantAnimation.State.Running:
            self._sidebar_anim.stop()

        is_open = self.sidebar.isVisible() and self.splitter.sizes()[0] > 10
        total_w = sum(self.splitter.sizes())

        self._sidebar_anim = QVariantAnimation(self)
        self._sidebar_anim.setDuration(120)
        self._sidebar_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if is_open:
            self._last_sidebar_width = max(160, self.splitter.sizes()[0])
            self._sidebar_anim.setStartValue(self.splitter.sizes()[0])
            self._sidebar_anim.setEndValue(0)
            def on_tick(w):
                self.splitter.setSizes([int(w), total_w - int(w)])
            self._sidebar_anim.valueChanged.connect(on_tick)
            def on_done():
                self.sidebar.setVisible(False)
                self.canvas.zoom_to_fit()
            self._sidebar_anim.finished.connect(on_done)
        else:
            self.sidebar.setVisible(True)
            target_w = getattr(self, "_last_sidebar_width", 190)
            self._sidebar_anim.setStartValue(0)
            self._sidebar_anim.setEndValue(target_w)
            def on_tick(w):
                self.splitter.setSizes([int(w), total_w - int(w)])
            self._sidebar_anim.valueChanged.connect(on_tick)
            self._sidebar_anim.finished.connect(self.canvas.zoom_to_fit)

        self._sidebar_anim.start()

    def _toggle_markup_bar(self):
        is_vis = not self.markup_bar.isVisible()
        self.markup_bar.setVisible(is_vis)
        self.markup_toggle_btn.setChecked(is_vis)
        if not is_vis:
            # Unselect and reset active tool when markup bar is hidden
            self.markup_bar.unselect_all()
            self.canvas.unselect_tools()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._update_window_chrome_state()

    def _update_window_chrome_state(self):
        is_max = self.isMaximized()
        if hasattr(self, 'root_layout'):
            m = 0 if is_max else 10
            self.root_layout.setContentsMargins(m, m, m, m)
        if hasattr(self, 'shadow_effect'):
            self.shadow_effect.setEnabled(not is_max)
        if hasattr(self, 'toolbar_widget'):
            self.toolbar_widget.update_title_geometry()

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.ActivationChange:
            if hasattr(self, 'traffic_cluster'):
                self.traffic_cluster.set_active_state(self.isActiveWindow())
        elif event.type() == QEvent.Type.WindowStateChange:
            self._update_window_chrome_state()
        super().changeEvent(event)

    def _get_resize_edge(self, pos: QPoint) -> Optional[Qt.Edge]:
        if self.isMaximized():
            return None
        margin = 12
        w = self.width()
        h = self.height()
        x = pos.x()
        y = pos.y()
        
        left = (x <= margin)
        right = (x >= w - margin)
        top = (y <= margin)
        bottom = (y >= h - margin)
        
        if top and left:
            return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        if top and right:
            return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        if bottom and left:
            return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        if bottom and right:
            return Qt.Edge.BottomEdge | Qt.Edge.RightEdge
        if left:
            return Qt.Edge.LeftEdge
        if right:
            return Qt.Edge.RightEdge
        if top:
            return Qt.Edge.TopEdge
        if bottom:
            return Qt.Edge.BottomEdge
        return None

    def mouseMoveEvent(self, event: QMouseEvent):
        edge = self._get_resize_edge(event.position().toPoint())
        if edge:
            if (edge & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge)) and (edge & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge)):
                if (edge & Qt.Edge.TopEdge and edge & Qt.Edge.LeftEdge) or (edge & Qt.Edge.BottomEdge and edge & Qt.Edge.RightEdge):
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edge & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            if edge:
                win_handle = self.windowHandle()
                if win_handle and hasattr(win_handle, "startSystemResize"):
                    win_handle.startSystemResize(edge)
                    return
        super().mousePressEvent(event)

    def _toggle_frameless_mode(self, enabled: bool):
        self.is_frameless = enabled
        self.traffic_cluster.setVisible(enabled)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, enabled)
        self.show()

    def _detect_system_theme(self) -> str:
        app = QApplication.instance()
        if app and hasattr(app, "styleHints"):
            try:
                cs = app.styleHints().colorScheme()
                if cs == Qt.ColorScheme.Light:
                    return MacTheme.LIGHT
                elif cs == Qt.ColorScheme.Dark:
                    return MacTheme.DARK
            except Exception:
                pass
        try:
            import subprocess
            res = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                                 capture_output=True, text=True, timeout=1)
            if "prefer-dark" in res.stdout.lower() or "dark" in res.stdout.lower():
                return MacTheme.DARK
            elif "prefer-light" in res.stdout.lower() or "light" in res.stdout.lower():
                return MacTheme.LIGHT
        except Exception:
            pass
        return MacTheme.DARK

    def _on_system_color_scheme_changed(self, scheme):
        target = MacTheme.DARK if scheme == Qt.ColorScheme.Dark else MacTheme.LIGHT
        if self.current_theme != target:
            self.current_theme = target
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
            self._apply_theme(self.current_theme, animate=True)

    def _toggle_theme(self):
        if self.current_theme == MacTheme.DARK:
            self.current_theme = MacTheme.LIGHT
            self.theme_btn.setText("🌙")
        else:
            self.current_theme = MacTheme.DARK
            self.theme_btn.setText("☀️")
        self._apply_theme(self.current_theme, animate=True)

    def _apply_theme(self, theme_name: str, animate: bool = False):
        if animate and self.isVisible() and hasattr(self, "window_frame"):
            pix = self.window_frame.grab()
            overlay = QLabel(self.window_frame)
            overlay.setPixmap(pix)
            overlay.resize(self.window_frame.size())
            overlay.show()
            overlay.raise_()

            effect = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(200)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.finished.connect(overlay.deleteLater)
            self._theme_anim = anim

            qss = MacTheme.get_stylesheet(theme_name)
            self.setStyleSheet(qss)
            self._update_all_icons()
            self.sidebar.thumb_list.update()
            self.traffic_cluster.update()
            anim.start()
        else:
            qss = MacTheme.get_stylesheet(theme_name)
            self.setStyleSheet(qss)
            self._update_all_icons()
            self.sidebar.thumb_list.update()
            self.traffic_cluster.update()

    def _rotate_left(self):
        if self.document:
            page = self.canvas.current_page
            self.document.rotate_page(page, -90)
            self.canvas.zoom_to_fit()
            def undo_rot():
                self.document.rotate_page(page, 90)
                self.canvas.zoom_to_fit()
            def redo_rot():
                self.document.rotate_page(page, -90)
                self.canvas.zoom_to_fit()
            self.canvas.history.push(ActionCommand("Rotate Left", undo_rot, redo_rot))

    def _rotate_right(self):
        if self.document:
            page = self.canvas.current_page
            self.document.rotate_page(page, 90)
            self.canvas.zoom_to_fit()
            def undo_rot():
                self.document.rotate_page(page, -90)
                self.canvas.zoom_to_fit()
            def redo_rot():
                self.document.rotate_page(page, 90)
                self.canvas.zoom_to_fit()
            self.canvas.history.push(ActionCommand("Rotate Right", undo_rot, redo_rot))

    def _open_adjust_color(self):
        if not self.document:
            return
        page = self.canvas.current_page
        if self.document._pil_image:
            img = self.document._pil_image
        else:
            pix = self.document.render_page(page, zoom=1.5)
            import io
            buf = io.BytesIO()
            pix.save(buf, "PNG")
            from PIL import Image
            img = Image.open(buf)

        old_img = img.copy()
        dialog = AdjustColorDialog(img, self)
        dialog.adjustments_applied.connect(lambda adjusted: self._on_color_adjustments_applied(adjusted, old_img, page))
        dialog.exec()

    def _on_color_adjustments_applied(self, new_img, old_img, page):
        if self.document:
            self.document.update_image(new_img, page)
            self.canvas.update()
            def undo_color():
                self.document.update_image(old_img, page)
                self.canvas.update()
            def redo_color():
                self.document.update_image(new_img, page)
                self.canvas.update()
            self.canvas.history.push(ActionCommand("Adjust Color", undo_color, redo_color))

    def _open_adjust_size(self):
        if not self.document or not self.document._pil_image:
            QMessageBox.information(self, "Adjust Size", "Size adjustment is available for image documents.")
            return

        page = self.canvas.current_page
        old_img = self.document._pil_image.copy()
        dialog = AdjustSizeDialog(self.document._pil_image, self.document.metadata.get("file_size", 0), self)
        
        def on_size(resized):
            self.document.update_image(resized, page)
            def undo_sz():
                self.document.update_image(old_img, page)
            def redo_sz():
                self.document.update_image(resized, page)
            self.canvas.history.push(ActionCommand("Adjust Size", undo_sz, redo_sz))

        dialog.size_applied.connect(on_size)
        dialog.exec()

    def _open_signature_dialog(self):
        dialog = SignatureDialog(self)
        dialog.signature_selected.connect(self._on_signature_selected)
        dialog.exec()

    def _on_signature_selected(self, sig_pixmap):
        self.canvas.active_signature_pixmap = sig_pixmap
        self.canvas.set_active_tool(AnnotationType.SIGNATURE)
        self._show_status("Click anywhere on the document to stamp your signature.")

    def _show_inspector(self):
        if not self.document:
            return
        if not self.inspector_dialog:
            self.inspector_dialog = InspectorDialog(self.document.metadata, self)
        self.inspector_dialog.show()
        self.inspector_dialog.raise_()

    def _on_search(self):
        query = self.search_edit.text().strip()
        if not self.document or not query:
            self.canvas.search_results.clear()
            self.canvas.update()
            return
        
        results = self.document.search_text(query)
        self.canvas.search_results = results
        if results:
            first_match = results[0]
            self.canvas.set_page(first_match.page_num)
            self.sidebar.select_page(first_match.page_num)
            self._show_status(f"Found {len(results)} matches for '{query}'")
        else:
            self._show_status(f"No matches found for '{query}'")
        self.canvas.update()

    def _update_status(self):
        if self.document:
            w, h = self.document.get_page_size(self.canvas.current_page)
            curr = self.canvas.current_page + 1
            tot = self.document.page_count
            p_text = f"Page {curr} of {tot} — {int(w)} × {int(h)} pt"
            self.page_status_label.setText(p_text)
            self.page_badge.setText(f"{curr} of {tot}")
            self.page_badge.setVisible(tot > 1)
            self.toolbar_widget.update_title_geometry()

            zoom_str = "Fit" if getattr(self.canvas, '_auto_fit', False) else f"{int(self.canvas.zoom * 100)}%"
            if hasattr(self, "floating_pill") and self.floating_pill:
                if tot > 1:
                    self.floating_pill.show_status(f"Page {curr} of {tot}  •  {zoom_str}")
                else:
                    self.floating_pill.show_status(f"{zoom_str}  •  {int(w)} × {int(h)} pt")
            if hasattr(self, "slideshow_hud") and self.slideshow_hud and getattr(self, "_is_slideshow", False):
                self.slideshow_hud.update_page_info(curr, tot)
        else:
            self.page_status_label.setText("No document")
            self.page_badge.setVisible(False)
            self.toolbar_widget.update_title_geometry()

    def _show_status(self, msg: str, timeout: int = 4000):
        self.status_bar.showMessage(msg, timeout)
        if hasattr(self, "floating_pill") and self.floating_pill:
            self.floating_pill.show_status(msg)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def keyPressEvent(self, event: QKeyEvent):
        if getattr(self, "_is_slideshow", False):
            if event.key() == Qt.Key.Key_Escape:
                self._toggle_slideshow()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Space:
                self._toggle_slideshow_timer()
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.next_page()
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                self.prev_page()
                event.accept()
                return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "slideshow_hud") and self.slideshow_hud and self.slideshow_hud.isVisible():
            self.slideshow_hud._reposition()

    # --- Drag and Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not paths:
            return

        # If a single directory was dropped, open folder
        if len(paths) == 1 and os.path.isdir(paths[0]):
            self.open_folder(paths[0])
        elif len(paths) == 1:
            self.open_file(paths[0])
        else:
            self.open_files(paths)

    # --- Software Update Checks ---
    def _check_for_updates_startup(self):
        """Non-blocking background check for new versions on launch."""
        settings = QSettings("TriviLabs", "PreviewMacOS")
        auto_check = settings.value("check_updates_on_startup", True, type=bool)
        if not auto_check:
            return

        import time
        last_check = settings.value("last_update_check_time", 0.0, type=float)
        now = time.time()
        # Check at most once every 24 hours automatically
        if now - last_check < 86400:
            return

        self._start_update_check(is_manual=False)

    def _check_for_updates_manual(self):
        """User-initiated manual update check with visual progress feedback."""
        self._show_status("Checking for updates...", 3000)
        self._start_update_check(is_manual=True)

    def _start_update_check(self, is_manual: bool = False):
        if self._update_worker and self._update_worker.isRunning():
            return

        from preview import __version__
        self._update_worker = UpdateCheckWorker(current_version=__version__, is_manual=is_manual, parent=self)
        if is_manual:
            self._update_worker.update_available.connect(self._show_update_dialog)
            self._update_worker.no_update_available.connect(self._on_no_update_manual)
            self._update_worker.check_failed.connect(self._on_update_check_failed_manual)
        else:
            self._update_worker.update_available.connect(self._on_update_available_startup)

        self._update_worker.start()

    def _on_update_available_startup(self, update_info: UpdateInfo):
        """Displays non-intrusive in-app banner when background check finds an update."""
        import time
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("last_update_check_time", time.time())

        # If user marked this specific version as skipped, honor their preference
        skipped = settings.value("skipped_version", "", type=str)
        if skipped == update_info.version:
            return

        if not self.update_banner:
            self.update_banner = UpdateBanner(update_info, self)
            self.update_banner.view_requested.connect(lambda: self._show_update_dialog(update_info))
            # Insert above the splitter
            idx = self.main_layout.indexOf(self.splitter)
            if idx >= 0:
                self.main_layout.insertWidget(idx, self.update_banner)
            else:
                self.main_layout.addWidget(self.update_banner)
        else:
            self.update_banner.setVisible(True)

        # Show popup notification asking the user to update
        self._show_update_dialog(update_info)

    def _show_update_dialog(self, update_info: UpdateInfo):
        """Opens macOS Sparkle style software update sheet."""
        if self.update_banner:
            self.update_banner.setVisible(False)
        from preview import __version__
        dlg = UpdateDialog(update_info, current_version=__version__, parent=self)
        dlg.exec()

    def _on_no_update_manual(self, current_ver: str):
        """Shows informative dialog confirming the user has the newest version."""
        import time
        settings = QSettings("TriviLabs", "PreviewMacOS")
        settings.setValue("last_update_check_time", time.time())

        msg = QMessageBox(self)
        msg.setWindowTitle("Software Update")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            msg.setIconPixmap(QPixmap(icon_path).scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("<h3>You're up to date!</h3>")
        msg.setInformativeText(f"Preview {current_ver} is currently the newest version available.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _on_update_check_failed_manual(self, err: str):
        """Shows warning dialog when manual update check fails."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Software Update")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("<h3>Unable to Check for Updates</h3>")
        msg.setInformativeText(f"Could not connect to the update server:\n{err}\n\nPlease check your internet connection and try again.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
