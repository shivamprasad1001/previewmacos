"""
macOS Preview image adjustment engine.
Provides Exposure, Contrast, Saturation, Temperature, Tint, Sharpness, and Auto-Levels adjustments.
"""

from typing import Tuple, List
from PIL import Image, ImageEnhance, ImageOps

class ColorAdjustEngine:
    """Applies macOS-style color and lighting adjustments to PIL Images."""

    @staticmethod
    def adjust(
        image: Image.Image,
        exposure: float = 0.0,       # -1.0 to 1.0 (0 default)
        contrast: float = 0.0,       # -1.0 to 1.0 (0 default)
        saturation: float = 0.0,     # -1.0 to 1.0 (0 default)
        temperature: float = 0.0,    # -1.0 (cool/blue) to 1.0 (warm/orange)
        tint: float = 0.0,           # -1.0 (green) to 1.0 (magenta)
        sharpness: float = 0.0,      # -1.0 to 1.0 (0 default)
        sepia: bool = False
    ) -> Image.Image:
        """Applies full parameter set to the input image and returns enhanced copy."""
        img = image.copy()
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # 1. Combined Exposure, Contrast, Temperature, Tint via fast C lookup table
        if exposure != 0.0 or contrast != 0.0 or temperature != 0.0 or tint != 0.0:
            exp_factor = max(0.0, 1.0 + exposure)
            con_factor = max(0.0, 1.0 + contrast)
            r_scale = 1.0 + temperature * 0.25 + tint * 0.15
            g_scale = 1.0 - abs(temperature) * 0.05 - tint * 0.2
            b_scale = 1.0 - temperature * 0.25 + tint * 0.15

            lut_r = [min(255, max(0, int((128.0 + (i * exp_factor - 128.0) * con_factor) * r_scale))) for i in range(256)]
            lut_g = [min(255, max(0, int((128.0 + (i * exp_factor - 128.0) * con_factor) * g_scale))) for i in range(256)]
            lut_b = [min(255, max(0, int((128.0 + (i * exp_factor - 128.0) * con_factor) * b_scale))) for i in range(256)]

            if img.mode == "RGBA":
                lut = lut_r + lut_g + lut_b + list(range(256))
            else:
                lut = lut_r + lut_g + lut_b
            img = img.point(lut)

        # 2. Saturation (factor: 1.0 is neutral)
        if saturation != 0.0:
            factor = 1.0 + saturation
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(max(0.0, factor))

        # 3. Sharpness
        if sharpness != 0.0:
            factor = 1.0 + sharpness * 1.5
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(max(0.0, factor))

        # 4. Sepia effect
        if sepia:
            img = ColorAdjustEngine._apply_sepia(img)

        return img

    @staticmethod
    def _apply_temp_tint(img: Image.Image, temp: float, tint: float) -> Image.Image:
        r_scale = 1.0 + temp * 0.25 + tint * 0.15
        g_scale = 1.0 - abs(temp) * 0.05 - tint * 0.2
        b_scale = 1.0 - temp * 0.25 + tint * 0.15

        lut_r = [min(255, max(0, int(i * r_scale))) for i in range(256)]
        lut_g = [min(255, max(0, int(i * g_scale))) for i in range(256)]
        lut_b = [min(255, max(0, int(i * b_scale))) for i in range(256)]

        if img.mode == "RGBA":
            return img.point(lut_r + lut_g + lut_b + list(range(256)))
        return img.point(lut_r + lut_g + lut_b)

    @staticmethod
    def _apply_sepia(img: Image.Image) -> Image.Image:
        has_alpha = (img.mode == "RGBA")
        alpha = None
        if has_alpha:
            alpha = img.split()[3]
            img = img.convert("RGB")

        gray = ImageOps.grayscale(img)
        sepia = ImageOps.colorize(gray, "#2e1503", "#fbeccb")

        if has_alpha and alpha:
            sepia.putalpha(alpha)
        return sepia

    @staticmethod
    def auto_levels(image: Image.Image) -> Image.Image:
        """macOS 'Auto Levels' equivalent: normalizes image histogram."""
        has_alpha = (image.mode == "RGBA")
        alpha = None
        if has_alpha:
            alpha = image.split()[3]
            img = image.convert("RGB")
        else:
            img = image.copy()

        equalized = ImageOps.autocontrast(img, cutoff=1)
        if has_alpha and alpha:
            equalized.putalpha(alpha)
        return equalized

    @staticmethod
    def get_histogram(image: Image.Image) -> Tuple[List[int], List[int], List[int]]:
        """Calculates R, G, B histogram data for the preview histogram graph."""
        if image.mode != "RGB":
            img = image.convert("RGB")
        else:
            img = image
        # Downscale for instant histogram calculation
        small = img.resize((150, 150), Image.Resampling.BOX)
        hist = small.histogram()
        r = hist[0:256]
        g = hist[256:512]
        b = hist[512:768]
        return r, g, b
