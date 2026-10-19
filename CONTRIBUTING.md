# Contributing to Preview (macOS Edition)

Thank you for your interest in contributing to **Preview (macOS Edition)**! This project aims to deliver a pixel-faithful, responsive, and robust reconstruction of Apple's Preview app for Linux and Windows.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git
- `libgl1` and `libegl1` (on Debian/Ubuntu systems for OpenGL support)

### 2. Clone the Repository
```bash
git clone https://github.com/shivamprasad1001/previewmacos.git
cd previewmacos
```

### 3. Set Up a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Locally
```bash
# Launch application
./run.sh

# Or open a specific document
./run.sh ~/path/to/document.pdf
```

---

## 🧪 Testing Guidelines

Before submitting any code changes, ensure all unit tests pass cleanly:

```bash
python3 test_preview_features.py
```

If you add a new feature or fix a bug, please write a corresponding test case in `test_preview_features.py`.

---

## 🎨 Design Philosophy & Coding Standards

1. **Pixel-Faithful macOS Parity**:
   - Follow Apple Human Interface Guidelines (HIG) for layout, margins, typography, and color contrast.
   - All icons should use authentic macOS vector shapes generated through `preview/icons.py`.
2. **Modular Architecture**:
   - Keep business logic in `preview/core/` (document loading, annotations, color adjustment, history).
   - Keep Qt presentation logic in `preview/ui/` (canvas, sidebars, toolbars, dialogs).
3. **Cross-Platform Compatibility**:
   - Avoid hardcoding Unix-only or Windows-only shell commands unless properly guarded by `sys.platform`.
   - Ensure paths use `os.path.join` or `pathlib.Path`.

---

## 📦 Building Packages Locally

### Debian/Ubuntu `.deb` Package:
```bash
chmod +x build_deb.sh
./build_deb.sh
sudo dpkg -i dist/preview-app_*.deb
```

### Windows Setup Installer:
1. Run `windows\build_win.bat` to generate the PyInstaller bundle.
2. Compile `windows\setup.iss` with Inno Setup to generate `dist\Preview-Setup-*.exe`.

---

## 🚀 Submitting a Pull Request

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add support for PDF password encryption"
   ```
3. Push to your branch:
   ```bash
   git push origin feature/amazing-feature
   ```
4. Open a Pull Request on GitHub against the `main` branch.

---

## 📜 Code of Conduct

Please be respectful and constructive in all community interactions. We are committed to providing a welcoming and inclusive environment for everyone.
