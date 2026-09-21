"""Conversation memory management.

Handles loading and storing conversation history from Supabase.
Messages are append-only — once written, they cannot be modified or deleted.
"""

from dataclasses import dataclass
from typing import Optional
from app.database import supabase_admin


@dataclass(frozen=True)
class Message:
    thread_id: str
    seq: int
    role: str
    content: str
    agent_name: Optional[str] = None


class Memory:
    """Manages conversation threads and message history."""

    def __init__(self, thread_id: str):
        self.thread_id = thread_id

    def load_history(self) -> list[dict]:
        """Load full conversation history for the thread, ordered by sequence."""
        result = supabase_admin.table("message").select("*").eq(
            "thread_id", self.thread_id
        ).order("seq").execute()
        return result.data

    def load_recent(self, limit: int = 20) -> list[dict]:
        """Load the most recent N messages for context window management."""
        result = supabase_admin.table("message").select("*").eq(
            "thread_id", self.thread_id
        ).order("seq", desc=True).limit(limit).execute()
        return list(reversed(result.data))

    def append(self, role: str, content: str, agent_name: Optional[str] = None) -> Message:
        """Append a new message to the thread. Returns the saved message."""
        next_seq = self._next_seq()
        row = {
            "thread_id": self.thread_id,
            "seq": next_seq,
            "role": role,
            "content": content,
        }
        if agent_name:
            row["agent_name"] = agent_name

        result = supabase_admin.table("message").insert(row).execute()
        data = result.data[0]
        return Message(
            thread_id=data["thread_id"],
            seq=data["seq"],
            role=data["role"],
            content=data["content"],
            agent_name=data.get("agent_name"),
        )

    def _next_seq(self) -> int:
        """Get the next sequence number for this thread."""
        result = supabase_admin.table("message").select("seq").eq(
            "thread_id", self.thread_id
        ).order("seq", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]["seq"] + 1
        return 1

    def to_openai_messages(self, history: Optional[list[dict]] = None) -> list[dict]:
        """Convert stored messages to OpenAI chat format."""
        if history is None:
            history = self.load_history()
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["role"] in ("user", "assistant", "system")
        ]

    @staticmethod
    def create_thread(customer_id: int, title: str = "New Conversation") -> str:
        """Create a new conversation thread. Returns the thread ID."""
        result = supabase_admin.table("thread").insert({
            "customer_id": customer_id,
            "title": title,
        }).execute()
        return result.data[0]["id"]

    @staticmethod
    def get_threads(customer_id: int) -> list[dict]:
        """Get all threads for a customer, newest first."""
        result = supabase_admin.table("thread").select("*").eq(
            "customer_id", customer_id
        ).order("created_at", desc=True).execute()
        return result.data
