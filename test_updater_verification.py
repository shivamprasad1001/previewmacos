import hashlib
import io
import urllib.error
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QMessageBox

from preview.core.updater import (
    UpdateDownloadWorker,
    UpdateInfo,
    install_update,
    is_allowed_download_url,
)
from preview.ui.update_dialog import UpdateDialog


class _FakeResponse:
    def __init__(self, payload: bytes, url: str):
        self._stream = io.BytesIO(payload)
        self._url = url
        self.headers = {"Content-Length": str(len(payload))}

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_allowed_download_urls():
    assert is_allowed_download_url(
        "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    )
    assert is_allowed_download_url(
        "https://objects.githubusercontent.com/github-production-release-asset-2e65be/preview.deb"
    )
    assert not is_allowed_download_url("http://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/a.deb")
    assert not is_allowed_download_url("https://github.com/someoneelse/previewmacos/releases/download/v1.0/a.deb")
    assert not is_allowed_download_url("https://evil.example.com/preview.deb")


def test_download_matching_hash_verifies_and_allows_install(tmp_path):
    payload = b"fake-deb-installer-binary-content"
    expected_sha = hashlib.sha256(payload).hexdigest()
    asset_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    sums_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/SHA256SUMS.txt"
    sums_payload = f"{expected_sha}  preview-app_1.7.2_amd64.deb\n".encode("utf-8")
    target = tmp_path / "preview-app_1.7.2_amd64.deb"

    def fake_urlopen(req, timeout=15):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url == asset_url:
            return _FakeResponse(payload, asset_url)
        if url == sums_url:
            return _FakeResponse(sums_payload, sums_url)
        raise AssertionError(f"Unexpected URL: {url}")

    worker = UpdateDownloadWorker(asset_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.urlopen", side_effect=fake_urlopen):
        worker.run()

    assert failed_msgs == []
    assert finished_paths == [str(target)]
    assert worker.verified_sha256 == expected_sha
    assert target.exists()

    with patch("preview.core.updater.platform.system", return_value="Windows"), patch(
        "subprocess.Popen"
    ) as mock_popen:
        ok, _ = install_update(str(target), expected_sha256=worker.verified_sha256)
        assert ok is True
        mock_popen.assert_called_once()


def test_download_wrong_hash_deletes_file_and_fails(tmp_path):
    payload = b"tampered-deb-content"
    wrong_sha = "0" * 64
    asset_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    sums_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/SHA256SUMS.txt"
    sums_payload = f"{wrong_sha}  preview-app_1.7.2_amd64.deb\n".encode("utf-8")
    target = tmp_path / "preview-app_1.7.2_amd64.deb"

    def fake_urlopen(req, timeout=15):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url == asset_url:
            return _FakeResponse(payload, asset_url)
        if url == sums_url:
            return _FakeResponse(sums_payload, sums_url)
        raise AssertionError(f"Unexpected URL: {url}")

    worker = UpdateDownloadWorker(asset_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.urlopen", side_effect=fake_urlopen):
        worker.run()

    assert finished_paths == []
    assert len(failed_msgs) == 1
    assert "mismatch" in failed_msgs[0].lower()
    assert worker.verified_sha256 is None
    assert not target.exists()


def test_download_missing_checksum_file_deletes_file_and_fails(tmp_path):
    payload = b"valid-bytes-without-sums"
    asset_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/Preview-Setup-1.7.2.exe"
    sums_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/SHA256SUMS.txt"
    target = tmp_path / "Preview-Setup-1.7.2.exe"

    def fake_urlopen(req, timeout=15):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url == asset_url:
            return _FakeResponse(payload, asset_url)
        if url == sums_url:
            raise urllib.error.HTTPError(sums_url, 404, "Not Found", {}, None)
        raise AssertionError(f"Unexpected URL: {url}")

    worker = UpdateDownloadWorker(asset_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.urlopen", side_effect=fake_urlopen):
        worker.run()

    assert finished_paths == []
    assert len(failed_msgs) == 1
    assert "SHA256SUMS.txt" in failed_msgs[0]
    assert worker.verified_sha256 is None
    assert not target.exists()


def test_disallowed_url_rejected_without_network(tmp_path):
    target = tmp_path / "evil.deb"
    worker = UpdateDownloadWorker("https://evil.example.com/evil.deb", str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.urlopen") as mock_urlopen:
        worker.run()

    mock_urlopen.assert_not_called()
    assert finished_paths == []
    assert len(failed_msgs) == 1
    assert "disallowed" in failed_msgs[0].lower()
    assert not target.exists()


def test_install_update_unreachable_without_verified_hash(tmp_path):
    app = QApplication.instance() or QApplication([])
    assert app is not None

    fake_file = tmp_path / "update.deb"
    fake_file.write_bytes(b"unverified")

    ok, msg = install_update(str(fake_file))
    assert ok is False
    assert "verified" in msg.lower()

    ok_wrong, _ = install_update(str(fake_file), expected_sha256="a" * 64)
    assert ok_wrong is False

    info = UpdateInfo(
        version="1.8.0",
        tag_name="v1.8.0",
        title="Preview 1.8.0",
        body="Notes",
        html_url="https://github.com/shivamprasad1001/previewmacos/releases/tag/v1.8.0",
        deb_url="https://github.com/shivamprasad1001/previewmacos/releases/download/v1.8.0/preview.deb",
    )
    dlg = UpdateDialog(info, current_version="1.7.2")
    try:
        dlg.downloaded_filepath = str(fake_file)
        with patch("preview.ui.update_dialog.install_update") as mock_install:
            dlg._install_and_restart()
            mock_install.assert_not_called()

        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg._on_download_failed("SHA-256 checksum mismatch")
            mock_warn.assert_called_once()
            assert dlg.downloaded_filepath is None
            assert dlg.verified_sha256 is None
    finally:
        dlg.close()
