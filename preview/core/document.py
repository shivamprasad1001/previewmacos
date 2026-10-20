"""
Document model supporting both multi-page PDFs (via PyMuPDF) and Image collections/folders (via Pillow).
Provides high-DPI rendering, thumbnail caching, text extraction, search, and page manipulations.
"""

import os
import re
import io
import shutil
import tempfile
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

import pymupdf
from PIL import Image
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, Qt, QBuffer, QIODevice

SUPPORTED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif', '.gif'}

class PasswordRequiredError(Exception):
    """Raised when an encrypted PDF requires a user password."""
    pass

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

    def __init__(self, initial_target: Optional[Any] = None, password: Optional[str] = None):
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
                self.load_file(initial_target, password=password)

    def load_file(self, file_path: str, password: Optional[str] = None) -> bool:
        """Loads a PDF, single image, or folder."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if os.path.isdir(file_path):
            return self.load_folder(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return self._load_single_pdf(file_path, password=password)
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

    def _load_single_pdf(self, file_path: str, password: Optional[str] = None) -> bool:
        self._reset_state()
        self.file_path = os.path.abspath(file_path)
        self.file_name = os.path.basename(file_path)
        self.is_pdf = True
        self._pdf_doc = pymupdf.open(file_path)
        
        if self._pdf_doc.is_encrypted:
            if password is not None:
                rc = self._pdf_doc.authenticate(password)
                if rc == 0:
                    raise PasswordRequiredError("Incorrect password for PDF.")
            else:
                rc = self._pdf_doc.authenticate("")
                if rc == 0:
                    raise PasswordRequiredError(f"Password required to open '{self.file_name}'.")

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

    def authenticate_password(self, password: str) -> bool:
        """Authenticates an encrypted PDF with the given password."""
        if self.is_pdf and self._pdf_doc and self._pdf_doc.is_encrypted:
            rc = self._pdf_doc.authenticate(password)
            if rc > 0:
                self.page_count = len(self._pdf_doc)
                self.current_page = 0
                self.document_changed.emit()
                return True
        return False

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
                scale = zoom
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
        cache_key = (page_idx, int(width), rot)
        if cache_key in self._thumbnail_cache:
            return self._thumbnail_cache[cache_key]

        w_pt, h_pt = self.get_page_size(page_idx)
        if w_pt <= 0:
            w_pt = 1
        zoom = width / w_pt
        pixmap = self.render_page(page_idx, zoom=zoom)
        self._thumbnail_cache[cache_key] = pixmap
        return pixmap

    def _invalidate_thumbnail(self, page_idx: Optional[int] = None):
        if page_idx is None:
            self._thumbnail_cache.clear()
        else:
            self._thumbnail_cache = {
                k: v for k, v in self._thumbnail_cache.items() 
                if not ((isinstance(k, tuple) and k[0] == page_idx) or k == page_idx)
            }

    def rotate_page(self, page_idx: int, degrees: int = 90):
        """Rotates a specific page by +90 or -90 degrees."""
        current = self.rotations.get(page_idx, 0)
        self.rotations[page_idx] = (current + degrees) % 360
        self._invalidate_thumbnail(page_idx)
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

    def get_page_links(self, page_idx: int) -> List[Dict[str, Any]]:
        """Returns clickable internal and external hyperlinks on the specified PDF page."""
        links: List[Dict[str, Any]] = []
        if not self.is_pdf or not self._pdf_doc or not (0 <= page_idx < self.page_count):
            return links
        try:
            page = self._pdf_doc[page_idx]
            for l in page.get_links():
                r = l.get("from")
                if r:
                    rect = QRectF(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0)
                    links.append({
                        "rect": rect,
                        "uri": l.get("uri"),
                        "page": l.get("page"),  # Destination page index
                        "kind": l.get("kind")
                    })
        except Exception:
            pass
        return links

    def get_page_words(self, page_idx: int) -> List[Tuple[QRectF, str]]:
        """Returns individual word bounding boxes and strings for interactive text selection."""
        words: List[Tuple[QRectF, str]] = []
        if not self.is_pdf or not self._pdf_doc or not (0 <= page_idx < self.page_count):
            return words
        try:
            page = self._pdf_doc[page_idx]
            raw_words = page.get_text("words")
            for w in raw_words:
                rect = QRectF(w[0], w[1], w[2] - w[0], w[3] - w[1])
                words.append((rect, w[4]))
        except Exception:
            pass
        return words

    def get_form_fields(self, page_idx: int) -> List[Dict[str, Any]]:
        """Returns interactive form fields (widgets) on the specified page."""
        fields: List[Dict[str, Any]] = []
        if not self.is_pdf or not self._pdf_doc or not (0 <= page_idx < self.page_count):
            return fields
        try:
            page = self._pdf_doc[page_idx]
            for w in page.widgets():
                r = w.rect
                fields.append({
                    "name": w.field_name,
                    "type": w.field_type_string,
                    "rect": QRectF(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0),
                    "value": w.field_value
                })
        except Exception:
            pass
        return fields

    def set_form_field_value(self, page_idx: int, field_name: str, value: Any) -> bool:
        """Sets a form widget value and refreshes page rendering."""
        if not self.is_pdf or not self._pdf_doc or not (0 <= page_idx < self.page_count):
            return False
        try:
            page = self._pdf_doc[page_idx]
            for w in page.widgets():
                if w.field_name == field_name:
                    w.field_value = value
                    w.update()
                    self.is_dirty = True
                    self._rendered_cache.clear()
                    self._invalidate_thumbnail(page_idx)
                    self.page_changed.emit(page_idx)
                    return True
        except Exception:
            pass
        return False

    def update_image(self, new_pil_image: Image.Image, page_idx: Optional[int] = None):
        """Updates internal image after adjustments, filters or crop."""
        idx = page_idx if page_idx is not None else self.current_page
        self._image_cache[idx] = new_pil_image
        if idx == self.current_page:
            self._pil_image = new_pil_image
        self._invalidate_thumbnail(idx)
        self._rendered_cache = {k: v for k, v in self._rendered_cache.items() if k[0] != idx}
        self.is_dirty = True
        self.metadata["width"] = new_pil_image.width
        self.metadata["height"] = new_pil_image.height
        self.metadata["dimensions"] = f"{new_pil_image.width} × {new_pil_image.height}"
        self.document_changed.emit()

    def delete_page(self, page_idx: int) -> bool:
        """Deletes a specific page from the document. Returns True if successful."""
        if self.page_count <= 1 or not (0 <= page_idx < self.page_count):
            return False

        if self.is_pdf and self._pdf_doc:
            try:
                self._pdf_doc.delete_page(page_idx)
                self.page_count = len(self._pdf_doc)
            except Exception:
                return False
        else:
            if 0 <= page_idx < len(self.image_paths):
                del self.image_paths[page_idx]
                self.page_count = len(self.image_paths)
            else:
                return False

        # Adjust rotations map
        new_rotations = {}
        for idx, deg in self.rotations.items():
            if idx < page_idx:
                new_rotations[idx] = deg
            elif idx > page_idx:
                new_rotations[idx - 1] = deg
        self.rotations = new_rotations

        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self._image_cache.clear()
        self.is_dirty = True

        if self.current_page >= self.page_count:
            self.current_page = max(0, self.page_count - 1)

        if not self.is_pdf and self.page_count > 0:
            self._load_current_image(self.current_page)

        self.document_changed.emit()
        self.page_changed.emit(self.current_page)
        return True

    def duplicate_page(self, page_idx: int) -> bool:
        """Duplicates the given page immediately after it."""
        if not (0 <= page_idx < self.page_count):
            return False

        if self.is_pdf and self._pdf_doc:
            try:
                temp = pymupdf.open('pdf', self._pdf_doc.tobytes())
                self._pdf_doc.insert_pdf(temp, from_page=page_idx, to_page=page_idx, start_at=page_idx + 1)
                self.page_count = len(self._pdf_doc)
            except Exception:
                return False
        else:
            if 0 <= page_idx < len(self.image_paths):
                self.image_paths.insert(page_idx + 1, self.image_paths[page_idx])
                self.page_count = len(self.image_paths)
            else:
                return False

        # Adjust rotations map
        new_rotations = {}
        for idx, deg in self.rotations.items():
            if idx <= page_idx:
                new_rotations[idx] = deg
            else:
                new_rotations[idx + 1] = deg
        if page_idx in self.rotations:
            new_rotations[page_idx + 1] = self.rotations[page_idx]
        self.rotations = new_rotations

        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self._image_cache.clear()
        self.is_dirty = True

        self.document_changed.emit()
        return True

    def insert_blank_page(self, after_page_idx: int) -> bool:
        """Inserts a blank page after the specified page index."""
        if not (0 <= after_page_idx < self.page_count):
            after_page_idx = max(0, self.page_count - 1)

        w_pt, h_pt = self.get_page_size(after_page_idx)
        insert_at = after_page_idx + 1

        if self.is_pdf and self._pdf_doc:
            try:
                self._pdf_doc.new_page(pno=insert_at, width=w_pt, height=h_pt)
                self.page_count = len(self._pdf_doc)
            except Exception:
                return False
        else:
            # For image collection, create a blank white canvas image
            try:
                blank_img = Image.new("RGB", (max(100, int(w_pt)), max(100, int(h_pt))), color="white")
                import tempfile
                tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tf.close()
                blank_img.save(tf.name)
                self.image_paths.insert(insert_at, tf.name)
                self.page_count = len(self.image_paths)
            except Exception:
                return False

        # Shift rotations
        new_rotations = {}
        for idx, deg in self.rotations.items():
            if idx < insert_at:
                new_rotations[idx] = deg
            else:
                new_rotations[idx + 1] = deg
        self.rotations = new_rotations

        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self._image_cache.clear()
        self.is_dirty = True

        self.document_changed.emit()
        return True

    def extract_text(self, page_idx: Optional[int] = None) -> str:
        """Extracts text from the current page or entire document."""
        if not self.is_pdf or not self._pdf_doc:
            return ""

        try:
            if page_idx is not None:
                if 0 <= page_idx < len(self._pdf_doc):
                    return self._pdf_doc[page_idx].get_text()
                return ""
            else:
                pages_text = []
                for p_idx, page in enumerate(self._pdf_doc):
                    txt = page.get_text().strip()
                    if txt:
                        pages_text.append(f"--- Page {p_idx + 1} ---\n{txt}")
                return "\n\n".join(pages_text)
        except Exception:
            return ""

    def export_all_to_pdf(self, output_path: str):
        """Exports the entire document (PDF or multi-image collection) to a clean PDF."""
        import io
        if self.is_pdf and self._pdf_doc:
            for p_idx, deg in self.rotations.items():
                if deg != 0 and p_idx < len(self._pdf_doc):
                    page = self._pdf_doc[p_idx]
                    page.set_rotation((page.rotation + deg) % 360)
            self._pdf_doc.save(output_path)
        else:
            master = pymupdf.open()
            for idx in range(self.page_count):
                img = self._get_pil_for_page(idx)
                if not img:
                    continue
                rot = self.rotations.get(idx, 0)
                if rot != 0:
                    img = img.rotate(-rot, expand=True)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95)
                img_doc = pymupdf.open(stream=buf.getvalue(), filetype="jpg")
                pdf_bytes = img_doc.convert_to_pdf()
                page_pdf = pymupdf.open("pdf", pdf_bytes)
                master.insert_pdf(page_pdf)
            master.save(output_path)
            master.close()
        self.is_dirty = False

    def export_document(self, output_path: str, format_name: str = "PDF", quality: int = 95, page_idx: Optional[int] = None):
        ext = os.path.splitext(output_path)[1].lower()
        target_page = self.current_page if page_idx is None else page_idx
        
        if self.is_pdf and self._pdf_doc:
            if ext == '.pdf':
                for p_idx, deg in self.rotations.items():
                    if deg != 0 and p_idx < len(self._pdf_doc):
                        page = self._pdf_doc[p_idx]
                        page.set_rotation((page.rotation + deg) % 360)
                self._pdf_doc.save(output_path)
            else:
                pix = self.render_page(target_page, zoom=2.0)
                pix.save(output_path, quality=quality)
        else:
            img = self._get_pil_for_page(target_page)
            if not img:
                return
            rot = self.rotations.get(target_page, 0)
            if rot != 0:
                img = img.rotate(-rot, expand=True)

            if ext == '.pdf':
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output_path, "PDF", resolution=150.0)
            elif ext in ['.jpg', '.jpeg']:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality)
            elif ext == '.webp':
                img.save(output_path, "WEBP", quality=quality)
            else:
                img.save(output_path, quality=quality)
        
        self.is_dirty = False

    def move_page(self, from_idx: int, to_idx: int) -> bool:
        """Moves a page from from_idx to to_idx (supports both PDF and image collections)."""
        if from_idx == to_idx or not (0 <= from_idx < self.page_count) or not (0 <= to_idx < self.page_count):
            return False

        if self.is_pdf and self._pdf_doc:
            try:
                target_to = -1 if (to_idx == self.page_count - 1 and from_idx < to_idx) else (to_idx + 1 if from_idx < to_idx else to_idx)
                self._pdf_doc.move_page(from_idx, target_to)
            except Exception:
                return False
        else:
            if 0 <= from_idx < len(self.image_paths) and 0 <= to_idx < len(self.image_paths):
                path = self.image_paths.pop(from_idx)
                self.image_paths.insert(to_idx, path)
            else:
                return False

        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self._image_cache.clear()
        self.rotations.clear()
        self.is_dirty = True
        self.current_page = to_idx
        self.document_changed.emit()
        self.page_changed.emit(to_idx)
        return True

    def insert_file(self, file_path: str, after_page_idx: int) -> bool:
        """Inserts a PDF or image into the document after the specified page index."""
        if not os.path.exists(file_path):
            return False
        if after_page_idx < 0:
            after_page_idx = -1
        elif after_page_idx >= self.page_count:
            after_page_idx = self.page_count - 1

        insert_pos = after_page_idx + 1

        if self.is_pdf and self._pdf_doc:
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext == ".pdf":
                    src_pdf = pymupdf.open(file_path)
                    self._pdf_doc.insert_pdf(src_pdf, start_at=insert_pos)
                    src_pdf.close()
                elif ext in SUPPORTED_IMAGE_EXTS:
                    img = Image.open(file_path)
                    w, h = float(img.width), float(img.height)
                    page = self._pdf_doc.new_page(pno=insert_pos, width=w, height=h)
                    page.insert_image(page.rect, filename=file_path)
                else:
                    return False
                self.page_count = len(self._pdf_doc)
            except Exception:
                return False
        else:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in SUPPORTED_IMAGE_EXTS:
                self.image_paths.insert(insert_pos, os.path.abspath(file_path))
                self.page_count = len(self.image_paths)
            elif ext == ".pdf":
                src_pdf = pymupdf.open(file_path)
                for pno in range(len(src_pdf)):
                    p = src_pdf[pno]
                    pix = p.get_pixmap(dpi=150)
                    tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    pix.save(tf.name)
                    tf.close()
                    self.image_paths.insert(insert_pos + pno, tf.name)
                src_pdf.close()
                self.page_count = len(self.image_paths)
            else:
                return False

        self._thumbnail_cache.clear()
        self._rendered_cache.clear()
        self.is_dirty = True
        self.document_changed.emit()
        return True

    @classmethod
    def merge_pdfs(cls, pdf_paths: List[str], output_path: str) -> bool:
        """Merges multiple PDF files into a single destination PDF."""
        if not pdf_paths:
            return False
        try:
            merged = pymupdf.open()
            for p in pdf_paths:
                if os.path.isfile(p):
                    doc = pymupdf.open(p)
                    merged.insert_pdf(doc)
                    doc.close()
            merged.save(output_path)
            merged.close()
            return True
        except Exception:
            return False

    def split_pdf(self, output_path: str, page_indices: List[int]) -> bool:
        """Extracts specified page indices into a new standalone PDF."""
        if not self.is_pdf or not self._pdf_doc:
            return False
        try:
            split_doc = pymupdf.open()
            for p_idx in page_indices:
                if 0 <= p_idx < self.page_count:
                    split_doc.insert_pdf(self._pdf_doc, from_page=p_idx, to_page=p_idx)
            split_doc.save(output_path)
            split_doc.close()
            return True
        except Exception:
            return False

    def set_pdf_password(self, user_pw: str, owner_pw: Optional[str] = None):
        """Sets a security password to encrypt the document upon saving."""
        self._pending_user_pw = user_pw
        self._pending_owner_pw = owner_pw or user_pw
        self.is_dirty = True

    def apply_permanent_redactions(self, page_idx: Optional[int] = None) -> bool:
        """Applies pending redactions to the PDF permanently, stripping text/graphics underneath."""
        if not self.is_pdf or not self._pdf_doc:
            return False
        pages = [page_idx] if page_idx is not None else list(range(self.page_count))
        for p in pages:
            if 0 <= p < len(self._pdf_doc):
                self._pdf_doc[p].apply_redactions()
        self.is_dirty = True
        self._rendered_cache.clear()
        self._thumbnail_cache.clear()
        self.document_changed.emit()
        return True

    def save_with_annotations(
        self, 
        output_path: str, 
        annotations_map: Dict[int, List[Any]], 
        user_pw: Optional[str] = None, 
        owner_pw: Optional[str] = None
    ) -> bool:
        """
        Saves document to output_path while baking user annotations (pen, highlighter,
        shapes, text, notes, signatures, redactions) directly into the file.
        """
        abs_out = os.path.abspath(output_path)
        ext = os.path.splitext(output_path)[1].lower()

        if self.is_pdf and self._pdf_doc:
            for p_idx, deg in self.rotations.items():
                if deg != 0 and p_idx < len(self._pdf_doc):
                    page = self._pdf_doc[p_idx]
                    page.set_rotation((page.rotation + deg) % 360)
            self.rotations.clear()

            from preview.core.annotations import AnnotationType

            for p_idx, annots in annotations_map.items():
                if 0 <= p_idx < len(self._pdf_doc):
                    page = self._pdf_doc[p_idx]
                    for item in annots:
                        itype = getattr(item, "item_type", None)
                        if not itype:
                            continue

                        def qcol_to_rgb(qc):
                            if qc and qc.isValid():
                                return (qc.red() / 255.0, qc.green() / 255.0, qc.blue() / 255.0)
                            return (0.0, 0.0, 0.0)

                        stroke_rgb = qcol_to_rgb(getattr(item, "stroke_color", None))
                        fill_qc = getattr(item, "fill_color", None)
                        has_fill = fill_qc and fill_qc.isValid() and fill_qc.alpha() > 0
                        fill_rgb = qcol_to_rgb(fill_qc) if has_fill else None
                        w = getattr(item, "stroke_width", 2.0)

                        if itype == AnnotationType.PEN:
                            if len(item.points) > 1:
                                pt_list = [(float(p.x()), float(p.y())) for p in item.points]
                                annot = page.add_ink_annot([pt_list])
                                annot.set_colors(stroke=stroke_rgb)
                                annot.set_border(width=w)
                                annot.update()

                        elif itype == AnnotationType.HIGHLIGHTER:
                            if len(item.points) > 1:
                                pt_list = [(float(p.x()), float(p.y())) for p in item.points]
                                annot = page.add_ink_annot([pt_list])
                                annot.set_colors(stroke=stroke_rgb)
                                annot.set_border(width=max(12.0, w * 3))
                                annot.set_opacity(0.4)
                                annot.update()

                        elif itype in (AnnotationType.RECTANGLE, AnnotationType.ROUNDED_RECT):
                            r = pymupdf.Rect(item.rect.left(), item.rect.top(), item.rect.right(), item.rect.bottom())
                            annot = page.add_rect_annot(r)
                            annot.set_colors(stroke=stroke_rgb, fill=fill_rgb)
                            annot.set_border(width=w)
                            annot.update()

                        elif itype == AnnotationType.ELLIPSE:
                            r = pymupdf.Rect(item.rect.left(), item.rect.top(), item.rect.right(), item.rect.bottom())
                            annot = page.add_circle_annot(r)
                            annot.set_colors(stroke=stroke_rgb, fill=fill_rgb)
                            annot.set_border(width=w)
                            annot.update()

                        elif itype in (AnnotationType.LINE, AnnotationType.ARROW):
                            if len(item.points) >= 2:
                                p1 = pymupdf.Point(item.points[0].x(), item.points[0].y())
                                p2 = pymupdf.Point(item.points[1].x(), item.points[1].y())
                                annot = page.add_line_annot(p1, p2)
                                annot.set_colors(stroke=stroke_rgb)
                                annot.set_border(width=w)
                                annot.update()

                        elif itype == AnnotationType.TEXT:
                            r = pymupdf.Rect(item.rect.left(), item.rect.top(), item.rect.right(), item.rect.bottom())
                            fsize = getattr(item, "font_size", 16)
                            annot = page.add_freetext_annot(r, item.text, fontsize=fsize, text_color=stroke_rgb, fill_color=fill_rgb)
                            annot.update()

                        elif itype == AnnotationType.NOTE:
                            pt = pymupdf.Point(item.rect.left(), item.rect.top())
                            annot = page.add_text_annot(pt, item.text)
                            annot.update()

                        elif itype == AnnotationType.REDACT:
                            r = pymupdf.Rect(item.rect.left(), item.rect.top(), item.rect.right(), item.rect.bottom())
                            page.add_redact_annot(r, fill=(0, 0, 0))
                            page.apply_redactions()

                        elif itype == AnnotationType.SIGNATURE:
                            if len(item.points) > 1 or item.rect.isValid():
                                r = pymupdf.Rect(item.rect.left(), item.rect.top(), item.rect.right(), item.rect.bottom())
                                if r.width > 0 and r.height > 0:
                                    pix = QPixmap(int(r.width * 2), int(r.height * 2))
                                    pix.fill(Qt.GlobalColor.transparent)
                                    p = QPainter(pix)
                                    p.setRenderHint(QPainter.RenderHint.Antialiasing)
                                    pen = QPen(item.stroke_color, item.stroke_width * 2)
                                    p.setPen(pen)
                                    for i in range(1, len(item.points)):
                                        p1 = (item.points[i-1] - item.rect.topLeft()) * 2
                                        p2 = (item.points[i] - item.rect.topLeft()) * 2
                                        p.drawLine(p1, p2)
                                    p.end()
                                    buf = QBuffer()
                                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                                    pix.save(buf, "PNG")
                                    page.insert_image(r, stream=buf.data().data())
                                    buf.close()

            is_same_file = (self.file_path and os.path.abspath(self.file_path) == abs_out)
            save_kwargs: Dict[str, Any] = {"deflate": True}
            pw = user_pw or getattr(self, "_pending_user_pw", None)
            if pw:
                save_kwargs["encryption"] = pymupdf.PDF_ENCRYPT_AES_256
                save_kwargs["user_pw"] = pw
                save_kwargs["owner_pw"] = owner_pw or pw

            if is_same_file:
                dir_name = os.path.dirname(abs_out)
                with tempfile.NamedTemporaryFile(suffix=".pdf", dir=dir_name, delete=False) as tf:
                    tmp_name = tf.name
                self._pdf_doc.save(tmp_name, **save_kwargs)
                self._pdf_doc.close()
                shutil.move(tmp_name, abs_out)
                self._pdf_doc = pymupdf.open(abs_out)
            else:
                self._pdf_doc.save(abs_out, **save_kwargs)

            self.file_path = abs_out
            self.file_name = os.path.basename(abs_out)
            self.is_dirty = False
            self._thumbnail_cache.clear()
            self._rendered_cache.clear()
            self.document_changed.emit()
            return True

        else:
            if ext == ".pdf":
                master = pymupdf.open()
                for idx in range(self.page_count):
                    page_pix = self.render_page(idx, zoom=2.0)
                    annot_painter = QPainter(page_pix)
                    if idx in annotations_map:
                        for item in annotations_map[idx]:
                            item.draw(annot_painter, zoom=2.0)
                    annot_painter.end()
                    
                    buf = QBuffer()
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    page_pix.save(buf, "PNG")
                    img_doc = pymupdf.open(stream=buf.data().data(), filetype="png")
                    pdf_bytes = img_doc.convert_to_pdf()
                    p_pdf = pymupdf.open("pdf", pdf_bytes)
                    master.insert_pdf(p_pdf)
                    buf.close()
                master.save(abs_out)
                master.close()
            else:
                idx = self.current_page
                page_pix = self.render_page(idx, zoom=1.0)
                annot_painter = QPainter(page_pix)
                if idx in annotations_map:
                    for item in annotations_map[idx]:
                        item.draw(annot_painter, zoom=1.0)
                annot_painter.end()
                page_pix.save(abs_out)

            self.is_dirty = False
            self._thumbnail_cache.clear()
            self._rendered_cache.clear()
            self.document_changed.emit()
            return True
