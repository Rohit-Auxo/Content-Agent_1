"""Static content used to build agent prompts: personas, platforms, variant
strategies, and the anti-AI base rules. Also the prompt-builder functions for
each of the agent's five steps."""

from models import AnalysisResult, GenerationRequest, KBEntry

# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------

PERSONAS = {
    "tl": {
        "label": "Thought Leader",
        "type": "individual",
        "voice": (
            "Speaks with a forward-looking, big-picture point of view. Connects "
            "specific observations to broader industry shifts. Builds frameworks "
            "and names patterns rather than just reporting facts. Confident but "
            "not arrogant — earns authority through original synthesis, not "
            "credentials-dropping."
        ),
    },
    "pr": {
        "label": "Practitioner",
        "type": "individual",
        "voice": (
            "Speaks from the trenches. Tactical, specific, 'here's exactly how "
            "I did X and what happened.' Distrusts abstraction — grounds every "
            "claim in a concrete example, number, or step. No fluff, no theory "
            "without a receipt."
        ),
    },
    "fo": {
        "label": "Founder",
        "type": "individual",
        "voice": (
            "Speaks as someone building something with real stakes. Direct, "
            "occasionally raw, comfortable admitting what's hard or what failed. "
            "Behind-the-scenes tone — pulls back the curtain rather than "
            "presenting a polished corporate front."
        ),
    },
    "pb": {
        "label": "Personal Brand",
        "type": "individual",
        "voice": (
            "Personality-forward and relatable. Opinions land like they came "
            "from a specific person with a specific sense of humor, not a "
            "brand committee. Uses personal anecdotes and plain language over "
            "polish."
        ),
    },
    "bs": {
        "label": "B2B SaaS",
        "type": "business",
        "voice": (
            "Product-led and outcome-focused. Ties every claim to a measurable "
            "benefit (time saved, revenue gained, risk reduced). Professional "
            "but not stiff — speaks to a buyer who is busy and skeptical of "
            "hype."
        ),
    },
    "co": {
        "label": "Consulting",
        "type": "business",
        "voice": (
            "Authority and trust-building. Leans on case studies, frameworks, "
            "and demonstrated expertise. Measured, precise language — every "
            "sentence should sound like it could survive a client asking "
            "'how do you know that?'"
        ),
    },
    "hc": {
        "label": "Healthcare",
        "type": "business",
        "voice": (
            "Careful, empathetic, patient-centered. Never overstates clinical "
            "claims or gives the impression of medical advice. Warm but "
            "precise — trust is the entire point."
        ),
    },
    "ec": {
        "label": "Ecommerce",
        "type": "business",
        "voice": (
            "Conversion-aware and benefit-driven. Leads with the concrete "
            "outcome for the customer, uses social proof and light urgency "
            "where earned. Energetic but never shouty."
        ),
    },
}

# ---------------------------------------------------------------------------
# Platforms
# ---------------------------------------------------------------------------

PLATFORMS = {
    "linkedin": {
        "label": "LinkedIn",
        "rules": (
            "Ideal length 900-1600 characters. The first 1-2 lines are the "
            "hook and must work standalone before the 'see more' cutoff "
            "(~210 characters) — never bury the point. Use short paragraphs "
            "(1-3 sentences) separated by line breaks, not dense blocks. "
            "3-5 hashtags maximum, placed at the very end, never inline. "
            "No link-in-first-line (kills reach) — mention 'link in comments' "
            "if a URL is needed. Professional but human register."
        ),
    },
    "twitter": {
        "label": "Twitter / X",
        "rules": (
            "Single post, hard cap 280 characters unless explicitly written "
            "as a numbered thread. The first sentence IS the hook — no "
            "warm-up. Conversational, clipped, confident. Minimal to zero "
            "hashtags (1 max, only if it's a real community tag). No "
            "corporate hedging."
        ),
    },
    "email": {
        "label": "Email",
        "rules": (
            "Output a subject line followed by the body, separated by a "
            "blank line, formatted as 'Subject: ...' then the body. Subject "
            "under 60 characters, curiosity or benefit driven, no clickbait "
            "punctuation spam. Body reads like it's from one person to one "
            "person — short paragraphs, one clear call-to-action near the "
            "end, no more than one ask."
        ),
    },
    "instagram": {
        "label": "Instagram",
        "rules": (
            "Caption written to accompany a visual, so it can reference "
            "'this' or 'here' naturally. Strong first line before the fold. "
            "Conversational, can use emoji sparingly for rhythm (not as "
            "bullet substitutes). 5-10 relevant hashtags grouped at the very "
            "end after a line break."
        ),
    },
    "facebook": {
        "label": "Facebook",
        "rules": (
            "Conversational and community-oriented, longer than Twitter but "
            "shorter than LinkedIn (roughly 400-900 characters). Works well "
            "with a direct question to prompt comments. Minimal hashtags "
            "(0-2), plain and warm register, avoid corporate polish."
        ),
    },
}

