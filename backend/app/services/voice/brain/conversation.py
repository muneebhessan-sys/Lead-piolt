from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationTurn:
    role: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationBrain:
    def __init__(self, system_prompt: str = "You are a helpful lead qualification assistant.") -> None:
        self.system_prompt = system_prompt
        self.history: list[ConversationTurn] = []

    def append(self, role: str, text: str, **metadata: Any) -> ConversationTurn:
        turn = ConversationTurn(role=role, text=text, metadata=metadata)
        self.history.append(turn)
        return turn

    def build_prompt(self) -> str:
        lines = [self.system_prompt]
        for turn in self.history:
            lines.append(f"{turn.role}: {turn.text}")
        return "\n".join(lines)

    async def respond(self, user_text: str) -> str:
        self.append("user", user_text)
        response = f"Thanks for the message. I can help qualify this lead: {user_text.strip()}"
        self.append("assistant", response)
        return response
