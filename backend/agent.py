"""Agent orchestrator. For each selected platform, runs analyze -> plan ->
generate (in parallel across platforms; sequential within a platform since
each step depends on the previous one). Critique is not part of the
automatic pipeline — it's only run on demand via run_review()."""

import asyncio
import json
import os
import re
from typing import Awaitable, Callable, Optional

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from models import (
    AnalysisResult,
    GenerationRequest,
    KBEntry,
    PersonaKey,
    PlatformKey,
    PlatformResult,
    RegenRequest,
    Variant,
    VariantScores,
)
from prompts import (
    VARIANT_ORDER,
    VARIANTS,
    build_analysis_prompt,
    build_critique_prompt,
    build_generation_prompt,
    build_plan_prompt,
    format_kb_context,
)

load_dotenv()

MODEL = "claude-sonnet-4-6"

_client: Optional[AsyncAnthropic] = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


EmitFn = Callable[[str, Optional[str], str, Optional[dict]], Awaitable[None]]


async def call_llm(prompt: str, max_tokens: int = 1500) -> str:
    resp = await get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


async def _noop_emit(step: str, platform: Optional[str], status: str, data: Optional[dict] = None) -> None:
    return None


async def _run_platform(
    req: GenerationRequest,
    platform: PlatformKey,
    kb_context: str,
    emit: EmitFn,
) -> PlatformResult:
    await emit("analyze", platform, "start", None)
    analysis_raw = await call_llm(build_analysis_prompt(req, platform, kb_context), max_tokens=1536)
    analysis = AnalysisResult(**extract_json(analysis_raw))
    await emit("analyze", platform, "done", analysis.model_dump())

    await emit("plan", platform, "start", None)
    plan_raw = await call_llm(build_plan_prompt(req, platform, analysis, kb_context), max_tokens=2048)
    plans = extract_json(plan_raw)
    await emit("plan", platform, "done", plans)

    await emit("generate", platform, "start", None)

    async def gen_one(key: str) -> tuple[str, str]:
        content = await call_llm(
            build_generation_prompt(req, platform, analysis, plans.get(key, ""), key, kb_context),
            max_tokens=1500,
        )
        return key, content.strip()

    gen_results = await asyncio.gather(*[gen_one(key) for key in VARIANT_ORDER])
    variants = [
        Variant(key=key, label=VARIANTS[key]["label"], content=content) for key, content in gen_results
    ]
    await emit("generate", platform, "done", {v.key: v.content for v in variants})

    return PlatformResult(platform=platform, analysis=analysis, variants=variants)


async def run_generation(
    req: GenerationRequest,
    kb_entries: list[KBEntry],
    emit: EmitFn = _noop_emit,
) -> list[PlatformResult]:
    await emit("kb_context", None, "start", None)
    kb_context = format_kb_context(kb_entries)
    await emit("kb_context", None, "done", {"entry_count": len(kb_entries)})

    return list(
        await asyncio.gather(*[_run_platform(req, platform, kb_context, emit) for platform in req.platforms])
    )


async def run_regen(req: RegenRequest, kb_entries: list[KBEntry]) -> Variant:
    kb_context = format_kb_context(kb_entries)
    content = await call_llm(
        build_generation_prompt(req, req.platform, req.analysis, "", req.variant_key, kb_context),
        max_tokens=1500,
    )
    return Variant(key=req.variant_key, label=VARIANTS[req.variant_key]["label"], content=content.strip())


async def run_review(
    persona: PersonaKey, platform: PlatformKey, variant_key: str, content: str
) -> tuple[VariantScores, str]:
    raw = await call_llm(build_critique_prompt(persona, platform, content, variant_key), max_tokens=500)
    data = extract_json(raw)
    return VariantScores(**data.get("scores", {})), data.get("notes", "")
