from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PersonalizationData:
    business_name: str
    category: str | None
    city: str | None
    region: str | None
    website: str | None
    phone: str | None
    rating: str | None
    review_count: int | None
    evidence: list[str]
    niche_keywords: list[str]
    niche_pain_points: list[str]
    niche_value_props: list[str]


def extract_personalization_data(
    business: Any,
    audit_evidence: list[str],
    niche_keywords: list[str] | None = None,
    niche_pain_points: list[str] | None = None,
    niche_value_props: list[str] | None = None,
) -> PersonalizationData:
    return PersonalizationData(
        business_name=_get_attr(business, "business_name", "this business"),
        category=_get_attr(business, "category", None),
        city=_get_attr(business, "city", None),
        region=_get_attr(business, "region", None),
        website=_get_attr(business, "website", None),
        phone=_get_attr(business, "phone", None),
        rating=_get_attr(business, "rating", None),
        review_count=_get_attr(business, "review_count", None),
        evidence=audit_evidence or [],
        niche_keywords=niche_keywords or [],
        niche_pain_points=niche_pain_points or [],
        niche_value_props=niche_value_props or [],
    )


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def build_personalization_snippets(data: PersonalizationData) -> dict[str, str]:
    snippets: dict[str, str] = {}

    location_parts = filter(None, [data.city, data.region])
    location = ", ".join(location_parts) if any(location_parts) else "your area"

    snippets["location"] = location
    snippets["business_category"] = data.category or "your industry"

    if data.rating and data.review_count:
        snippets["social_proof"] = f"{data.rating} stars from {data.review_count} reviews"
    elif data.review_count:
        snippets["social_proof"] = f"{data.review_count} reviews"
    elif data.rating:
        snippets["social_proof"] = f"{data.rating} star rating"
    else:
        snippets["social_proof"] = "your reputation"

    if data.website:
        domain = re.sub(r"^https?://", "", data.website).split("/")[0]
        snippets["website_reference"] = f"your site ({domain})"
    else:
        snippets["website_reference"] = "your online presence"

    if data.phone:
        snippets["contact_reference"] = "your listed phone number"
    else:
        snippets["contact_reference"] = "your contact information"

    evidence_refs = data.evidence[:3]
    snippets["evidence_summary"] = "; ".join(evidence_refs) if evidence_refs else "public business information"

    if data.niche_keywords:
        snippets["niche_hook"] = f"your work in {', '.join(data.niche_keywords[:3])}"
    else:
        snippets["niche_hook"] = "your business"

    if data.niche_pain_points:
        snippets["pain_point"] = data.niche_pain_points[0]
    else:
        snippets["pain_point"] = "growth challenges"

    if data.niche_value_props:
        snippets["value_prop"] = data.niche_value_props[0]
    else:
        snippets["value_prop"] = "measurable results"

    return snippets


def apply_personalization_rules(
    text: str,
    rules: str,
    snippets: dict[str, str],
) -> str:
    if not rules:
        return text

    result = text
    for key, value in snippets.items():
        placeholder = f"{{{{ {key} }}}}"
        if placeholder in result:
            result = result.replace(placeholder, value)

    return result


def generate_personalized_opening(
    data: PersonalizationData,
    tone: str,
    language: str,
) -> str:
    snippets = build_personalization_snippets(data)

    if tone == "Direct":
        return f"I have a specific idea for {snippets['business_category']} businesses in {snippets['location']}."
    elif tone == "Friendly":
        return f"I came across {data.business_name} in {snippets['location']} and thought you might be interested."
    elif tone == "Consultative":
        return f"I've been researching {snippets['business_category']} in {snippets['location']} and have an observation to share."
    elif tone == "Casual":
        return f"Hey, quick thought on {data.business_name} in {snippets['location']}."
    else:
        return f"I noticed your {snippets['niche_hook']} in {snippets['location']} and wanted to reach out about a focused opportunity."


def generate_personalized_body(
    data: PersonalizationData,
    offer: str,
    services: str,
    snippets: dict[str, str],
) -> str:
    parts = []
    if offer:
        parts.append(offer)
    if services:
        parts.append(services)
    if data.niche_value_props:
        parts.append(f"Specifically, we help with {data.niche_value_props[0].lower()}.")
    body = " ".join(parts) if parts else "I believe there is a strong fit for a short conversation about your business goals."
    return body


def generate_personalized_verification(data: PersonalizationData) -> str:
    if data.evidence:
        return "; ".join(data.evidence[:3])
    return "We based this message on the current public business information available."