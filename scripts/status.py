"""CLI script to check status of runs and threads.

Usage:
    python -m scripts.status                    # all recent runs
    python -m scripts.status --thread <id>      # runs for a thread
    python -m scripts.status --run <id>         # detailed run info
"""

import argparse
from app.database import supabase_admin
from scripts._term import header, info, success, error as err_fmt


def main():
    parser = argparse.ArgumentParser(description="Check run/thread status")
    parser.add_argument("--thread", type=str, help="Thread ID to inspect")
    parser.add_argument("--run", type=str, help="Run ID to inspect in detail")
    args = parser.parse_args()

    print(header("SmartBank — Status"))

    if args.run:
        show_run_detail(args.run)
    elif args.thread:
        show_thread(args.thread)
    else:
        show_recent_runs()


def show_recent_runs():
    runs = supabase_admin.table("run").select("*").order(
        "created_at", desc=True
    ).limit(20).execute()
    print(f"Recent runs ({len(runs.data)}):\n")
    for r in runs.data:
        status_icon = {"succeeded": "✓", "failed": "✗", "running": "●", "queued": "○"}.get(r["status"], "?")
        routed = r.get("routed_to") or "—"
        print(f"  {status_icon} {r['id'][:20]}  status={r['status']}  agent={routed}  thread={r['thread_id'][:8]}…")


def show_thread(thread_id: str):
    thread = supabase_admin.table("thread").select("*").eq(
        "id", thread_id
    ).single().execute()
    if not thread.data:
        print(err_fmt(f"Thread {thread_id} not found"))
        return
    t = thread.data
    print(f"Thread: {t['id']}")
    print(f"Customer: {t['customer_id']}  Title: {t.get('title', '—')}")
    print()

    messages = supabase_admin.table("message").select("*").eq(
        "thread_id", thread_id
    ).order("seq").execute()
    print(f"Messages ({len(messages.data)}):")
    for m in messages.data:
        agent = f" [{m['agent_name']}]" if m.get("agent_name") else ""
        content_preview = m["content"][:80].replace("\n", " ")
        print(f"  #{m['seq']} {m['role']}{agent}: {content_preview}")

    print()
    runs = supabase_admin.table("run").select("*").eq(
        "thread_id", thread_id
    ).order("created_at").execute()
    print(f"Runs ({len(runs.data)}):")
    for r in runs.data:
        print(f"  {r['id'][:20]}  status={r['status']}  agent={r.get('routed_to', '—')}")


def show_run_detail(run_id: str):
    run = supabase_admin.table("run").select("*").eq("id", run_id).single().execute()
    if not run.data:
        print(err_fmt(f"Run {run_id} not found"))
        return
    r = run.data
    print(f"Run:     {r['id']}")
    print(f"Thread:  {r['thread_id']}")
    print(f"Status:  {r['status']}")
    print(f"Agent:   {r.get('routed_to', '—')}")
    print(f"Created: {r.get('created_at', '—')}")
    print()

    logs = supabase_admin.table("agent_log").select("*").eq(
        "run_id", run_id
    ).order("created_at").execute()
    print(f"Agent logs ({len(logs.data)}):")
    for log in logs.data:
        detail_preview = str(log.get("detail", ""))[:60]
        print(f"  [{log['agent_name']}] {log['action']}: {detail_preview}")


if __name__ == "__main__":
    main()
