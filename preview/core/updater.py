"""
Software Update Checker for Preview macOS.
Checks GitHub Releases API asynchronously in a background thread for new versions.
"""

import os
import re
import json
import hashlib
import hmac
import logging
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import platform

from PyQt6.QtCore import QThread, pyqtSignal
from preview import __version__

GITHUB_API_LATEST = "https://api.github.com/repos/shivamprasad1001/previewmacos/releases/latest"
GITHUB_RELEASES_PAGE = "https://github.com/shivamprasad1001/previewmacos/releases"
ALLOWED_REPO_PATH_PREFIX = "/shivamprasad1001/previewmacos/"
# GitHub release downloads on github.com/<owner>/<repo>/releases/download/...
# redirect to GitHub's release asset CDN/storage hosts:
# - objects.githubusercontent.com (primary GitHub release asset storage)
# - release-assets.githubusercontent.com (GitHub release asset CDN)
# - github-releases.githubusercontent.com (legacy/regional GitHub release asset host)
ALLOWED_ASSET_HOSTS = frozenset({
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "github-releases.githubusercontent.com",
})

_STDLIB_URLOPEN = urllib.request.urlopen


class _ValidatedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Validate every HTTP redirect target against the HTTPS + host allowlist."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        if not is_allowed_download_url(resolved):
            raise urllib.error.URLError(f"Disallowed redirect URL: {resolved}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_validated_url(url: str, timeout: int = 15):
    """Open an allowlisted HTTPS URL, validating every redirect hop."""
    if not is_allowed_download_url(url):
        raise urllib.error.URLError(f"Disallowed URL: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Preview-App-Downloader"},
    )
    if urllib.request.urlopen is not _STDLIB_URLOPEN:
        resp = urllib.request.urlopen(req, timeout=timeout)
    else:
        opener = urllib.request.build_opener(_ValidatedRedirectHandler())
        resp = opener.open(req, timeout=timeout)

    final_url = resp.geturl() if hasattr(resp, "geturl") else None
    if isinstance(final_url, str) and final_url and not is_allowed_download_url(final_url):
        if hasattr(resp, "close"):
            resp.close()
        raise urllib.error.URLError(f"Disallowed redirect URL: {final_url}")
    return resp


def is_allowed_download_url(url: str) -> bool:
    """Return True only for HTTPS URLs on the project repo or GitHub release asset hosts."""
    if not url or not isinstance(url, str):
        return False
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme.lower() != "https":
        return False
    host = (parsed.hostname or "").lower()
    if host == "github.com":
        return parsed.path.startswith(ALLOWED_REPO_PATH_PREFIX)
    return host in ALLOWED_ASSET_HOSTS


def derive_checksums_url(download_url: str) -> str:
    """Return the SHA256SUMS.txt URL in the same release directory as download_url."""
    parsed = urllib.parse.urlparse(download_url.strip())
    base_path = parsed.path.rsplit("/", 1)[0]
    return urllib.parse.urlunparse(parsed._replace(path=f"{base_path}/SHA256SUMS.txt", query="", fragment=""))


