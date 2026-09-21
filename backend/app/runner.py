"""Core execution engine for agent runs.

Drives the LLM turn-by-turn: generates a model response, executes any
tool calls, records every step to the database for crash recovery,
and loops until the model produces a final text response.

Adapted from the reference project's runner pattern.
"""

import json
import uuid
from typing import Optional
from app.database import supabase_admin
from app.providers import Provider, Turn, OpenAIProvider
from app.tools.dispatch import get_openai_tools, dispatch_tool_call
from app.idempotency import idempotency_key, once

SIDE_EFFECT_TOOLS = {
    "apply_for_loan", "block_card", "unblock_card",
    "file_complaint", "escalate_complaint", "book_interview_slot",
}


class Runner:
    """Executes a single agent run with tool calling and step recording."""

    def __init__(self, provider: Optional[Provider] = None):
        self.provider = provider or OpenAIProvider()

    def execute_run(
        self,
        run_id: str,
        thread_id: str,
        system_prompt: str,
        messages: list[dict],
        tool_instance,
        max_steps: int = 10,
    ) -> str:
        """Execute a run to completion. Returns the final text reply.

        Each model turn and tool call is recorded as a run_step in the
        database so that a crashed run can be rebuilt and resumed.
        """
        tools = get_openai_tools(tool_instance) if tool_instance else []
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        self._update_run_status(run_id, "running")

        step_seq = self._get_last_step_seq(run_id)

        for _ in range(max_steps):
            turn = self.provider.generate(full_messages, tools)
            step_seq += 1
            self._record_step(run_id, step_seq, "model", {
                "content": turn.content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "args": tc.arguments}
                    for tc in turn.tool_calls
                ] if turn.has_tool_calls else None,
            })

            if not turn.has_tool_calls:
                reply = turn.content or ""
                self._update_run_status(run_id, "succeeded")
                return reply

            full_messages.append(self._turn_to_message(turn))

            for tc in turn.tool_calls:
                step_seq += 1
                result = self._call_tool(
                    run_id, step_seq, tool_instance, tc.name, tc.arguments
                )
                self._record_step(run_id, step_seq, "tool", {
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "args": tc.arguments,
                    "result": result[:1000],
                })
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        self._update_run_status(run_id, "failed")
        return "I apologize, but I was unable to complete your request. Please try again."

    def _call_tool(self, run_id: str, step_seq: int, tool_instance,
                    fn_name: str, fn_args: dict) -> str:
        """Call a tool, wrapping side-effect tools in idempotency."""
        if fn_name in SIDE_EFFECT_TOOLS:
            key = idempotency_key(run_id, step_seq, fn_name, fn_args)
            return once(key, lambda: dispatch_tool_call(tool_instance, fn_name, fn_args))
        return dispatch_tool_call(tool_instance, fn_name, fn_args)

    def rebuild(self, run_id: str) -> list[dict]:
        """Reconstruct conversation state from recorded steps for crash recovery.

        Loads all run_steps for the given run and rebuilds the messages
        list as the model saw it before the crash.
        """
        steps = supabase_admin.table("run_step").select("*").eq(
            "run_id", run_id
        ).order("step_seq").execute()

        messages = []
        for step in steps.data:
            detail = step["detail"]
            if step["step_type"] == "model":
                if detail.get("tool_calls"):
                    messages.append({
                        "role": "assistant",
                        "content": detail.get("content"),
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"]),
                                },
                            }
                            for tc in detail["tool_calls"]
                        ],
                    })
                elif detail.get("content"):
                    messages.append({
                        "role": "assistant",
                        "content": detail["content"],
                    })
            elif step["step_type"] == "tool":
                messages.append({
                    "role": "tool",
                    "tool_call_id": detail["tool_call_id"],
                    "content": detail["result"],
                })
        return messages

    def _record_step(self, run_id: str, step_seq: int,
                      step_type: str, detail: dict) -> None:
        supabase_admin.table("run_step").insert({
            "id": f"step_{uuid.uuid4().hex[:12]}",
            "run_id": run_id,
            "step_seq": step_seq,
            "step_type": step_type,
            "detail": detail,
        }).execute()

    def _get_last_step_seq(self, run_id: str) -> int:
        result = supabase_admin.table("run_step").select("step_seq").eq(
            "run_id", run_id
        ).order("step_seq", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]["step_seq"]
        return 0

    def _update_run_status(self, run_id: str, status: str) -> None:
        update = {"status": status}
        if status == "running":
            update["started_at"] = "now()"
        elif status in ("succeeded", "failed"):
            update["completed_at"] = "now()"
        supabase_admin.table("run").update(update).eq("id", run_id).execute()

    def _turn_to_message(self, turn: Turn) -> dict:
        msg: dict = {"role": "assistant"}
        if turn.content:
            msg["content"] = turn.content
        if turn.has_tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in turn.tool_calls
            ]
        return msg
