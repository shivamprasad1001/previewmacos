"""
Unit and integration tests for the Studio Pro icon system in preview/icons.py.
Verifies physical tool icons, studio controls, backward compatibility,
color tinting in dark and light themes, dropdown variants, and vector fallbacks.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor
from preview.icons import Icon, MacIconFactory, BUILTIN_SVGS

# Ensure single offscreen Qt application
app = QApplication.instance()
if not app:
    app = QApplication([])


class TestStudioIcons(unittest.TestCase):

    def test_highlighter_variants(self):
        names = ["highlighter", "chisel_highlighter", "chisel-highlighter", "marker", "highlight", "chisel"]
        for name in names:
            pix = Icon.pixmap(name, color="#f5f5f7", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            self.assertEqual(pix.width(), 36)  # High-DPI 2x scale
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_fountain_pen_variants(self):
        names = ["fountain_pen", "fountain-pen", "ink_pen", "nib", "calligraphy", "fountain_pen_vertical", "fountain-pen-vertical"]
        for name in names:
            pix = Icon.pixmap(name, color="#0a84ff", size=20)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_rubber_stamp_variants(self):
        names = ["stamp", "rubber_stamp", "rubber-stamp", "approved", "seal", "watermark"]
        for name in names:
            pix = Icon.pixmap(name, color="#ff453a", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_scissors_and_crop_shears(self):
        names = ["scissors", "shears", "crop_shears", "crop-shears", "cut", "snip"]
        for name in names:
            pix = Icon.pixmap(name, color="#ffffff", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_loupe_and_magnifier(self):
        names = ["loupe", "magnifier", "magnifying_loupe", "magnifying-loupe", "jeweler_loupe", "zoom_loupe"]
        for name in names:
            pix = Icon.pixmap(name, color="#30d158", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_adjustment_sliders(self):
        names = ["sliders", "equalizer", "adjustment_sliders", "sliders-vertical", "sliders_vertical", "sliders-horizontal"]
        for name in names:
            pix = Icon.pixmap(name, color="#ffd60a", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_settings_gear(self):
        names = ["gear", "settings", "cog", "preferences", "options"]
        for name in names:
            pix = Icon.pixmap(name, color="#bf5af2", size=18)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_window_controls(self):
        controls = ["window_close", "window_minimize", "window_maximize", "window_restore"]
        for name in controls:
            pix = Icon.pixmap(name, color="#ff453a", size=14)
            self.assertFalse(pix.isNull(), f"Failed to render {name}")
            icon = Icon.get(name)
            self.assertFalse(icon.isNull(), f"Failed to get icon for {name}")

    def test_backward_compatibility_icons(self):
        legacy_names = [
            "sidebar", "open", "view", "edit", "organize", "zoom_in", "zoom_out", "rotate",
            "markup", "search", "info", "select", "hand", "pen", "text", "note", "sign",
            "trash", "duplicate", "close", "arrow_left", "arrow_right", "chevron-left"
        ]
        for name in legacy_names:
            pix = Icon.pixmap(name, size=16)
            self.assertFalse(pix.isNull(), f"Legacy icon {name} returned null pixmap")
            self.assertGreater(pix.width(), 0)

    def test_dropdown_icons(self):
        icon_dd = Icon.get("shapes", color="#f5f5f7", size=18, with_dropdown=True)
        self.assertFalse(icon_dd.isNull())

        icon_dd2 = Icon.create_dropdown_tool_icon("select", color_hex="#0a84ff", width=36, height=22)
        self.assertFalse(icon_dd2.isNull())

        icon_dd3 = MacIconFactory.create_dropdown_tool_icon("highlighter", "#f5f5f7", 38, 32)
        self.assertFalse(icon_dd3.isNull())

    def test_theme_color_toggle(self):
        col_dark = Icon.get_theme_color("dark")
        self.assertEqual(col_dark, "#f5f5f7")

        col_light = Icon.get_theme_color("light")
        self.assertEqual(col_light, "#1c1c1e")

        Icon.set_theme("light")
        pix_light = Icon.pixmap("highlighter")
        self.assertFalse(pix_light.isNull())
        Icon.set_theme("dark")

        qcol = QColor("#2563eb")
        pix_q = Icon.pixmap("gear", color=qcol)
        self.assertFalse(pix_q.isNull())

    def test_builtins_and_fallback(self):
        self.assertIn("highlighter", BUILTIN_SVGS)
        self.assertIn("fountain-pen", BUILTIN_SVGS)
        self.assertIn("rubber-stamp", BUILTIN_SVGS)
        self.assertIn("scissors", BUILTIN_SVGS)
        self.assertIn("gear", BUILTIN_SVGS)

        pix_unknown = Icon.pixmap("non_existent_symbol_404")
        self.assertFalse(pix_unknown.isNull())
        self.assertGreater(pix_unknown.width(), 0)


if __name__ == "__main__":
    unittest.main()
