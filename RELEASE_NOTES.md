# Preview macOS v1.6.0 Release Notes

Welcome to **Preview macOS v1.6.0**! This major milestone delivers six high-priority features: native macOS-style Multi-Tab document interface, interactive Magnifier Loupe and Callout bubble annotations, bounded LRU cache with background page prefetching for 500+ page documents, multithreaded batch image resizing and format conversion, system dark/light theme auto-detection, and the 'Reduce File Size' Quartz PDF compression filter.

---

### 🌟 What's New in v1.6.0

#### 📑 Multi-Tab Document Interface (macOS-Style Window Tabs)
* **Isolated Per-Tab State:** Open multiple PDF documents and images within a single unified window. Each tab independently preserves its active page, zoom ratio, pan offset, annotations, and undo/redo history.
* **macOS Window Tabs (`MacTabBarContainer`):** Authentic tab bar with drag-to-reorder, close buttons (`×`), and dirty state indicators (`●`).
* **Open File in New Tab:** When opening or dragging files while a document is open, Preview offers the option to open in a new tab or replace the current document.
* **Keyboard Shortcuts:** `Ctrl+T` (New Tab), `Ctrl+W` (Close Tab), `Ctrl+Shift+W` (Close Window), `Ctrl+Tab` (Next Tab), `Ctrl+Shift+Tab` (Previous Tab), `Ctrl+Shift+T` (Toggle Tab Bar).

#### 🔍 Magnifier Loupe Tool & Speech Bubble Callout
* **Interactive Magnifier Loupe:** Circular magnifying glass annotation enlarging the document pixels underneath in real-time (1.2x to 5.0x zoom) with interactive magnification handle.
* **Speech Bubble Callout:** Curved dialogue bubble with text wrapping and an adjustable anchor pointer tail to spotlight specific sections or data spikes.
* **High-DPI Vector & PDF Baking:** High-fidelity rasterization and vector rendering when exporting or saving to PDF.

#### ⚡ Page Prefetching & LRU Eviction (500+ Page Support)
* **Bounded LRU Memory Cache:** Implemented strict memory bounding (default 50 rendered pages / ~64MB) preventing memory exhaustion or sluggishness on massive 500+ page documents.
* **Directional Background Prefetching:** Dedicated `PagePrefetchWorker` thread renders adjacent pages ($\pm 2$) in anticipation of scrolling for zero-latency page flips.

#### 🔄 Batch Image Resizing & Format Conversion
* **Multi-Threaded Conversion Sheet:** Accessible via `File > Batch Process Images...`, supporting batch processing across PNG, JPEG, WebP, TIFF, and BMP formats.
* **Dimension Scaling Options:** Scale by percentage, constrain to max bounding dimensions (`1920 × 1080`), or fit within bounding boxes while preserving EXIF metadata.

#### 🌓 System Dark/Light Theme Auto-Detection
* **Desktop Environment Integration:** Auto-detects system dark/light mode across GNOME, KDE Plasma, and FreeDesktop D-Bus settings (`colorSchemeChanged`, `gsettings`, `kreadconfig6`).
* **Theme Menu:** Added `Theme > Auto (System)` alongside manual Dark and Light mode toggles with live vector icon adaptation.

#### 🗜️ 'Reduce File Size' PDF Compression Filter
* **Native Quartz Filter:** Integrated directly into the macOS Export Dialog (`File > Export...`).
* **Intelligent Downsampling:** Downsamples high-res images to custom DPI, re-compresses streams with optimized JPEG quality, deflates object streams, and cleans unused PDF objects.
* **Live Reduction Estimation:** Real-time feedback calculating before/after byte sizes and percentage savings.

---

# Preview macOS v1.4.0 Release Notes

Welcome to **Preview macOS v1.4.0**! This release brings major enhancements to toolbar controls, authentic macOS segmented styling, advanced selection tools (true Oval and Lasso crop/cut with transparency masking), rich font styling, and live color palettes.

---

### 💖 A Sincere Note of Thanks
A heartfelt thank you to all our users, contributors, and testers! Your feedback, screenshots, feature requests, and issue reports continue to drive Preview macOS closer to 100% pixel-perfect parity with Apple Preview. We couldn't build this without your passion and dedication to open-source excellence!