def compute_sha256(filepath: str) -> str:
    """Compute the lowercase hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_sha256sums(content: str, target_filename: str) -> Optional[str]:
    """Extract the expected SHA-256 hex digest for target_filename from SHA256SUMS.txt content."""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        checksum, name = parts[0].strip(), parts[1].strip().lstrip("*")
        if os.path.basename(name) == target_filename and re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
            return checksum.lower()
    return None

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
    checksums_url: Optional[str] = None
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
    checksums_url = None
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if name == "sha256sums.txt" and not checksums_url:
            checksums_url = url
        elif name.endswith(".deb") and not deb_url:
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
        checksums_url=checksums_url,
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

    def __init__(self, download_url: str, target_filepath: str, checksums_url: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_filepath = target_filepath
        self.checksums_url = checksums_url
        self.verified_sha256: Optional[str] = None
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _cleanup_download(self):
        if os.path.exists(self.target_filepath):
            try:
                os.remove(self.target_filepath)
            except OSError:
                logging.getLogger(__name__).warning(
                    "Failed to remove temporary download %s",
                    self.target_filepath,
                    exc_info=True,
                )

    def _verify_checksum(self) -> Tuple[bool, Optional[str], str]:
        """Fetch SHA256SUMS.txt from the same release and verify the downloaded file."""
        checksums_url = self.checksums_url or derive_checksums_url(self.download_url)
        if not is_allowed_download_url(checksums_url):
            return False, None, f"Disallowed checksum URL: {checksums_url}"

        try:
            with _open_validated_url(checksums_url, timeout=15) as resp:
                checksums_text = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return False, None, f"Could not fetch SHA256SUMS.txt: {e}"

        target_filename = os.path.basename(urllib.parse.urlparse(self.download_url).path) or os.path.basename(self.target_filepath)
        expected_hash = parse_sha256sums(checksums_text, target_filename)
        if not expected_hash:
            return False, None, f"Checksum entry not found for {target_filename} in SHA256SUMS.txt"

        actual_hash = compute_sha256(self.target_filepath)
        if not hmac.compare_digest(actual_hash.lower(), expected_hash.lower()):
            return False, None, (
                f"SHA-256 checksum mismatch for {target_filename} "
                f"(expected {expected_hash}, got {actual_hash})"
            )

        return True, actual_hash.lower(), ""

    def run(self):
        import time
        self.verified_sha256 = None
        if not is_allowed_download_url(self.download_url):
            self.failed.emit(f"Disallowed download URL: {self.download_url}")
            return

        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.target_filepath)), exist_ok=True)
            with _open_validated_url(self.download_url, timeout=15) as resp:
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
                            self._cleanup_download()
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

            ok, verified_hash, err_msg = self._verify_checksum()
            if not ok:
                self._cleanup_download()
                self.failed.emit(err_msg)
                return

            self.verified_sha256 = verified_hash
            self.finished.emit(self.target_filepath)
        except Exception as e:
            self._cleanup_download()
            self.failed.emit(str(e))


def _clean_subprocess_env() -> Dict[str, str]:
    """Return os.environ without PyInstaller runtime library overrides."""
    env = os.environ.copy()
    if "LD_LIBRARY_PATH_ORIG" in env:
        orig = env.pop("LD_LIBRARY_PATH_ORIG")
        if orig:
            env["LD_LIBRARY_PATH"] = orig
        else:
            env.pop("LD_LIBRARY_PATH", None)
    elif getattr(sys, "frozen", False):
        env.pop("LD_LIBRARY_PATH", None)

    if getattr(sys, "frozen", False):
        for var in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QML2_IMPORT_PATH"):
            env.pop(var, None)

    for var in ("_MEIPASS2", "_PYI_ARCHIVE_FILE", "_PYI_APPLICATION_HOME_DIR"):
        env.pop(var, None)
    return env


def _stage_linux_deb(abs_deb: str) -> Tuple[str, Optional[str]]:
    """Copy a verified .deb into a world-readable temp dir for apt/dpkg (_apt access)."""
    stage_dir = None
    try:
        stage_dir = tempfile.mkdtemp(prefix="preview-update-")
        staged_deb = os.path.join(stage_dir, os.path.basename(abs_deb))
        shutil.copy2(abs_deb, staged_deb)
        os.chmod(stage_dir, 0o755)
        os.chmod(staged_deb, 0o644)
        return staged_deb, stage_dir
    except Exception:
        if stage_dir:
            shutil.rmtree(stage_dir, ignore_errors=True)
        return abs_deb, None


def _launch_linux_deb_gui_fallback(abs_deb: str, env: Dict[str, str]) -> Optional[Tuple[bool, str]]:
    """Launch a dedicated local .deb GUI installer if present (never xdg-open/Cosmic Store)."""
    for tool in ("gdebi-gtk", "eddy", "qapt-deb-installer"):
        gui_bin = shutil.which(tool)
        if not gui_bin:
            continue
        try:
            subprocess.Popen(
                [gui_bin, abs_deb],
                env=env,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            return True, f"Opening verified update package in {tool}..."
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to launch %s fallback installer: %s", tool, e)
    return None


def install_update(filepath: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str]:
    """
    Executes the native installer or package manager for the downloaded update.
    Requires a verified SHA-256 checksum matching the file on disk.
    Returns (success, message).
    """
    if not expected_sha256 or not os.path.isfile(filepath):
        return False, "Update package cannot be installed without a verified SHA-256 checksum."

    actual_sha256 = compute_sha256(filepath)
    if not hmac.compare_digest(actual_sha256.lower(), expected_sha256.strip().lower()):
        return False, "Update package SHA-256 verification failed."

    system = platform.system().lower()

    if "linux" in system:
        abs_deb = os.path.abspath(filepath)
        clean_env = _clean_subprocess_env()
        pkexec_bin = shutil.which("pkexec")

        if not pkexec_bin:
            fallback = _launch_linux_deb_gui_fallback(abs_deb, clean_env)
            if fallback is not None:
                return fallback
            return (
                False,
                "Automatic installation requires 'pkexec' (Polkit).\n\n"
                f"To install the verified package manually, run:\nsudo apt install -y {shlex.quote(abs_deb)}",
            )

        staged_deb, stage_dir = _stage_linux_deb(abs_deb)
        install_cmd = (
            'if command -v apt-get >/dev/null 2>&1; then '
            'DEBIAN_FRONTEND=noninteractive apt-get install -y "$1" || dpkg -i "$1"; '
            'else dpkg -i "$1"; fi'
        )
        try:
            proc = subprocess.run(
                [pkexec_bin, "/bin/sh", "-c", install_cmd, "preview-updater", staged_deb],
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            return (
                False,
                "Package installation timed out waiting for authorization or apt/dpkg.\n\n"
                f"To install manually, run:\nsudo apt install -y {shlex.quote(abs_deb)}",
            )
        except Exception as e:
            return False, f"Failed to launch installer: {e}"
        finally:
            if stage_dir:
                shutil.rmtree(stage_dir, ignore_errors=True)

        if proc.returncode == 0:
            relaunch_bin = shutil.which("preview-app") or (
                "/usr/bin/preview-app" if os.path.exists("/usr/bin/preview-app") else None
            )
            if relaunch_bin:
                try:
                    subprocess.Popen(
                        [relaunch_bin],
                        env=clean_env,
                        start_new_session=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        close_fds=True,
                    )
                except Exception as e:
                    logging.getLogger(__name__).warning(
                        "Package updated, but failed to relaunch %s: %s", relaunch_bin, e
                    )
            return True, "Update installed successfully. Restarting Preview..."

        stderr_text = (proc.stderr or "").strip()
        stdout_text = (proc.stdout or "").strip()
        detail = stderr_text or stdout_text

        if proc.returncode == 126:
            return False, "Update installation was cancelled (administrator authorization is required)."

        if proc.returncode == 127 or "no authentication agent" in detail.lower():
            fallback = _launch_linux_deb_gui_fallback(abs_deb, clean_env)
            if fallback is not None:
                return fallback

        msg = f"Package installation failed (exit code {proc.returncode})."
        if detail:
            msg += f"\n\n{detail}"
        msg += (
            f"\n\nTo install the verified package manually in a terminal, run:\n"
            f"sudo apt install -y {shlex.quote(abs_deb)}"
        )
        return False, msg

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

