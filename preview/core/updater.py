"""
Software Update Checker for Preview macOS.
Checks GitHub Releases API asynchronously in a background thread for new versions.
"""

import os
import re
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Tuple
import platform

from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from preview import __version__

GITHUB_API_LATEST = "https://api.github.com/repos/shivamprasad1001/previewmacos/releases/latest"
GITHUB_RELEASES_PAGE = "https://github.com/shivamprasad1001/previewmacos/releases"

@dataclass
class UpdateInfo:
    """Encapsulates information about an available software update."""
    version: str
    tag_name: str
    title: str
    body: str
    html_url: str
    deb_url: Optional[str] = None
    exe_url: Optional[str] = None
    published_at: str = ""

    @property
    def recommended_download_url(self) -> str:
        """Returns the platform-specific asset download URL or the HTML release page."""
        system = platform.system().lower()
        if "linux" in system and self.deb_url:
            return self.deb_url
        elif "windows" in system and self.exe_url:
            return self.exe_url
        return self.html_url


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Extracts numeric tuple from version strings like 'v1.1.1' -> (1, 1, 1)."""
    digits = re.findall(r"\d+", v_str)
    return tuple(int(d) for d in digits) if digits else (0,)


def check_for_update_sync(current_version: str = __version__, timeout: int = 4) -> Tuple[bool, Optional[UpdateInfo], Optional[str]]:
    """
    Synchronously queries GitHub Releases API for the latest release.
    Returns:
        (has_update, update_info, error_message)
    """
    req = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={
            "User-Agent": f"Preview-App-Updater/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return False, None, f"HTTP Error {response.status}"
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return False, None, f"Network error: {e.reason}"
    except Exception as e:
        return False, None, str(e)

    tag_name = data.get("tag_name", "")
    if not tag_name:
        return False, None, "Invalid release data from server"

    remote_clean = tag_name.lstrip("vV")
    remote_ver = parse_version(remote_clean)
    local_ver = parse_version(current_version)

    has_update = remote_ver > local_ver

    # Extract asset URLs
    deb_url = None
    exe_url = None
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if name.endswith(".deb") and not deb_url:
            deb_url = url
        elif (name.endswith(".exe") or "setup" in name) and not exe_url:
            exe_url = url

    update_info = UpdateInfo(
        version=remote_clean,
        tag_name=tag_name,
        title=data.get("name") or tag_name,
        body=data.get("body") or "No release notes provided.",
        html_url=data.get("html_url") or GITHUB_RELEASES_PAGE,
        deb_url=deb_url,
        exe_url=exe_url,
        published_at=data.get("published_at", "")[:10]
    )

    return has_update, update_info, None


class UpdateCheckWorker(QThread):
    """Asynchronous worker thread to check for updates without blocking the UI."""

    update_available = pyqtSignal(object)       # UpdateInfo
    no_update_available = pyqtSignal(str)       # current_version
    check_failed = pyqtSignal(str)              # error_message

    def __init__(self, current_version: str = __version__, is_manual: bool = False, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.is_manual = is_manual

    def run(self):
        has_update, update_info, err = check_for_update_sync(self.current_version)
        if err:
            self.check_failed.emit(err)
        elif has_update and update_info:
            self.update_available.emit(update_info)
        else:
            self.no_update_available.emit(self.current_version)


class UpdateDownloadWorker(QThread):
    """
    Downloads update asset asynchronously in chunks, emitting live progress percentage,
    download speed, and transferred bytes.
    """
    progress = pyqtSignal(int, int, int, float)  # percent, downloaded_bytes, total_bytes, speed_mb_s
    finished = pyqtSignal(str)                   # target_filepath
    failed = pyqtSignal(str)                     # error_message

    def __init__(self, download_url: str, target_filepath: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_filepath = target_filepath
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        import time
        try:
            os.makedirs(os.path.dirname(self.target_filepath), exist_ok=True)
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "Preview-App-Downloader"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                total_size = resp.headers.get("Content-Length")
                total_bytes = int(total_size) if total_size else 0

                downloaded = 0
                chunk_size = 65536  # 64 KB
                start_time = time.time()
                last_emit = 0.0

                with open(self.target_filepath, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if os.path.exists(self.target_filepath):
                                try:
                                    os.remove(self.target_filepath)
                                except Exception:
                                    pass
                            self.failed.emit("Download cancelled by user.")
                            return

                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()

                        if now - last_emit >= 0.1 or downloaded == total_bytes:
                            elapsed = max(0.001, now - start_time)
                            speed_mb_s = (downloaded / (1024 * 1024)) / elapsed
                            percent = int(downloaded * 100 / total_bytes) if total_bytes > 0 else 0
                            self.progress.emit(percent, downloaded, total_bytes, speed_mb_s)
                            last_emit = now

            self.finished.emit(self.target_filepath)
        except Exception as e:
            if os.path.exists(self.target_filepath):
                try:
                    os.remove(self.target_filepath)
                except Exception:
                    pass
            self.failed.emit(str(e))


def install_update(filepath: str) -> Tuple[bool, str]:
    """
    Executes the native installer or package manager for the downloaded update.
    Returns (success, message).
    """
    import subprocess
    import stat
    system = platform.system().lower()

    if "linux" in system:
        script_path = "/tmp/preview_auto_update.sh"
        escaped_deb = os.path.abspath(filepath)

        script_content = f"""#!/usr/bin/env bash
# macOS Preview Linux Auto-Update Runner
sleep 1.2

# Try graphical polkit installation with pkexec
if command -v pkexec >/dev/null 2>&1 && command -v dpkg >/dev/null 2>&1; then
    pkexec dpkg -i "{escaped_deb}"
    INSTALL_EXIT=$?
    if [ $INSTALL_EXIT -eq 0 ]; then
        if command -v preview-app >/dev/null 2>&1; then
            preview-app &
        fi
        exit 0
    fi
fi

# Fallback: Open with system Software Store / GDebi
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "{escaped_deb}" &
    exit 0
fi

exit 1
"""
        try:
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            subprocess.Popen(["/bin/bash", script_path], start_new_session=True, close_fds=True)
            return True, "Installing update... Please authorize when prompted."
        except Exception as e:
            return False, f"Failed to launch installer: {e}"

    elif "windows" in system:
        try:
            subprocess.Popen([filepath, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"], shell=True)
            return True, "Starting Windows installer..."
        except Exception as e:
            return False, f"Failed to start installer: {e}"

    # Generic fallback
    try:
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
        return True, "Opening update package..."
    except Exception as e:
        return False, str(e)

