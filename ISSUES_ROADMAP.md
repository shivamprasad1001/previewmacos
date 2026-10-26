# Feature & Improvement Issues Roadmap

This document outlines the prioritized issues and features planned for Preview macOS.

---

## Issue #1: [Feature] Multi-Tab Document Interface (macOS-style Window Tabs)
**Labels:** `enhancement`, `ui`, `workflow`

### Description
Real macOS Preview allows opening multiple documents (PDFs, images) as tabs within a single window, rather than forcing separate windows for every file.

### Proposed Implementation
- Add a styled `QTabBar` below the unified toolbar with macOS-style close buttons (`x`), tab reordering, and dirty state indicators.
- Support `Ctrl+T` (New Tab), `Ctrl+W` (Close Active Tab), and `Ctrl+Tab` / `Ctrl+Shift+Tab` to cycle tabs.
- Each tab maintains independent zoom levels, active page index, scroll position, and undo/redo stacks.

### Acceptance Criteria
- [ ] Implement macOS tab bar widget with smooth active indicator.
- [ ] Support dragging tabs to reorder.
- [ ] Handle independent document states (zoom, active page, undo history) per tab.
- [ ] Add menu items: **View > Show Tab Bar**, **File > New Tab**, **File > Close Tab**.

---

## Issue #2: [Feature] Magnifier Loupe Tool & Speech Bubble Callout
**Labels:** `enhancement`, `markup`, `graphics`

### Description
macOS Preview features a signature **Magnifier Loupe** annotation (a circular magnifying glass that enlarges whatever is underneath) and a **Speech Bubble / Callout** shape with an adjustable pointer tail.

### Proposed Implementation
- **Loupe Tool:** A circular vector item with magnification factor (1.5x–3x) that draws a magnified clip of the underlying page and has a thickness handle.
- **Callout Tool:** Speech bubble shape with a movable control point for the bubble tail.

### Acceptance Criteria
- [ ] Add Loupe annotation item in `preview/core/annotations.py` and `preview/ui/canvas.py`.
- [ ] Add Callout bubble with bezier or triangular tail anchor.
- [ ] Add toolbar icons to the secondary markup bar.
- [ ] Ensure baked PDF export handles Loupe magnification and callout shapes.

---

## Issue #3: [Packaging] AppImage and Flatpak Distribution Support
**Labels:** `packaging`, `linux`, `enhancement`

### Description
Currently, Linux users on non-Debian distributions (Arch Linux, Fedora, openSUSE, Manjaro) cannot easily install the `.deb` package.

### Proposed Implementation
- Add an `AppImage` build script (`build_appimage.sh`) using `appimagetool` or `linuxdeploy`.
- Add Flatpak manifest (`io.github.shivamprasad1001.Preview.yaml`) for Flathub submission.

### Acceptance Criteria
- [ ] Create `build_appimage.sh` for portable, single-file Linux execution.
- [ ] Add AppImage build step to `.github/workflows/build_releases.yml`.
- [ ] Test on Fedora and Arch Linux environments.

---

## Issue #4: [Performance] Page Prefetching & Eviction for Large 500+ Page Documents
**Labels:** `performance`, `core`, `memory`

### Description
When viewing large books or documentation (500–2,000 pages), rendering all thumbnails or keeping high-resolution cached pixmaps in memory can cause high RAM usage.

### Proposed Implementation
- Implement an LRU cache with memory limits (e.g., maximum 50 cached high-DPI full-page pixmaps).
- Add smart prefetching: automatically render page $N-1$ and $N+1$ in a background `QThread` when page $N$ is viewed.

### Acceptance Criteria
- [ ] Add memory-bounded LRU cache to `preview/core/document.py`.
- [ ] Prefetch adjacent pages in worker thread for instant page turning.
- [ ] Benchmark memory footprint with a 1,000-page PDF.

---

## Issue #5: [Feature] Batch Image Resizing & Format Conversion
**Labels:** `enhancement`, `tools`, `images`

### Description
macOS Preview allows selecting multiple images in the sidebar or opening a folder and batch exporting them (e.g. converting 50 PNGs to WebP/JPEG, or scaling all images by percentage).

### Proposed Implementation
- Add **Tools > Batch Resize / Convert Images...** dialog.
- Options: Target format (JPEG, PNG, WebP, TIFF), dimensions (Scale %, max width/height), and output quality.

### Acceptance Criteria
- [ ] Build batch conversion dialog UI matching macOS design tokens.
- [ ] Multithreaded batch processing with progress dialog.
- [ ] Preserve EXIF metadata option.

---

## Issue #6: [UI] System Dark/Light Theme Auto-Detection
**Labels:** `ui`, `theme`, `polish`

### Description
Currently, theme switching is manual. The app should automatically match the system appearance on startup and when the desktop theme changes (GNOME `org.freedesktop.appearance-color-scheme`, KDE, or Windows dark mode registry).

### Proposed Implementation
- Listen to `QGuiApplication.styleHints().colorSchemeChanged`.
- Fallback to reading `gsettings get org.gnome.desktop.interface color-scheme` on Linux.

### Acceptance Criteria
- [x] Implement `ThemeManager.follow_system_theme()` in `preview/theme.py`.
- [x] Add "Auto (System Default)" option to View > Appearance menu.

---

## Issue #7: [Feature] "Reduce File Size" PDF Compression Filter
**Labels:** `enhancement`, `pdf`, `tools`

### Description
One of the most frequently used features in macOS Preview is **File > Export... > Quartz Filter: Reduce File Size**.

### Proposed Implementation
- Downsample embedded images (e.g. to 150 DPI or re-encode high-res JPEGs with optimized compression).
- Strip redundant font subsets and unused objects using PyMuPDF's `garbage=4, deflate=True, clean=True` parameters.

### Acceptance Criteria
- [ ] Add "Reduce File Size" preset to `preview/ui/export_dialog.py`.
- [ ] Provide before/after size estimation.
