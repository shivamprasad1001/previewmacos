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
