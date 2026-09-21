"""LLM provider abstraction.

Wraps OpenAI so that tests can swap in a scripted/mock provider
without hitting the real API. Same pattern as the reference project.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol
from openai import OpenAI
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class Turn:
    content: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class Provider(Protocol):
    """Interface that any LLM provider must implement."""

    def generate(self, messages: list[dict], tools: list[dict]) -> Turn:
        ...


class OpenAIProvider:
    """Production provider using OpenAI's chat completions API."""

    def __init__(self, model: str = LLM_MODEL, api_key: str = LLM_API_KEY, base_url: str = LLM_BASE_URL):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, messages: list[dict], tools: list[dict]) -> Turn:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        if choice.message.tool_calls:
            calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in choice.message.tool_calls
            ]
            return Turn(content=choice.message.content, tool_calls=calls)

        return Turn(content=choice.message.content or "")


class ScriptedProvider:
    """Test provider that returns pre-scripted turns in order.

    Usage in tests:
        provider = ScriptedProvider([
            Turn(content=None, tool_calls=[ToolCall("1", "get_balance", {"customer_id": 1})]),
            Turn(content="Your balance is ₹1,25,000"),
        ])
    """

    def __init__(self, turns: list[Turn]):
        self._turns = list(turns)
        self._index = 0

    def generate(self, messages: list[dict], tools: list[dict]) -> Turn:
        if self._index >= len(self._turns):
            return Turn(content="[ScriptedProvider exhausted]")
        turn = self._turns[self._index]
        self._index += 1
        return turn


class EchoProvider:
    """Test provider that echoes back the last user message."""

    def generate(self, messages: list[dict], tools: list[dict]) -> Turn:
        for msg in reversed(messages):
            if msg["role"] == "user":
                return Turn(content=f"Echo: {msg['content']}")
        return Turn(content="Echo: (no user message)")
