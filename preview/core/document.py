"""
Document model supporting both multi-page PDFs (via PyMuPDF) and Image collections/folders (via Pillow).
Provides high-DPI rendering, thumbnail caching, text extraction, search, and page manipulations.
"""

import os
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

import pymupdf
from PIL import Image
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QObject, pyqtSignal, QRectF

SUPPORTED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif'}

def natural_sort_key(s: str):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

@dataclass
class SearchResult:
    page_num: int
    rect: QRectF
    text: str

class Document(QObject):
    """Unified document representation for PDFs and Image collections/folders."""
    
    document_changed = pyqtSignal()
    page_changed = pyqtSignal(int)

    def __init__(self, initial_target: Optional[Any] = None):
        super().__init__()
        self.file_path: Optional[str] = None
        self.file_name: str = "Untitled"
        self.is_pdf: bool = False
        self.page_count: int = 0
        self.current_page: int = 0
        self.rotations: Dict[int, int] = {}  # page_idx -> degree
        self.is_dirty: bool = False
        self.metadata: Dict[str, Any] = {}
        
        # Multi-image list
        self.image_paths: List[str] = []
        self._image_cache: Dict[int, Image.Image] = {}

        # Internal engines
        self._pdf_doc: Optional[pymupdf.Document] = None
        self._pil_image: Optional[Image.Image] = None  # Current active image
        self._thumbnail_cache: Dict[int, QPixmap] = {}
        self._rendered_cache: Dict[Tuple[int, float, int], QPixmap] = {}

        if initial_target:
            if isinstance(initial_target, list):
                self.load_files(initial_target)
            elif os.path.isdir(initial_target):
                self.load_folder(initial_target)
            elif os.path.isfile(initial_target):
                self.load_file(initial_target)

    def load_file(self, file_path: str) -> bool:
        """Loads a PDF, single image, or folder."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if os.path.isdir(file_path):
            return self.load_folder(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return self._load_single_pdf(file_path)
        elif ext in SUPPORTED_IMAGE_EXTS:
            return self.load_files([file_path])
        else:
            # Try loading as image fallback
            return self.load_files([file_path])

    def load_files(self, file_paths: List[str]) -> bool:
        """Loads a list of image files as a multi-page image collection."""
        valid_paths = [os.path.abspath(p) for p in file_paths if os.path.isfile(p)]
        if not valid_paths:
            return False

        # If single PDF
        if len(valid_paths) == 1 and valid_paths[0].lower().endswith('.pdf'):
            return self._load_single_pdf(valid_paths[0])

        self._reset_state()
        self.is_pdf = False
        self.image_paths = valid_paths
        self.page_count = len(valid_paths)
        self.file_path = valid_paths[0]

        if len(valid_paths) == 1:
            self.file_name = os.path.basename(valid_paths[0])
        else:
            folder_name = os.path.basename(os.path.dirname(valid_paths[0])) or "Images"
            self.file_name = f"{folder_name} ({len(valid_paths)} images)"

        self._load_current_image(0)
        self.document_changed.emit()
        return True

    def load_folder(self, folder_path: str) -> bool:
        """Finds all supported images in a folder and loads them in natural order."""
        if not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Not a directory: {folder_path}")

        all_files = os.listdir(folder_path)
        all_files.sort(key=natural_sort_key)

        image_files = [
            os.path.join(folder_path, f) for f in all_files 
            if os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTS
        ]

        if not image_files:
            raise FileNotFoundError(f"No supported images found in: {folder_path}")

        return self.load_files(image_files)

    def _reset_state(self):
        self.rotations.clear()
        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self._image_cache.clear()
        self.is_dirty = False
        self.current_page = 0
        if self._pdf_doc:
            try:
                self._pdf_doc.close()
            except Exception:
                pass
            self._pdf_doc = None
        self._pil_image = None

    def _load_single_pdf(self, file_path: str) -> bool:
        self._reset_state()
        self.file_path = os.path.abspath(file_path)
        self.file_name = os.path.basename(file_path)
        self.is_pdf = True
        self._pdf_doc = pymupdf.open(file_path)
        self.page_count = len(self._pdf_doc)
        
        meta = self._pdf_doc.metadata or {}
        stat = os.stat(file_path)
        self.metadata = {
            "title": meta.get("title", "") or self.file_name,
            "author": meta.get("author", "Unknown"),
            "subject": meta.get("subject", ""),
            "keywords": meta.get("keywords", ""),
            "producer": meta.get("producer", ""),
            "creator": meta.get("creator", ""),
            "format": meta.get("format", "PDF"),
            "file_size": stat.st_size,
            "page_count": self.page_count,
        }
        self.current_page = 0
        self.document_changed.emit()
        return True

    def _get_pil_for_page(self, page_idx: int) -> Optional[Image.Image]:
        if self.is_pdf:
            return None
        if page_idx in self._image_cache:
            return self._image_cache[page_idx]
        if 0 <= page_idx < len(self.image_paths):
            try:
                img = Image.open(self.image_paths[page_idx])
                self._image_cache[page_idx] = img
                return img
            except Exception:
                return None
        return None

    def _load_current_image(self, page_idx: int):
        img = self._get_pil_for_page(page_idx)
        self._pil_image = img
        if img and 0 <= page_idx < len(self.image_paths):
            path = self.image_paths[page_idx]
            stat = os.stat(path) if os.path.exists(path) else None
            dpi = img.info.get("dpi", (72, 72))
            self.metadata = {
                "title": os.path.basename(path),
                "format": img.format or "Image",
                "mode": img.mode,
                "dimensions": f"{img.width} × {img.height}",
                "width": img.width,
                "height": img.height,
                "dpi": dpi[0] if isinstance(dpi, tuple) else dpi,
                "file_size": stat.st_size if stat else 0,
                "page_count": self.page_count,
            }

    def set_current_page(self, page_idx: int):
        if 0 <= page_idx < self.page_count and page_idx != self.current_page:
            self.current_page = page_idx
            if not self.is_pdf:
                self._load_current_image(page_idx)
            self.page_changed.emit(page_idx)

    def get_page_size(self, page_idx: int = 0) -> Tuple[float, float]:
        """Returns (width, height) of the given page in points or pixels."""
        if self.is_pdf and self._pdf_doc:
            if 0 <= page_idx < self.page_count:
                page = self._pdf_doc[page_idx]
                rot = (page.rotation + self.rotations.get(page_idx, 0)) % 360
                rect = page.rect
                if rot in (90, 270):
                    return rect.height, rect.width
                return rect.width, rect.height
        else:
            img = self._get_pil_for_page(page_idx)
            if img:
                rot = self.rotations.get(page_idx, 0) % 360
                if rot in (90, 270):
                    return float(img.height), float(img.width)
                return float(img.width), float(img.height)
        return (600.0, 800.0)

    def render_page(self, page_idx: int, zoom: float = 1.0) -> QPixmap:
        """Renders page with given zoom and rotation to QPixmap."""
        rot = self.rotations.get(page_idx, 0)
        cache_key = (page_idx, round(zoom, 2), rot)
        if cache_key in self._rendered_cache:
            return self._rendered_cache[cache_key]

        if self.is_pdf and self._pdf_doc:
            if 0 <= page_idx < self.page_count:
                page = self._pdf_doc[page_idx]
                total_rot = (page.rotation + rot) % 360
                scale = zoom * 1.5
                mat = pymupdf.Matrix(scale, scale).prerotate(total_rot)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                img_data = pix.samples
                bytes_per_line = pix.stride
                qimg = QImage(img_data, pix.width, pix.height, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                self._rendered_cache[cache_key] = pixmap
                return pixmap

        else:
            img = self._get_pil_for_page(page_idx)
            if img:
                if rot != 0:
                    img = img.rotate(-rot, expand=True)
                
                target_w = max(1, int(img.width * zoom))
                target_h = max(1, int(img.height * zoom))
                resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                if resized.mode != "RGBA":
                    resized = resized.convert("RGBA")
                data = resized.tobytes("raw", "RGBA")
                qimg = QImage(data, resized.width, resized.height, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                self._rendered_cache[cache_key] = pixmap
                return pixmap

        fallback = QPixmap(100, 100)
        fallback.fill()
        return fallback

    def get_thumbnail(self, page_idx: int, width: int = 120) -> QPixmap:
        """Generates a high-quality thumbnail for the sidebar with caching."""
        rot = self.rotations.get(page_idx, 0)
        cache_key = page_idx
        if cache_key in self._thumbnail_cache and rot == 0:
            return self._thumbnail_cache[cache_key]

        w_pt, h_pt = self.get_page_size(page_idx)
        if w_pt <= 0:
            w_pt = 1
        zoom = width / w_pt
        pixmap = self.render_page(page_idx, zoom=zoom)
        if rot == 0:
            self._thumbnail_cache[cache_key] = pixmap
        return pixmap

    def rotate_page(self, page_idx: int, degrees: int = 90):
        """Rotates a specific page by +90 or -90 degrees."""
        current = self.rotations.get(page_idx, 0)
        self.rotations[page_idx] = (current + degrees) % 360
        self._thumbnail_cache.pop(page_idx, None)
        self._rendered_cache = {k: v for k, v in self._rendered_cache.items() if k[0] != page_idx}
        self.is_dirty = True
        self.page_changed.emit(page_idx)

    def rotate_all(self, degrees: int = 90):
        for p in range(self.page_count):
            self.rotate_page(p, degrees)

    def search_text(self, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not self.is_pdf or not self._pdf_doc or not query.strip():
            return results

        q = query.strip()
        for idx, page in enumerate(self._pdf_doc):
            rects = page.search_for(q)
            for r in rects:
                results.append(SearchResult(
                    page_num=idx,
                    rect=QRectF(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0),
                    text=q
                ))
        return results

    def get_outline(self) -> List[Tuple[int, str, int]]:
        if self.is_pdf and self._pdf_doc:
            try:
                toc = self._pdf_doc.get_toc()
                return [(item[0], item[1], item[2] - 1) for item in toc]
            except Exception:
                return []
        return []

    def update_image(self, new_pil_image: Image.Image, page_idx: Optional[int] = None):
        """Updates internal image after adjustments, filters or crop."""
        idx = page_idx if page_idx is not None else self.current_page
        self._image_cache[idx] = new_pil_image
        if idx == self.current_page:
            self._pil_image = new_pil_image
        self._thumbnail_cache.pop(idx, None)
        self._rendered_cache = {k: v for k, v in self._rendered_cache.items() if k[0] != idx}
        self.is_dirty = True
        self.metadata["width"] = new_pil_image.width
        self.metadata["height"] = new_pil_image.height
        self.metadata["dimensions"] = f"{new_pil_image.width} × {new_pil_image.height}"
        self.document_changed.emit()

    def export_document(self, output_path: str, format_name: str = "PDF", quality: int = 95):
        ext = os.path.splitext(output_path)[1].lower()
        
        if self.is_pdf and self._pdf_doc:
            if ext == '.pdf':
                for p_idx, deg in self.rotations.items():
                    if deg != 0 and p_idx < len(self._pdf_doc):
                        page = self._pdf_doc[p_idx]
                        page.set_rotation((page.rotation + deg) % 360)
                self._pdf_doc.save(output_path)
            else:
                pix = self.render_page(self.current_page, zoom=2.0)
                pix.save(output_path)
        else:
            img = self._get_pil_for_page(self.current_page)
            if not img:
                return
            rot = self.rotations.get(self.current_page, 0)
            if rot != 0:
                img = img.rotate(-rot, expand=True)

            if ext == '.pdf':
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output_path, "PDF", resolution=100.0)
            elif ext in ['.jpg', '.jpeg']:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality)
            else:
                img.save(output_path, quality=quality)
        
        self.is_dirty = False
