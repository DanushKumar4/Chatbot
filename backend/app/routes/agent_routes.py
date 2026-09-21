from fastapi import APIRouter
from app.database import supabase_admin

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/logs/{thread_id}")
def get_agent_logs(thread_id: str):
    """Get all agent activity logs for a thread — used by the monitoring panel."""
    logs = supabase_admin.table("agent_log").select("*").eq("thread_id", thread_id).order("created_at").execute()
    return {"logs": logs.data}


@router.get("/runs/{thread_id}")
def get_runs(thread_id: str):
    """Get all runs for a thread with their routing info."""
    runs = supabase_admin.table("run").select("*").eq("thread_id", thread_id).order("created_at", desc=True).execute()
    return {"runs": runs.data}


@router.get("/stats")
def get_agent_stats():
    """Get overall agent usage statistics for the monitoring dashboard."""
    logs = supabase_admin.table("agent_log").select("agent_name, action").execute()

    stats = {}
    for log in logs.data:
        agent = log["agent_name"]
        if agent not in stats:
            stats[agent] = {"total_actions": 0, "tool_calls": 0, "routes": 0}
        stats[agent]["total_actions"] += 1
        if log["action"] == "tool_call":
            stats[agent]["tool_calls"] += 1
        if log["action"] == "routed":
            stats[agent]["routes"] += 1

    runs = supabase_admin.table("run").select("status").execute()
    run_stats = {"total": len(runs.data), "succeeded": 0, "failed": 0, "running": 0}
    for r in runs.data:
        if r["status"] in run_stats:
            run_stats[r["status"]] += 1

    return {"agent_stats": stats, "run_stats": run_stats}
