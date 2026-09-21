"""Tests for the tool dispatch module."""

import json
from app.tools.dispatch import get_openai_tools, dispatch_tool_call


class FakeTools:
    def greet(self, name: str) -> dict:
        """Say hello to someone."""
        return {"message": f"Hello, {name}!"}

    def add(self, a: int, b: int) -> dict:
        """Add two numbers."""
        return {"result": a + b}

    def _private(self):
        """Should not be exposed."""
        pass


def test_get_openai_tools_excludes_private():
    tools = get_openai_tools(FakeTools())
    names = [t["function"]["name"] for t in tools]
    assert "greet" in names
    assert "add" in names
    assert "_private" not in names


def test_get_openai_tools_format():
    tools = get_openai_tools(FakeTools())
    for tool in tools:
        assert tool["type"] == "function"
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]


def test_dispatch_tool_call():
    result = dispatch_tool_call(FakeTools(), "greet", {"name": "Rahul"})
    parsed = json.loads(result)
    assert parsed["message"] == "Hello, Rahul!"


def test_dispatch_type_coercion():
    result = dispatch_tool_call(FakeTools(), "add", {"a": "3", "b": 4.0})
    parsed = json.loads(result)
    assert parsed["result"] == 7


def test_dispatch_unknown_tool():
    result = dispatch_tool_call(FakeTools(), "nonexistent", {})
    parsed = json.loads(result)
    assert "error" in parsed
