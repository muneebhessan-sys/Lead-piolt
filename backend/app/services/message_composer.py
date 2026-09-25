from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import BaseLoader, Environment


@dataclass
class MessageDraft:
    subject: str
    body: str


class MessageComposerEngine:
    def __init__(self):
        self.env = Environment(loader=BaseLoader(), autoescape=False)

    def compose(
        self,
        profile: Any | None,
        business_name: str,
        offer: str | None = None,
        service_summary: str | None = None,
        cta: str | None = None,
        evidence: list[str] | None = None,
        tone: str | None = None,
        niche: str | None = None,
        previous_conversation: str = "",
    ) -> MessageDraft:
        profile = profile or {}
        offer = offer or getattr(profile, "offer", "") or ""
        service_summary = service_summary or getattr(profile, "services", "") or ""
        tone = tone or getattr(profile, "tone", "Professional") or "Professional"
        cta = cta or getattr(profile, "cta", "") or "Book a quick call"
        niche = niche or getattr(profile, "niche", "") or ""
        evidence = evidence or []
        rules = getattr(profile, "rules", "") or ""
        do_not_say = getattr(profile, "do_not_say", "") or ""
        personalization_rules = getattr(profile, "personalization_rules", "") or ""
        conversation = previous_conversation.strip()
        conversation_lower = conversation.lower()
        if any(marker in conversation_lower for marker in ("not interested", "do not contact", "don't contact", "stop")):
            return MessageDraft(
                subject=f"Re: {business_name}",
                body="Thank you for letting me know. I will respect your decision and will not follow up further.",
            )
        if "portfolio" in conversation_lower:
            cta = cta or "I can share a portfolio when helpful."
        if any(marker in conversation_lower for marker in ("already have a website", "we have a website", "have a website")):
            opening = f"Thanks for clarifying that {business_name} already has a website."
            body = "Rather than suggesting a new site, we can look at practical improvements to user experience, performance, or enquiries when there is evidence those would help."
        else:
            opening = (
                f"I noticed your {niche} business and wanted to reach out about a focused opportunity."
                if niche
                else "I wanted to reach out with a focused opportunity for your business."
            )
            body = " ".join(filter(None, [offer, service_summary])).strip() or "I believe there is a strong fit for a short conversation about your business goals."
        template = self.env.from_string(
            """Hi {{ business_name }},

{{ opening }}

{{ body }}

{{ personalization }}

{{ verification }}

{{ cta }}

{{ closing }}

Rules: {{ rules }}
Do not say: {{ do_not_say }}
"""
        )
        personalization = personalization_rules or "Use business-specific references when available and keep the message concise and confident."
        verification = "; ".join(evidence) if evidence else "We based this message on the current public business information available."
        output = template.render(
            business_name=business_name,
            opening=opening,
            body=body,
            personalization=personalization,
            verification=verification,
            cta=cta,
            closing="Best regards,",
            rules=rules or "Keep it direct, specific, and relevant.",
            do_not_say=do_not_say or "Do not make promises or use generic filler.",
        )
        subject = f"{tone} outreach for {business_name}"
        return MessageDraft(subject=subject, body=output.strip())
