import logging
import sys

from preview.logging_setup import setup_logging


def test_logging_setup_records_deliberate_error(tmp_path):
    old_hook = sys.excepthook
    try:
        log_file = setup_logging(log_dir=tmp_path)
        assert log_file == tmp_path / "preview.log"

        try:
            raise RuntimeError("deliberate test error for logging verification")
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            sys.excepthook(exc_type, exc_value, exc_tb)

        for handler in logging.getLogger().handlers:
            handler.flush()

        log_text = log_file.read_text(encoding="utf-8")
        assert "RuntimeError: deliberate test error for logging verification" in log_text
        assert "Uncaught exception" in log_text
    finally:
        sys.excepthook = old_hook
        root = logging.getLogger()
        for handler in list(root.handlers):
            if getattr(handler, "_preview_rotating_handler", False):
                root.removeHandler(handler)
                handler.close()
