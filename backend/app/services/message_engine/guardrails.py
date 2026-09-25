from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GuardrailConfig:
    max_subject_length: int = 120
    max_body_length: int = 3500
    min_body_length: int = 50
    max_emoji_count: int = 0
    banned_phrases: tuple[str, ...] = (
        "guaranteed",
        "guarantee",
        "risk-free",
        "no risk",
        "100%",
        "instant",
        "overnight",
        "secret",
        "hidden",
        "miracle",
        "magic",
        "revolutionary",
        "groundbreaking",
        "once in a lifetime",
        "act now",
        "limited time",
        "exclusive offer",
        "free money",
        "get rich",
        "make money fast",
        "double your",
        "triple your",
        "earn $",
        "$$$",
        "cash",
        "profit",
        "investment opportunity",
        "work from home",
        "be your own boss",
        "financial freedom",
        "passive income",
        "click here",
        "buy now",
        "order now",
        "limited supply",
        "while supplies last",
        "urgent",
        "immediate",
        "congratulations",
        "you have been selected",
        "winner",
        "prize",
        "claim your",
        "verify your account",
        "update your payment",
        "security alert",
        "account suspended",
    )
    spam_keywords: tuple[str, ...] = (
        "viagra",
        "cialis",
        "casino",
        "lottery",
        "winner",
        "inheritance",
        "prince",
        "nigeria",
        "bitcoin investment",
        "crypto investment",
        "forex signals",
        "binary options",
        "mlm",
        "pyramid",
        "get paid to",
        "survey money",
        "data entry jobs",
        "envelope stuffing",
    )
    max_exclamation_marks: int = 2
    max_capital_words_ratio: float = 0.3
    max_link_count: int = 1


DEFAULT_CONFIG = GuardrailConfig()

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000026FF"
    "\U00002B00-\U00002BFF"
    "]+",
    flags=re.UNICODE,
)

URL_PATTERN = re.compile(
    r"https?://[^\s]+|www\.[^\s]+|\b[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?",
    flags=re.IGNORECASE,
)


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool
    violations: list[str]
    warnings: list[str]


def count_emojis(text: str) -> int:
    return len(EMOJI_PATTERN.findall(text))


def count_links(text: str) -> int:
    return len(URL_PATTERN.findall(text))


def count_exclamations(text: str) -> int:
    return text.count("!")


def capital_words_ratio(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    capital_count = sum(1 for w in words if w.isupper() and len(w) > 2)
    return capital_count / len(words)


def check_banned_phrases(text: str, banned: tuple[str, ...]) -> list[str]:
    violations = []
    text_lower = text.lower()
    for phrase in banned:
        if phrase in text_lower:
            violations.append(f"Banned phrase detected: '{phrase}'")
    return violations


def check_spam_keywords(text: str, spam_keywords: tuple[str, ...]) -> list[str]:
    violations = []
    text_lower = text.lower()
    for keyword in spam_keywords:
        if keyword in text_lower:
            violations.append(f"Spam keyword detected: '{keyword}'")
    return violations


def check_do_not_say(text: str, do_not_say: str) -> list[str]:
    violations = []
    if not do_not_say:
        return violations
    for phrase in [p.strip() for p in do_not_say.split(",") if p.strip()]:
        if phrase.lower() in text.lower():
            violations.append(f"Do-not-say violation: '{phrase}'")
    return violations


def validate_draft(
    subject: str,
    body: str,
    config: GuardrailConfig | None = None,
    do_not_say: str = "",
) -> ValidationResult:
    cfg = config or DEFAULT_CONFIG
    violations: list[str] = []
    warnings: list[str] = []

    full_text = f"{subject}\n{body}"

    if len(subject) > cfg.max_subject_length:
        violations.append(f"Subject exceeds {cfg.max_subject_length} characters ({len(subject)})")
    elif len(subject) > cfg.max_subject_length * 0.8:
        warnings.append(f"Subject approaching length limit ({len(subject)}/{cfg.max_subject_length})")

    if len(body) > cfg.max_body_length:
        violations.append(f"Body exceeds {cfg.max_body_length} characters ({len(body)})")
    elif len(body) < cfg.min_body_length:
        violations.append(f"Body below minimum length ({len(body)}/{cfg.min_body_length})")

    emoji_count = count_emojis(full_text)
    if emoji_count > cfg.max_emoji_count:
        violations.append(f"Emoji count exceeds limit ({emoji_count}/{cfg.max_emoji_count})")
    elif emoji_count > 0:
        warnings.append(f"Emojis detected ({emoji_count})")

    link_count = count_links(full_text)
    if link_count > cfg.max_link_count:
        violations.append(f"Link count exceeds limit ({link_count}/{cfg.max_link_count})")

    exclamation_count = count_exclamations(full_text)
    if exclamation_count > cfg.max_exclamation_marks:
        violations.append(f"Too many exclamation marks ({exclamation_count}/{cfg.max_exclamation_marks})")

    cap_ratio = capital_words_ratio(full_text)
    if cap_ratio > cfg.max_capital_words_ratio:
        violations.append(f"Excessive capitalization ({cap_ratio:.0%} > {cfg.max_capital_words_ratio:.0%})")

    violations.extend(check_banned_phrases(full_text, cfg.banned_phrases))
    violations.extend(check_spam_keywords(full_text, cfg.spam_keywords))
    violations.extend(check_do_not_say(full_text, do_not_say))

    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        warnings=warnings,
    )


def sanitize_draft(
    subject: str,
    body: str,
    config: GuardrailConfig | None = None,
) -> tuple[str, str]:
    cfg = config or DEFAULT_CONFIG
    clean_subject = subject.strip()
    clean_body = body.strip()

    clean_body = EMOJI_PATTERN.sub("", clean_body)
    clean_subject = EMOJI_PATTERN.sub("", clean_subject)

    if len(clean_subject) > cfg.max_subject_length:
        clean_subject = clean_subject[: cfg.max_subject_length - 3] + "..."

    if len(clean_body) > cfg.max_body_length:
        clean_body = clean_body[: cfg.max_body_length - 3] + "..."

    return clean_subject, clean_body