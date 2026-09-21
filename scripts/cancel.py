"""CLI script to cancel a queued or running run.

Usage:
    python -m scripts.cancel <run_id>
"""

import argparse
from app.database import supabase_admin
from scripts._term import header, success, error as err_fmt, info


def main():
    parser = argparse.ArgumentParser(description="Cancel a run")
    parser.add_argument("run_id", help="The run ID to cancel")
    args = parser.parse_args()

    print(header("SmartBank — Cancel Run"))

    run = supabase_admin.table("run").select("*").eq("id", args.run_id).single().execute()
    if not run.data:
        print(err_fmt(f"Run {args.run_id} not found"))
        return

    r = run.data
    print(info(f"Run: {r['id']}  Status: {r['status']}  Agent: {r.get('routed_to', '—')}"))

    if r["status"] in ("succeeded", "failed", "cancelled", "dead"):
        print(err_fmt(f"Cannot cancel — run is already {r['status']}"))
        return

    if r["status"] == "queued":
        supabase_admin.table("run").update({
            "status": "cancelled",
            "completed_at": "now()",
        }).eq("id", args.run_id).execute()
        print(success("Run cancelled immediately (was queued)"))
    else:
        supabase_admin.table("run").update({
            "cancel_requested": True,
        }).eq("id", args.run_id).execute()
        print(success("Cancel requested — worker will stop at next step"))


if __name__ == "__main__":
    main()
