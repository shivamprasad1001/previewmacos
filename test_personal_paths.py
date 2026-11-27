import os
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from preview.ui.help_window import HelpWindow


def test_no_personal_username_in_tracked_files():
    repo_root = Path(__file__).resolve().parent
    # Handle both root-level and tests/-level placement
    if repo_root.name == "tests":
        repo_root = repo_root.parent
    needle = "zoro" + "0x1"
    result = subprocess.run(
        ["git", "grep", "-n", needle],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1 and result.stdout == "", (
        f"Found personal path reference in git-tracked files:\n{result.stdout}"
    )


def test_help_window_finds_content_from_other_cwd(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None

    monkeypatch.chdir(tmp_path)
    win = HelpWindow()
    try:
        assert os.path.isdir(win.content_dir)
        assert os.path.isfile(os.path.join(win.content_dir, "dictionary.json"))
    finally:
        win.close()


def test_desktop_file_has_no_personal_paths():
    repo_root = Path(__file__).resolve().parent
    if repo_root.name == "tests":
        repo_root = repo_root.parent
    desktop_text = (repo_root / "preview.desktop").read_text(encoding="utf-8")
    assert "Exec=preview-app %F" in desktop_text
    assert "Icon=preview-macos" in desktop_text
