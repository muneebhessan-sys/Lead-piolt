from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ToneRule:
    opening_style: str
    closing_style: str
    sentence_length: str
    formality: str
    emphasis: str


@dataclass(slots=True, frozen=True)
class LanguageRule:
    locale: str
    direction: str
    greeting: str
    sign_off: str


@dataclass(slots=True, frozen=True)
class NicheRule:
    keywords: list[str]
    pain_points: list[str]
    value_props: list[str]
    cta_variants: list[str]


TONE_RULES: dict[str, ToneRule] = {
    "Professional": ToneRule(
        opening_style="I noticed your business and wanted to reach out about a focused opportunity.",
        closing_style="Best regards,",
        sentence_length="medium",
        formality="high",
        emphasis="credibility and relevance",
    ),
    "Direct": ToneRule(
        opening_style="I have a specific idea for your business.",
        closing_style="Thanks,",
        sentence_length="short",
        formality="low",
        emphasis="clarity and brevity",
    ),
    "Friendly": ToneRule(
        opening_style="I came across your business and thought you might be interested.",
        closing_style="Warm regards,",
        sentence_length="medium",
        formality="low",
        emphasis="rapport and helpfulness",
    ),
    "Consultative": ToneRule(
        opening_style="I've been researching your market and have an observation to share.",
        closing_style="Sincerely,",
        sentence_length="long",
        formality="high",
        emphasis="insight and partnership",
    ),
    "Casual": ToneRule(
        opening_style="Hey, quick thought on your business.",
        closing_style="Cheers,",
        sentence_length="short",
        formality="very_low",
        emphasis="approachability",
    ),
}

LANGUAGE_RULES: dict[str, LanguageRule] = {
    "English": LanguageRule(
        locale="en_US",
        direction="ltr",
        greeting="Hi",
        sign_off="Best regards,",
    ),
    "Spanish": LanguageRule(
        locale="es_ES",
        direction="ltr",
        greeting="Hola",
        sign_off="Saludos cordiales,",
    ),
    "French": LanguageRule(
        locale="fr_FR",
        direction="ltr",
        greeting="Bonjour",
        sign_off="Cordialement,",
    ),
    "German": LanguageRule(
        locale="de_DE",
        direction="ltr",
        greeting="Hallo",
        sign_off="Mit freundlichen Grüßen,",
    ),
    "Portuguese": LanguageRule(
        locale="pt_BR",
        direction="ltr",
        greeting="Olá",
        sign_off="Atenciosamente,",
    ),
    "Italian": LanguageRule(
        locale="it_IT",
        direction="ltr",
        greeting="Ciao",
        sign_off="Cordiali saluti,",
    ),
}

NICHE_RULES: dict[str, NicheRule] = {
    "home services": NicheRule(
        keywords=["local", "reliable", "licensed", "emergency", "maintenance"],
        pain_points=["seasonal demand", "lead quality", "scheduling gaps", "reputation management"],
        value_props=["steady lead flow", "review generation", "schedule optimization", "local visibility"],
        cta_variants=["Book a quick call", "See a demo", "Get a free audit", "Chat for 10 minutes"],
    ),
    "healthcare": NicheRule(
        keywords=["patient", "compliance", "HIPAA", "care quality", "appointments"],
        pain_points=["patient acquisition", "no-shows", "reputation", "compliance burden"],
        value_props=["patient growth", "automated reminders", "review management", "compliance support"],
        cta_variants=["Schedule a consultation", "View case study", "Get compliance check", "Book 15 minutes"],
    ),
    "real estate": NicheRule(
        keywords=["listings", "buyers", "sellers", "market data", "closures"],
        pain_points=["lead conversion", "market volatility", "time management", "competition"],
        value_props=["qualified leads", "market insights", "automation tools", "brand building"],
        cta_variants=["See market report", "Book strategy call", "Get lead audit", "Quick chat"],
    ),
    "legal": NicheRule(
        keywords=["cases", "clients", "practice areas", "referrals", "reputation"],
        pain_points=["client intake", "case management", "marketing ethics", "referral network"],
        value_props=["qualified inquiries", "intake automation", "ethical marketing", "referral growth"],
        cta_variants=["Schedule consultation", "Review case study", "Get marketing audit", "Brief call"],
    ),
    "automotive": NicheRule(
        keywords=["vehicles", "service", "inventory", "customers", "loyalty"],
        pain_points=["seasonal slumps", "customer retention", "inventory turnover", "online reputation"],
        value_props=["service reminders", "loyalty programs", "reputation management", "digital retailing"],
        cta_variants=["Book service lane review", "See retention demo", "Get reputation audit", "Quick call"],
    ),
    "restaurant": NicheRule(
        keywords=["diners", "reservations", "reviews", "menu", "takeout"],
        pain_points=["slow nights", "review management", "delivery margins", "staffing"],
        value_props=["reservation optimization", "review generation", "direct ordering", "loyalty programs"],
        cta_variants=["Book tasting", "See review demo", "Get margin analysis", "10-minute chat"],
    ),
    "fitness": NicheRule(
        keywords=["members", "classes", "retention", "personal training", "facility"],
        pain_points=["member churn", "seasonal drops", "class attendance", "lead conversion"],
        value_props=["retention automation", "lead nurturing", "class optimization", "referral programs"],
        cta_variants=["Book facility tour", "See retention case study", "Get churn audit", "Quick call"],
    ),
    "beauty": NicheRule(
        keywords=["clients", "appointments", "stylists", "products", "loyalty"],
        pain_points=["no-shows", "product retail", "stylist retention", "booking gaps"],
        value_props=["automated reminders", "retail optimization", "loyalty programs", "online booking"],
        cta_variants=["Book demo", "See booking system", "Get revenue audit", "Quick chat"],
    ),
}


