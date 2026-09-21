"""Tests for the memory/conversation module.

Note: These tests require a live Supabase connection.
For unit testing without Supabase, mock the supabase_admin client.
"""

from app.memory import Memory


def test_to_openai_messages_filters_roles():
    history = [
        {"role": "user", "content": "hello", "agent_name": None},
        {"role": "assistant", "content": "hi", "agent_name": "super_agent"},
        {"role": "tool", "content": '{"result": 42}', "agent_name": None},
        {"role": "user", "content": "thanks", "agent_name": None},
    ]
    mem = Memory.__new__(Memory)
    result = mem.to_openai_messages(history)
    assert len(result) == 3
    assert all(m["role"] in ("user", "assistant") for m in result)


def test_to_openai_messages_preserves_order():
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
        {"role": "user", "content": "third"},
    ]
    mem = Memory.__new__(Memory)
    result = mem.to_openai_messages(history)
    assert [m["content"] for m in result] == ["first", "second", "third"]
