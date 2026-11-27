"""
Main Window for Preview macOS Linux clone.
Implements unified macOS toolbar, authentic traffic light controls, collapsible sidebar,
markup bar, canvas, menus, keyboard shortcuts, multi-image & folder support, and file drag-and-drop.
"""

import logging
import os
import sys
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolButton, QLineEdit, QLabel, QFileDialog, QInputDialog, QMessageBox, QAbstractButton,
    QApplication, QMenu, QMenuBar, QStatusBar, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QDialog
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QKeySequence, QDragEnterEvent, QDropEvent, QColor,
    QMouseEvent, QPainter, QBrush, QPen, QFont, QKeyEvent, QPixmap, QCloseEvent, QShortcut
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QTimer, QRectF, QEvent, QPropertyAnimation, QVariantAnimation, QEasingCurve, QSettings

from preview.theme import MacTheme, ThemeManager
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
from preview.ui.batch_dialog import BatchConvertDialog
from preview.ui.save_dialog import MacSaveConfirmationDialog
from preview.ui.tab_bar import MacTabBarContainer, DocumentTabState
from preview.core.updater import UpdateCheckWorker, UpdateInfo
from preview.ui.update_dialog import UpdateDialog, UpdateBanner
from preview.ui.inspector_panel import MacInspectorPanel
from preview.ui.organize_toolbar import OrganizeActionBar

from preview.ui.main_window.export_print import ExportPrintMixin
from preview.ui.main_window.file_session import FileSessionMixin
from preview.ui.main_window.window_events_and_tools import WindowEventsAndToolsMixin
from preview.ui.main_window.workspace_modes import WorkspaceModesMixin
from preview.ui.main_window.menus import MenusMixin
from preview.ui.main_window.chrome import (
    FloatingStatusPill as FloatingStatusPill,
    FloatingSlideshowHUD as FloatingSlideshowHUD,
    TrafficLightButton as TrafficLightButton,
    StudioCloseButton as StudioCloseButton,
    StudioWindowControls as StudioWindowControls,
    TrafficLightCluster as TrafficLightCluster,
    DraggableToolbar as DraggableToolbar,
    DraggableMenuBar as DraggableMenuBar,
)

