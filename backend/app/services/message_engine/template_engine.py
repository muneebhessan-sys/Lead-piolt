from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from jinja2 import BaseLoader, Environment, Template

try:
    from app.models import MessageTemplate
except Exception:  # pragma: no cover - model may not exist yet
    MessageTemplate = None  # type: ignore


@dataclass(slots=True)
class TemplateSpec:
    name: str
    subject_template: str
    body_template: str
    language: str
    tone: str
    niche: str
    channel: str
    is_active: bool = True
    priority: int = 0


class TemplateEngine:
    def __init__(self, db_session: Any | None = None):
        self.env = Environment(loader=BaseLoader(), autoescape=False)
        self._db = db_session
        self._fallback_templates = self._build_fallback_templates()

    def _build_fallback_templates(self) -> list[TemplateSpec]:
        return [
            TemplateSpec(
                name="default_email",
                subject_template="{{ tone }} outreach for {{ business_name }}",
                body_template=(
                    "Hi {{ business_name }},\n\n"
                    "{{ opening }}\n\n"
                    "{{ body }}\n\n"
                    "{{ personalization }}\n\n"
                    "{{ verification }}\n\n"
                    "{{ cta }}\n\n"
                    "Best regards,\n"
                    "{{ sender_name }}"
                ),
                language="English",
                tone="Professional",
                niche="",
                channel="EMAIL",
                priority=0,
            ),
            TemplateSpec(
                name="direct_email",
                subject_template="Quick question for {{ business_name }}",
                body_template=(
                    "Hi {{ business_name }},\n\n"
                    "{{ opening }}\n\n"
                    "{{ body }}\n\n"
                    "{{ cta }}\n\n"
                    "Thanks,\n"
                    "{{ sender_name }}"
                ),
                language="English",
                tone="Direct",
                niche="",
                channel="EMAIL",
                priority=10,
            ),
            TemplateSpec(
                name="friendly_email",
                subject_template="Thinking of {{ business_name }}",
                body_template=(
                    "Hi {{ business_name }},\n\n"
                    "{{ opening }}\n\n"
                    "{{ body }}\n\n"
                    "{{ personalization }}\n\n"
                    "{{ cta }}\n\n"
                    "Warm regards,\n"
                    "{{ sender_name }}"
                ),
                language="English",
                tone="Friendly",
                niche="",
                channel="EMAIL",
                priority=10,
            ),
        ]

    def select_template(
        self,
        language: str,
        tone: str,
        niche: str,
        channel: str = "EMAIL",
    ) -> TemplateSpec:
        if self._db and MessageTemplate is not None:
            query = self._db.query(MessageTemplate).filter(
                MessageTemplate.language == language,
                MessageTemplate.tone == tone,
                MessageTemplate.channel == channel,
                MessageTemplate.is_active.is_(True),
            )
            if niche:
                niche_templates = query.filter(MessageTemplate.niche == niche).all()
                if niche_templates:
                    return max(niche_templates, key=lambda t: t.priority)
            general_templates = query.filter(
                (MessageTemplate.niche == "") | (MessageTemplate.niche.is_(None))
            ).all()
            if general_templates:
                return max(general_templates, key=lambda t: t.priority)

        candidates = [
            t
            for t in self._fallback_templates
            if t.language == language
            and t.tone == tone
            and t.channel == channel
            and (t.niche == "" or t.niche == niche)
        ]
        if candidates:
            return max(candidates, key=lambda t: t.priority)

        candidates = [
            t
            for t in self._fallback_templates
            if t.language == language and t.channel == channel
        ]
        if candidates:
            return max(candidates, key=lambda t: t.priority)

        return self._fallback_templates[0]

    def render_subject(self, spec: TemplateSpec, ctx: dict[str, Any]) -> str:
        template = self.env.from_string(spec.subject_template)
        return template.render(**ctx).strip()

    def render_body(self, spec: TemplateSpec, ctx: dict[str, Any]) -> str:
        template = self.env.from_string(spec.body_template)
        return template.render(**ctx).strip()

    def render(self, spec: TemplateSpec, ctx: dict[str, Any]) -> tuple[str, str]:
        return self.render_subject(spec, ctx), self.render_body(spec, ctx)


TemplateRuleEngine = TemplateEngine