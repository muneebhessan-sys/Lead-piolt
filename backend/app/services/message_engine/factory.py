from __future__ import annotations

from typing import Any

from .base import BaseMessageEngine, ComposeContext, MessageDraft, MessageGenerator
from .template_engine import TemplateEngine, TemplateRuleEngine
from .rules import build_context, get_language_rule, get_tone_rule
from .synonyms import rewrite_with_synonyms
from .personalization import (
    PersonalizationData,
    apply_personalization_rules,
    build_personalization_snippets,
    extract_personalization_data,
    generate_personalized_body,
    generate_personalized_opening,
    generate_personalized_verification,
)
from .guardrails import (
    DEFAULT_CONFIG,
    GuardrailConfig,
    ValidationResult,
    sanitize_draft,
    validate_draft,
)


class MessageEngine(BaseMessageEngine):
    def __init__(
        self,
        db_session: Any | None = None,
        guardrail_config: GuardrailConfig | None = None,
        enable_synonyms: bool = True,
        sender_name: str = "Your Team",
    ):
        self.template_engine = TemplateEngine(db_session)
        self.guardrail_config = guardrail_config or DEFAULT_CONFIG
        self.enable_synonyms = enable_synonyms
        self.sender_name = sender_name

    def compose(self, ctx: ComposeContext) -> MessageDraft:
        language_rule = get_language_rule(ctx.language)
        tone_rule = get_tone_rule(ctx.tone)

        personalization_data = extract_personalization_data(
            business=ctx.profile.business if hasattr(ctx.profile, "business") else None,
            audit_evidence=ctx.audit_evidence,
            niche_keywords=getattr(ctx, "niche_keywords", None),
            niche_pain_points=getattr(ctx, "niche_pain_points", None),
            niche_value_props=getattr(ctx, "niche_value_props", None),
        )

        snippets = build_personalization_snippets(personalization_data)

        base_context = build_context(
            business_name=ctx.business_name,
            tone=ctx.tone,
            language=ctx.language,
            niche=ctx.niche,
            offer=ctx.offer,
            services=ctx.services,
            cta=ctx.cta,
            rules=ctx.rules,
            do_not_say=ctx.do_not_say,
            personalization_rules=ctx.personalization_rules,
            additional_instructions=ctx.additional_instructions,
            evidence=ctx.audit_evidence,
            sender_name=self.sender_name,
        )

        base_context.update(snippets)
        base_context["greeting"] = language_rule.greeting
        base_context["sign_off"] = language_rule.sign_off
        base_context["opening_style"] = tone_rule.opening_style
        base_context["closing_style"] = tone_rule.closing_style

        base_context["opening"] = generate_personalized_opening(
            personalization_data, ctx.tone, ctx.language
        )
        base_context["body"] = generate_personalized_body(
            personalization_data, ctx.offer, ctx.services, snippets
        )
        base_context["personalization"] = ctx.personalization_rules or "Use business-specific references when available and keep the message concise and confident."
        base_context["verification"] = generate_personalized_verification(personalization_data)

        template_spec = self.template_engine.select_template(
            language=ctx.language,
            tone=ctx.tone,
            niche=ctx.niche,
            channel="EMAIL",
        )

        subject, body = self.template_engine.render(template_spec, base_context)

        subject = apply_personalization_rules(subject, ctx.personalization_rules, snippets)
        body = apply_personalization_rules(body, ctx.personalization_rules, snippets)

        if self.enable_synonyms:
            subject = rewrite_with_synonyms(ctx.lead_id, subject)
            body = rewrite_with_synonyms(ctx.lead_id, body)

        subject, body = sanitize_draft(subject, body, self.guardrail_config)

        return MessageDraft(subject=subject, body=body)

    def validate(self, draft: MessageDraft, ctx: ComposeContext) -> tuple[bool, list[str]]:
        result = validate_draft(
            draft.subject,
            draft.body,
            self.guardrail_config,
            ctx.do_not_say,
        )
        return result.is_valid, result.violations


class MessageEngineFactory:
    @staticmethod
    def create(
        db_session: Any | None = None,
        guardrail_config: GuardrailConfig | None = None,
        enable_synonyms: bool = True,
        sender_name: str = "Your Team",
    ) -> MessageGenerator:
        return MessageEngine(
            db_session=db_session,
            guardrail_config=guardrail_config,
            enable_synonyms=enable_synonyms,
            sender_name=sender_name,
        )

    @staticmethod
    def create_default() -> MessageGenerator:
        return MessageEngine()


def get_message_generator() -> MessageGenerator:
    return MessageEngine()


TemplateRuleEngine = MessageEngine