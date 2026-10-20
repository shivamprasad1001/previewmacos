#!/usr/bin/env python3
"""
Renders annotated screenshots for the Image Guide from clean screenshots and JSON specs.
Style rules:
- Thin red (#E5484D) lines, 2px.
- White-outlined number circles (1, 2, 3).
- Arrows pointing at tools.
- Rectangle highlight boxes on key areas.
- Blur on sensitive/private areas.
- Preserves clean originals so annotations remain editable.
"""

import json
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RED_ACCENT = (229, 72, 77)  # #E5484D
WHITE = (255, 255, 255)
LINE_WIDTH = 2

def get_font(size: int = 12):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
        "preview/assets/fonts/Inter-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_arrow(draw: ImageDraw.ImageDraw, x1: float, y1: float, x2: float, y2: float, color=RED_ACCENT, width=LINE_WIDTH):
    """Draws a line with an arrowhead at (x2, y2)."""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    arrow_angle = math.pi / 6  # 30 degrees
    
    p1 = (x2 - arrow_len * math.cos(angle - arrow_angle), y2 - arrow_len * math.sin(angle - arrow_angle))
    p2 = (x2 - arrow_len * math.cos(angle + arrow_angle), y2 - arrow_len * math.sin(angle + arrow_angle))
    draw.polygon([(x2, y2), p1, p2], fill=color)

def draw_number_circle(draw: ImageDraw.ImageDraw, cx: float, cy: float, text: str, font, radius=11):
    """Draws a red circle with white outline and bold white number."""
    # Outer white outline
    draw.ellipse([cx - radius - 1.5, cy - radius - 1.5, cx + radius + 1.5, cy + radius + 1.5], fill=WHITE)
    # Red inner circle
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=RED_ACCENT)
    
    # Center text
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = cx - tw / 2.0
    ty = cy - th / 2.0 - 1.0
    draw.text((tx, ty), text, fill=WHITE, font=font)

def apply_blur(image: Image.Image, x: int, y: int, w: int, h: int, radius: int = 8) -> Image.Image:
    """Blurs a rectangular region within image."""
    box = (x, y, x + w, y + h)
    region = image.crop(box)
    blurred = region.filter(ImageFilter.GaussianBlur(radius))
    image.paste(blurred, box)
    return image

def render_image_guide_item(spec_file: str, output_dir: str):
    with open(spec_file, "r", encoding="utf-8") as f:
        spec = json.load(f)
        
    src_path = spec["source_image"]
    if not os.path.exists(src_path):
        print(f"Warning: Source image {src_path} not found. Skipping {spec_file}.")
        return None

    img = Image.open(src_path).convert("RGBA")
    
    # 1. Apply blurs first
    for ann in spec.get("annotations", []):
        if ann["type"] == "blur":
            img = apply_blur(img, ann["x"], ann["y"], ann["w"], ann["h"])

    # 2. Draw vector overlays
    draw = ImageDraw.Draw(img)
    font = get_font(12)

    for ann in spec.get("annotations", []):
        atype = ann["type"]
        if atype == "box":
            x, y, w, h = ann["x"], ann["y"], ann["w"], ann["h"]
            draw.rectangle([x, y, x + w, y + h], outline=RED_ACCENT, width=LINE_WIDTH)
        elif atype == "arrow":
            draw_arrow(draw, ann["x1"], ann["y1"], ann["x2"], ann["y2"], color=RED_ACCENT, width=LINE_WIDTH)
        elif atype == "number":
            draw_number_circle(draw, ann["x"], ann["y"], str(ann["text"]), font)

    out_name = spec.get("output_image", os.path.basename(spec_file).replace(".json", ".png"))
    out_path = os.path.join(output_dir, out_name)
    img.save(out_path, "PNG")
    print(f"Generated: {out_path} ({spec.get('caption', '')})")
    return out_path

if __name__ == "__main__":
    import glob
    specs = sorted(glob.glob("help/content/image_guide/*.json"))
    out_dir = "help/generated"
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    for s in specs:
        if render_image_guide_item(s, out_dir):
            count += 1
    print(f"Rendered {count} annotated screenshots.")
