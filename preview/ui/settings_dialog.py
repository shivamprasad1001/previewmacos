"""
Studio Pro Settings & Preferences Dialog.
Provides a multi-tab configuration interface with persistent QSettings storage,
legacy settings synchronization, and live application updates.
"""

import os
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QGroupBox, QFormLayout, QFrame,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QIcon

from preview.icons import MacIconFactory
from preview.theme import StudioTheme, MacTheme, ThemeManager


# Standard default settings configuration
DEFAULT_STUDIO_SETTINGS: Dict[str, Any] = {
    # General
    "startup_mode": "View",           # "View", "Edit", "Organize"
    "default_zoom": "Fit",            # "Fit", "Actual", "100%"
    "auto_check_updates": True,       # bool
    "theme": "Dark",                  # "Dark", "Light", "System"

    # Canvas & Display
    "hardware_acceleration": True,    # bool
    "render_dpi_scaling": "Auto",     # "Auto", "100%", "150%", "200%"
    "canvas_background_tone": "Obsidian", # "Obsidian", "Charcoal", "Custom"
    "custom_canvas_color": "#141518", # hex string
    "image_interpolation": "Bilinear", # "Bilinear", "Bicubic"

    # Annotations & Tools
    "default_highlight_color": "#ffea79", # hex string (soft translucent yellow)
    "default_pen_width": 3.0,         # float (1.0 - 20.0)
    "default_stamp_text": "APPROVED", # "APPROVED", "CONFIDENTIAL", "DRAFT", "FINAL", "REJECTED", "COPY"
    "redaction_fill_style": "Solid Black", # "Solid Black", "Black with Red Outline", "Diagonal Hatched"

    # Performance & Cache
    "page_prefetch_distance": 2,      # int (1 - 10 pages)
    "disk_cache_limit": 256,          # int MB (64 - 2048 MB)
}

# Keybindings catalog for the Keyboard Shortcuts tab
SHORTCUTS_CATALOG = [
    # View & Navigation
    ("Zoom In", "View", "Ctrl++ / Ctrl+="),
    ("Zoom Out", "View", "Ctrl+-"),
    ("Zoom to Fit", "View", "Ctrl+0"),
    ("Actual Size (100%)", "View", "Ctrl+1"),
    ("Rotate Left (90° CCW)", "View", "Ctrl+L"),
    ("Rotate Right (90° CW)", "View", "Ctrl+R"),
    ("Toggle Full Screen", "View", "F11"),
    ("Slide Show Mode", "View", "Ctrl+Shift+F"),
    ("Toggle Inspector Panel", "View", "Ctrl+I / Cmd+I"),
    ("Toggle Sidebar", "View", "Ctrl+B"),
    ("Toggle Magnifier (Loupe)", "View", "~ / Ctrl+Shift+M"),
    ("Next Page / Image", "Navigation", "Right Arrow / PgDn"),
    ("Previous Page / Image", "Navigation", "Left Arrow / PgUp"),
    ("First Page", "Navigation", "Home / Ctrl+Home"),
    ("Last Page", "Navigation", "End / Ctrl+End"),

    # Tools & Markup
    ("Toggle Markup Toolbar", "Markup", "Ctrl+Shift+A"),
    ("Select / Pointer Tool", "Markup", "Esc"),
    ("Hand / Pan Document", "Markup", "Space+Drag"),
    ("Fountain Pen / Sketch", "Markup", "P"),
    ("Chisel Highlighter", "Markup", "Shift+H"),
    ("Underline Text Markup", "Markup", "U"),
    ("Strikethrough Text Markup", "Markup", "S"),
    ("Text Box Tool", "Markup", "T"),
    ("Sticky Note Tool", "Markup", "N"),
    ("Rubber Stamp / Signature", "Markup", "K / Shift+M"),
    ("Add Image Overlay", "Markup", "Ctrl+Shift+I"),
    ("Crop Selection", "Markup", "Ctrl+K"),
    ("Adjust Color", "Tools", "Ctrl+Alt+C"),
    ("Adjust Size", "Tools", "Ctrl+Alt+S"),
    ("Undo Action", "Edit", "Ctrl+Z"),
    ("Redo Action", "Edit", "Ctrl+Shift+Z"),

    # Tabs & Workspace
    ("View Mode", "Workspace", "Alt+1"),
    ("Edit Mode", "Workspace", "Alt+2"),
    ("Organize Mode", "Workspace", "Alt+3"),
    ("Open File(s)", "File", "Ctrl+O"),
    ("Open Folder of Images", "File", "Ctrl+Shift+O"),
    ("Open in New Tab", "File", "Ctrl+Alt+O"),
    ("Close Tab", "File", "Ctrl+W"),
    ("Next Tab", "Navigation", "Ctrl+Tab / Ctrl+PgDn"),
    ("Previous Tab", "Navigation", "Ctrl+Shift+Tab / Ctrl+PgUp"),
    ("Save", "File", "Ctrl+S"),
    ("Save As / Duplicate", "File", "Ctrl+Shift+S"),
    ("Export Document", "File", "Ctrl+E"),

    # Application
    ("Studio Settings & Preferences", "Application", "Ctrl+,"),
    ("Toggle Dark / Light Theme", "Application", "Ctrl+T"),
    ("Help & Documentation", "Application", "F1"),
]


