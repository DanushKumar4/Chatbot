"""Shared test fixtures.

Sets up mock providers and test data so that tests
never hit real OpenAI or Supabase APIs.
"""

import pytest
from app.providers import ScriptedProvider, EchoProvider, Turn, ToolCall


@pytest.fixture
def echo_provider():
    return EchoProvider()


@pytest.fixture
def scripted_provider():
    """Factory fixture — call with a list of Turns."""
    def _make(turns):
        return ScriptedProvider(turns)
    return _make


@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "What is my account balance?"},
    ]


@pytest.fixture
def sample_history():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Welcome to SmartBank! How can I help?"},
        {"role": "user", "content": "I want to check my loan status"},
    ]
