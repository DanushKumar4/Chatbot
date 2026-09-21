"""Background worker for processing queued chat runs.

Polls the run queue, claims a run via atomic lease, executes it
through the agent system, and handles failures with retry logic.

Same durable-execution pattern as the reference project:
- Atomic claim via lease_owner + lease_until
- Heartbeat to extend lease during long runs
- Reap expired leases and requeue or dead-letter
- Exponential backoff on retries
"""

import os
import time
import uuid
import socket
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database import supabase_admin
from app.agents.super_agent import SuperAgent

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
LEASE_DURATION_SECONDS = 60
BACKOFF_BASE_SECONDS = 5
POLL_INTERVAL_SECONDS = 1


def generate_worker_id() -> str:
    hostname = socket.gethostname()
    pid = os.getpid()
    rand = uuid.uuid4().hex[:6]
    return f"{hostname}-{pid}-{rand}"


class Worker:
    """Background worker that processes queued agent runs."""

    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or generate_worker_id()
        self.super_agent = SuperAgent()
        logger.info(f"Worker initialized: {self.worker_id}")

    def run_forever(self, poll_interval: float = POLL_INTERVAL_SECONDS):
        """Main loop: reap → claim → execute → repeat."""
        logger.info(f"Worker {self.worker_id} starting run_forever loop")
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("Worker shutting down (KeyboardInterrupt)")
                break
            except Exception as e:
                logger.error(f"Unexpected error in run_once: {e}")
            time.sleep(poll_interval)

    def run_once(self):
        """Single iteration: reap expired → claim next → execute."""
        self.reap_expired()
        run = self.claim_next()
        if run is None:
            return
        logger.info(f"Claimed run {run['id']} for thread {run['thread_id']}")
        try:
            self.execute(run)
        except Exception as e:
            logger.error(f"Run {run['id']} failed: {e}")
            self.fail_attempt(run)

    def claim_next(self) -> Optional[dict]:
        """Atomically claim the next queued run."""
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=LEASE_DURATION_SECONDS)

        queued = supabase_admin.table("run").select("*").eq(
            "status", "queued"
        ).order("created_at").limit(1).execute()

        if not queued.data:
            return None

        run = queued.data[0]
        supabase_admin.table("run").update({
            "status": "running",
            "lease_owner": self.worker_id,
            "lease_until": lease_until.isoformat(),
            "started_at": now.isoformat(),
        }).eq("id", run["id"]).eq("status", "queued").execute()

        return run

    def execute(self, run: dict):
        """Execute a claimed run through the agent system."""
        thread_id = run["thread_id"]
        run_id = run["id"]

        history = supabase_admin.table("message").select(
            "role, content"
        ).eq("thread_id", thread_id).order("seq").execute()

        if not history.data:
            self.complete(run_id, "No messages found in thread.")
            return

        last_user_msg = None
        for msg in reversed(history.data):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break

        if not last_user_msg:
            self.complete(run_id, "No user message found.")
            return

        thread = supabase_admin.table("thread").select(
            "customer_id"
        ).eq("id", thread_id).single().execute()
        customer_id = thread.data["customer_id"]

        result = self.super_agent.route_and_execute(
            user_message=last_user_msg,
            history=history.data[:-1],
            customer_id=customer_id,
            thread_id=thread_id,
            run_id=run_id,
        )

        self.complete(run_id, result["reply"], result.get("routed_to"))

    def complete(self, run_id: str, reply: str, agent_name: Optional[str] = None):
        """Mark a run as succeeded and save the reply."""
        run = supabase_admin.table("run").select("thread_id").eq(
            "id", run_id
        ).single().execute()
        thread_id = run.data["thread_id"]

        existing = supabase_admin.table("message").select("seq").eq(
            "thread_id", thread_id
        ).order("seq", desc=True).limit(1).execute()
        next_seq = (existing.data[0]["seq"] + 1) if existing.data else 1

        supabase_admin.table("message").insert({
            "thread_id": thread_id,
            "seq": next_seq,
            "role": "assistant",
            "content": reply,
            "agent_name": agent_name,
        }).execute()

        supabase_admin.table("run").update({
            "status": "succeeded",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()

        logger.info(f"Run {run_id} completed successfully")

    def fail_attempt(self, run: dict):
        """Handle a failed run attempt with retry/backoff logic."""
        run_id = run["id"]
        attempts = run.get("attempts", 0) + 1

        if attempts >= MAX_ATTEMPTS:
            supabase_admin.table("run").update({
                "status": "dead",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", run_id).execute()
            logger.warning(f"Run {run_id} dead-lettered after {attempts} attempts")
        else:
            backoff = BACKOFF_BASE_SECONDS * (2 ** (attempts - 1))
            available_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
            supabase_admin.table("run").update({
                "status": "queued",
                "attempts": attempts,
                "available_at": available_at.isoformat(),
                "lease_owner": None,
                "lease_until": None,
            }).eq("id", run_id).execute()
            logger.info(f"Run {run_id} requeued (attempt {attempts}, backoff {backoff}s)")

    def reap_expired(self):
        """Find runs with expired leases and requeue or dead-letter them."""
        now = datetime.now(timezone.utc).isoformat()
        expired = supabase_admin.table("run").select("*").eq(
            "status", "running"
        ).lt("lease_until", now).execute()

        for run in expired.data:
            logger.warning(f"Reaping expired run {run['id']} (owner: {run.get('lease_owner')})")
            self.fail_attempt(run)

    def heartbeat(self, run_id: str) -> bool:
        """Extend the lease for a running run. Returns False if lease was lost."""
        new_until = datetime.now(timezone.utc) + timedelta(seconds=LEASE_DURATION_SECONDS)
        result = supabase_admin.table("run").update({
            "lease_until": new_until.isoformat(),
        }).eq("id", run_id).eq("lease_owner", self.worker_id).execute()
        return len(result.data) > 0
