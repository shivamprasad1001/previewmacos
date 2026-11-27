# Preview macOS v1.7.3 Release Notes

Welcome to **Preview macOS v1.7.3**! This release fixes the Linux auto-updater (it now installs the downloaded `.deb` instead of opening the Cosmic Store), verifies every update against a published SHA-256 checksum before installing, fixes Windows window rendering, and polishes the sidebar, toolbar and full screen exit controls. Under the hood, the project now has a much stronger test and CI setup, plus rotating log files for easier bug reports.

---

### 🛠️ Fixes and Improvements in v1.7.3

#### 🔄 Linux Auto-Updater Fix (Issue #20)
* **Installs the update instead of opening a store:** On Linux, **Check for Updates** downloads the `.deb` and installs it through Polkit (`pkexec`) with `apt-get`, so it no longer hands the file to `xdg-open` (which opened the Cosmic Store on Pop!_OS).
* **App stays open until you authorize:** Preview no longer quits before the authorization prompt appears.
* **Clear fallbacks:** If `pkexec` is unavailable, Preview tries a dedicated local `.deb` installer (`gdebi-gtk`, `eddy` or `qapt-deb-installer`). If everything fails, you see the exact `sudo apt install -y <file>` command to run manually.
* **Clean environment for the installer:** PyInstaller library overrides are removed before calling system tools, avoiding library conflicts during install.

#### 🔐 Verified Updates
* **SHA-256 verification:** Every downloaded installer is checked against `SHA256SUMS.txt` from the same GitHub release. If the checksum is missing or does not match, the download is deleted and an error is shown. Nothing is installed.
* **Download allowlist:** Updates may only come from `https://github.com/shivamprasad1001/previewmacos/` and GitHub's release asset hosts. Every redirect hop is validated.
* **Note:** The checksum protects against corrupted or tampered downloads. It is not a cryptographic signature of the release itself.

#### 🪟 Windows
* **Window rendering fix:** Disabled the translucent layered window shadow on Windows, which could cause the app window to render empty or transparent.
* **SmartScreen reminder:** The installer is still not code-signed. If SmartScreen appears, click "More info" then "Run anyway", and verify the file against `SHA256SUMS.txt` on the release page. Code signing is planned.

#### 🗂️ Sidebar, Toolbar and Full Screen
* **Sidebar header:** Fixed clipping of the **Thumbnails / Contact Sheet** switch and a layout race when entering Organize mode.
* **Thumbnail cards:** Cards and their hover/selection bounds now match each page's aspect ratio, so wide or tall pages no longer have large empty padding.
* **Light Mode:** Fixed the sidebar scrollbar track color.
* **Toolbar:** Fixed the mode pill overflowing vertically, long titles now truncate properly, and spacing is more compact on narrow windows.
* **Full Screen / Slideshow:** The floating exit control now renders correctly on Light Mode canvases, shows an **Exit** label with an icon, and uses the right tooltip (`Exit Full Screen (Esc)` or `Exit Slideshow (Esc)`).

#### 🐛 Bug Fixes
* Fixed a crash in **Zoom to Fit** when two-page (two-up) view is active.
* Fixed several undefined-name errors and silent error handling found by the new lint checks.

#### 🧰 Diagnostics
* **Log files:** Preview now writes a rotating log file and records uncaught errors, which makes bug reports much easier.
  * Linux: `~/.local/state/previewmacos/logs/preview.log`
  * Windows: `%LOCALAPPDATA%\previewmacos\Logs\preview.log`

#### 🐧 Packaging
* The desktop entry (`preview.desktop`) no longer contains a developer-specific path. It now launches `preview-app` and uses the `preview-macos` icon name.
* Help content is found correctly when launched from any working directory and from the packaged build.

#### 🧪 Quality and Project Maintenance
* All tests moved to `tests/` and run in CI on Python 3.10, 3.11 and 3.12 with `ruff` linting.
* Added tests for update verification, redirect validation, logging and help-content discovery, plus a smoke test that triggers every menu action.
* The large `main_window.py` was split into smaller modules under `preview/ui/main_window/`. This is an internal change with no behavior difference.
* Added `pyproject.toml` with project metadata and lint configuration.
* `SECURITY.md` now lists 1.7.x as supported.

---

### ⬆️ Upgrading from v1.7.2 or earlier
The updater fix lives in the new version, so v1.7.2 and earlier cannot use it. Install v1.7.3 once manually:

```bash
sudo apt install ./preview-app_1.7.3_amd64.deb
```

Windows users can run the new installer over the existing install. Future updates will install automatically.

### ✅ Verify your download
Compare the hash of your downloaded file with `SHA256SUMS.txt` on the release page:

```bash
sha256sum preview-app_1.7.3_amd64.deb
```
