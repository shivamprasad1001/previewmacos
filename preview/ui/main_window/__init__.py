"""
Main Window for Preview macOS Linux clone.
Implements unified macOS toolbar, authentic traffic light controls, collapsible sidebar,
markup bar, canvas, menus, keyboard shortcuts, multi-image & folder support, and file drag-and-drop.
"""

import logging
import os
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

class MacMainWindow(MenusMixin, FileSessionMixin, ExportPrintMixin, QMainWindow):
    """The central macOS Preview application window."""

    def __init__(self, initial_target: Optional[str] = None, initial_file: Optional[str] = None, **kwargs):
        super().__init__()
        self.setObjectName("DocumentViewer")
        self.setWindowTitle("Document Viewer")
        self.resize(1150, 780)
        self.setMinimumSize(640, 480)
        self.setAcceptDrops(True)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
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
                logging.getLogger(__name__).exception("Failed to connect system colorSchemeChanged signal")

        # Window chrome flags for rounded corners and shadow
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
    def toggle_fullscreen(self, auto_advance: bool = False):
        """Presents the document image in full screen display without window toolbars or sidebars."""
        is_active = self.isFullScreen() or getattr(self, "_is_fullscreen_image", False) or getattr(self, "_is_slideshow", False)

        if is_active:
            self._is_fullscreen_image = False
            self._is_slideshow = False
            if hasattr(self, "_slideshow_timer"):
                self._slideshow_timer.stop()
            if hasattr(self, "slideshow_hud"):
                self.slideshow_hud.hide()

            self.showNormal()
            if getattr(self, "_saved_maximized", False):
                self.showMaximized()

            # Restore original chrome visibility
            self.toolbar_widget.show()
            if getattr(self, "_saved_sidebar_vis", True):
                self.sidebar.show()
            else:
                self.sidebar.hide()

            if getattr(self, "_saved_markup_vis", False):
                self.markup_bar.show()
            else:
                self.markup_bar.hide()

            if getattr(self, "_saved_organize_vis", False):
                self.organize_bar.show()
            else:
                self.organize_bar.hide()

            if hasattr(self, "inspector_panel"):
                if getattr(self, "_saved_inspector_vis", False):
                    self.inspector_panel.show()
                else:
                    self.inspector_panel.hide()

            if getattr(self, "_saved_statusbar_vis", True):
                self.status_bar.show()

            if hasattr(self, "_saved_splitter_sizes") and self._saved_splitter_sizes:
                self.splitter.setSizes(self._saved_splitter_sizes)

            self.canvas.zoom_to_fit()
            if hasattr(self, "fullscreen_btn"):
                self.fullscreen_btn.setToolTip("Full Screen (F11)")
            self._show_status("Exited full screen mode.")
        else:
            self._is_fullscreen_image = True
            self._is_slideshow = auto_advance

            # Save existing layout states
            self._saved_maximized = self.isMaximized()
            self._saved_sidebar_vis = self.sidebar.isVisible()
            self._saved_markup_vis = self.markup_bar.isVisible()
            self._saved_organize_vis = self.organize_bar.isVisible()
            self._saved_inspector_vis = hasattr(self, "inspector_panel") and self.inspector_panel.isVisible()
            self._saved_statusbar_vis = self.status_bar.isVisible()
            self._saved_splitter_sizes = self.splitter.sizes()

            # Hide all chrome so ONLY the document/image fills the screen
            self.toolbar_widget.hide()
            self.sidebar.hide()
            self.markup_bar.hide()
            self.organize_bar.hide()
            if hasattr(self, "inspector_panel"):
                self.inspector_panel.hide()
            self.status_bar.hide()

            total_w = sum(self.splitter.sizes()) if sum(self.splitter.sizes()) > 0 else self.width()
            self.splitter.setSizes([0, total_w, 0])

            self.showFullScreen()
            self.canvas.zoom_to_fit()

            if hasattr(self, "slideshow_hud") and self.slideshow_hud:
                if self.document:
                    self.slideshow_hud.update_page_info(self.canvas.current_page + 1, self.document.page_count)
                self.slideshow_hud.show()
                self.slideshow_hud.raise_()
                self.slideshow_hud._reposition()

            if auto_advance:
                if not hasattr(self, "_slideshow_timer"):
                    self._slideshow_timer = QTimer(self)
                    self._slideshow_timer.setInterval(3500)
                    self._slideshow_timer.timeout.connect(self._slideshow_advance)
                self._slideshow_timer.start()
                self.slideshow_hud.set_playing(True)
                self._show_status("Slideshow started (Press Esc to exit, Space to pause/resume)")
            else:
                if hasattr(self, "_slideshow_timer"):
                    self._slideshow_timer.stop()
                if hasattr(self, "slideshow_hud"):
                    self.slideshow_hud.set_playing(False)
                self._show_status("Full screen image mode (Press Esc or F11 to exit)")

            if hasattr(self, "fullscreen_btn"):
                self.fullscreen_btn.setToolTip("Full Screen (F11)")

        self._update_all_icons()

    def _toggle_slideshow(self):
        is_active = getattr(self, "_is_slideshow", False) or getattr(self, "_is_fullscreen_image", False)
        if is_active:
            self.toggle_fullscreen(auto_advance=False)
        else:
            self.toggle_fullscreen(auto_advance=True)

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
        self._sync_toolbar_contexts()

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
        self._update_modified_ui()
        self._sync_toolbar_contexts()

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
            target_w = getattr(self, "_last_sidebar_width", 240)
            self._sidebar_anim.setStartValue(0)
            self._sidebar_anim.setEndValue(target_w)
            def on_tick(w):
                self.splitter.setSizes([int(w), total_w - int(w)])
            self._sidebar_anim.valueChanged.connect(on_tick)
            self._sidebar_anim.finished.connect(self.canvas.zoom_to_fit)

        self._sidebar_anim.start()

    def set_sidebar_visible(self, visible: bool):
        """Sets sidebar visibility with smooth transition."""
        if not hasattr(self, "sidebar") or not hasattr(self, "splitter"):
            return
        is_open = self.sidebar.isVisible() and self.splitter.sizes()[0] > 10
        if is_open != visible:
            self._toggle_sidebar()

    def set_workspace_mode(self, mode: str):
        """Switches workspace between View, Edit, and Organize modes."""
        self.current_workspace_mode = mode

        # Update mode segmented buttons
        if hasattr(self, "mode_view_btn"):
            self.mode_view_btn.setChecked(mode == "View")
        if hasattr(self, "mode_edit_btn"):
            self.mode_edit_btn.setChecked(mode == "Edit")
        if hasattr(self, "mode_organize_btn"):
            self.mode_organize_btn.setChecked(mode == "Organize")

        if mode == "View":
            self.markup_bar.setVisible(False)
            self.organize_bar.setVisible(False)
            self.markup_toggle_btn.setChecked(False)
            self.canvas.set_markup_enabled(False)
            self.markup_bar.unselect_all()
            self.canvas.unselect_tools()
            self.set_inspector_visible(False)
            self._show_status("View Mode: Distraction-free reading")

        elif mode == "Edit":
            self.organize_bar.setVisible(False)
            self.markup_bar.setVisible(True)
            self.markup_toggle_btn.setChecked(True)
            self.canvas.set_markup_enabled(True)
            self.set_inspector_visible(True)
            if hasattr(self, "markup_bar") and hasattr(self.markup_bar, "handle_resize"):
                self.markup_bar.handle_resize(self.width())
            if self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)
            self._show_status("Edit Mode: Annotation and markup tools active")

        elif mode == "Organize":
            self.markup_bar.setVisible(False)
            self.markup_toggle_btn.setChecked(False)
            self.canvas.set_markup_enabled(False)
            self.markup_bar.unselect_all()
            self.canvas.unselect_tools()
            self.organize_bar.setVisible(True)
            self.set_inspector_visible(False)
            # Switch sidebar to Contact Sheet to present multi-page grid
            if hasattr(self.sidebar, "set_view_mode"):
                self.sidebar.set_view_mode("Contact Sheet")
            # Widen sidebar splitter for better multi-page grid display
            sizes = self.splitter.sizes()
            total_w = sum(sizes) if sum(sizes) > 0 else self.width()
            target_sb_w = min(420, max(320, int(total_w * 0.38)))
            self.splitter.setSizes([target_sb_w, max(300, total_w - target_sb_w), 0])
            self._show_status("Organize Mode: Page reordering, insertion, and document actions")

        self._sync_toolbar_contexts()
        self._update_all_icons()

    def _toggle_markup_bar(self):
        is_vis = not self.markup_bar.isVisible()
        self.set_markup_visible(is_vis)

    def set_markup_visible(self, visible: bool):
        """Shows or hides the markup toolbar by toggling the workspace mode."""
        if visible:
            self.set_workspace_mode("Edit")
        else:
            self.set_workspace_mode("View")

    def _toggle_inspector_panel(self):
        self.set_inspector_visible(not self.inspector_panel.isVisible(), animated=True)

    def _show_inspector(self):
        self._toggle_inspector_panel()

    def set_inspector_visible(self, visible: bool, animated: bool = False):
        if not hasattr(self, "inspector_panel"):
            return
        if hasattr(self, "inspector_btn"):
            self.inspector_btn.setChecked(visible)

        if hasattr(self, "_inspector_anim") and self._inspector_anim and self._inspector_anim.state() == QVariantAnimation.State.Running:
            self._inspector_anim.stop()

        sizes = self.splitter.sizes()
        total_w = sum(sizes) if sum(sizes) > 0 else self.width()
        sb_w = sizes[0] if len(sizes) > 0 else 240
        current_insp_w = sizes[2] if len(sizes) > 2 else 0
        target_w = 280 if visible else 0

        if not animated or not self.isVisible():
            self.inspector_panel.setVisible(visible)
            if visible and self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)
            canvas_w = max(200, total_w - sb_w - target_w)
            self.splitter.setSizes([sb_w, canvas_w, target_w])
            self._update_all_icons()
            return

        if visible:
            self.inspector_panel.setVisible(True)
            if self.document:
                self.inspector_panel.set_document(self.document, self.canvas.current_page)

        self._inspector_anim = QVariantAnimation(self)
        self._inspector_anim.setDuration(160)
        self._inspector_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._inspector_anim.setStartValue(current_insp_w)
        self._inspector_anim.setEndValue(target_w)

        def on_tick(w):
            w_int = int(w)
            cw = max(200, total_w - sb_w - w_int)
            self.splitter.setSizes([sb_w, cw, w_int])

        def on_done():
            if not visible:
                self.inspector_panel.setVisible(False)
            self.canvas.zoom_to_fit()
            self._update_all_icons()

        self._inspector_anim.valueChanged.connect(on_tick)
        self._inspector_anim.finished.connect(on_done)
        self._inspector_anim.start()

    def _stub_flip_horizontal(self) -> None:
        if not self.document:
            return
        if self.document.is_pdf:
            self._show_status("Flip is only available for image documents.")
            return
        page = self.canvas.current_page
        self.document.flip_page_horizontal(page)
        self.canvas.zoom_to_fit()
        self._sync_toolbar_contexts()


    def _stub_flip_vertical(self) -> None:
        if not self.document:
            return
        if self.document.is_pdf:
            self._show_status("Flip is only available for image documents.")
            return
        page = self.canvas.current_page
        self.document.flip_page_vertical(page)
        self.canvas.zoom_to_fit()
        self._sync_toolbar_contexts()


    def _stub_crop(self) -> None:
        # Delegate to the canvas's existing crop pipeline (handles PIL crop + history)
        if hasattr(self.canvas, "apply_crop"):
            self.canvas.apply_crop()
            self._sync_toolbar_contexts()


    def _stub_resize(self) -> None:
        if not self.document or self.document.is_pdf:
            self._show_status("Resize is only available for image documents.")
            return
        w, h = self.document.get_page_size(self.canvas.current_page)
        new_w, ok = QInputDialog.getInt(self, "Resize Page", "New width (px):",
                                         int(w), 32, 10000, 1)
        if not ok:
            return
        new_h, ok = QInputDialog.getInt(self, "Resize Page", "New height (px):",
                                         int(h), 32, 10000, 1)
        if not ok:
            return
        if self.document.resize_page(self.canvas.current_page, new_w, new_h):
            self.canvas.zoom_to_fit()
            self._show_status(f"Resized to {new_w} × {new_h}")
            self._sync_toolbar_contexts()


    def _stub_move_up(self) -> None:
        if not self.document:
            return
        cur = self.canvas.current_page
        if cur <= 0:
            return
        if self.document.move_page(cur, cur - 1):
            self.canvas.set_page(cur - 1)
            self.document.set_current_page(cur - 1)
            self.sidebar.reload_thumbnails()
            self.sidebar.select_page(cur - 1)
            self._update_status()
            self._sync_toolbar_contexts()


    def _stub_move_down(self) -> None:
        if not self.document:
            return
        cur = self.canvas.current_page
        if cur >= self.document.page_count - 1:
            return
        if self.document.move_page(cur, cur + 1):
            self.canvas.set_page(cur + 1)
            self.document.set_current_page(cur + 1)
            self.sidebar.reload_thumbnails()
            self.sidebar.select_page(cur + 1)
            self._update_status()
            self._sync_toolbar_contexts()


    def _stub_reduce_size(self) -> None:
        if not self.document:
            return
        from PyQt6.QtWidgets import QFileDialog
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Reduce File Size — Save As", "Reduced.pdf",
            "PDF Document (*.pdf)"
        )
        if not out_path:
            return
        if self.document.reduce_file_size(out_path):
            import os
            before = os.path.getsize(self.document.file_path) if (self.document.file_path and os.path.exists(self.document.file_path)) else 0
            after = os.path.getsize(out_path) if os.path.exists(out_path) else 0
            pct = int((1 - after / before) * 100) if before > 0 else 0
            self._show_status(f"Reduced from {before // 1024} KB to {after // 1024} KB ({pct}% smaller)")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Reduce Failed", "Could not reduce file size.")


    def _stub_insert_clipboard(self) -> None:
        from PyQt6.QtWidgets import QApplication
        from PIL.ImageQt import fromqimage
        clipboard = QApplication.clipboard()
        qimg = clipboard.image()
        if qimg.isNull():
            self._show_status("Clipboard does not contain an image.")
            return
        try:
            pil_img = fromqimage(qimg)
            if self.document is None:
                self._show_status("No document open — open a document first.")
                return
            if self.document.insert_from_clipboard_image(pil_img, self.canvas.current_page):
                self.sidebar.reload_thumbnails()
                self.canvas.set_page(self.canvas.current_page + 1)
                self.document.set_current_page(self.canvas.current_page)
                self.sidebar.select_page(self.canvas.current_page)
                self._show_status("Pasted image as new page.")
                self._sync_toolbar_contexts()
            else:
                self._show_status("Failed to paste image from clipboard.")
        except Exception as e:
            self._show_status(f"Clipboard paste error: {e}")

    # ---------------------------

    def _undo(self) -> None:
        if hasattr(self, "canvas") and self.canvas:
            self.canvas.undo()

    def _redo(self) -> None:
        if hasattr(self, "canvas") and self.canvas:
            self.canvas.redo()

    def _apply_redactions_permanently(self) -> None:
        self._apply_redactions_menu()

    def _sync_toolbar_contexts(self) -> None:
        doc = self.document
        if hasattr(self, "organize_bar") and self.organize_bar:
            if doc is None:
                if hasattr(self.organize_bar, "set_context"):
                    self.organize_bar.set_context(has_document=False)
            else:
                if hasattr(self.organize_bar, "set_context"):
                    self.organize_bar._is_pdf = bool(getattr(doc, "is_pdf", False))
                    self.organize_bar.set_context(
                        has_document=True,
                        page_count=doc.page_count,
                        current_page=getattr(self.canvas, "current_page", doc.current_page),
                    )
        if hasattr(self, "markup_bar") and self.markup_bar:
            has_sel = bool(getattr(self.canvas, "_crop_box", None) or getattr(self.canvas, "_selected_annotation", None))
            if hasattr(self.markup_bar, "set_context"):
                self.markup_bar.set_context(
                    has_selection=has_sel,
                    pending_redactions=getattr(self, "_pending_redaction_count", 0),
                    has_document=doc is not None,
                )

    def _connect_organize_bar(self):
        self.organize_bar.rotate_left_requested.connect(self._rotate_left)
        self.organize_bar.rotate_right_requested.connect(self._rotate_right)
        self.organize_bar.duplicate_page_requested.connect(lambda: self.sidebar._duplicate_page(self.canvas.current_page))
        self.organize_bar.insert_blank_requested.connect(lambda: self.sidebar._insert_blank_page(self.canvas.current_page))
        self.organize_bar.insert_file_requested.connect(lambda: self.sidebar._insert_page_from_file(self.canvas.current_page))
        self.organize_bar.delete_page_requested.connect(lambda: self.sidebar._confirm_and_delete_page(self.canvas.current_page))
        self.organize_bar.merge_requested.connect(self._merge_pdfs)
        self.organize_bar.split_requested.connect(self._split_pdf)
        self.organize_bar.export_requested.connect(self._export_file)

        # Extended organize bar actions
        if hasattr(self.organize_bar, "flip_horizontal_requested"):
            self.organize_bar.flip_horizontal_requested.connect(self._stub_flip_horizontal)
        if hasattr(self.organize_bar, "flip_vertical_requested"):
            self.organize_bar.flip_vertical_requested.connect(self._stub_flip_vertical)
        if hasattr(self.organize_bar, "crop_requested"):
            self.organize_bar.crop_requested.connect(self._stub_crop)
        if hasattr(self.organize_bar, "resize_requested"):
            self.organize_bar.resize_requested.connect(self._stub_resize)
        if hasattr(self.organize_bar, "move_up_requested"):
            self.organize_bar.move_up_requested.connect(self._stub_move_up)
        if hasattr(self.organize_bar, "move_down_requested"):
            self.organize_bar.move_down_requested.connect(self._stub_move_down)
        if hasattr(self.organize_bar, "reduce_size_requested"):
            self.organize_bar.reduce_size_requested.connect(self._stub_reduce_size)
        if hasattr(self.organize_bar, "insert_clipboard_requested"):
            self.organize_bar.insert_clipboard_requested.connect(self._stub_insert_clipboard)

    def _connect_inspector_panel(self):
        self.inspector_panel.close_requested.connect(lambda: self.set_inspector_visible(False))
        self.inspector_panel.annotation_updated.connect(self._on_inspector_annotation_updated)
        self.inspector_panel.delete_annotation_requested.connect(self._on_inspector_delete_annotation)
        self.inspector_panel.apply_redaction_requested.connect(self._apply_redactions_menu)
        self.inspector_panel.color_adjusted.connect(self._on_inspector_color_adjusted)
        self.inspector_panel.color_reset_requested.connect(self._on_inspector_color_reset)

    def _on_annotation_selected(self, annot):
        self.markup_bar.set_selected_annotation(annot)
        if hasattr(self, "inspector_panel"):
            self.inspector_panel.set_selected_annotation(annot)
            if annot is not None and not self.inspector_panel.isVisible():
                self.set_inspector_visible(True)
        self._sync_toolbar_contexts()

    def _on_document_or_annotations_modified(self):
        self._update_modified_ui()
        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            self.inspector_panel.refresh_annotations_list()

    def _on_inspector_annotation_updated(self, annot=None):
        self.canvas.update()
        self.canvas.document_modified.emit(True)
        self._update_modified_ui()

    def _on_inspector_delete_annotation(self, annot):
        if not self.document:
            return
        annots = self.canvas.annotations.get(self.canvas.current_page, [])
        if annot in annots:
            annots.remove(annot)
        if getattr(self.canvas, "_selected_annotation", None) == annot:
            self.canvas._selected_annotation = None
        self.canvas.update()
        self.markup_bar.set_selected_annotation(None)
        self.inspector_panel.set_selected_annotation(None)
        self.inspector_panel.refresh_annotations_list()
        self.canvas.document_modified.emit(True)
        self._update_modified_ui()

    def _on_inspector_color_adjusted(self, new_img):
        if self.document and not self.document.is_pdf:
            self.document.update_image(new_img, self.canvas.current_page)
            self.canvas.update()
            self.canvas.document_modified.emit(True)
            self._update_modified_ui()

    def _on_inspector_color_reset(self):
        if hasattr(self.inspector_panel, "_original_image") and self.inspector_panel._original_image:
            self._on_inspector_color_adjusted(self.inspector_panel._original_image.copy())

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
        if hasattr(self, 'window_controls'):
            col = self._get_icon_color()
            self.window_controls.update_icons(col)

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.ActivationChange:
            if hasattr(self, 'traffic_cluster'):
                self.traffic_cluster.set_active_state(self.isActiveWindow())
        elif event.type() == QEvent.Type.WindowStateChange:
            self._update_window_chrome_state()
        super().changeEvent(event)

    def _get_resize_edge(self, pos: QPoint) -> Optional[Qt.Edge]:
        if not getattr(self, "is_frameless", False) or self.isMaximized():
            return None
        margin = 6
        w = self.width()
        h = self.height()
        x = pos.x()
        y = pos.y()

        left = (x <= margin)
        right = (x >= w - margin)
        top = (y <= 3)
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
        if getattr(self, "is_frameless", False) and not self.isMaximized():
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
                super().mouseMoveEvent(event)
                return
        self.unsetCursor()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent):
        self.unsetCursor()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def start_window_drag(self, event: Optional[QMouseEvent] = None) -> bool:
        """Initiate native OS window manager move (Wayland / X11 / macOS / Windows)."""
        self.unsetCursor()

        if self.isMaximized():
            self._toggle_maximize()
            QApplication.processEvents()

        win_handle = self.windowHandle()
        if not win_handle:
            self.winId()
            win_handle = self.windowHandle()

        if win_handle and hasattr(win_handle, "startSystemMove"):
            try:
                if win_handle.startSystemMove():
                    return True
            except Exception as e:
                print(f"[window] startSystemMove failed: {e}")
        return False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "is_frameless", False):
            edge = self._get_resize_edge(event.position().toPoint())
            if edge:
                win_handle = self.windowHandle()
                if win_handle and hasattr(win_handle, "startSystemResize"):
                    win_handle.startSystemResize(edge)
                    return
            elif event.position().y() <= 40:
                if self.start_window_drag(event):
                    event.accept()
                    return
        super().mousePressEvent(event)

    def _toggle_frameless_mode(self, enabled: bool):
        self.is_frameless = enabled
        if hasattr(self, 'window_controls'):
            self.window_controls.setVisible(enabled)
        elif hasattr(self, 'traffic_cluster'):
            self.traffic_cluster.setVisible(enabled)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, enabled)
        self.show()

    def _detect_system_theme(self) -> str:
        return ThemeManager.follow_system_theme()

    def _on_theme_manager_changed(self, new_theme: str):
        if self.current_theme != new_theme:
            self.current_theme = new_theme
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
            self._apply_theme(self.current_theme, animate=True)

    def _on_system_color_scheme_changed(self, scheme):
        if getattr(self, "appearance_mode", "auto") == "auto":
            target = MacTheme.DARK if scheme == Qt.ColorScheme.Dark else MacTheme.LIGHT
            if self.current_theme != target:
                self.current_theme = target
                if hasattr(self, 'theme_btn'):
                    self.theme_btn.setText("☀️" if self.current_theme == MacTheme.DARK else "🌙")
                self._apply_theme(self.current_theme, animate=True)

    def _set_appearance_mode(self, mode: str):
        self.appearance_mode = mode
        if hasattr(self, "theme_auto_act"):
            self.theme_auto_act.setChecked(mode == "auto")
        if hasattr(self, "theme_dark_act"):
            self.theme_dark_act.setChecked(mode == MacTheme.DARK)
        if hasattr(self, "theme_light_act"):
            self.theme_light_act.setChecked(mode == MacTheme.LIGHT)
        if hasattr(self, "theme_manager"):
            self.theme_manager.set_mode(mode)
            resolved = self.theme_manager.get_resolved_theme()
        else:
            resolved = ThemeManager.follow_system_theme() if mode == "auto" else mode
        if self.current_theme != resolved:
            self.current_theme = resolved
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText("")
            self._apply_theme(self.current_theme, animate=True)

    def _toggle_theme(self):
        new_mode = MacTheme.LIGHT if self.current_theme == MacTheme.DARK else MacTheme.DARK
        self._set_appearance_mode(new_mode)

    def apply_theme(self, theme_name: str, animate: bool = False):
        self._apply_theme(theme_name, animate=animate)

    def _apply_theme(self, theme_name: str, animate: bool = False):
        self.current_theme = theme_name
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
            for child, method in (
                (getattr(self, "sidebar", None),         "update_theme"),
                (getattr(self, "tab_container", None),   "update_theme"),
                (getattr(self, "markup_bar", None),      "update_theme"),
                (getattr(self, "organize_bar", None),    "update_theme"),
                (getattr(self, "inspector_panel", None), "update_theme"),
            ):
                if child is None:
                    continue
                fn = getattr(child, method, None)
                if callable(fn):
                    try:
                        fn(theme_name)
                    except Exception as e:
                        print(f"[theme] {type(child).__name__}.{method} failed: {e}")
            self._sync_toolbar_contexts()
            anim.start()
        else:
            qss = MacTheme.get_stylesheet(theme_name)
            self.setStyleSheet(qss)
            self._update_all_icons()
            self.sidebar.thumb_list.update()
            self.traffic_cluster.update()
            for child, method in (
                (getattr(self, "sidebar", None),         "update_theme"),
                (getattr(self, "tab_container", None),   "update_theme"),
                (getattr(self, "markup_bar", None),      "update_theme"),
                (getattr(self, "organize_bar", None),    "update_theme"),
                (getattr(self, "inspector_panel", None), "update_theme"),
            ):
                if child is None:
                    continue
                fn = getattr(child, method, None)
                if callable(fn):
                    try:
                        fn(theme_name)
                    except Exception as e:
                        print(f"[theme] {type(child).__name__}.{method} failed: {e}")
            self._sync_toolbar_contexts()

    def _rotate_left(self):
        if self.canvas and (self.canvas.crop_box or self.canvas._selected_annotation):
            self.canvas.rotate_selection(-90)
            return
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
        if self.canvas and (self.canvas.crop_box or self.canvas._selected_annotation):
            if self.document and self.document.is_pdf and self.canvas.crop_box and not self.canvas._selected_annotation:
                pass
            else:
                self.canvas.rotate_selection(90)
                return
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
        if self.document.is_pdf or not self.document._pil_image:
            QMessageBox.information(
                self,
                "Adjust Color",
                "Color adjustment is available only for image documents."
            )
            return

        page = self.canvas.current_page
        img = self.document._pil_image
        self._color_page = page
        self._color_initial_image = img.copy()
        self._color_last_committed = img.copy()

        if not self.color_dialog:
            self.color_dialog = AdjustColorDialog(img, self)
            self.color_dialog.adjustments_applied.connect(self._on_color_live_preview)
            self.color_dialog.adjustments_committed.connect(self._on_color_adjustments_committed)
        else:
            self.color_dialog.set_image(img)

        self.color_dialog.show()
        self.color_dialog.raise_()
        self.color_dialog.activateWindow()

    def _on_color_live_preview(self, new_img):
        if self.document and not self.document.is_pdf and hasattr(self, "_color_page"):
            self.document.update_image(new_img, self._color_page)
            self.canvas.update()

    def _on_color_adjustments_committed(self, new_img):
        if not self.document or self.document.is_pdf or not hasattr(self, "_color_page"):
            return
        page = self._color_page
        before_img = getattr(self, "_color_last_committed", self._color_initial_image).copy()
        after_img = new_img.copy()
        self._color_last_committed = after_img.copy()

        self.document.update_image(after_img, page)
        self.canvas.update()

        def undo_color():
            if self.document and not self.document.is_pdf:
                self.document.update_image(before_img, page)
                self.canvas.update()

        def redo_color():
            if self.document and not self.document.is_pdf:
                self.document.update_image(after_img, page)
                self.canvas.update()

        self.canvas.history.push(ActionCommand("Adjust Color", undo_color, redo_color))

    def _on_color_adjustments_applied(self, new_img, old_img, page):
        """Maintained for backward compatibility with direct callers/tests."""
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
        if not self.document or not self.document._pil_image or self.document.is_pdf:
            QMessageBox.information(self, "Adjust Size", "Size adjustment is available only for image documents.")
            return

        page = self.canvas.current_page
        old_img = self.document._pil_image.copy()
        file_sz = self.document.metadata.get("file_size", 0)
        if file_sz <= 0 and getattr(self.document, "file_path", None) and os.path.isfile(self.document.file_path):
            try:
                file_sz = os.path.getsize(self.document.file_path)
            except OSError:
                file_sz = 0
        dialog = AdjustSizeDialog(self.document._pil_image, file_sz, self)

        def on_size(resized):
            self.document.update_image(resized, page)
            def undo_sz():
                self.document.update_image(old_img, page)
            def redo_sz():
                self.document.update_image(resized, page)
            self.canvas.history.push(ActionCommand("Adjust Size", undo_sz, redo_sz))

        dialog.size_applied.connect(on_size)
        dialog.exec()

    def _open_batch_dialog(self):
        initial_paths = []
        if self.document and not self.document.is_pdf:
            if self.document.image_paths:
                initial_paths = list(self.document.image_paths)
            elif self.document.file_path:
                initial_paths = [self.document.file_path]
        dialog = BatchConvertDialog(image_paths=initial_paths, parent=self)
        dialog.exec()

    def _open_signature_dialog(self):
        dialog = SignatureDialog(self)
        dialog.signature_selected.connect(self._on_signature_selected)
        dialog.exec()

    def _on_signature_selected(self, sig_pixmap):
        self.canvas.active_signature_pixmap = sig_pixmap
        self.canvas.set_active_tool(AnnotationType.SIGNATURE)
        self._show_status("Click anywhere on the document to stamp your signature.")

    def _add_image_overlay(self):
        """Opens a file dialog to select an image overlay to place on the document, like Canva."""
        if not self.document:
            self._show_status("Open an image or PDF document first to add an image overlay.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Image Overlay",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.svg *.gif);;All Files (*)"
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._show_status("Failed to load image for overlay.")
            return

        self.set_markup_visible(True)
        self.canvas.add_image_overlay(pixmap)
        self._show_status("Image overlay added. Drag to reposition, resize with corner handles.")

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
            p_text = f"Page {curr} of {tot} - {int(w)} × {int(h)} pt"
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

        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            self.inspector_panel.set_document(self.document, self.canvas.current_page if self.document else 0)

    def _show_status(self, msg: str, timeout: int = 4000):
        self.page_status_label.setText(msg)
        if hasattr(self, "floating_pill") and self.floating_pill:
            self.floating_pill.show_status(msg)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def open_settings_dialog(self):
        """Opens the Studio Settings & Preferences multi-tab dialog."""
        from preview.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.settings_changed.connect(self._on_settings_applied)
        dlg.exec()

    def _on_settings_applied(self, cfg: dict):
        """Applies configuration changes immediately across the main window."""
        if "theme" in cfg:
            theme_choice = str(cfg["theme"]).lower()
            if theme_choice == "system":
                theme_choice = "auto"
            self._set_appearance_mode(theme_choice)

        if "startup_mode" in cfg:
            self.set_workspace_mode(str(cfg["startup_mode"]))

        if "default_pen_width" in cfg and hasattr(self, "markup_bar"):
            self.markup_bar.stroke_width = float(cfg["default_pen_width"])
            self.canvas.stroke_width = float(cfg["default_pen_width"])

        if "default_highlight_color" in cfg and hasattr(self, "markup_bar"):
            self.markup_bar.stroke_color = QColor(str(cfg["default_highlight_color"]))

        if "canvas_background_tone" in cfg and hasattr(self, "canvas"):
            tone = str(cfg["canvas_background_tone"])
            if tone == "Obsidian":
                self.canvas.setStyleSheet("background-color: #141518;")
            elif tone == "Charcoal":
                self.canvas.setStyleSheet("background-color: #1e2026;")
            elif tone == "Custom" and "custom_canvas_color" in cfg:
                self.canvas.setStyleSheet(f"background-color: {cfg['custom_canvas_color']};")


    def _show_help(self, page_id: str = "what-is-preview"):
        if not hasattr(self, "_help_window") or self._help_window is None:
            from preview.ui.help_window import HelpWindow
            self._help_window = HelpWindow(theme=self.current_theme, parent=self)
        else:
            self._help_window.current_theme = self.current_theme
            self._help_window._apply_theme()
        if page_id:
            self._help_window.navigate_to(page_id)
        self._help_window.show()
        self._help_window.raise_()
        self._help_window.activateWindow()

    def _show_shortcuts_guide(self):
        self._show_help(page_id="shortcuts")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F1:
            self._show_help()
            event.accept()
            return

        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_I:
                self._add_image_overlay()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V and not (hasattr(self, "search_edit") and self.search_edit.hasFocus()):
                clipboard = QApplication.clipboard()
                pixmap = clipboard.pixmap()
                if not pixmap.isNull():
                    self.set_markup_visible(True)
                    self.canvas.add_image_overlay(pixmap)
                    event.accept()
                    return
        if getattr(self, "_is_fullscreen_image", False) or getattr(self, "_is_slideshow", False) or self.isFullScreen():
            if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
                self.toggle_fullscreen(auto_advance=False)
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
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen(auto_advance=False)
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()
        if hasattr(self, "slideshow_hud") and self.slideshow_hud and self.slideshow_hud.isVisible():
            self.slideshow_hud._reposition()
            if getattr(self, "_is_fullscreen_image", False):
                self.canvas.zoom_to_fit()
        if hasattr(self, "inspector_panel") and self.inspector_panel.isVisible():
            if w < 860:
                self.set_inspector_visible(False)
        if hasattr(self, "markup_bar") and hasattr(self.markup_bar, "handle_resize"):
            self.markup_bar.handle_resize(w)

        # Responsive toolbar adaptation: collapse buttons to icon-only when narrow (< 1060px)
        if hasattr(self, "mode_view_btn") and hasattr(self, "mode_edit_btn") and hasattr(self, "mode_organize_btn"):
            if w < 1060:
                self.mode_view_btn.setText("")
                self.mode_edit_btn.setText("")
                self.mode_organize_btn.setText("")
                self.mode_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                self.mode_edit_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                self.mode_organize_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            else:
                self.mode_view_btn.setText("View")
                self.mode_edit_btn.setText("Edit")
                self.mode_organize_btn.setText("Organize")
                self.mode_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                self.mode_edit_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                self.mode_organize_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        if hasattr(self, "search_edit"):
            self.search_edit.setFixedWidth(90 if w < 1024 else 130)

        if hasattr(self, "open_btn"):
            if w < 960:
                self.open_btn.setText("")
                self.open_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            else:
                self.open_btn.setText("Open")
                self.open_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        if w < 820 and hasattr(self, "sidebar") and self.sidebar.isVisible():
            self.set_sidebar_visible(False)

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

        # If a document is already open, automatically open in a new tab
        if self.document is not None:
            if len(paths) == 1 and os.path.isdir(paths[0]):
                self.new_tab()
                self.open_folder(paths[0])
            elif len(paths) == 1:
                self.new_tab(paths[0])
            else:
                self.new_tab_files(paths)
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
        if os.environ.get("CI") or os.environ.get("PREVIEW_TESTING"):
            return
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
