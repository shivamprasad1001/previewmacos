import importlib
import pkgutil
import sys
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pymupdf
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
)

import preview.ui.main_window as main_window_pkg
from preview.ui.main_window import MacMainWindow


def test_import_all_main_window_submodules():
    imported = []
    for mod_info in pkgutil.iter_modules(main_window_pkg.__path__, prefix=f"{main_window_pkg.__name__}."):
        mod = importlib.import_module(mod_info.name)
        assert mod is not None
        imported.append(mod_info.name)
    assert len(imported) >= 6


def _collect_actions(menu: QMenu) -> list[QAction]:
    actions: list[QAction] = []
    for act in menu.actions():
        if act.isSeparator():
            continue
        sub = act.menu()
        if sub is not None:
            actions.extend(_collect_actions(sub))
        else:
            actions.append(act)
    return actions


def test_trigger_all_menubar_actions_smoke(tmp_path):
    app = QApplication.instance() or QApplication([])
    assert app is not None

    pdf_path = tmp_path / "smoke.pdf"
    doc = pymupdf.open()
    for idx in range(2):
        page = doc.new_page(width=400, height=400)
        page.insert_text((40, 60), f"Smoke Test PDF Page {idx + 1}")
    doc.save(str(pdf_path))
    doc.close()

    win = MacMainWindow(initial_file=str(pdf_path))
    win._skip_save_prompt = True

    actions: list[QAction] = []
    for top_act in win.top_menubar.actions():
        sub = top_act.menu()
        if sub is not None:
            actions.extend(_collect_actions(sub))

    assert len(actions) > 10

    failures: list[str] = []
    old_excepthook = sys.excepthook

    def _capture_exc(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, (NameError, AttributeError, ImportError)):
            failures.append(f"{exc_type.__name__}: {exc_value}")

    patches = [
        patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok),
        patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok),
        patch.object(QMessageBox, "critical", return_value=QMessageBox.StandardButton.Ok),
        patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No),
        patch.object(QMessageBox, "about", return_value=None),
        patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Ok),
        patch.object(QFileDialog, "getOpenFileName", return_value=("", "")),
        patch.object(QFileDialog, "getOpenFileNames", return_value=([], "")),
        patch.object(QFileDialog, "getSaveFileName", return_value=("", "")),
        patch.object(QFileDialog, "getExistingDirectory", return_value=""),
        patch.object(QInputDialog, "getText", return_value=("", False)),
        patch.object(QInputDialog, "getInt", return_value=(1, False)),
        patch.object(QDialog, "exec", return_value=0),
        patch("PyQt6.QtPrintSupport.QPrinter", MagicMock()),
        patch("PyQt6.QtPrintSupport.QPrintDialog", MagicMock()),
        patch("PyQt6.QtPrintSupport.QPrintPreviewDialog", MagicMock()),
        patch("PyQt6.QtGui.QDesktopServices.openUrl", return_value=True),
        patch.object(win, "_start_update_check", return_value=None),
        patch.object(win, "close", return_value=True),
    ]

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        sys.excepthook = _capture_exc
        try:
            for act in actions:
                label = act.text() or "(unnamed)"
                try:
                    act.trigger()
                    app.processEvents()
                except (NameError, AttributeError, ImportError) as exc:
                    failures.append(f"Action '{label}': {type(exc).__name__}: {exc}")
        finally:
            sys.excepthook = old_excepthook

    try:
        win.document.close() if hasattr(win.document, "close") else None
    except Exception:
        pass
    win.deleteLater()

    assert not failures, "Smoke test failures:\n" + "\n".join(failures)