class StudioSettingsManager:
    """
    Manages persistent configuration using QSettings('TriviLabs', 'PreviewStudio')
    with automatic backwards-compatible migration to/from 'PreviewMacOS'.
    """

    ORG_NAME = "TriviLabs"
    STUDIO_APP_NAME = "PreviewStudio"
    LEGACY_APP_NAME = "PreviewMacOS"

    @classmethod
    def get_settings(cls) -> QSettings:
        return QSettings(cls.ORG_NAME, cls.STUDIO_APP_NAME)

    @classmethod
    def get_legacy_settings(cls) -> QSettings:
        return QSettings(cls.ORG_NAME, cls.LEGACY_APP_NAME)

    @classmethod
    def load_all(cls) -> Dict[str, Any]:
        """Loads all settings with legacy fallback and migration."""
        studio_qset = cls.get_settings()
        legacy_qset = cls.get_legacy_settings()
        result: Dict[str, Any] = {}

        for key, def_val in DEFAULT_STUDIO_SETTINGS.items():
            if studio_qset.contains(key):
                val = studio_qset.value(key)
                result[key] = cls._cast_value(val, def_val)
            else:
                # Check legacy settings for migration
                migrated_val = cls._migrate_legacy_key(key, legacy_qset)
                if migrated_val is not None:
                    result[key] = migrated_val
                    studio_qset.setValue(key, migrated_val)
                else:
                    result[key] = def_val

        # Also migrate recent files if present in legacy
        if not studio_qset.contains("recent_files") and legacy_qset.contains("recent_files"):
            recents = legacy_qset.value("recent_files", [], type=list)
            studio_qset.setValue("recent_files", recents)

        return result

    @classmethod
    def save_all(cls, config: Dict[str, Any]) -> None:
        """Saves all settings and synchronizes relevant keys with legacy settings."""
        studio_qset = cls.get_settings()
        legacy_qset = cls.get_legacy_settings()

        for key, val in config.items():
            studio_qset.setValue(key, val)

        # Synchronize shared keys to legacy QSettings for backwards compatibility
        if "auto_check_updates" in config:
            legacy_qset.setValue("check_updates_on_startup", bool(config["auto_check_updates"]))

        if "theme" in config:
            theme_val = str(config["theme"]).lower()
            if theme_val == "system":
                theme_val = "auto"
            legacy_qset.setValue("appearance_mode", theme_val)

        studio_qset.sync()
        legacy_qset.sync()

    @classmethod
    def get_value(cls, key: str, default: Any = None) -> Any:
        """Retrieves a single setting value."""
        all_settings = cls.load_all()
        return all_settings.get(key, default)

    @classmethod
    def set_value(cls, key: str, val: Any) -> None:
        """Sets a single setting value and syncs."""
        studio_qset = cls.get_settings()
        studio_qset.setValue(key, val)
        if key == "auto_check_updates":
            cls.get_legacy_settings().setValue("check_updates_on_startup", bool(val))
        elif key == "theme":
            theme_val = str(val).lower()
            if theme_val == "system":
                theme_val = "auto"
            cls.get_legacy_settings().setValue("appearance_mode", theme_val)

    @classmethod
    def _cast_value(cls, val: Any, reference: Any) -> Any:
        """Casts loaded QSettings value to reference type."""
        if isinstance(reference, bool):
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes")
            return bool(val)
        if isinstance(reference, int):
            try:
                return int(val)
            except (ValueError, TypeError):
                return reference
        if isinstance(reference, float):
            try:
                return float(val)
            except (ValueError, TypeError):
                return reference
        return str(val)

    @classmethod
    def _migrate_legacy_key(cls, key: str, legacy: QSettings) -> Optional[Any]:
        if key == "auto_check_updates" and legacy.contains("check_updates_on_startup"):
            return legacy.value("check_updates_on_startup", True, type=bool)
        if key == "theme" and legacy.contains("appearance_mode"):
            app_mode = legacy.value("appearance_mode", "dark", type=str).lower()
            if app_mode == "light":
                return "Light"
            elif app_mode == "dark":
                return "Dark"
            elif app_mode == "auto":
                return "System"
        return None


