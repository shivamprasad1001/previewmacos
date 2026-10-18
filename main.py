#!/usr/bin/env python3
"""
macOS Preview for Linux - Main Application Entry Point
"""

import sys
import os

# Ensure package is found in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from preview.ui.main_window import MacMainWindow

def main():
    # Set high-DPI attributes for crisp rendering on retina and 4K displays
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Preview")
    app.setApplicationDisplayName("Document Viewer")
    app.setDesktopFileName("Preview")

    font_path = os.path.join(current_dir, "preview", "assets", "fonts", "Inter-Variable.ttf")
    if os.path.exists(font_path):
        from PyQt6.QtGui import QFontDatabase, QFont
        QFontDatabase.addApplicationFont(font_path)
        app.setFont(QFont("Inter", 13))

    icon_path = os.path.join(current_dir, "preview", "assets", "icon.png")
    if os.path.exists(icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))

    # Initial file or folder from command line if supplied
    initial_target = None
    if len(sys.argv) > 1 and (os.path.isfile(sys.argv[1]) or os.path.isdir(sys.argv[1])):
        initial_target = sys.argv[1]

    window = MacMainWindow(initial_target=initial_target)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
