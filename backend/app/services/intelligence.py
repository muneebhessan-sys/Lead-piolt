"""Deterministic, evidence-bound intelligence; no external model is required."""
from dataclasses import dataclass

@dataclass
class Insight:
    score: int
    classification: str
    reasons: list[str]

class IntelligenceEngine:
    def score(self, website_status: str | None, has_phone: bool, has_website: bool) -> Insight:
        reasons: list[str] = []; score = 0
        if not has_website: score += 40; reasons.append("No website is recorded")
        elif website_status in {"UNREACHABLE", "POOR"}: score += 30; reasons.append(f"Website status is {website_status.lower()}")
        if has_phone: score += 10; reasons.append("Phone contact is available")
        return Insight(score=min(score, 100), classification="HIGH" if score >= 40 else "STANDARD", reasons=reasons)

    def compose(self, business_name: str, evidence: list[str], instruction: str) -> str:
        facts = "; ".join(evidence) if evidence else "No verified website findings are available."
        return f"Hello {business_name},\n\n{instruction.strip()}\n\nVerified context: {facts}\n\nBest regards"
