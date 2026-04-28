"""MAL Document Intelligence — upload / enterprise import → text extraction → Q&A."""
import logging
import uuid
import warnings
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

warnings.filterwarnings("ignore", category=UserWarning, module="requests")

import requests
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from chat_agent import ChatAgent
from config import settings
from connectors import init_integration_pools, shutdown_integration_pools
from connectors.registry import bpm_pool, filenet_pool
from document_store import DocumentStore
from integration_settings_store import (
    IntegrationsSaveBody,
    public_view,
    read_effective,
    save_integration_settings,
)
from ocr_pipeline import OCRPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
for _name in ("urllib3", "onnxruntime"):
    logging.getLogger(_name).setLevel(logging.WARNING)

ocr_pipeline = None
document_store: DocumentStore | None = None
chat_agent = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    upload_time: str
    ocr_status: str
    vision_status: str


class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    use_rag: bool = True
    preferred_language: Optional[str] = None


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict] = []
    model: str
    used_rag: bool


class DocumentList(BaseModel):
    documents: List[dict]


class IntegrationImportBody(BaseModel):
    """Exactly one of relative_path (under configured base URL) or resource_url (same host as base)."""

    relative_path: Optional[str] = None
    resource_url: Optional[str] = None
    filename: str = Field(..., min_length=1, max_length=512)

    @model_validator(mode="after")
    def _one_source(self) -> "IntegrationImportBody":
        rp = (self.relative_path or "").strip()
        ru = (self.resource_url or "").strip()
        if bool(rp) == bool(ru):
            raise ValueError("Provide exactly one of relative_path or resource_url")
        return self


def _safe_filename(raw: str) -> str:
    if not raw or "\x00" in raw:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if "/" in raw or "\\" in raw:
        raise HTTPException(status_code=400, detail="Filename must not contain paths")
    base = Path(raw).name.strip()
    if not base or base in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return base


def _persist_and_schedule(
    content: bytes,
    filename: str,
    background_tasks: Optional[BackgroundTasks],
) -> DocumentUploadResponse:
    if not document_store or not ocr_pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")

    safe_name = _safe_filename(filename)
    doc_id = str(uuid.uuid4())
    file_path = settings.UPLOADS_DIR / f"{doc_id}_{safe_name}"

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("Saved file: %s", file_path)
    document_store.register(doc_id, safe_name, str(file_path))

    if background_tasks:
        background_tasks.add_task(
            process_document_async,
            doc_id,
            str(file_path),
            safe_name,
        )

    return DocumentUploadResponse(
        document_id=doc_id,
        filename=safe_name,
        upload_time=datetime.now().isoformat(),
        ocr_status="processing",
        vision_status="skipped",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ocr_pipeline, document_store, chat_agent

    try:
        if not settings.GROQ_API_KEY or not str(settings.GROQ_API_KEY).strip():
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your project root .env file."
            )

        ocr_langs = [
            x.strip() for x in settings.OCR_LANGUAGE.split(",") if x.strip()
        ] or ["ar"]

        logger.info("Initializing text extractor (PDF + images)...")
        ocr_pipeline = OCRPipeline(languages=",".join(ocr_langs), device="cpu")

        document_store = DocumentStore()
        logger.info("Document store ready.")

        init_integration_pools(settings)

        logger.info("Initializing Q&A (%s)...", settings.GROQ_MODEL)
        chat_agent = ChatAgent(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            document_store=document_store,
        )

        logger.info("Startup complete.")

    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise

    yield

    shutdown_integration_pools()
    logger.info("Shutting down...")


app = FastAPI(
    title="MAL Document Intelligence System",
    description="Upload or import documents, then ask questions grounded in their text.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "MAL Document Intelligence System",
        "version": "2.0.0",
        "status": "ready",
    }


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    return _persist_and_schedule(content, file.filename, background_tasks)