---

### 🌟 What's New

#### 🗂️ Segmented Open Button `[ 📁 Open | ▼ ]`
* **Direct Open Action:** Clicking the primary "Open" segment directly opens the file browser dialog (<kbd>Ctrl</kbd>+<kbd>O</kbd>).
* **Dedicated Dropdown Menu:** Clicking the downward arrow segment `▼` reveals instant options to **Open File(s)...** or **Open Folder of Images...** (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>O</kbd>).
* **Authentic macOS Styling:** Pixel-perfect rounded borders, subtle divider line, and hover feedback matching macOS Big Sur / Sonoma design standards.

#### ✂️ Advanced Selection & Cut Tools (Rectangle, Oval, Lasso)
* **Dropdown Selection Tool:** The selection button is now a dropdown menu offering:
  * **Rectangular Selection**
  * **Oval / Elliptical Selection**
  * **Lasso Selection** (freehand polygon tracing)
* **True Oval & Lasso Cropping with Alpha Masking:**
  * Cropping an elliptical selection now automatically cuts out the oval shape and creates a transparent background outside the ellipse.
  * Cropping a lasso selection creates a clean polygon cutout with a transparent background.
* **Selection Cut & Clear (`Delete` / `Backspace`):**
  * Pressing <kbd>Delete</kbd> or <kbd>Backspace</kbd> with an active selection cuts and erases that area to transparent pixels.
* **Copy Selection to Clipboard (`Ctrl`+`C` / `Ctrl`+`X`):**
  * Copying an active oval or lasso selection transfers the transparently masked image directly to the system clipboard.
* **Outside Selection Dimming:** The canvas now smoothly dims the area outside any active selection box or polygon, making the target area pop out cleanly.

#### 🎨 Quick macOS Color Palettes
* **Stroke & Fill Color Dropdowns:** Both color buttons now feature a color swatch preview with a dropdown arrow `[ Swatch | ▼ ]`.
* **Instant Preset Palette:** Quick access to 11 macOS standard colors (Red, Orange, Yellow, Green, Cyan, Blue, Purple, Pink, Black, Gray, White), plus **No Fill (Transparent)** and **Show Colors...** for custom color wheel selection.
* **Live Annotation Updates:** Selecting a color immediately updates any currently highlighted annotation on the canvas.

#### 🔤 Rich Font Formatting
* **Text Controls Toolbar:** Added dedicated controls for **Font Size** (`QSpinBox`), **Font Family** (`QFontComboBox`), **Bold (`B`)**, **Italic (`I`)**, and **Underline (`U`)**.
* **Text Options Dropdown `[ A | ▼ ]`:** Instant menu to switch text alignment (**Align Left**, **Align Center**, **Align Right**) and select quick font size presets (10pt to 64pt).
* **Rich Text Rendering:** Canvas text annotations render with exact bold, italic, underline, and alignment styles.

#### 🖌️ Icon Redesign & Dropdown Indicators
* **SF Symbols Apple Pencil:** Redesigned the markup toolbar toggle icon to match Apple's authentic circular pencil tip symbol.
* **Crisp Dropdown Indicators:** Vector-rendered anti-aliased downward arrow triangles `▼` across all tool dropdowns.

---

### 🐛 Bug Fixes & Refinements
* **Fixed Selection Tool Behavior:** Fixed Oval and Lasso tools previously drawing vector shapes instead of creating selection/cut regions.
* **Fixed Color Adjustment Glitches:** Resolved issue where image color adjustments could cause temporary zoom out or intermediate display glitches during slider dragging.
* **Fixed Secondary Window Mobility:** Secondary tool dialogs (Adjust Color, Adjust Size, Inspector) can now be freely repositioned and resized without layout locks.
* **Expanded Test Suite:** Added comprehensive automated verification tests for segmented open controls, selection modes, and alpha crop masking (40 test cases passing).

---

# Preview macOS v1.3.1 Release Notes

Welcome to **Preview macOS v1.3.1**! This patch release addresses a critical standalone packaging and startup failure encountered in the v1.3.0 release binaries.

---

