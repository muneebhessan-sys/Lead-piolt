from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence


class MessageGenerator(ABC):
    @abstractmethod
    def generate(self, lead: Any, profile: Any, channel: str) -> str:
        """Generate a message for the provided lead and instruction profile."""


@dataclass(slots=True)
class MessageDraft:
    subject: str
    body: str


@dataclass(slots=True)
class ComposeContext:
    lead_id: int
    business_name: str
    profile: Any
    service_profile: Any | None
    audit_evidence: list[str]
    instruction: str
    tone: str
    language: str
    niche: str
    offer: str
    services: str
    cta: str
    rules: str
    do_not_say: str
    personalization_rules: str
    additional_instructions: str


class BaseMessageEngine(MessageGenerator, ABC):
    @abstractmethod
    def compose(self, ctx: ComposeContext) -> MessageDraft:
        """Compose a message draft from the given context."""

    def generate(self, lead: Any, profile: Any, channel: str) -> str:
        """Convenience wrapper that composes a message and returns the body only."""
        ctx = ComposeContext(
            lead_id=getattr(lead, "id", 0),
            business_name=getattr(getattr(lead, "business", None), "business_name", getattr(lead, "business_name", "Business")),
            profile=profile,
            service_profile=None,
            audit_evidence=[],
            instruction=getattr(profile, "additional_instructions", "") or "",
            tone=getattr(profile, "tone", "Professional") or "Professional",
            language=getattr(profile, "language", "English") or "English",
            niche=getattr(profile, "niche", "") or "",
            offer=getattr(profile, "offer", "") or "",
            services=getattr(profile, "services", "") or "",
            cta=getattr(profile, "cta", "") or "",
            rules=getattr(profile, "rules", "") or "",
            do_not_say=getattr(profile, "do_not_say", "") or "",
            personalization_rules=getattr(profile, "personalization_rules", "") or "",
            additional_instructions=getattr(profile, "additional_instructions", "") or "",
        )
        return self.compose(ctx).body

    @abstractmethod
    def validate(self, draft: MessageDraft, ctx: ComposeContext) -> tuple[bool, list[str]]:
        """Validate a draft against guardrails. Returns (is_valid, violations)."""

    def _get_attr(self, obj: Any, name: str, default: Any = "") -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)