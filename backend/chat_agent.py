"""Q&A with document text as context (no vector search)."""
import logging
from typing import Any, Dict, List, Optional

import requests

from document_store import DocumentStore

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


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

    def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        use_rag: bool = True,
        max_tokens: int = 2048,
        temperature: float = 0.35,
    ) -> Dict[str, Any]:
        _ = use_rag  # API compatibility; flow is OCR → Groq only
        try:
            doc_text = self.document_store.build_context(document_id=document_id)
            if doc_text.strip():
                user_content = (
                    "Document text:\n\n"
                    f"{doc_text}\n\n---\n\nQuestion: {question}\n\nAnswer clearly and concisely."
                )
            else:
                user_content = (
                    f"No document text is available yet (upload a file and wait for processing). "
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