class MacMainWindow(MenusMixin, FileSessionMixin, ExportPrintMixin, WorkspaceModesMixin, WindowEventsAndToolsMixin, QMainWindow):
    """The central macOS Preview application window."""

    def __init__(self, initial_target: Optional[str] = None, initial_file: Optional[str] = None, **kwargs):
        super().__init__()
        self.setObjectName("DocumentViewer")
        self.setWindowTitle("Document Viewer")
        self.resize(1150, 780)
        self.setMinimumSize(640, 480)
        self.setAcceptDrops(True)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.theme_manager = ThemeManager.instance()
        self.appearance_mode: str = "auto"
        self.current_theme: str = self.theme_manager.get_resolved_theme()
        self.theme_manager.theme_changed.connect(self._on_theme_manager_changed)
        self.current_workspace_mode: str = "View"
        self.document: Optional[Document] = None
        self.inspector_dialog: Optional[InspectorDialog] = None
        self.color_dialog: Optional[AdjustColorDialog] = None
        self.is_frameless: bool = True
        self._last_sidebar_width: int = 220
        self._sidebar_anim: Optional[QVariantAnimation] = None
        self._update_worker: Optional[UpdateCheckWorker] = None
        self.update_banner: Optional[UpdateBanner] = None

        # Listen for system theme changes
        app = QApplication.instance()
        if app and hasattr(app, "styleHints"):
            try:
                app.styleHints().colorSchemeChanged.connect(self._on_system_color_scheme_changed)
            except Exception:
                logging.getLogger(__name__).exception("Failed to connect system colorSchemeChanged signal")

        # Window chrome flags for rounded corners and shadow
        if sys.platform == "win32":
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
            )
        else:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self._setup_ui()
        self._setup_menus()
        self._apply_theme(self.current_theme, animate=False)

        # Background update check on startup (delayed 2.5s)
        if not (os.environ.get("CI") or os.environ.get("PREVIEW_TESTING")):
            QTimer.singleShot(2500, self._check_for_updates_startup)

        target = initial_target or initial_file
        if target:
            if os.path.isdir(target):
                self.open_folder(target)
            elif os.path.isfile(target):
                self.open_file(target)

    def _setup_ui(self):
        use_translucent = sys.platform != "win32"
        if use_translucent:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.root_widget = QWidget()
        self.root_widget.setObjectName("rootContainer")
        if use_translucent:
            self.root_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.root_widget.setMouseTracking(True)
        self.setCentralWidget(self.root_widget)

        self.root_layout = QVBoxLayout(self.root_widget)
        margin = 10 if use_translucent else 0
        self.root_layout.setContentsMargins(margin, margin, margin, margin)
        self.root_layout.setSpacing(0)

        # Window Frame with 10px rounded corners & soft drop shadow
        self.window_frame = QWidget()
        self.window_frame.setObjectName("windowFrame")
        self.root_layout.addWidget(self.window_frame)

        if use_translucent:
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
        self.top_menubar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.main_layout.addWidget(self.top_menubar)

        # 1. Canvas & Sidebar instantiation
        self.sidebar = MacSidebar(self)
        self.sidebar.page_selected.connect(self._on_sidebar_page_selected)

        self.canvas = CanvasView(self)
        self.canvas.zoom_changed.connect(self._on_canvas_zoom_changed)
        self.canvas.status_message.connect(self._show_status)
        self.canvas.page_next_requested.connect(self.next_page)
        self.canvas.page_prev_requested.connect(self.prev_page)
        self.canvas.document_modified.connect(lambda _: self._on_document_or_annotations_modified())
        self.canvas.annotation_selected.connect(self._on_annotation_selected)

        # 2. Secondary Markup Toolbar (collapsible 38px)
        self.markup_bar = MarkupToolbar(self)
        self.markup_bar.setVisible(False)
        self._connect_markup_bar()
        self.canvas.crop_available.connect(self.markup_bar.set_crop_enabled)

        # 2.5 Mode C Organize Action Bar (collapsible)
        self.organize_bar = OrganizeActionBar(self)
        self.organize_bar.setVisible(False)
        self._connect_organize_bar()

        # 3. Unified macOS Toolbar (fixed 52px tall, 1px bottom border)
        self._setup_toolbar()
        self.main_layout.addWidget(self.toolbar_widget)
        self.main_layout.addWidget(self.markup_bar)
        self.main_layout.addWidget(self.organize_bar)

        # 3.5 macOS Tab Bar (collapsible / multi-tab)
        self.tab_container = MacTabBarContainer(self)
        self.tab_container.new_tab_clicked.connect(self._on_new_tab_triggered)
        self.tab_container.tab_close_requested.connect(self.close_tab)
        self.tab_container.current_changed.connect(self._on_tab_bar_current_changed)
        self.tab_container.tab_moved.connect(self._on_tab_moved)
        self.main_layout.addWidget(self.tab_container)

        self.tabs: List[DocumentTabState] = []
        self.active_tab_index: int = -1
        self.show_tab_bar_always: bool = False

        # 3.8 Right Inspector Panel (collapsible 280px)
        self.inspector_panel = MacInspectorPanel(self)
        self.inspector_panel.setVisible(False)
        self._connect_inspector_panel()

        # 4. Central Splitter (Sidebar + Canvas + Inspector) takes 100% remaining space
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.inspector_panel)
        self.splitter.setSizes([240, 960, 0])
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

        self._init_tabs()

    def _create_divider(self) -> QWidget:
        div = QWidget()
        div.setObjectName("toolbarDivider")
        div.setFixedSize(1, 20)
        return div

    def _setup_toolbar(self):
        self.toolbar_widget = DraggableToolbar(self)
        self.toolbar_widget.setObjectName("macToolbar")
        self.toolbar_widget.setFixedHeight(48)
        self.toolbar_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(16, 0, 16, 0)
        toolbar_layout.setSpacing(0)

        # 1. Left Group: Sidebar Toggle + Back/Forward + Open
        # Sidebar toggle (32x32)
        self.sidebar_btn = QToolButton()
        self.sidebar_btn.setObjectName("sidebarBtn")
        self.sidebar_btn.setFixedSize(32, 32)
        self.sidebar_btn.setToolTip("Toggle Sidebar (Ctrl+B) - Learn more (F1)")
        self.sidebar_btn.setAccessibleName("Toggle Sidebar")
        self.sidebar_btn.clicked.connect(self._toggle_sidebar)
        toolbar_layout.addWidget(self.sidebar_btn)

        toolbar_layout.addSpacing(8)

        # Nav segmented pair (64x32)
        self.nav_segmented = QWidget()
        self.nav_segmented.setObjectName("navSegmented")
        self.nav_segmented.setFixedSize(64, 32)
        nav_layout = QHBoxLayout(self.nav_segmented)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.prev_btn = QToolButton()
        self.prev_btn.setObjectName("prevBtn")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setToolTip("Previous Page / Image (Left Arrow)")
        self.prev_btn.setAccessibleName("Previous Page")
        self.prev_btn.clicked.connect(self.prev_page)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QToolButton()
        self.next_btn.setObjectName("nextBtn")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setToolTip("Next Page / Image (Right Arrow)")
        self.next_btn.setAccessibleName("Next Page")
        self.next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_btn)

        toolbar_layout.addWidget(self.nav_segmented)

        toolbar_layout.addSpacing(8)

        # Open Segmented Control (32px tall)
        self.open_segmented = QWidget()
        self.open_segmented.setObjectName("openSegmented")
        self.open_segmented.setFixedHeight(32)
        open_seg_layout = QHBoxLayout(self.open_segmented)
        open_seg_layout.setContentsMargins(0, 0, 0, 0)
        open_seg_layout.setSpacing(0)

        self.open_btn = QToolButton()
        self.open_btn.setObjectName("openMainBtn")
        self.open_btn.setFixedHeight(32)
        self.open_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.open_btn.setText("Open")
        self.open_btn.setToolTip("Open Document or Images (Ctrl+O) - Learn more (F1)")
        self.open_btn.setAccessibleName("Open Document")
        self.open_btn.clicked.connect(self._open_file_dialog)
        open_seg_layout.addWidget(self.open_btn)

        self.open_arrow_btn = QToolButton()
        self.open_arrow_btn.setObjectName("openArrowBtn")
        self.open_arrow_btn.setFixedSize(20, 32)
        self.open_arrow_btn.setToolTip("Open Options")
        self.open_arrow_btn.setAccessibleName("Open Options")

        open_menu = QMenu(self)
        open_files_action = QAction("Open File(s)...", self)
        open_files_action.setShortcut(QKeySequence("Ctrl+O"))
        open_files_action.triggered.connect(self._open_file_dialog)
        open_menu.addAction(open_files_action)

        # open_new_tab_action = QAction("Open in New Tab...", self)
        # open_new_tab_action.setShortcut(QKeySequence("Ctrl+Alt+O"))
        # open_new_tab_action.triggered.connect(self._on_new_tab_triggered)
        # open_menu.addAction(open_new_tab_action)

        open_folder_action = QAction("Open Folder of Images...", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self._open_folder_dialog)
        open_menu.addAction(open_folder_action)

        self.open_arrow_btn.setMenu(open_menu)
        self.open_arrow_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        open_seg_layout.addWidget(self.open_arrow_btn)

        toolbar_layout.addWidget(self.open_segmented)

        # Thin Vertical Divider 1
        toolbar_layout.addSpacing(16)
        self.divider1 = self._create_divider()
        toolbar_layout.addWidget(self.divider1)
        toolbar_layout.addSpacing(16)

        toolbar_layout.addStretch(1)

        # 2. Center Group: Document Filename + Mode Segmented Control
        self.center_container = QWidget()
        self.center_container.setObjectName("toolbarCenterContainer")
        center_layout = QHBoxLayout(self.center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_widget = QWidget(self.center_container)
        self.title_widget.setObjectName("titleWidget")
        title_box = QHBoxLayout(self.title_widget)
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(6)
        title_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.proxy_icon_label = QLabel()
        self.proxy_icon_label.setFixedSize(16, 16)
        self.title_label = QLabel("No document")
        self.title_label.setObjectName("windowTitleLabel")
        self.page_badge = QLabel("")
        self.page_badge.setObjectName("pageBadge")
        self.page_badge.setVisible(False)

        title_box.addWidget(self.proxy_icon_label)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.page_badge)
        center_layout.addWidget(self.title_widget)

        center_layout.addSpacing(8)

        # Mode Segmented Control: [ View | Edit | Organize ]
        self.mode_segmented = QWidget(self.center_container)
        self.mode_segmented.setObjectName("modeSegmented")
        self.mode_segmented.setFixedHeight(32)
        mode_layout = QHBoxLayout(self.mode_segmented)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(0)

        self.mode_view_btn = QToolButton()
        self.mode_view_btn.setObjectName("modeViewBtn")
        self.mode_view_btn.setCheckable(True)
        self.mode_view_btn.setChecked(True)
        self.mode_view_btn.setText("View")
        self.mode_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.mode_view_btn.setFixedHeight(32)
        self.mode_view_btn.setToolTip("View Mode: Clean document reading (Alt+1)")
        self.mode_view_btn.setAccessibleName("View Mode")
        self.mode_view_btn.clicked.connect(lambda: self.set_workspace_mode("View"))
        mode_layout.addWidget(self.mode_view_btn)

        self.mode_edit_btn = QToolButton()
        self.mode_edit_btn.setObjectName("modeEditBtn")
        self.mode_edit_btn.setCheckable(True)
        self.mode_edit_btn.setText("Edit")
        self.mode_edit_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.mode_edit_btn.setFixedHeight(32)
        self.mode_edit_btn.setToolTip("Edit Mode: Annotation and markup tools (Alt+2)")
        self.mode_edit_btn.setAccessibleName("Edit Mode")
        self.mode_edit_btn.clicked.connect(lambda: self.set_workspace_mode("Edit"))
        mode_layout.addWidget(self.mode_edit_btn)

        self.mode_organize_btn = QToolButton()
        self.mode_organize_btn.setObjectName("modeOrganizeBtn")
        self.mode_organize_btn.setCheckable(True)
        self.mode_organize_btn.setText("Organize")
        self.mode_organize_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.mode_organize_btn.setFixedHeight(32)
        self.mode_organize_btn.setToolTip("Organize Mode: Page & document management (Alt+3)")
        self.mode_organize_btn.setAccessibleName("Organize Mode")
        self.mode_organize_btn.clicked.connect(lambda: self.set_workspace_mode("Organize"))
        mode_layout.addWidget(self.mode_organize_btn)

        center_layout.addWidget(self.mode_segmented)
        toolbar_layout.addWidget(self.center_container)

        toolbar_layout.addStretch(1)

        # Thin Vertical Divider 2
        toolbar_layout.addSpacing(16)
        self.divider2 = self._create_divider()
        toolbar_layout.addWidget(self.divider2)
        toolbar_layout.addSpacing(16)

        # 3. Right Group: Zoom + Rotate + Markup + Search + Info + Theme
        self.zoom_segmented = QWidget()
        self.zoom_segmented.setObjectName("zoomSegmented")
        self.zoom_segmented.setFixedSize(64, 32)
        zoom_layout = QHBoxLayout(self.zoom_segmented)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(0)

        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setObjectName("zoomOutBtn")
        self.zoom_out_btn.setFixedSize(32, 32)
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-) - Learn more (F1)")
        self.zoom_out_btn.setAccessibleName("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setObjectName("zoomInBtn")
        self.zoom_in_btn.setFixedSize(32, 32)
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++) - Learn more (F1)")
        self.zoom_in_btn.setAccessibleName("Zoom In")
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)

        toolbar_layout.addWidget(self.zoom_segmented)

        toolbar_layout.addSpacing(6)

        # Full Screen mode button (32x32)
        self.fullscreen_btn = QToolButton()
        self.fullscreen_btn.setObjectName("fullscreenBtn")
        self.fullscreen_btn.setFixedSize(32, 32)
        self.fullscreen_btn.setToolTip("Full Screen (F11)")
        self.fullscreen_btn.setAccessibleName("Toggle Full Screen")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        toolbar_layout.addWidget(self.fullscreen_btn)

        toolbar_layout.addSpacing(8)

        # Rotate button (32x32)
        self.rotate_btn = QToolButton()
        self.rotate_btn.setObjectName("rotateBtn")
        self.rotate_btn.setFixedSize(0, 0)
        self.rotate_btn.setToolTip("Rotate (Ctrl+R) - Learn more (F1)")
        self.rotate_btn.setAccessibleName("Rotate Clockwise")
        self.rotate_btn.clicked.connect(self._rotate_right)
        self.rotate_right_btn = self.rotate_btn
        self.rotate_left_btn = self.rotate_btn
        toolbar_layout.addWidget(self.rotate_btn)

        toolbar_layout.addSpacing(8)

        # Markup primary button (32px tall)
        self.markup_toggle_btn = QToolButton()
        self.markup_toggle_btn.setObjectName("markupPillBtn")
        self.markup_toggle_btn.setCheckable(True)
        self.markup_toggle_btn.setText("Markup")
        self.markup_toggle_btn.setFixedHeight(32)
        self.markup_toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.markup_toggle_btn.setToolTip("Show/Hide Markup Toolbar (Ctrl+Shift+A) - Learn more (F1)")
        self.markup_toggle_btn.setAccessibleName("Markup Tools")
        self.markup_toggle_btn.clicked.connect(self._toggle_markup_bar)
        toolbar_layout.addWidget(self.markup_toggle_btn)

        toolbar_layout.addSpacing(8)

        # Search Bar
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("macSearchField")
        self.search_edit.setPlaceholderText("Search")
        self.search_edit.setFixedHeight(32)
        self.search_edit.setFixedWidth(130)
        self.search_edit.setAccessibleName("Search Document")
        self.search_edit.returnPressed.connect(self._on_search)
        self.search_action = self.search_edit.addAction(
            MacIconFactory.create_icon("search", "#8e8e93", 14),
            QLineEdit.ActionPosition.LeadingPosition
        )
        toolbar_layout.addWidget(self.search_edit)

        toolbar_layout.addSpacing(8)

        # Inspector button (32x32)
        self.inspector_btn = QToolButton()
        self.inspector_btn.setObjectName("inspectorBtn")
        self.inspector_btn.setCheckable(True)
        self.inspector_btn.setFixedSize(32, 32)
        self.inspector_btn.setToolTip("Show/Hide Inspector Panel (Ctrl+I) - Learn more (F1)")
        self.inspector_btn.setAccessibleName("Inspector Panel")
        self.inspector_btn.clicked.connect(self._toggle_inspector_panel)
        toolbar_layout.addWidget(self.inspector_btn)

        toolbar_layout.addSpacing(8)

        # Theme toggle (32x32)
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setToolTip("Toggle Dark/Light Mode (Ctrl+T) - Learn more (F1)")
        self.theme_btn.setAccessibleName("Toggle Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar_layout.addWidget(self.theme_btn)

        toolbar_layout.addSpacing(6)

        # Settings gear button (32x32)
        self.settings_btn = QToolButton()
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setToolTip("Preferences (Ctrl+,)")
        self.settings_btn.setAccessibleName("Preferences")
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        toolbar_layout.addWidget(self.settings_btn)

        # Modern standard window controls placed in topbar (menubar top-right corner)
        self.divider3 = None
        self.window_controls = StudioWindowControls(self)
        self.traffic_cluster = self.window_controls  # Fully backwards-compatible alias
        self.top_menubar.setCornerWidget(self.window_controls, Qt.Corner.TopRightCorner)
        self.window_controls.setVisible(self.is_frameless)

        self._update_all_icons()

    def _get_icon_color(self) -> str:
        return "#f5f5f7" if self.current_theme == MacTheme.DARK else "#2c2c2e"

    def _update_all_icons(self):
        col = self._get_icon_color()
        self.sidebar_btn.setIcon(MacIconFactory.create_icon("panel-left", col, 18))
        self.prev_btn.setIcon(MacIconFactory.create_icon("chevron-left", col, 18))
        self.next_btn.setIcon(MacIconFactory.create_icon("chevron-right", col, 18))
        self.open_btn.setIcon(MacIconFactory.create_icon("folder-open", col, 18))
        if hasattr(self, "open_arrow_btn"):
            self.open_arrow_btn.setIcon(MacIconFactory.create_icon("chevron-down", col, 12))
        self.proxy_icon_label.setPixmap(MacIconFactory.create_icon("file-text", col, 16).pixmap(16, 16))
        self.zoom_out_btn.setIcon(MacIconFactory.create_icon("zoom-out", col, 18))
        self.zoom_in_btn.setIcon(MacIconFactory.create_icon("zoom-in", col, 18))
        self.rotate_btn.setIcon(MacIconFactory.create_icon("rotate-cw", col, 18))
        if hasattr(self, "fullscreen_btn"):
            fs_icon = "minimize" if self.isFullScreen() else "maximize"
            self.fullscreen_btn.setIcon(MacIconFactory.create_icon(fs_icon, col, 18))
        self.markup_toggle_btn.setIcon(MacIconFactory.create_icon("pen-tool", "#ffffff" if self.markup_toggle_btn.isChecked() else col, 20))
        self.inspector_btn.setIcon(MacIconFactory.create_icon("info", "#ffffff" if self.inspector_btn.isChecked() else col, 18))
        if hasattr(self, "settings_btn"):
            self.settings_btn.setIcon(MacIconFactory.create_icon("gear", col, 18))
        if hasattr(self, "window_controls"):
            self.window_controls.update_icons(col)

        # Mode segmented icons
        if hasattr(self, "mode_view_btn"):
            self.mode_view_btn.setIcon(MacIconFactory.create_icon("eye", "#ffffff" if self.mode_view_btn.isChecked() else col, 16))
        if hasattr(self, "mode_edit_btn"):
            self.mode_edit_btn.setIcon(MacIconFactory.create_icon("pencil", "#ffffff" if self.mode_edit_btn.isChecked() else col, 16))
        if hasattr(self, "mode_organize_btn"):
            self.mode_organize_btn.setIcon(MacIconFactory.create_icon("layout-grid", "#ffffff" if self.mode_organize_btn.isChecked() else col, 16))

        # Theme icon without emoji text
        if hasattr(self, "theme_btn"):
            theme_icon = "sun" if self.current_theme == MacTheme.DARK else "moon"
            self.theme_btn.setIcon(MacIconFactory.create_icon(theme_icon, col, 18))
            self.theme_btn.setText("")

        # Search field inside magnifier
        if hasattr(self, "search_action"):
            search_col = "#98989d" if self.current_theme == MacTheme.DARK else "#6e6e73"
            self.search_action.setIcon(MacIconFactory.create_icon("search", search_col, 14))

        self.markup_bar.update_icons(col)
        if hasattr(self, "organize_bar"):
            self.organize_bar.update_icons(col)
        if hasattr(self, "inspector_panel"):
            self.inspector_panel.update_icons(col)

    def _connect_markup_bar(self):
        self.markup_bar.tool_changed.connect(self.canvas.set_active_tool)
        self.markup_bar.stroke_color_changed.connect(self.canvas.set_stroke_color)
        self.markup_bar.stroke_width_changed.connect(self.canvas.set_stroke_width)
        self.markup_bar.fill_color_changed.connect(self.canvas.set_fill_color)
        self.markup_bar.font_size_changed.connect(self.canvas.set_font_size)
        self.markup_bar.font_family_changed.connect(self.canvas.set_font_family)
        self.markup_bar.font_bold_changed.connect(self.canvas.set_font_bold)
        self.markup_bar.font_italic_changed.connect(self.canvas.set_font_italic)
        self.markup_bar.font_underline_changed.connect(self.canvas.set_font_underline)
        self.markup_bar.text_align_changed.connect(self.canvas.set_text_alignment)
        self.markup_bar.adjust_color_requested.connect(self._open_adjust_color)
        self.markup_bar.adjust_size_requested.connect(self._open_adjust_size)
        self.markup_bar.rotate_requested.connect(self._rotate_left)
        self.markup_bar.rotate_selection_requested.connect(self._rotate_right)
        if hasattr(self.markup_bar, "rotate_right_requested"):
            self.markup_bar.rotate_right_requested.connect(self._rotate_right)
        self.markup_bar.crop_requested.connect(self.canvas.apply_crop)
        self.markup_bar.signature_requested.connect(self._open_signature_dialog)
        self.markup_bar.image_overlay_requested.connect(self._add_image_overlay)
        self.canvas.tool_deselected.connect(self.markup_bar.unselect_all)

        # --- Undo / Redo ---
        self.markup_bar.undo_requested.connect(self._undo)
        self.markup_bar.redo_requested.connect(self._redo)

        # --- Permanent redactions ---
        if hasattr(self, "_apply_redactions_permanently"):
            self.markup_bar.apply_redactions_requested.connect(
                self._apply_redactions_permanently
            )
        else:
            print("[WARN] No _apply_redactions_permanently handler on MainWindow — "
                  "apply_redactions_requested will not do anything.")

        # --- Strikethrough (text format) ---
        self.markup_bar.font_strikethrough_changed.connect(
            lambda on: self.canvas.set_strikethrough(on)
        )

        # --- Line styles (dashed/dotted) ---
        self.markup_bar.stroke_style_changed.connect(
            lambda style: self.canvas.set_stroke_style(style)
        )

        # --- Fill opacity ---
        self.markup_bar.fill_opacity_changed.connect(
            lambda pct: self.canvas.set_fill_opacity(pct / 100.0)
        )










































    # --- Open Recent Documents ---




    # --- PDF View & Manipulation Operations ---







    # --- Export & Print ---





    # --- Live Text Extraction ---


    # --- Fullscreen Document / Image Presentation Mode ---
































    # ---------------------------





















































    # --- Drag and Drop ---


    # --- Software Update Checks ---






