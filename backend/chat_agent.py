"""Q&A with document text as context (no vector search)."""
import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests

from document_store import DocumentStore

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _strip_json_fences(raw: str) -> str:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def _classification_excerpt(ocr_text: str, max_chars: int = 3200, max_lines: int = 45) -> str:
    """Small snippet for Groq only (avoids 413 / huge payloads). First PDF 'page' + line cap."""
    text = (ocr_text or "").strip()
    if not text:
        return ""
    first_block = text.split("\n\n")[0].strip() or text
    lines = first_block.splitlines()[:max_lines]
    snippet = "\n".join(lines).strip() or first_block
    if len(snippet) < 80:
        snippet = text[:max_chars]
    return snippet[:max_chars]


class ChatAgent:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        document_store: DocumentStore,
    ):
        if not api_key or not str(api_key).strip():
            raise ValueError("GROQ_API_KEY is required for chat")
        self.api_key = str(api_key).strip()
        self.model_name = model_name
        self.document_store = document_store

    def _groq_complete(
        self, user_content: str, max_tokens: int = 2048, temperature: float = 0.35
    ) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You answer from the user's document text when it is provided. "
                        "Quote or paraphrase accurately. If the answer is not in the text, say so. "
                        "Match the user's language (Arabic or English). "
                        "If the text looks like a form, application, or labeled fields (including Arabic forms), "
                        "and the user asks what the document is about, for a summary, or about fields/values, "
                        "give a short purpose/overview first, then list clear field → value lines only when "
                        "those labels or values appear in the text—do not invent fields. "
                        "For tables, preserve row meaning in plain language."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        r = requests.post(
            GROQ_CHAT_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    def _groq_chat_payload(
        self,
        messages: List[dict],
        max_tokens: int,
        temperature: float,
        response_format: Optional[dict] = None,
    ) -> dict:
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        return payload

    def analyze_document_structure(self, ocr_text: str) -> Dict[str, Any]:
        """LLM: document type, short summary, form fields / entities (JSON)."""
        excerpt = _classification_excerpt(ocr_text)
        if not excerpt:
            return {
                "document_type": "Unknown",
                "classification_summary": "",
                "fields": [],
                "entities": [],
            }

        user_msg = (
            "The following is only the beginning of a document (first page / first lines). "
            "Infer document type and visible structure from this snippet only. "
            "Return **only** a JSON object (no markdown) with exactly these keys:\n"
            '"document_type": string (e.g. invoice, form, contract, letter, id, table, other),\n'
            '"classification_summary": string (one or two sentences),\n'
            '"fields": array of {"label": string, "value": string, "confidence": "high"|"medium"|"low"},\n'
            '"entities": array of {"type": string, "value": string} for names, dates, amounts, IDs if clearly present.\n'
            "Rules: Prefer Arabic or English labels as they appear. Do not invent values; if unsure leave value empty. "
            "Limit fields to at most 25 rows.\n\n"
            "OCR snippet:\n\n"
            f"{excerpt}"
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict document analyst. Output only valid JSON matching the user schema."
                ),
            },
            {"role": "user", "content": user_msg},
        ]

        last_err: Optional[str] = None
        for fmt in ({"type": "json_object"}, None):
            try:
                payload = self._groq_chat_payload(
                    messages,
                    max_tokens=2048,
                    temperature=0.15,
                    response_format=fmt,
                )
                r = requests.post(
                    GROQ_CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=120,
                )
                r.raise_for_status()
                raw = (r.json()["choices"][0]["message"]["content"] or "").strip()
                parsed = json.loads(_strip_json_fences(raw))
                if not isinstance(parsed, dict):
                    raise ValueError("root must be object")
                out = {
                    "document_type": str(parsed.get("document_type", "other") or "other"),
                    "classification_summary": str(
                        parsed.get("classification_summary", "") or ""
                    ),
                    "fields": parsed.get("fields") if isinstance(parsed.get("fields"), list) else [],
                    "entities": parsed.get("entities")
                    if isinstance(parsed.get("entities"), list)
                    else [],
                }
                return out
            except Exception as e:
                last_err = str(e)
                logger.warning("analyze_document_structure attempt failed (format=%s): %s", fmt, e)
                continue

        return {
            "document_type": "Unknown",
            "classification_summary": "",
            "fields": [],
            "entities": [],
            "error": last_err or "analysis failed",
        }

    def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        use_rag: bool = True,
        preferred_language: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.35,
    ) -> Dict[str, Any]:
        _ = use_rag  # API compatibility; flow is OCR → Groq only
        try:
            pref = (preferred_language or "").strip().lower()
            lang_hint = ""
            if pref in {"ar", "arabic"}:
                lang_hint = "Answer in Arabic.\n\n"
            elif pref in {"en", "english"}:
                lang_hint = "Answer in English.\n\n"

            doc_text = self.document_store.build_context(document_id=document_id)
            if doc_text.strip():
                user_content = (
                    f"{lang_hint}Document text:\n\n"
                    f"{doc_text}\n\n---\n\nQuestion: {question}\n\nAnswer clearly and concisely."
                )
            else:
                user_content = (
                    f"{lang_hint}No document text is available yet (upload a file and wait for processing). "
                    f"Question: {question}\n\nAnswer briefly, or say you need document content."
                )

            answer = self._groq_complete(
                user_content, max_tokens=max_tokens, temperature=temperature
            )

            return {
                "success": True,
                "question": question,
                "answer": answer,
                "sources": [],
                "model": self.model_name,
                "used_rag": False,
            }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question,
            }

    def batch_qa(
        self,
        questions: List[str],
        document_id: Optional[str] = None,
        use_rag: bool = True,
    ) -> List[Dict[str, Any]]:
        return [self.answer_question(q, document_id, use_rag) for q in questions]
