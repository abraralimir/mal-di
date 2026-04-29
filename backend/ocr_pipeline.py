"""
Lightweight text extraction: native PDF text (PyMuPDF) first, then
RapidOCR (ONNX) for pages/images with little or no embedded text.
Returns full_text plus per-page layout (normalized bboxes) for UI overlays.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import fitz  # PyMuPDF
import numpy as np

logger = logging.getLogger(__name__)

# Minimum characters on a PDF page before we skip OCR for that page
_MIN_NATIVE_PAGE_CHARS = 40

_MAX_BLOCKS_PER_PAGE = 140
_MAX_BLOCKS_TOTAL = 450


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _norm_rect(x0: float, y0: float, x1: float, y1: float) -> Tuple[float, float, float, float]:
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return _clamp01(x0), _clamp01(y0), _clamp01(x1), _clamp01(y1)


def _quad_to_norm(quad: Any, w: int, h: int) -> Optional[Tuple[float, float, float, float]]:
    if quad is None or w <= 0 or h <= 0:
        return None
    try:
        if hasattr(quad, "tolist"):
            quad = quad.tolist()
        pts = []
        for p in quad:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                pts.append((float(p[0]), float(p[1])))
        if len(pts) < 4:
            return None
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return _norm_rect(min(xs) / w, min(ys) / h, max(xs) / w, max(ys) / h)
    except (TypeError, ValueError, IndexError):
        return None


class OCRPipeline:
    """Extracts text from PDFs and images without heavy deep-learning stacks."""

    def __init__(self, languages: Optional[str] = None, device: Optional[str] = None):
        self._languages = languages or "ar,en"
        self._device = device
        self._rapid = None

    def _get_rapid(self):
        if self._rapid is None:
            from rapidocr_onnxruntime import RapidOCR

            self._rapid = RapidOCR()
        return self._rapid

    def _parse_rapid_item(self, item: Any) -> Tuple[Optional[Any], str]:
        """Return (quad_or_none, text) from one RapidOCR result row."""
        if not isinstance(item, (list, tuple)) or not item:
            return None, ""
        text: str = ""
        quad: Any = None
        if len(item) >= 2 and isinstance(item[1], str):
            quad, text = item[0], item[1]
        elif len(item) >= 1 and isinstance(item[0], str):
            text = item[0]
        else:
            quad = item[0] if item else None
            if len(item) >= 2 and not isinstance(item[1], str):
                pass
        return quad, (text or "").strip()

    def _ocr_ndarray_layout(self, bgr: np.ndarray) -> Tuple[str, List[Dict[str, Any]]]:
        if bgr is None or bgr.size == 0:
            return "", []
        h, w = int(bgr.shape[0]), int(bgr.shape[1])
        rapid = self._get_rapid()
        result, _elapsed = rapid(bgr)
        if not result:
            return "", []
        lines: List[str] = []
        blocks: List[Dict[str, Any]] = []
        for item in result:
            quad, text = self._parse_rapid_item(item)
            if not text:
                continue
            lines.append(text)
            nr = _quad_to_norm(quad, w, h) if quad is not None else None
            if nr:
                x0, y0, x1, y1 = nr
                blocks.append(
                    {
                        "text": text[:400],
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "source": "ocr",
                    }
                )
            else:
                blocks.append({"text": text[:400], "x0": 0, "y0": 0, "x1": 1, "y1": 0.02, "source": "ocr"})
        return "\n".join(lines), blocks[:_MAX_BLOCKS_PER_PAGE]

    def _native_blocks_for_page(self, page: fitz.Page) -> List[Dict[str, Any]]:
        pw = float(page.rect.width) or 1.0
        ph = float(page.rect.height) or 1.0
        blocks: List[Dict[str, Any]] = []
        try:
            td = page.get_text("dict") or {}
        except Exception:
            return []
        for b in td.get("blocks") or []:
            if b.get("type") != 0:
                continue
            for line in b.get("lines") or []:
                text = "".join(s.get("text", "") for s in line.get("spans") or [])
                text = (text or "").strip()
                if not text:
                    continue
                bbox = line.get("bbox")
                if not bbox or len(bbox) < 4:
                    continue
                x0, y0, x1, y1 = _norm_rect(
                    float(bbox[0]) / pw,
                    float(bbox[1]) / ph,
                    float(bbox[2]) / pw,
                    float(bbox[3]) / ph,
                )
                blocks.append(
                    {
                        "text": text[:400],
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "source": "native",
                    }
                )
                if len(blocks) >= _MAX_BLOCKS_PER_PAGE:
                    return blocks
        return blocks

    def _extract_pdf_layout(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        doc = fitz.open(file_path)
        pages_out: List[Dict[str, Any]] = []
        text_parts: List[str] = []
        total_blocks = 0
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                pw = float(page.rect.width) or 1.0
                ph = float(page.rect.height) or 1.0
                native = (page.get_text("text") or "").strip()
                if len(native) >= _MIN_NATIVE_PAGE_CHARS:
                    blocks = self._native_blocks_for_page(page)
                    if not blocks and native.strip():
                        blocks = [
                            {
                                "text": native.strip()[:800],
                                "x0": 0.02,
                                "y0": 0.02,
                                "x1": 0.98,
                                "y1": 0.98,
                                "source": "native",
                            }
                        ]
                    if total_blocks + len(blocks) > _MAX_BLOCKS_TOTAL:
                        blocks = blocks[: max(0, _MAX_BLOCKS_TOTAL - total_blocks)]
                    total_blocks += len(blocks)
                    pages_out.append(
                        {
                            "page_index": page_index,
                            "width_pt": pw,
                            "height_pt": ph,
                            "source": "native",
                            "blocks": blocks,
                        }
                    )
                    text_parts.append(native)
                else:
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                        pix.height, pix.width, pix.n
                    )
                    if pix.n == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                    elif pix.n == 1:
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    else:
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    ocr_text, blocks = self._ocr_ndarray_layout(img)
                    for b in blocks:
                        b["source"] = "ocr"
                    if total_blocks + len(blocks) > _MAX_BLOCKS_TOTAL:
                        blocks = blocks[: max(0, _MAX_BLOCKS_TOTAL - total_blocks)]
                    total_blocks += len(blocks)
                    pages_out.append(
                        {
                            "page_index": page_index,
                            "width_pt": pw,
                            "height_pt": ph,
                            "source": "ocr",
                            "blocks": blocks,
                        }
                    )
                    if ocr_text:
                        text_parts.append(ocr_text)
                    elif native:
                        text_parts.append(native)
        finally:
            doc.close()
        return "\n\n".join(p for p in text_parts if p), pages_out

    def _extract_image_layout(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"Could not read image: {file_path}")
        text, blocks = self._ocr_ndarray_layout(image)
        h, w = image.shape[:2]
        pages_out = [
            {
                "page_index": 0,
                "width_pt": float(w),
                "height_pt": float(h),
                "source": "ocr",
                "blocks": blocks,
            }
        ]
        return text, pages_out

    def ocr_document(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "full_text": "",
                "pages": [],
                "error": f"File not found: {file_path}",
            }

        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                text, pages = self._extract_pdf_layout(str(path))
            elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                text, pages = self._extract_image_layout(str(path))
            else:
                return {
                    "success": False,
                    "full_text": "",
                    "pages": [],
                    "error": f"Unsupported format: {suffix}",
                }

            text = (text or "").strip()
            if not text:
                return {
                    "success": False,
                    "full_text": "",
                    "pages": [],
                    "error": "No readable text found in this file.",
                }

            return {"success": True, "full_text": text, "pages": pages, "error": None}
        except Exception as e:
            logger.exception("Text extraction failed for %s", file_path)
            return {"success": False, "full_text": "", "pages": [], "error": str(e)}
