"""Tests for the LLM provider abstraction."""

from app.providers import ScriptedProvider, EchoProvider, Turn, ToolCall


def test_echo_provider():
    provider = EchoProvider()
    turn = provider.generate(
        [{"role": "user", "content": "hello"}],
        [],
    )
    assert turn.content == "Echo: hello"
    assert not turn.has_tool_calls


def test_echo_provider_no_user():
    provider = EchoProvider()
    turn = provider.generate(
        [{"role": "system", "content": "You are a bot"}],
        [],
    )
    assert "no user message" in turn.content


def test_scripted_provider_returns_turns_in_order():
    turns = [
        Turn(content="First"),
        Turn(content="Second"),
    ]
    provider = ScriptedProvider(turns)
    assert provider.generate([], []).content == "First"
    assert provider.generate([], []).content == "Second"


def test_scripted_provider_exhausted():
    provider = ScriptedProvider([Turn(content="Only one")])
    provider.generate([], [])
    turn = provider.generate([], [])
    assert "exhausted" in turn.content


def test_scripted_provider_with_tool_calls():
    tc = ToolCall(id="tc1", name="get_balance", arguments={"customer_id": 1})
    turns = [
        Turn(tool_calls=[tc]),
        Turn(content="Your balance is ₹1,25,000"),
    ]
    provider = ScriptedProvider(turns)
    first = provider.generate([], [])
    assert first.has_tool_calls
    assert first.tool_calls[0].name == "get_balance"

    second = provider.generate([], [])
    assert not second.has_tool_calls
    assert "balance" in second.content