def get_tone_rule(tone: str) -> ToneRule:
    return TONE_RULES.get(tone, TONE_RULES["Professional"])


def get_language_rule(language: str) -> LanguageRule:
    return LANGUAGE_RULES.get(language, LANGUAGE_RULES["English"])


def get_niche_rule(niche: str) -> NicheRule | None:
    niche_lower = (niche or "").lower().strip()
    return NICHE_RULES.get(niche_lower)


def apply_tone(ctx: dict[str, Any], tone: str) -> dict[str, Any]:
    rule = get_tone_rule(tone)
    ctx = ctx.copy()
    ctx.setdefault("opening_style", rule.opening_style)
    ctx.setdefault("closing_style", rule.closing_style)
    ctx.setdefault("tone_emphasis", rule.emphasis)
    return ctx


def apply_language(ctx: dict[str, Any], language: str) -> dict[str, Any]:
    rule = get_language_rule(language)
    ctx = ctx.copy()
    ctx.setdefault("greeting", rule.greeting)
    ctx.setdefault("sign_off", rule.sign_off)
    ctx.setdefault("locale", rule.locale)
    return ctx


def apply_niche(ctx: dict[str, Any], niche: str) -> dict[str, Any]:
    rule = get_niche_rule(niche)
    if not rule:
        return ctx
    ctx = ctx.copy()
    ctx.setdefault("niche_keywords", rule.keywords)
    ctx.setdefault("niche_pain_points", rule.pain_points)
    ctx.setdefault("niche_value_props", rule.value_props)
    ctx.setdefault("niche_cta_variants", rule.cta_variants)
    return ctx


def build_context(
    business_name: str,
    tone: str,
    language: str,
    niche: str,
    offer: str,
    services: str,
    cta: str,
    rules: str,
    do_not_say: str,
    personalization_rules: str,
    additional_instructions: str,
    evidence: list[str],
    sender_name: str = "Your Team",
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "business_name": business_name,
        "sender_name": sender_name,
        "offer": offer,
        "services": services,
        "cta": cta,
        "rules": rules or "Keep it direct, specific, and relevant.",
        "do_not_say": do_not_say or "Do not make promises or use generic filler.",
        "personalization_rules": personalization_rules,
        "additional_instructions": additional_instructions,
        "evidence": evidence,
        "verification": "; ".join(evidence) if evidence else "We based this message on the current public business information available.",
    }

    opening = (
        f"I noticed your {niche} business and wanted to reach out about a focused opportunity."
        if niche
        else "I wanted to reach out with a focused opportunity for your business."
    )
    body = " ".join(filter(None, [offer, services])).strip() or "I believe there is a strong fit for a short conversation about your business goals."
    personalization = personalization_rules or "Use business-specific references when available and keep the message concise and confident."

    ctx["opening"] = opening
    ctx["body"] = body
    ctx["personalization"] = personalization

    ctx = apply_tone(ctx, tone)
    ctx = apply_language(ctx, language)
    ctx = apply_niche(ctx, niche)

    return ctx