# ---------------------------------------------------------------------------
# Variant strategies
# ---------------------------------------------------------------------------

VARIANTS = {
    "safe": {
        "label": "Safe / On-Brand",
        "description": (
            "The reliable, polished version. Follows platform best practices "
            "and persona voice closely. Lower risk, consistent performer — "
            "the piece you'd publish if you could only ship one."
        ),
    },
    "pattern": {
        "label": "Pattern Interrupt",
        "description": (
            "Opens with something unexpected — a contrarian claim, an odd "
            "specific detail, a structure that breaks the usual format for "
            "this platform. Designed to stop the scroll and earn the second "
            "sentence. Higher risk, higher ceiling."
        ),
    },
}

VARIANT_ORDER = ["safe", "pattern"]

# ---------------------------------------------------------------------------
# Anti-AI base rules
# ---------------------------------------------------------------------------

BASE_RULES = """Anti-AI writing rules — follow all of these strictly:
- Never use: "unlock", "unleash", "leverage", "elevate", "delve", "dive in",
  "game-changer", "revolutionize", "seamless", "robust", "in today's
  fast-paced world", "navigate the landscape", "at the end of the day",
  "it's important to note", "in conclusion", "whether you're X or Y",
  "imagine a world where", or any "not just X, but Y" construction.
- Maximum one em dash in the entire piece. Prefer periods and commas.
- Do not write in perfectly parallel rule-of-three lists more than once.
  Real writing has uneven rhythm.
- Vary sentence length on purpose — mix short, blunt sentences with longer
  ones. Do not let every sentence run the same length.
- Open with something concrete and specific (a detail, a number, a moment),
  never with an abstract statement or a rhetorical question.
- Include at least one specific, verifiable-feeling detail: a number, a
  name, a timeframe, a real-sounding example.
- Do not summarize or restate the point at the end. End on the last new
  thing you have to say.
- Do not hedge-stack ("might potentially perhaps"). Say the thing.
- No emoji used as bullet points or section markers.
- Sound like one specific person actually said this out loud, not a brand
  voice written by committee."""


# ---------------------------------------------------------------------------
# Global KB seed
# ---------------------------------------------------------------------------

def build_global_kb_seed() -> list[dict]:
    seed = [{"title": "Anti-AI Writing Rules", "content": BASE_RULES}]
    for key in ["linkedin", "twitter", "email", "instagram", "facebook"]:
        platform = PLATFORMS[key]
        seed.append(
            {
                "title": f"{platform['label']} Channel Guidelines",
                "content": platform["rules"],
            }
        )
    return seed


GLOBAL_KB_SEED = build_global_kb_seed()


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def format_kb_context(entries: list[KBEntry]) -> str:
    if not entries:
        return "(no knowledge base entries)"
    by_tier = {"global": [], "client": [], "user": []}
    for e in entries:
        by_tier[e.tier].append(e)
    parts = []
    for tier in ["global", "client", "user"]:
        if not by_tier[tier]:
            continue
        parts.append(f"[{tier.upper()}]")
        for e in by_tier[tier]:
            parts.append(f"- {e.title}: {e.content}")
    return "\n".join(parts)


def _brief_block(req: GenerationRequest, platform_key: str) -> str:
    persona = PERSONAS[req.persona]
    platform = PLATFORMS[platform_key]
    return f"""PERSONA: {persona['label']} ({req.persona_type})
{persona['voice']}

PLATFORM: {platform['label']}
{platform['rules']}

AUDIENCE: {req.audience}
BRIEF / PROBLEM TO ADDRESS: {req.problem}
DESIRED TONE: {req.tone}"""