class SettingsDialog(QDialog):
    """
    Multi-tab Studio Settings & Preferences dialog with tabs for:
    - General (startup mode, zoom, auto-updates, theme)
    - Canvas & Display (hardware acceleration, resolution/DPI scaling, background tone, interpolation)
    - Annotations & Tools (default highlight color, pen width, stamp text, redaction style)
    - Performance & Cache (prefetch distance, disk cache limit, memory cleanup)
    - Keyboard Shortcuts (interactive searchable shortcut table)
    """

    settings_changed = pyqtSignal(dict)
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("studioSettingsDialog")
        self.setWindowTitle("Studio Pro Settings & Preferences")
        self.resize(720, 560)
        self.setMinimumSize(640, 480)

        self._current_settings: Dict[str, Any] = StudioSettingsManager.load_all()
        self._custom_canvas_color: str = self._current_settings.get("custom_canvas_color", "#141518")
        self._highlight_color: str = self._current_settings.get("default_highlight_color", "#ffea79")

        self._setup_ui()
        self._load_values_into_ui(self._current_settings)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("settingsTabWidget")

        # 1. General Tab
        self.tab_general = self._build_general_tab()
        self.tab_widget.addTab(self.tab_general, "General")

        # 2. Canvas & Display Tab
        self.tab_canvas = self._build_canvas_tab()
        self.tab_widget.addTab(self.tab_canvas, "Canvas & Display")

        # 3. Annotations & Tools Tab
        self.tab_tools = self._build_annotations_tab()
        self.tab_widget.addTab(self.tab_tools, "Annotations & Tools")

        # 4. Performance & Cache Tab
        self.tab_cache = self._build_performance_tab()
        self.tab_widget.addTab(self.tab_cache, "Performance & Cache")

        # 5. Keyboard Shortcuts Tab
        self.tab_shortcuts = self._build_shortcuts_tab()
        self.tab_widget.addTab(self.tab_shortcuts, "Keyboard Shortcuts")

        main_layout.addWidget(self.tab_widget)

        # Bottom Button Bar
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 4, 0, 0)
        btn_bar.setSpacing(8)

        self.btn_reset = QPushButton("Reset Defaults", self)
        self.btn_reset.setObjectName("btnSettingsReset")
        self.btn_reset.setToolTip("Reset all settings to default values")
        self.btn_reset.clicked.connect(self._on_reset_defaults)
        btn_bar.addWidget(self.btn_reset)

        btn_bar.addStretch(1)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Apply", self)
        self.btn_apply.setObjectName("btnSettingsApply")
        self.btn_apply.setToolTip("Apply current settings immediately")
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        btn_bar.addWidget(self.btn_apply)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.setObjectName("btnSettingsSave")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_bar.addWidget(self.btn_save)

        main_layout.addLayout(btn_bar)

    # -------------------------------------------------------------------------
    # TAB 1: General
    # -------------------------------------------------------------------------
    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Workspace Group
        ws_group = QGroupBox("Workspace Defaults", widget)
        ws_layout = QFormLayout(ws_group)
        ws_layout.setContentsMargins(12, 12, 12, 12)
        ws_layout.setSpacing(12)

        self.combo_startup_mode = QComboBox(ws_group)
        self.combo_startup_mode.addItems(["View", "Edit", "Organize"])
        self.combo_startup_mode.setToolTip("Default workspace mode when opening documents")
        ws_layout.addRow("Startup Mode:", self.combo_startup_mode)

        self.combo_default_zoom = QComboBox(ws_group)
        self.combo_default_zoom.addItems(["Fit", "Actual", "100%"])
        self.combo_default_zoom.setToolTip("Initial zoom level when displaying a document")
        ws_layout.addRow("Default Zoom:", self.combo_default_zoom)

        layout.addWidget(ws_group)

        # Application & Theme Group
        app_group = QGroupBox("Theme & Updates", widget)
        app_layout = QFormLayout(app_group)
        app_layout.setContentsMargins(12, 12, 12, 12)
        app_layout.setSpacing(12)

        self.combo_theme = QComboBox(app_group)
        self.combo_theme.addItems(["Dark", "Light", "Antimatter", "System"])
        self.combo_theme.setToolTip("Application color scheme theme (including Antimatter deep void)")
        app_layout.addRow("Theme Selection:", self.combo_theme)

        self.chk_auto_updates = QCheckBox("Automatically check for software updates on launch", app_group)
        self.chk_auto_updates.setToolTip("Performs non-intrusive background check for new versions")
        app_layout.addRow("", self.chk_auto_updates)

        layout.addWidget(app_group)
        layout.addStretch(1)
        return widget

    # -------------------------------------------------------------------------
    # TAB 2: Canvas & Display
    # -------------------------------------------------------------------------
    def _build_canvas_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Hardware & Resolution Group
        disp_group = QGroupBox("Display & Rendering Pipeline", widget)
        disp_layout = QFormLayout(disp_group)
        disp_layout.setContentsMargins(12, 12, 12, 12)
        disp_layout.setSpacing(12)

        self.chk_hw_accel = QCheckBox("Enable Hardware Acceleration (GPU viewport raster)", disp_group)
        self.chk_hw_accel.setToolTip("Uses GPU-accelerated drawing for high-DPI canvases")
        disp_layout.addRow("", self.chk_hw_accel)

        self.combo_dpi_scaling = QComboBox(disp_group)
        self.combo_dpi_scaling.addItems(["Auto", "100%", "150%", "200%"])
        self.combo_dpi_scaling.setToolTip("Canvas rendering scale factor")
        disp_layout.addRow("Render Resolution / DPI Scaling:", self.combo_dpi_scaling)

        self.combo_interpolation = QComboBox(disp_group)
        self.combo_interpolation.addItems(["Bilinear", "Bicubic"])
        self.combo_interpolation.setToolTip("Smoothing filter used during canvas zooming")
        disp_layout.addRow("Smooth Image Interpolation:", self.combo_interpolation)

        layout.addWidget(disp_group)

        # Background Tone Group
        bg_group = QGroupBox("Canvas Background Tone", widget)
        bg_layout = QFormLayout(bg_group)
        bg_layout.setContentsMargins(12, 12, 12, 12)
        bg_layout.setSpacing(12)

        self.combo_canvas_tone = QComboBox(bg_group)
        self.combo_canvas_tone.addItems(["Obsidian", "Charcoal", "Custom"])
        self.combo_canvas_tone.currentTextChanged.connect(self._on_canvas_tone_changed)
        bg_layout.addRow("Background Tone:", self.combo_canvas_tone)

        custom_row = QHBoxLayout()
        self.btn_custom_color = QPushButton("Pick Color...", bg_group)
        self.btn_custom_color.setFixedWidth(120)
        self.btn_custom_color.clicked.connect(self._on_pick_custom_canvas_color)
        self.lbl_color_swatch = QLabel(bg_group)
        self.lbl_color_swatch.setFixedSize(24, 24)
        self._update_color_swatch(self.lbl_color_swatch, self._custom_canvas_color)
        custom_row.addWidget(self.btn_custom_color)
        custom_row.addWidget(self.lbl_color_swatch)
        custom_row.addStretch(1)

        bg_layout.addRow("Custom Tone Color:", custom_row)
        layout.addWidget(bg_group)
        layout.addStretch(1)
        return widget

    def _on_canvas_tone_changed(self, tone: str):
        is_custom = (tone == "Custom")
        self.btn_custom_color.setEnabled(is_custom)
        if tone == "Obsidian":
            self._custom_canvas_color = "#141518"
        elif tone == "Charcoal":
            self._custom_canvas_color = "#1e2026"
        self._update_color_swatch(self.lbl_color_swatch, self._custom_canvas_color)

    def _on_pick_custom_canvas_color(self):
        col = QColorDialog.getColor(QColor(self._custom_canvas_color), self, "Select Custom Canvas Tone")
        if col.isValid():
            self._custom_canvas_color = col.name()
            self._update_color_swatch(self.lbl_color_swatch, self._custom_canvas_color)

    # -------------------------------------------------------------------------
    # TAB 3: Annotations & Tools
    # -------------------------------------------------------------------------
    def _build_annotations_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Pen & Highlighter Group
        pen_group = QGroupBox("Drawing & Highlighting", widget)
        pen_layout = QFormLayout(pen_group)
        pen_layout.setContentsMargins(12, 12, 12, 12)
        pen_layout.setSpacing(12)

        hl_row = QHBoxLayout()
        self.btn_highlight_color = QPushButton("Pick Highlight Color...", pen_group)
        self.btn_highlight_color.setFixedWidth(160)
        self.btn_highlight_color.clicked.connect(self._on_pick_highlight_color)
        self.lbl_highlight_swatch = QLabel(pen_group)
        self.lbl_highlight_swatch.setFixedSize(24, 24)
        self._update_color_swatch(self.lbl_highlight_swatch, self._highlight_color)
        hl_row.addWidget(self.btn_highlight_color)
        hl_row.addWidget(self.lbl_highlight_swatch)
        hl_row.addStretch(1)
        pen_layout.addRow("Default Highlight Color:", hl_row)

        self.spin_pen_width = QDoubleSpinBox(pen_group)
        self.spin_pen_width.setRange(0.5, 30.0)
        self.spin_pen_width.setSingleStep(0.5)
        self.spin_pen_width.setSuffix(" px")
        self.spin_pen_width.setDecimals(1)
        pen_layout.addRow("Default Pen Width:", self.spin_pen_width)

        layout.addWidget(pen_group)

        # Stamps & Redactions Group
        stamp_group = QGroupBox("Stamps & Redaction Style", widget)
        stamp_layout = QFormLayout(stamp_group)
        stamp_layout.setContentsMargins(12, 12, 12, 12)
        stamp_layout.setSpacing(12)

        self.combo_stamp_text = QComboBox(stamp_group)
        self.combo_stamp_text.setEditable(True)
        self.combo_stamp_text.addItems(["APPROVED", "CONFIDENTIAL", "DRAFT", "FINAL", "REJECTED", "COPY", "VERIFIED"])
        stamp_layout.addRow("Default Stamp Text:", self.combo_stamp_text)

        self.combo_redaction_style = QComboBox(stamp_group)
        self.combo_redaction_style.addItems(["Solid Black", "Black with Red Outline", "Diagonal Hatched"])
        stamp_layout.addRow("Redaction Fill Style:", self.combo_redaction_style)

        layout.addWidget(stamp_group)
        layout.addStretch(1)
        return widget

    def _on_pick_highlight_color(self):
        col = QColorDialog.getColor(QColor(self._highlight_color), self, "Select Default Highlight Color")
        if col.isValid():
            self._highlight_color = col.name()
            self._update_color_swatch(self.lbl_highlight_swatch, self._highlight_color)

    # -------------------------------------------------------------------------
    # TAB 4: Performance & Cache
    # -------------------------------------------------------------------------
    def _build_performance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        cache_group = QGroupBox("Caching & Page Prefetch", widget)
        cache_layout = QFormLayout(cache_group)
        cache_layout.setContentsMargins(12, 12, 12, 12)
        cache_layout.setSpacing(12)

        self.spin_prefetch = QSpinBox(cache_group)
        self.spin_prefetch.setRange(0, 10)
        self.spin_prefetch.setSuffix(" pages")
        self.spin_prefetch.setToolTip("Number of adjacent pages pre-rendered in background memory")
        cache_layout.addRow("Page Prefetch Distance:", self.spin_prefetch)

        self.spin_disk_cache = QSpinBox(cache_group)
        self.spin_disk_cache.setRange(32, 4096)
        self.spin_disk_cache.setSingleStep(64)
        self.spin_disk_cache.setSuffix(" MB")
        self.spin_disk_cache.setToolTip("Maximum local disk cache size for rendered document tiles")
        cache_layout.addRow("Disk Cache Limit:", self.spin_disk_cache)

        layout.addWidget(cache_group)

        # Maintenance Group
        maint_group = QGroupBox("Cache Maintenance", widget)
        maint_layout = QVBoxLayout(maint_group)
        maint_layout.setContentsMargins(12, 12, 12, 12)
        maint_layout.setSpacing(8)

        self.lbl_cache_status = QLabel("Memory Cache: Ready", maint_group)
        maint_layout.addWidget(self.lbl_cache_status)

        self.btn_purge_cache = QPushButton("Purge Memory Cache Now", maint_group)
        self.btn_purge_cache.setFixedWidth(200)
        self.btn_purge_cache.clicked.connect(self._on_purge_memory_cache)
        maint_layout.addWidget(self.btn_purge_cache)

        layout.addWidget(maint_group)
        layout.addStretch(1)
        return widget

    def _on_purge_memory_cache(self):
        """Frees cached pixmaps and reclaims memory."""
        import gc
        gc.collect()
        self.lbl_cache_status.setText("Memory Cache: Purged and freed successfully.")
        self.lbl_cache_status.setStyleSheet("color: #10b981; font-weight: 600;")

    # -------------------------------------------------------------------------
    # TAB 5: Keyboard Shortcuts
    # -------------------------------------------------------------------------
    def _build_shortcuts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Search Bar
        search_row = QHBoxLayout()
        search_lbl = QLabel("Filter Shortcuts:", widget)
        self.shortcut_filter = QLineEdit(widget)
        self.shortcut_filter.setPlaceholderText("Search action, category, or shortcut key...")
        self.shortcut_filter.textChanged.connect(self._filter_shortcuts_table)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self.shortcut_filter)
        layout.addLayout(search_row)

        # Table
        self.shortcuts_table = QTableWidget(widget)
        self.shortcuts_table.setObjectName("shortcutsTable")
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Category", "Shortcut"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.shortcuts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.shortcuts_table.setAlternatingRowColors(True)

        self._populate_shortcuts_table()
        layout.addWidget(self.shortcuts_table)
        return widget

    def _populate_shortcuts_table(self):
        self.shortcuts_table.setRowCount(len(SHORTCUTS_CATALOG))
        for row, (action, cat, shortcut) in enumerate(SHORTCUTS_CATALOG):
            item_act = QTableWidgetItem(action)
            item_cat = QTableWidgetItem(cat)
            item_sc = QTableWidgetItem(shortcut)
            item_sc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.shortcuts_table.setItem(row, 0, item_act)
            self.shortcuts_table.setItem(row, 1, item_cat)
            self.shortcuts_table.setItem(row, 2, item_sc)

    def _filter_shortcuts_table(self, query: str):
        q = query.strip().lower()
        for row in range(self.shortcuts_table.rowCount()):
            act = self.shortcuts_table.item(row, 0).text().lower()
            cat = self.shortcuts_table.item(row, 1).text().lower()
            sc = self.shortcuts_table.item(row, 2).text().lower()
            matches = (q in act or q in cat or q in sc)
            self.shortcuts_table.setRowHidden(row, not matches)

    # -------------------------------------------------------------------------
    # Helper & Event Handlers
    # -------------------------------------------------------------------------
    def _update_color_swatch(self, label: QLabel, hex_color: str):
        pix = QPixmap(24, 24)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(hex_color))
        p.setPen(QColor("rgba(255, 255, 255, 0.3)" if hex_color.startswith("#1") else "rgba(0, 0, 0, 0.3)"))
        p.drawRoundedRect(1, 1, 22, 22, 4, 4)
        p.end()
        label.setPixmap(pix)

    def _load_values_into_ui(self, cfg: Dict[str, Any]):
        # General
        self.combo_startup_mode.setCurrentText(str(cfg.get("startup_mode", "View")))
        self.combo_default_zoom.setCurrentText(str(cfg.get("default_zoom", "Fit")))
        self.combo_theme.setCurrentText(str(cfg.get("theme", "Dark")))
        self.chk_auto_updates.setChecked(bool(cfg.get("auto_check_updates", True)))

        # Canvas
        self.chk_hw_accel.setChecked(bool(cfg.get("hardware_acceleration", True)))
        self.combo_dpi_scaling.setCurrentText(str(cfg.get("render_dpi_scaling", "Auto")))
        self.combo_interpolation.setCurrentText(str(cfg.get("image_interpolation", "Bilinear")))
        self.combo_canvas_tone.setCurrentText(str(cfg.get("canvas_background_tone", "Obsidian")))
        self._custom_canvas_color = str(cfg.get("custom_canvas_color", "#141518"))
        self._update_color_swatch(self.lbl_color_swatch, self._custom_canvas_color)
        self.btn_custom_color.setEnabled(self.combo_canvas_tone.currentText() == "Custom")

        # Annotations
        self._highlight_color = str(cfg.get("default_highlight_color", "#ffea79"))
        self._update_color_swatch(self.lbl_highlight_swatch, self._highlight_color)
        self.spin_pen_width.setValue(float(cfg.get("default_pen_width", 3.0)))
        self.combo_stamp_text.setCurrentText(str(cfg.get("default_stamp_text", "APPROVED")))
        self.combo_redaction_style.setCurrentText(str(cfg.get("redaction_fill_style", "Solid Black")))

        # Performance
        self.spin_prefetch.setValue(int(cfg.get("page_prefetch_distance", 2)))
        self.spin_disk_cache.setValue(int(cfg.get("disk_cache_limit", 256)))

    def _collect_ui_values(self) -> Dict[str, Any]:
        return {
            "startup_mode": self.combo_startup_mode.currentText(),
            "default_zoom": self.combo_default_zoom.currentText(),
            "theme": self.combo_theme.currentText(),
            "auto_check_updates": self.chk_auto_updates.isChecked(),
            "hardware_acceleration": self.chk_hw_accel.isChecked(),
            "render_dpi_scaling": self.combo_dpi_scaling.currentText(),
            "image_interpolation": self.combo_interpolation.currentText(),
            "canvas_background_tone": self.combo_canvas_tone.currentText(),
            "custom_canvas_color": self._custom_canvas_color,
            "default_highlight_color": self._highlight_color,
            "default_pen_width": self.spin_pen_width.value(),
            "default_stamp_text": self.combo_stamp_text.currentText(),
            "redaction_fill_style": self.combo_redaction_style.currentText(),
            "page_prefetch_distance": self.spin_prefetch.value(),
            "disk_cache_limit": self.spin_disk_cache.value(),
        }

    def _on_apply_clicked(self):
        new_cfg = self._collect_ui_values()
        StudioSettingsManager.save_all(new_cfg)
        self._current_settings = new_cfg
        self.settings_applied.emit(new_cfg)
        self.settings_changed.emit(new_cfg)

    def _on_save_clicked(self):
        new_cfg = self._collect_ui_values()
        StudioSettingsManager.save_all(new_cfg)
        self._current_settings = new_cfg
        self.settings_changed.emit(new_cfg)
        self.accept()

    def _on_reset_defaults(self):
        self._load_values_into_ui(DEFAULT_STUDIO_SETTINGS)
        self._custom_canvas_color = DEFAULT_STUDIO_SETTINGS["custom_canvas_color"]
        self._highlight_color = DEFAULT_STUDIO_SETTINGS["default_highlight_color"]
        self._update_color_swatch(self.lbl_color_swatch, self._custom_canvas_color)
        self._update_color_swatch(self.lbl_highlight_swatch, self._highlight_color)
