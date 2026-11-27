import hashlib
import io
import urllib.error
import urllib.request
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication, QMessageBox

from preview.core.updater import (
    UpdateDownloadWorker,
    UpdateInfo,
    _ValidatedRedirectHandler,
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


class _MockRedirectTransport(urllib.request.BaseHandler):
    """Mock HTTP/HTTPS handler that simulates 302 redirects and 200 payloads without network."""

    def __init__(self, routes):
        self.routes = routes
        self.visited = []

    def default_open(self, req):
        import email.message
        url = req.full_url
        self.visited.append(url)
        status, headers_dict, body = self.routes[url]
        headers = email.message.Message()
        for k, v in headers_dict.items():
            headers[k] = v
        stream = io.BytesIO(body)
        setattr(stream, "msg", "")
        resp = urllib.response.addinfourl(stream, headers, url, code=status)
        if status in (301, 302, 303, 307, 308):
            return self.parent.error("http", req, resp, status, "Found", headers)
        return resp


def test_redirect_chain_allowed_github_asset_host(tmp_path):
    payload = b"verified-redirected-deb"
    expected_sha = hashlib.sha256(payload).hexdigest()
    start_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    cdn_url = "https://objects.githubusercontent.com/github-production-release-asset/preview-app_1.7.2_amd64.deb"
    sums_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/SHA256SUMS.txt"
    sums_cdn_url = "https://release-assets.githubusercontent.com/SHA256SUMS.txt"
    sums_payload = f"{expected_sha}  preview-app_1.7.2_amd64.deb\n".encode("utf-8")

    transport = _MockRedirectTransport({
        start_url: (302, {"Location": cdn_url}, b""),
        cdn_url: (200, {"Content-Length": str(len(payload))}, payload),
        sums_url: (302, {"Location": sums_cdn_url}, b""),
        sums_cdn_url: (200, {"Content-Length": str(len(sums_payload))}, sums_payload),
    })
    opener = urllib.request.build_opener(_ValidatedRedirectHandler(), transport)

    target = tmp_path / "preview-app_1.7.2_amd64.deb"
    worker = UpdateDownloadWorker(start_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.build_opener", return_value=opener):
        worker.run()

    assert failed_msgs == []
    assert finished_paths == [str(target)]
    assert worker.verified_sha256 == expected_sha
    assert cdn_url in transport.visited
    assert sums_cdn_url in transport.visited


def test_redirect_chain_rejects_disallowed_host(tmp_path):
    start_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    evil_url = "https://evil.example.com/payload.deb"

    transport = _MockRedirectTransport({
        start_url: (302, {"Location": evil_url}, b""),
        evil_url: (200, {"Content-Length": "4"}, b"evil"),
    })
    opener = urllib.request.build_opener(_ValidatedRedirectHandler(), transport)

    target = tmp_path / "preview-app_1.7.2_amd64.deb"
    worker = UpdateDownloadWorker(start_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.build_opener", return_value=opener):
        worker.run()

    assert finished_paths == []
    assert len(failed_msgs) == 1
    assert "disallowed redirect" in failed_msgs[0].lower()
    assert evil_url not in transport.visited
    assert not target.exists()


def test_redirect_chain_rejects_https_to_http_downgrade(tmp_path):
    start_url = "https://github.com/shivamprasad1001/previewmacos/releases/download/v1.7.2/preview-app_1.7.2_amd64.deb"
    http_url = "http://objects.githubusercontent.com/github-production-release-asset/preview-app_1.7.2_amd64.deb"

    transport = _MockRedirectTransport({
        start_url: (302, {"Location": http_url}, b""),
        http_url: (200, {"Content-Length": "4"}, b"http"),
    })
    opener = urllib.request.build_opener(_ValidatedRedirectHandler(), transport)

    target = tmp_path / "preview-app_1.7.2_amd64.deb"
    worker = UpdateDownloadWorker(start_url, str(target))
    finished_paths = []
    failed_msgs = []
    worker.finished.connect(finished_paths.append)
    worker.failed.connect(failed_msgs.append)

    with patch("preview.core.updater.urllib.request.build_opener", return_value=opener):
        worker.run()

    assert finished_paths == []
    assert len(failed_msgs) == 1
    assert "disallowed redirect" in failed_msgs[0].lower()
    assert http_url not in transport.visited
    assert not target.exists()


def test_linux_install_update_runs_pkexec_apt_and_restarts_without_xdg_open(tmp_path):
    deb = tmp_path / "preview-app_1.7.3_amd64.deb"
    payload = b"fake-deb-payload"
    deb.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()

    def fake_which(name):
        if name in ("pkexec", "preview-app"):
            return f"/usr/bin/{name}"
        return None

    class _Proc:
        returncode = 0
        stdout = "Installed"
        stderr = ""

    with (
        patch("preview.core.updater.platform.system", return_value="Linux"),
        patch("preview.core.updater.shutil.which", side_effect=fake_which),
        patch("preview.core.updater.subprocess.run", return_value=_Proc()) as mock_run,
        patch("preview.core.updater.subprocess.Popen") as mock_popen,
    ):
        ok, msg = install_update(str(deb), expected_sha256=expected_sha)

    assert ok is True
    assert "restarting" in msg.lower()
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/usr/bin/pkexec"
    assert "apt-get install -y" in cmd[3]
    mock_popen.assert_called_once()
    assert mock_popen.call_args[0][0] == ["/usr/bin/preview-app"]


def test_linux_install_update_cancelled_polkit_does_not_open_store(tmp_path):
    deb = tmp_path / "preview-app_1.7.3_amd64.deb"
    payload = b"fake-deb-payload"
    deb.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()

    def fake_which(name):
        if name in ("pkexec", "eddy", "gdebi-gtk"):
            return f"/usr/bin/{name}"
        return None

    class _Proc:
        returncode = 126
        stdout = ""
        stderr = "Request dismissed"

    with (
        patch("preview.core.updater.platform.system", return_value="Linux"),
        patch("preview.core.updater.shutil.which", side_effect=fake_which),
        patch("preview.core.updater.subprocess.run", return_value=_Proc()),
        patch("preview.core.updater.subprocess.Popen") as mock_popen,
    ):
        ok, msg = install_update(str(deb), expected_sha256=expected_sha)

    assert ok is False
    assert "cancelled" in msg.lower()
    mock_popen.assert_not_called()


def test_linux_install_update_failure_never_uses_xdg_open_and_gives_apt_command(tmp_path):
    deb = tmp_path / "preview-app_1.7.3_amd64.deb"
    payload = b"fake-deb-payload"
    deb.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()

    def fake_which(name):
        if name == "pkexec":
            return "/usr/bin/pkexec"
        return None

    class _Proc:
        returncode = 127
        stdout = ""
        stderr = "Error executing command as another user: No authentication agent found"

    with (
        patch("preview.core.updater.platform.system", return_value="Linux"),
        patch("preview.core.updater.shutil.which", side_effect=fake_which),
        patch("preview.core.updater.subprocess.run", return_value=_Proc()),
        patch("preview.core.updater.subprocess.Popen") as mock_popen,
    ):
        ok, msg = install_update(str(deb), expected_sha256=expected_sha)

    assert ok is False
    assert "sudo apt install -y" in msg
    assert "xdg-open" not in msg
    mock_popen.assert_not_called()


def test_linux_install_update_no_agent_falls_back_only_to_dedicated_deb_installer(tmp_path):
    deb = tmp_path / "preview-app_1.7.3_amd64.deb"
    payload = b"fake-deb-payload"
    deb.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()

    def fake_which(name):
        if name in ("pkexec", "eddy"):
            return f"/usr/bin/{name}"
        return None

    class _Proc:
        returncode = 127
        stdout = ""
        stderr = "No authentication agent found"

    with (
        patch("preview.core.updater.platform.system", return_value="Linux"),
        patch("preview.core.updater.shutil.which", side_effect=fake_which),
        patch("preview.core.updater.subprocess.run", return_value=_Proc()),
        patch("preview.core.updater.subprocess.Popen") as mock_popen,
    ):
        ok, msg = install_update(str(deb), expected_sha256=expected_sha)

    assert ok is True
    assert "eddy" in msg.lower()
    mock_popen.assert_called_once()
    assert mock_popen.call_args[0][0] == ["/usr/bin/eddy", str(deb.resolve())]


def test_clean_subprocess_env_restores_pyinstaller_overrides():
    from preview.core.updater import _clean_subprocess_env

    fake_env = {
        "PATH": "/usr/bin",
        "LD_LIBRARY_PATH": "/usr/lib/preview-app/_internal",
        "LD_LIBRARY_PATH_ORIG": "/usr/local/lib",
        "QT_PLUGIN_PATH": "/usr/lib/preview-app/_internal/PyQt6/Qt6/plugins",
        "_MEIPASS2": "/tmp/_MEI123",
    }
    with (
        patch("preview.core.updater.os.environ", fake_env),
        patch("preview.core.updater.sys.frozen", True, create=True),
    ):
        cleaned = _clean_subprocess_env()

    assert cleaned["LD_LIBRARY_PATH"] == "/usr/local/lib"
    assert "QT_PLUGIN_PATH" not in cleaned
    assert "_MEIPASS2" not in cleaned
    assert cleaned["PATH"] == "/usr/bin"