def build_analysis_prompt(req: GenerationRequest, platform_key: str, kb_context: str) -> str:
    return f"""You are the analysis stage of a content-generation agent.

{_brief_block(req, platform_key)}

KNOWLEDGE BASE CONTEXT:
{kb_context}

Analyze this brief and produce a JSON object with:
- "summary": one or two sentence summary of what this content needs to achieve
- "key_angles": array of 3-5 distinct strategic angles worth exploring
- "hooks": array of 3-5 candidate opening hooks (short, punchy, concrete)
- "constraints": array of hard constraints from the persona, platform, or
  knowledge base that must be respected
- "tone_notes": 1-2 sentences on how the tone should manifest concretely

Respond with ONLY the JSON object. No markdown code fences, no commentary."""


def build_plan_prompt(
    req: GenerationRequest, platform_key: str, analysis: AnalysisResult, kb_context: str
) -> str:
    variant_desc = "\n".join(
        f"{i + 1}. {key.upper()} ({VARIANTS[key]['label']}): {VARIANTS[key]['description']}"
        for i, key in enumerate(VARIANT_ORDER)
    )
    json_shape = ", ".join(
        f'"{key}": "plan text for the {key} variant"' for key in VARIANT_ORDER
    )
    return f"""You are the planning stage of a content-generation agent.

{_brief_block(req, platform_key)}

ANALYSIS FROM THE PREVIOUS STEP:
- Summary: {analysis.summary}
- Key angles: {"; ".join(analysis.key_angles)}
- Candidate hooks: {"; ".join(analysis.hooks)}
- Constraints: {"; ".join(analysis.constraints)}
- Tone notes: {analysis.tone_notes}

KNOWLEDGE BASE CONTEXT:
{kb_context}

Create a content plan for {len(VARIANT_ORDER)} distinct variants of the same
piece of content, one per strategy below:

{variant_desc}

For each variant, decide: the specific hook to use, the structural
approach, which angle from the analysis it emphasizes, and the closing
move (CTA or resolution). Each variant must feel genuinely different from
the others, not a rewording.

Respond with ONLY a JSON object shaped exactly like:
{{{json_shape}}}
No markdown code fences, no commentary."""


def build_generation_prompt(
    req: GenerationRequest,
    platform_key: str,
    analysis: AnalysisResult,
    plan_text: str,
    variant_key: str,
    kb_context: str,
) -> str:
    variant = VARIANTS[variant_key]
    return f"""{BASE_RULES}

{_brief_block(req, platform_key)}

VARIANT STRATEGY: {variant['label']} — {variant['description']}

ANALYSIS:
- Summary: {analysis.summary}
- Key angles: {"; ".join(analysis.key_angles)}
- Constraints: {"; ".join(analysis.constraints)}
- Tone notes: {analysis.tone_notes}

CONTENT PLAN FOR THIS VARIANT:
{plan_text}

KNOWLEDGE BASE CONTEXT:
{kb_context}

Write the final piece of content now, ready to publish on {PLATFORMS[platform_key]['label']}.
Follow the platform format rules exactly. Follow the anti-AI rules strictly.
Output ONLY the content itself — no preamble, no explanation, no markdown
headers labeling which variant this is."""


def build_critique_prompt(persona_key: str, platform_key: str, content: str, variant_key: str) -> str:
    persona = PERSONAS[persona_key]
    platform = PLATFORMS[platform_key]
    variant = VARIANTS[variant_key]
    return f"""You are a sharp, critical editor reviewing content before it is published.

PERSONA: {persona['label']}
PLATFORM: {platform['label']} — {platform['rules']}
VARIANT STRATEGY: {variant['label']}

CONTENT TO CRITIQUE:
---
{content}
---

Score this content 0-100 on each dimension:
- hook_strength: does the opening line actually stop the scroll?
- authenticity: does it sound like a specific human, not an AI?
- clarity: is the message clear and easy to follow?
- platform_fit: does it match this platform's format and conventions?
- cta_strength: is the call-to-action (or deliberate lack of one) effective?
- overall: your holistic score

Also write 1-3 sentences of blunt, specific critique notes — what works,
what doesn't, and why.

Respond with ONLY JSON shaped exactly like:
{{"scores": {{"hook_strength": 0, "authenticity": 0, "clarity": 0, "platform_fit": 0, "cta_strength": 0, "overall": 0}}, "notes": "..."}}
No markdown code fences, no commentary."""
