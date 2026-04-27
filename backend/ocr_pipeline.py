"""
Lightweight text extraction: native PDF text (PyMuPDF) first, then
RapidOCR (ONNX) for pages/images with little or no embedded text.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import fitz  # PyMuPDF
import numpy as np

logger = logging.getLogger(__name__)

# Minimum characters on a PDF page before we skip OCR for that page
_MIN_NATIVE_PAGE_CHARS = 40


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

    def _ocr_ndarray(self, bgr: np.ndarray) -> str:
        if bgr is None or bgr.size == 0:
            return ""
        rapid = self._get_rapid()
        result, _elapsed = rapid(bgr)
        if not result:
            return ""
        lines: List[str] = []
        for item in result:
            if not isinstance(item, (list, tuple)) or not item:
                continue
            text: Optional[str] = None
            if len(item) >= 2 and isinstance(item[1], str):
                text = item[1]
            elif len(item) >= 1 and isinstance(item[0], str):
                text = item[0]
            if text and str(text).strip():
                lines.append(str(text).strip())
        return "\n".join(lines)

    def _extract_pdf(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        parts: List[str] = []
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                native = (page.get_text("text") or "").strip()
                if len(native) >= _MIN_NATIVE_PAGE_CHARS:
                    parts.append(native)
                    continue
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
                ocr_text = self._ocr_ndarray(img)
                if ocr_text:
                    parts.append(ocr_text)
                elif native:
                    parts.append(native)
        finally:
            doc.close()
        return "\n\n".join(p for p in parts if p)

    def _extract_image(self, file_path: str) -> str:
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"Could not read image: {file_path}")
        return self._ocr_ndarray(image)

    def ocr_document(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "full_text": "", "error": f"File not found: {file_path}"}

        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                text = self._extract_pdf(str(path))
            elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                text = self._extract_image(str(path))
            else:
                return {
                    "success": False,
                    "full_text": "",
                    "error": f"Unsupported format: {suffix}",
                }

            text = (text or "").strip()
            if not text:
                return {
                    "success": False,
                    "full_text": "",
                    "error": "No readable text found in this file.",
                }

            return {"success": True, "full_text": text, "error": None}
        except Exception as e:
            logger.exception("Text extraction failed for %s", file_path)
            return {"success": False, "full_text": "", "error": str(e)}