### 🐛 Critical Packaging & Startup Fixes
* **Resolved PyMuPDF 2.0 Startup Crash:** Fixed `FileNotFoundError: No such file or directory: '.../pymupdf/layout/resources/onnx/layout_rf2.4.1+imf1.yaml'` when launching packaged release builds (`.deb` and Windows `.exe`).
* **Dependency Version Constraints:** Capped `pymupdf>=1.24.0,<2.0.0` in `requirements.txt` to prevent automatic retrieval of PyMuPDF 2.0 and its unneeded ONNX layout models.
* **Full PyInstaller Asset Bundling:** Added `--collect-all pymupdf` across all build specifications and GitHub Actions CI pipelines to ensure all PyMuPDF native shared libraries, package metadata, and resources are bundled without missing dependencies.

---

# Preview macOS v1.3.0 Release Notes

Welcome to **Preview macOS v1.3.0**! This major release delivers full parity with Apple macOS Preview for PDF viewing, interactive forms, annotation baking, multi-page layouts, and sidebar management.

---

### 📄 Interactive PDF Viewing & Text Selection
* **Vector Text Selection:** Click and drag across PDF text with authentic macOS translucent blue selection highlights.
* **Double-Click & Select All:** Double-click any word or press <kbd>Ctrl</kbd>+<kbd>A</kbd> to select all text on the active page.
* **Copy to Clipboard:** Copy selected text with <kbd>Ctrl</kbd>+<kbd>C</kbd> or via the context menu.
* **Text Selection Shortcuts:** Right-click selected text to immediately **Highlight**, **Redact**, or **Strikethrough**.
* **Clickable Hyperlinks:**
  * External web URLs open seamlessly in your default browser.
  * Internal document links jump directly to destination pages.
  * Hovering over links displays a pointing hand cursor and target preview in the status bar.
* **Interactive AcroForms:** Fill out interactive PDF forms directly within the app (toggle checkboxes and edit text fields).
* **Multi-Page View Modes:**
  * **Single Page Mode:** Standard focused page reading.
  * **Two Pages (Two-Up) Mode:** Side-by-side reading layout with macOS drop shadows and synchronized zoom.

---

### 🛠️ PDF Organization, Editing & Security
* **Full Annotation Baking:** User markups (freehand pen strokes, highlighters, geometric shapes, text boxes, sticky notes, signatures, and redactions) are written directly into standard PDF annotation objects upon save or export.
* **Permanent Redactions:** Blackout redaction boxes can now be permanently burned into PDFs via **Edit > Permanently Burn Redactions...**, irreversibly stripping underlying sensitive text and graphics.
* **Drag-and-Drop Page Reordering:** Reorder pages visually by dragging and dropping thumbnails inside the sidebar.
* **Insert Page from File:** Right-click any thumbnail or select **Edit > Insert > Page from File...** to insert external PDFs or images into any position.
* **Merge PDFs:** Combine multiple PDF documents into a unified file via **File > Merge PDFs...**.
* **Split & Extract Pages:** Extract custom page ranges (e.g. `1-3, 5, 8-10`) into a new PDF via **File > Split / Extract Pages...**.
* **AES-256 PDF Password Security:** Encrypt documents with AES-256 passwords upon saving via **File > Set PDF Password...** and authenticate encrypted PDFs with a native macOS unlock dialog.

---

### 🎨 Sidebar & Thumbnail Slider Improvements
* **Zero Overlap Dynamic Delegate:** Fixed thumbnail card and page number badge overlap when adjusting the thumbnail size slider.
* **Contact Sheet Grid Layout:** Contact Sheet mode now enforces uniform mathematical grid sizing with automatic column reflow.
* **Auto-Expanding Sidebar:** Sidebar smoothly expands when scaling thumbnails up to prevent horizontal clipping.
* **High-DPI Thumbnail Caching:** Composite multi-resolution caching `(page_idx, width, rot)` ensures razor-sharp thumbnail rendering at any slider scale.

---

### 🐛 Bug Fixes & Refinements
* Fixed markup drawing out of document boundaries; all annotation tools now respect canvas boundaries.
* Fixed text box font family selector and inline text editing.
* Fixed sticky note editor dialog opening and persistence.
* Fixed Color Adjustment inspector toggle and Auto Levels button.
* Fixed print preview dialog crash on Linux Wayland environments.