@app.post("/integrations/bpm/document", response_model=DocumentUploadResponse)
async def import_document_from_bpm(
    body: IntegrationImportBody,
    background_tasks: BackgroundTasks,
):
    if not bpm_pool:
        raise HTTPException(
            status_code=503,
            detail="IBM BPM connector is not active. Set base URL and pool settings under Connections, then save.",
        )
    try:
        rp = (body.relative_path or "").strip()
        ru = (body.resource_url or "").strip()
        data, _ct = bpm_pool.get_bytes(
            relative_path=rp or None,
            resource_url=ru or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.RequestException as e:
        logger.warning("BPM fetch failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve the document from the configured BPM endpoint.",
        ) from e

    return _persist_and_schedule(data, body.filename, background_tasks)


@app.post("/integrations/filenet/document", response_model=DocumentUploadResponse)
async def import_document_from_filenet(
    body: IntegrationImportBody,
    background_tasks: BackgroundTasks,
):
    if not filenet_pool:
        raise HTTPException(
            status_code=503,
            detail="FileNet connector is not active. Set base URL and pool settings under Connections, then save.",
        )
    try:
        rp = (body.relative_path or "").strip()
        ru = (body.resource_url or "").strip()
        data, _ct = filenet_pool.get_bytes(
            relative_path=rp or None,
            resource_url=ru or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.RequestException as e:
        logger.warning("FileNet fetch failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve the document from the configured FileNet endpoint.",
        ) from e

    return _persist_and_schedule(data, body.filename, background_tasks)


@app.get("/integrations/settings")
async def get_integration_settings():
    eff = read_effective(settings)
    return {
        "form": public_view(eff),
        "runtime": {
            "ibm_bpm": bpm_pool.describe() if bpm_pool else None,
            "filenet": filenet_pool.describe() if filenet_pool else None,
        },
    }


@app.put("/integrations/settings")
async def put_integration_settings(body: IntegrationsSaveBody):
    save_integration_settings(settings, body)
    shutdown_integration_pools()
    init_integration_pools(settings)
    eff = read_effective(settings)
    return {
        "form": public_view(eff),
        "runtime": {
            "ibm_bpm": bpm_pool.describe() if bpm_pool else None,
            "filenet": filenet_pool.describe() if filenet_pool else None,
        },
    }


async def process_document_async(doc_id: str, file_path: str, filename: str):
    if not ocr_pipeline or not document_store:
        return
    try:
        logger.info("Text extraction for %s", doc_id)
        ocr_result = ocr_pipeline.ocr_document(file_path)
        if ocr_result.get("success"):
            text = ocr_result.get("full_text") or ""
            document_store.set_ocr_result(doc_id, text, True)
            logger.info("Extraction done %s chars", len(text))
        else:
            document_store.set_ocr_result(
                doc_id,
                "",
                False,
                str(ocr_result.get("error", "Extraction failed")),
            )
    except Exception as e:
        logger.error("Extraction task failed: %s", e)
        document_store.set_ocr_result(doc_id, "", False, str(e))


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if not chat_agent:
        raise HTTPException(status_code=503, detail="Chat not initialized")

    result = chat_agent.answer_question(
        question=request.question,
        document_id=request.document_id,
        use_rag=request.use_rag,
        preferred_language=request.preferred_language,
    )

    if result.get("success"):
        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result.get("sources") or [],
            model=result["model"],
            used_rag=result.get("used_rag", False),
        )
    raise HTTPException(status_code=500, detail=result.get("error", "Chat failed"))


@app.get("/documents", response_model=DocumentList)
async def list_documents():
    if not document_store:
        raise HTTPException(status_code=503, detail="Store not ready")
    return DocumentList(documents=document_store.list_documents())


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    if not document_store:
        raise HTTPException(status_code=503, detail="Store not ready")
    if document_store.delete(document_id):
        return {"success": True, "document_id": document_id}
    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": {
            "text_extraction": ocr_pipeline is not None,
            "qa": chat_agent is not None,
            "documents": document_store is not None,
            "chat": chat_agent is not None,
        },
        "integrations": {
            "ibm_bpm": bpm_pool is not None,
            "filenet": filenet_pool is not None,
            "ibm_bpm_pool": bpm_pool.describe() if bpm_pool else None,
            "filenet_pool": filenet_pool.describe() if filenet_pool else None,
        },
    }


if __name__ == "__main__":
    import uvicorn

    if settings.API_RELOAD:
        uvicorn.run(
            "app:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=True,
        )
    else:
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=False,
        )
