"""In-memory store: document_id → OCR text (no vector DB)."""
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
                "status": "processing",
                "added_at": datetime.now().isoformat(),
            }

    def set_ocr_result(self, document_id: str, ocr_text: str, success: bool, error: str = "") -> None:
        with self._lock:
            if document_id not in self._docs:
                return
            if success:
                self._docs[document_id]["ocr_text"] = ocr_text
                self._docs[document_id]["status"] = "ready"
            else:
                self._docs[document_id]["status"] = "failed"
                self._docs[document_id]["error"] = error or "Text extraction failed"

    def get_ocr_text(self, document_id: str) -> Optional[str]:
        with self._lock:
            d = self._docs.get(document_id)
            if not d or d.get("status") != "ready":
                return None
            t = (d.get("ocr_text") or "").strip()
            return t or None

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
                if d and d.get("status") == "ready" and (d.get("ocr_text") or "").strip():
                    parts.append(f"### File: {d['name']}\n{d['ocr_text'].strip()}")
            else:
                for d in self._docs.values():
                    if d.get("status") != "ready":
                        continue
                    txt = (d.get("ocr_text") or "").strip()
                    if not txt:
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
                out.append(
                    {
                        "document_id": doc_id,
                        "name": d.get("name", ""),
                        "chunks": 1,
                        "text_length": len(text),
                        "added_at": d.get("added_at", ""),
                        "status": d.get("status", "unknown"),
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
