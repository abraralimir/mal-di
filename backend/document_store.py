"""In-memory store: document_id → OCR text, layout, LLM analysis (no vector DB)."""
from __future__ import annotations

import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional


class DocumentStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._docs: Dict[str, Dict[str, Any]] = {}

    def register(self, document_id: str, name: str, file_path: str) -> None:
        with self._lock:
            self._docs[document_id] = {
                "document_id": document_id,
                "name": name,
                "file_path": file_path,
                "ocr_text": "",
                "layout_pages": [],
                "analysis": None,
                "status": "processing",
                "added_at": datetime.now().isoformat(),
            }

    def set_ocr_result(
        self,
        document_id: str,
        ocr_text: str,
        success: bool,
        error: str = "",
        layout_pages: Optional[List[dict]] = None,
    ) -> None:
        with self._lock:
            if document_id not in self._docs:
                return
            if success:
                self._docs[document_id]["ocr_text"] = ocr_text
                self._docs[document_id]["layout_pages"] = list(layout_pages or [])
                self._docs[document_id]["status"] = "processing"
            else:
                self._docs[document_id]["status"] = "failed"
                self._docs[document_id]["error"] = error or "Text extraction failed"
                self._docs[document_id]["layout_pages"] = []

    def set_analysis(self, document_id: str, analysis: Optional[dict]) -> None:
        with self._lock:
            if document_id not in self._docs:
                return
            self._docs[document_id]["analysis"] = analysis
            if self._docs[document_id].get("status") != "failed":
                self._docs[document_id]["status"] = "ready"

    def get_ocr_text(self, document_id: str) -> Optional[str]:
        with self._lock:
            d = self._docs.get(document_id)
            if not d or d.get("status") == "failed":
                return None
            t = (d.get("ocr_text") or "").strip()
            return t or None

    def get_document(self, document_id: str) -> Optional[dict]:
        with self._lock:
            d = self._docs.get(document_id)
            if not d:
                return None
            return dict(d)

    def build_context(
        self,
        document_id: Optional[str],
        max_chars: int = 95_000,
    ) -> str:
        """One document’s OCR, or all ready documents concatenated (truncated)."""
        with self._lock:
            parts: List[str] = []
            if document_id:
                d = self._docs.get(document_id)
                if (
                    d
                    and d.get("status") != "failed"
                    and (d.get("ocr_text") or "").strip()
                    and d.get("status") in ("ready", "processing")
                ):
                    parts.append(f"### File: {d['name']}\n{d['ocr_text'].strip()}")
            else:
                for d in self._docs.values():
                    if d.get("status") == "failed":
                        continue
                    txt = (d.get("ocr_text") or "").strip()
                    if not txt or d.get("status") not in ("ready", "processing"):
                        continue
                    parts.append(f"### File: {d['name']}\n{txt}")
            blob = "\n\n---\n\n".join(parts)
            if len(blob) > max_chars:
                blob = blob[:max_chars] + "\n\n[... truncated for model context ...]"
            return blob

    def list_documents(self) -> List[dict]:
        with self._lock:
            out: List[dict] = []
            for doc_id, d in self._docs.items():
                text = d.get("ocr_text") or ""
                layout = d.get("layout_pages") or []
                block_count = sum(len(p.get("blocks") or []) for p in layout)
                out.append(
                    {
                        "document_id": doc_id,
                        "name": d.get("name", ""),
                        "chunks": 1,
                        "text_length": len(text),
                        "added_at": d.get("added_at", ""),
                        "status": d.get("status", "unknown"),
                        "layout_blocks": block_count,
                        "has_analysis": d.get("analysis") is not None,
                    }
                )
            return out

    def delete(self, document_id: str) -> bool:
        with self._lock:
            if document_id not in self._docs:
                return False
            path = self._docs[document_id].get("file_path")
            del self._docs[document_id]
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
        return True
