"""CLI script to send a message to the bank assistant.

Usage:
    python -m scripts.ask --customer-id 1 "What is my account balance?"
    python -m scripts.ask --customer-id 1 --thread <thread-id> "Show my loans"
"""

import argparse
import uuid
import sys

from app.database import supabase_admin
from app.agents.super_agent import SuperAgent
from app.memory import Memory
from scripts._term import header, user_msg, bot_msg, info


def main():
    parser = argparse.ArgumentParser(description="Ask the SmartBank assistant a question")
    parser.add_argument("message", help="Your message to the assistant")
    parser.add_argument("--customer-id", type=int, default=1, help="Customer ID (default: 1)")
    parser.add_argument("--thread", type=str, default=None, help="Existing thread ID to continue")
    args = parser.parse_args()

    print(header("SmartBank AI Assistant"))

    if args.thread:
        thread_id = args.thread
        print(info(f"Continuing thread: {thread_id}"))
    else:
        thread_id = Memory.create_thread(args.customer_id, args.message[:50])
        print(info(f"New thread: {thread_id}"))

    memory = Memory(thread_id)
    memory.append("user", args.message)

    history = memory.load_history()
    openai_history = memory.to_openai_messages(history[:-1])

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    supabase_admin.table("run").insert({
        "id": run_id,
        "thread_id": thread_id,
        "status": "running",
    }).execute()

    print(user_msg(args.message))
    print(info("Routing to agent..."))

    super_agent = SuperAgent()
    result = super_agent.route_and_execute(
        user_message=args.message,
        history=[{"role": m["role"], "content": m["content"]} for m in history[:-1]],
        customer_id=args.customer_id,
        thread_id=thread_id,
        run_id=run_id,
    )

    memory.append("assistant", result["reply"], result.get("routed_to"))

    supabase_admin.table("run").update({
        "status": "succeeded",
        "routed_to": result.get("routed_to"),
        "completed_at": "now()",
    }).eq("id", run_id).execute()

    print()
    print(bot_msg(result.get("routed_to", "super_agent"), result["reply"]))
    print()
    print(info(f"Thread: {thread_id}  |  Run: {run_id}  |  Agent: {result.get('routed_to', 'self')}"))


if __name__ == "__main__":
    main()
