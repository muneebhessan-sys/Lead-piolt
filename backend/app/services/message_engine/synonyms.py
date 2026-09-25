from __future__ import annotations

import hashlib
import random
from typing import Any


SYNONYM_GROUPS: dict[str, list[tuple[str, float]]] = {
    "opportunity": [
        ("opportunity", 1.0),
        ("chance", 0.8),
        ("opening", 0.7),
        ("possibility", 0.6),
        ("prospect", 0.5),
    ],
    "business": [
        ("business", 1.0),
        ("company", 0.9),
        ("firm", 0.7),
        ("organization", 0.6),
        ("operation", 0.5),
    ],
    "reach out": [
        ("reach out", 1.0),
        ("contact", 0.9),
        ("connect with", 0.8),
        ("get in touch", 0.7),
        ("speak with", 0.6),
    ],
    "interested": [
        ("interested", 1.0),
        ("open to", 0.8),
        ("curious about", 0.7),
        ("receptive to", 0.6),
        ("considering", 0.5),
    ],
    "help": [
        ("help", 1.0),
        ("support", 0.9),
        ("assist", 0.8),
        ("enable", 0.7),
        ("empower", 0.6),
    ],
    "improve": [
        ("improve", 1.0),
        ("enhance", 0.9),
        ("boost", 0.8),
        ("optimize", 0.7),
        ("strengthen", 0.6),
        ("elevate", 0.5),
    ],
    "growth": [
        ("growth", 1.0),
        ("expansion", 0.8),
        ("scaling", 0.7),
        ("development", 0.6),
        ("advancement", 0.5),
    ],
    "lead": [
        ("lead", 1.0),
        ("prospect", 0.9),
        ("inquiry", 0.8),
        ("contact", 0.7),
        ("opportunity", 0.6),
    ],
    "call": [
        ("call", 1.0),
        ("conversation", 0.9),
        ("chat", 0.8),
        ("discussion", 0.7),
        ("meeting", 0.6),
    ],
    "quick": [
        ("quick", 1.0),
        ("brief", 0.9),
        ("short", 0.8),
        ("concise", 0.7),
        ("15-minute", 0.6),
    ],
    "strategy": [
        ("strategy", 1.0),
        ("approach", 0.9),
        ("plan", 0.8),
        ("method", 0.7),
        ("framework", 0.6),
    ],
    "solution": [
        ("solution", 1.0),
        ("approach", 0.9),
        ("system", 0.8),
        ("method", 0.7),
        ("framework", 0.6),
    ],
    "results": [
        ("results", 1.0),
        ("outcomes", 0.9),
        ("impact", 0.8),
        ("returns", 0.7),
        ("performance", 0.6),
    ],
    "partner": [
        ("partner", 1.0),
        ("collaborate with", 0.9),
        ("work with", 0.8),
        ("team up with", 0.7),
        ("join forces with", 0.6),
    ],
    "understand": [
        ("understand", 1.0),
        ("grasp", 0.8),
        ("recognize", 0.7),
        ("appreciate", 0.6),
    ],
    "unique": [
        ("unique", 1.0),
        ("distinct", 0.8),
        ("specialized", 0.7),
        ("tailored", 0.6),
        ("custom", 0.5),
    ],
    "proven": [
        ("proven", 1.0),
        ("demonstrated", 0.9),
        ("verified", 0.8),
        ("tested", 0.7),
        ("validated", 0.6),
    ],
}


def _seed_rng(lead_id: int, salt: str = "synonym") -> random.Random:
    seed_bytes = hashlib.sha256(f"{salt}:{lead_id}".encode()).digest()
    seed_int = int.from_bytes(seed_bytes[:8], "big")
    return random.Random(seed_int)


def select_synonym(lead_id: int, key: str, rng: random.Random | None = None) -> str:
    options = SYNONYM_GROUPS.get(key.lower())
    if not options:
        return key

    if rng is None:
        rng = _seed_rng(lead_id, key)

    total_weight = sum(w for _, w in options)
    r = rng.random() * total_weight
    cumulative = 0.0
    for word, weight in options:
        cumulative += weight
        if r <= cumulative:
            return word
    return options[-1][0]


def select_synonyms(lead_id: int, keys: list[str]) -> dict[str, str]:
    rng = _seed_rng(lead_id, "batch")
    return {key: select_synonym(lead_id, key, rng) for key in keys}


def rewrite_with_synonyms(lead_id: int, text: str) -> str:
    rng = _seed_rng(lead_id, "rewrite")
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        word = words[i].rstrip(".,;:!?").lower()
        if word in SYNONYM_GROUPS and rng.random() < 0.3:
            synonym = select_synonym(lead_id, word, rng)
            if words[i].endswith((".", ",", ";", ":", "!", "?")):
                synonym += words[i][-1]
            result.append(synonym)
        else:
            result.append(words[i])
        i += 1
    return " ".join(result)


def get_available_keys() -> list[str]:
    return sorted(SYNONYM_GROUPS.keys())