import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field

PersonaKey = Literal["tl", "pr", "fo", "pb", "bs", "co", "hc", "ec"]
PersonaType = Literal["individual", "business"]
PlatformKey = Literal["linkedin", "twitter", "email", "instagram", "facebook"]
VariantKey = Literal["safe", "pattern"]
KBTier = Literal["global", "client", "user"]
KBKind = Literal["general", "citation", "brand_guidelines", "tone_guidelines"]


class KBEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    tier: KBTier
    kind: KBKind = "general"
    title: str
    content: str


class KBEntryCreate(BaseModel):
    tier: Literal["client", "user"]
    kind: KBKind = "general"
    title: str
    content: str


class GenerationRequest(BaseModel):
    persona: PersonaKey
    persona_type: PersonaType
    audience: str
    problem: str
    tone: str
    platforms: list[PlatformKey]
    kb_ids: list[str] = []


class AnalysisResult(BaseModel):
    summary: str = ""
    key_angles: list[str] = []
    hooks: list[str] = []
    constraints: list[str] = []
    tone_notes: str = ""


class VariantScores(BaseModel):
    hook_strength: int = 0
    authenticity: int = 0
    clarity: int = 0
    platform_fit: int = 0
    cta_strength: int = 0
    overall: int = 0


class Variant(BaseModel):
    key: VariantKey
    label: str
    content: str
    scores: Optional[VariantScores] = None
    critique_notes: str = ""


class PlatformResult(BaseModel):
    platform: PlatformKey
    analysis: AnalysisResult
    variants: list[Variant]


class GenerationResponse(BaseModel):
    request_id: str
    channels: list[PlatformResult]


class RegenRequest(BaseModel):
    variant_key: VariantKey
    persona: PersonaKey
    persona_type: PersonaType
    audience: str
    problem: str
    tone: str
    platform: PlatformKey
    analysis: AnalysisResult
    kb_ids: list[str] = []


class ReviewRequest(BaseModel):
    variant_key: VariantKey
    persona: PersonaKey
    platform: PlatformKey
    content: str


class ReviewResult(BaseModel):
    scores: VariantScores
    critique_notes: str
