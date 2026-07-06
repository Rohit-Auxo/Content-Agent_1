import asyncio
import io
import json
import os
import uuid
from pathlib import Path
from typing import Literal

from docx import Document
from fastapi import APIRouter, Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

import agent
from models import (
    GenerationRequest,
    GenerationResponse,
    KBEntry,
    KBEntryCreate,
    KBKind,
    RegenRequest,
    ReviewRequest,
    ReviewResult,
    Variant,
)
from prompts import GLOBAL_KB_SEED, PERSONAS, PLATFORMS, VARIANTS

MAX_KB_CONTENT_CHARS = 20000


def extract_text_from_upload(filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        text = data.decode("utf-8", errors="replace")
    return text[:MAX_KB_CONTENT_CHARS]


def require_access_key(x_access_key: str | None = Header(default=None, alias="X-Access-Key")):
    """Gate every API route behind a shared access key when ACCESS_KEY is set
    in the environment. Left unset (local dev), this is a no-op — matching
    the original no-auth local behavior. Set it before hosting publicly."""
    configured = os.getenv("ACCESS_KEY", "").strip()
    if not configured:
        return
    if x_access_key != configured:
        raise HTTPException(status_code=401, detail="Invalid or missing access key")


app = FastAPI(title="Content Generation Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory KB store, pre-seeded with the global tier.
KB_STORE: dict[str, KBEntry] = {}
for seed in GLOBAL_KB_SEED:
    entry = KBEntry(tier="global", title=seed["title"], content=seed["content"])
    KB_STORE[entry.id] = entry

# All API routes live behind the access-key dependency. The frontend static
# files (mounted below) are intentionally NOT behind it — the browser has to
# be able to load the page before it can know to send the key.
api = APIRouter(dependencies=[Depends(require_access_key)])


@api.get("/personas")
def get_personas():
    return PERSONAS


@api.get("/platforms")
def get_platforms():
    return PLATFORMS


@api.get("/variants")
def get_variants():
    return VARIANTS


@api.get("/kb", response_model=list[KBEntry])
def list_kb(tier: str | None = None):
    entries = list(KB_STORE.values())
    if tier:
        entries = [e for e in entries if e.tier == tier]
    return entries


@api.post("/kb", response_model=KBEntry)
def create_kb(payload: KBEntryCreate):
    entry = KBEntry(tier=payload.tier, kind=payload.kind, title=payload.title, content=payload.content)
    KB_STORE[entry.id] = entry
    return entry


@api.post("/kb/upload", response_model=KBEntry)
async def upload_kb(
    tier: Literal["client", "user"] = Form(...),
    kind: KBKind = Form("general"),
    title: str = Form(...),
    file: UploadFile = File(...),
):
    data = await file.read()
    content = extract_text_from_upload(file.filename or "", data)
    entry = KBEntry(tier=tier, kind=kind, title=title, content=content)
    KB_STORE[entry.id] = entry
    return entry


@api.delete("/kb/{entry_id}")
def delete_kb(entry_id: str):
    entry = KB_STORE.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="entry not found")
    if entry.tier == "global":
        raise HTTPException(status_code=400, detail="cannot delete global entries")
    del KB_STORE[entry_id]
    return {"ok": True}


def gather_kb_entries(kb_ids: list[str]) -> list[KBEntry]:
    entries = [e for e in KB_STORE.values() if e.tier == "global"]
    entries += [KB_STORE[i] for i in kb_ids if i in KB_STORE and KB_STORE[i].tier != "global"]
    return entries


@api.post("/generate")
async def generate(req: GenerationRequest):
    """Streams newline-delimited JSON progress events (each tagged with the
    platform it belongs to, or null for pipeline-wide steps), then a final
    'complete' event carrying the full GenerationResponse. Each selected
    platform runs its own analyze -> plan -> generate pass in parallel;
    critique/review is not part of this pipeline — see /review."""
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(step: str, platform: str | None, status: str, data: dict | None):
        await queue.put({"step": step, "platform": platform, "status": status, "data": data})

    async def runner():
        try:
            kb_entries = gather_kb_entries(req.kb_ids)
            channels = await agent.run_generation(req, kb_entries, emit)
            response = GenerationResponse(
                request_id=uuid.uuid4().hex,
                channels=channels,
            )
            await queue.put({"step": "complete", "platform": None, "status": "done", "data": response.model_dump()})
        except Exception as exc:  # surfaced to the frontend as an error event
            await queue.put({"step": "error", "platform": None, "status": "error", "data": str(exc)})
        finally:
            await queue.put(None)

    task = asyncio.create_task(runner())

    async def stream():
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield json.dumps(item) + "\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@api.post("/regen", response_model=Variant)
async def regen(req: RegenRequest):
    kb_entries = gather_kb_entries(req.kb_ids)
    try:
        return await agent.run_regen(req, kb_entries)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@api.post("/review", response_model=ReviewResult)
async def review(req: ReviewRequest):
    try:
        scores, notes = await agent.run_review(req.persona, req.platform, req.variant_key, req.content)
        return ReviewResult(scores=scores, critique_notes=notes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


app.include_router(api)

# Serve the frontend as static files so the whole app is one deployable
# service on one origin. Mounted last so it doesn't shadow the API routes
# above (Starlette tries routes in registration order).
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
