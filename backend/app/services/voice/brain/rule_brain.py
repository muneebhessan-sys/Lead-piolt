from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class RuleBrain:
    """Deterministic intent and response engine with no model dependency."""

    greeting: str = "Hello, this is LeadPilot. How can I help you today?"
    transfer_message: str = "I will connect you with a team member now."
    goodbye_message: str = "Thank you for your time. Goodbye."
    history: list[tuple[str, str]] = field(default_factory=list)

    async def respond(self, text: str) -> str:
        normalized = text.strip().lower()
        if not normalized:
            response = "I did not catch that. Could you please repeat it?"
        elif re.search(r"\b(bye|goodbye|stop|end the call)\b", normalized):
            response = self.goodbye_message
        elif re.search(r"\b(human|person|agent|representative|transfer)\b", normalized):
            response = self.transfer_message
        elif re.search(r"\b(hello|hi|hey|salam|assalam)\b", normalized):
            response = self.greeting
        elif re.search(r"\b(price|pricing|cost|how much)\b", normalized):
            response = "I can help with pricing. What service are you interested in?"
        elif re.search(r"\b(yes|interested|interested?)\b", normalized):
            response = "Great. What is the best time for a team member to follow up?"
        else:
            response = "Thanks for sharing that. Could you tell me a little more about what you need?"
        self.history.append((text, response))
        return response
