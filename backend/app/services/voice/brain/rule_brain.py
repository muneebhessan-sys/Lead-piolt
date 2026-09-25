from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class RuleBrain:
    """Deterministic intent and response engine with no model dependency."""

    greeting: str = "Hello, this is LeadPilot. How can I help you today?"
    transfer_message: str = "I will connect you with a team member now."
    goodbye_message: str = "Thank you for your time. Goodbye."
    system_instructions: str = ""
    portfolio: str = ""
    pricing_rules: str = ""
    conversation_context: str = ""
    history: list[tuple[str, str]] = field(default_factory=list)

    async def respond(self, text: str) -> str:
        normalized = text.strip().lower()
        context = f" {self.conversation_context.lower()}" if self.conversation_context else ""
        if not normalized:
            response = "I did not catch that. Could you please repeat it?"
        elif re.search(r"\b(bye|goodbye|stop|end the call)\b", normalized):
            response = self.goodbye_message
        elif re.search(r"\b(human|person|agent|representative|transfer)\b", normalized):
            response = self.transfer_message
        elif re.search(r"\b(hello|hi|hey|salam|assalam)\b", normalized):
            response = self.greeting
        elif re.search(r"\b(price|pricing|cost|how much)\b", normalized):
            response = self.pricing_rules or "I can help with pricing. What service are you interested in?"
        elif "portfolio" in normalized:
            response = f"Here is the portfolio information: {self.portfolio}" if self.portfolio else "I can share portfolio information after the call."
        elif re.search(r"\b(already have|have a)\b.*\bwebsite\b", normalized):
            response = "That makes sense. Are there any parts of the current website you would like to improve, such as enquiries, mobile experience, or performance?"
        elif "website" in context and re.search(r"\b(inquir|leads|traffic|slow|performance)\b", normalized):
            response = "Thanks, that helps. It sounds like the focus may be improving the current site's ability to turn visits into enquiries. Which part would you most like to improve?"
        elif re.search(r"\b(yes|interested|interested?)\b", normalized):
            response = "Great. What is the best time for a team member to follow up?"
        else:
            response = "Thanks for sharing that. Could you tell me a little more about what you need?"
        self.history.append((text, response))
        return response
