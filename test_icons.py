"""
Unit and integration tests for the Studio Pro icon system in preview/icons.py.
Verifies physical tool icons, studio controls, backward compatibility,
color tinting in dark and light themes, dropdown variants, and vector fallbacks.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QPixmap, QIcon
from preview.icons import Icon, MacIconFactory, ICON_MAP, BUILTIN_SVGS

# Ensure single offscreen Qt application
app = QApplication.instance()
if not app:
    app = QApplication([])


def test_highlighter_variants():
    names = ["highlighter", "chisel_highlighter", "chisel-highlighter", "marker", "highlight", "chisel"]
    for name in names:
        pix = Icon.pixmap(name, color="#f5f5f7", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        assert pix.width() == 36  # High-DPI 2x scale
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_fountain_pen_variants():
    names = ["fountain_pen", "fountain-pen", "ink_pen", "nib", "calligraphy", "fountain_pen_vertical", "fountain-pen-vertical"]
    for name in names:
        pix = Icon.pixmap(name, color="#0a84ff", size=20)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_rubber_stamp_variants():
    names = ["stamp", "rubber_stamp", "rubber-stamp", "approved", "seal", "watermark"]
    for name in names:
        pix = Icon.pixmap(name, color="#ff453a", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_scissors_and_crop_shears():
    names = ["scissors", "shears", "crop_shears", "crop-shears", "cut", "snip"]
    for name in names:
        pix = Icon.pixmap(name, color="#ffffff", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_magnifying_loupe():
    names = ["loupe", "magnifier", "magnifying_loupe", "magnifying-loupe", "jeweler_loupe", "zoom_loupe"]
    for name in names:
        pix = Icon.pixmap(name, color="#30d158", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_adjustment_sliders():
    names = ["sliders", "equalizer", "adjustment_sliders", "sliders-vertical", "sliders-horizontal", "controls", "tuning", "faders"]
    for name in names:
        pix = Icon.pixmap(name, color="#2563eb", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_settings_gear():
    names = ["gear", "settings", "cog", "preferences", "options", "config"]
    for name in names:
        pix = Icon.pixmap(name, color="#98989d", size=18)
        assert not pix.isNull(), f"Failed to render {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get icon for {name}"


def test_window_controls():
    close_names = ["window_close", "window-close", "traffic_close", "win_close", "close", "x"]
    min_names = ["window_minimize", "window-minimize", "traffic_minimize", "win_minimize", "minimize"]
    max_names = ["window_maximize", "window-maximize", "traffic_maximize", "win_maximize", "window_fullscreen", "maximize"]
    restore_names = ["window_restore", "window-restore", "restore", "unmaximize"]

    for name in close_names + min_names + max_names + restore_names:
        pix = Icon.pixmap(name, size=14)
        assert not pix.isNull(), f"Failed to render window control {name}"
        icon = Icon.get(name)
        assert not icon.isNull(), f"Failed to get QIcon for {name}"


def test_backward_compatibility():
    legacy_keys = [
        "sidebar", "back", "forward", "open", "folder", "view", "mode_view", "eye",
        "edit", "mode_edit", "pencil", "organize", "mode_organize", "contact_sheet",
        "layout-grid", "zoom_in", "zoom_out", "zoom_fit", "rotate", "rotate_cw",
        "rotate_left", "markup", "pen-tool", "search", "info", "inspector", "theme",
        "moon", "sun", "select", "pointer", "mouse-pointer", "text_select", "hand",
        "pen", "text", "underline", "strikethrough", "note", "shapes", "redact",
        "sign", "signature", "image", "crop", "color_adjust", "size_adjust", "more",
        "undo", "redo", "duplicate", "copy", "trash", "delete", "merge", "split",
        "export", "share", "download", "bold", "italic", "check"
    ]
    for key in legacy_keys:
        pix = Icon.pixmap(key, size=18)
        assert not pix.isNull(), f"Backward compatibility broken for {key}"


def test_theme_awareness_and_qcolor():
    Icon.set_theme("dark")
    assert Icon.get_theme_color() == "#f5f5f7"
    pix_dark = Icon.pixmap("highlighter")
    assert not pix_dark.isNull()

    Icon.set_theme("light")
    assert Icon.get_theme_color() == "#1c1c1e"
    pix_light = Icon.pixmap("highlighter")
    assert not pix_light.isNull()

    # Reset
    Icon.set_theme("dark")

    # QColor passing
    qcol = QColor("#2563eb")
    pix_q = Icon.pixmap("gear", color=qcol)
    assert not pix_q.isNull()


def test_dropdown_icons():
    # Icon.get with_dropdown=True
    icon_dd = Icon.get("shapes", color="#f5f5f7", size=18, with_dropdown=True)
    assert not icon_dd.isNull()

    # create_dropdown_tool_icon
    icon_dd2 = Icon.create_dropdown_tool_icon("select", color_hex="#0a84ff", width=36, height=22)
    assert not icon_dd2.isNull()

    # MacIconFactory
    icon_dd3 = MacIconFactory.create_dropdown_tool_icon("highlighter", "#f5f5f7", 38, 32)
    assert not icon_dd3.isNull()


def test_builtins_and_fallback():
    # Verify physical tools exist in BUILTIN_SVGS
    assert "highlighter" in BUILTIN_SVGS
    assert "fountain-pen" in BUILTIN_SVGS
    assert "rubber-stamp" in BUILTIN_SVGS
    assert "scissors" in BUILTIN_SVGS
    assert "loupe" in BUILTIN_SVGS
    assert "sliders" in BUILTIN_SVGS
    assert "gear" in BUILTIN_SVGS
    assert "window-close" in BUILTIN_SVGS

    # Completely unknown icon name triggers vector fallback
    pix_unknown = Icon.pixmap("non_existent_symbol_404")
    assert not pix_unknown.isNull()
    assert pix_unknown.width() > 0
