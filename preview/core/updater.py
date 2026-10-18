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
