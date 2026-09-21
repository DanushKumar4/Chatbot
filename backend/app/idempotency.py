"""Idempotency layer for side-effect tools.

Ensures that tool calls with side effects (loan applications, card blocking,
complaint filing) are executed exactly once, even if the agent retries or
crashes mid-execution.

Pattern (same as reference project):
    key = idempotency_key(run_id, step_seq, tool_name, args)
    result = bank_db.once(key, lambda: actual_side_effect())
"""

import hashlib
import json
from typing import Any, Callable, Optional
from app.database import supabase_admin


def canonical_json(obj: Any) -> str:
    """Produce a deterministic JSON string for hashing.

    Normalizes floats-that-are-ints (12.0 → 12), sorts keys,
    and ensures consistent serialization across calls.
    """
    if isinstance(obj, dict):
        return json.dumps(
            {k: _normalize(v) for k, v in sorted(obj.items())},
            sort_keys=True,
            separators=(",", ":"),
        )
    return json.dumps(_normalize(obj), sort_keys=True, separators=(",", ":"))


def _normalize(val: Any) -> Any:
    if isinstance(val, float) and val == int(val):
        return int(val)
    if isinstance(val, dict):
        return {k: _normalize(v) for k, v in sorted(val.items())}
    if isinstance(val, (list, tuple)):
        return [_normalize(v) for v in val]
    return val


def idempotency_key(run_id: str, step_seq: int, tool_name: str, args: dict) -> str:
    """Generate a unique idempotency key from the run context and tool call.

    SHA-256 of (run_id, step_seq, tool_name, canonical(args)).
    Same inputs always produce the same key.
    """
    payload = canonical_json({
        "run_id": run_id,
        "step_seq": step_seq,
        "tool_name": tool_name,
        "args": args,
    })
    return hashlib.sha256(payload.encode()).hexdigest()


def once(key: str, effect: Callable[[], Any]) -> Any:
    """Execute a side effect exactly once for a given idempotency key.

    If the key already exists in the idempotency store, return the
    previously stored result without re-executing the effect.
    Otherwise, run the effect, store the result, and return it.
    """
    existing = supabase_admin.table("idempotency").select("result").eq(
        "key", key
    ).execute()

    if existing.data:
        return json.loads(existing.data[0]["result"])

    result = effect()

    supabase_admin.table("idempotency").insert({
        "key": key,
        "result": json.dumps(result, default=str),
    }).execute()

    return result
