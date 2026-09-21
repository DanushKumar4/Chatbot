import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import supabase_admin
from app.agents.super_agent import SuperAgent

router = APIRouter(prefix="/chat", tags=["chat"])
super_agent = SuperAgent()


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    customer_id: int


class NewThreadRequest(BaseModel):
    customer_id: int
    title: Optional[str] = "New Conversation"


@router.post("/send")
def send_message(req: ChatRequest):
    if not req.thread_id:
        thread = supabase_admin.table("thread").insert({
            "customer_id": req.customer_id,
            "title": req.message[:50],
        }).execute()
        thread_id = thread.data[0]["id"]
    else:
        thread_id = req.thread_id

    existing = supabase_admin.table("message").select("seq").eq("thread_id", thread_id).order("seq", desc=True).limit(1).execute()
    next_seq = (existing.data[0]["seq"] + 1) if existing.data else 1

    supabase_admin.table("message").insert({
        "thread_id": thread_id,
        "seq": next_seq,
        "role": "user",
        "content": req.message,
    }).execute()

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    supabase_admin.table("run").insert({
        "id": run_id,
        "thread_id": thread_id,
        "status": "running",
        "started_at": "now()",
    }).execute()

    history = supabase_admin.table("message").select("role, content").eq("thread_id", thread_id).order("seq").execute()

    try:
        result = super_agent.route_and_execute(
            user_message=req.message,
            history=history.data[:-1],
            customer_id=req.customer_id,
            thread_id=thread_id,
            run_id=run_id,
        )

        supabase_admin.table("message").insert({
            "thread_id": thread_id,
            "seq": next_seq + 1,
            "role": "assistant",
            "content": result["reply"],
            "agent_name": result.get("routed_to", result["agent"]),
        }).execute()

        supabase_admin.table("run").update({
            "status": "succeeded",
            "completed_at": "now()",
        }).eq("id", run_id).execute()

        return {
            "thread_id": thread_id,
            "run_id": run_id,
            "agent": result.get("routed_to", result["agent"]),
            "reply": result["reply"],
        }
    except Exception as e:
        supabase_admin.table("run").update({
            "status": "failed",
            "completed_at": "now()",
        }).eq("id", run_id).execute()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads")
def create_thread(req: NewThreadRequest):
    thread = supabase_admin.table("thread").insert({
        "customer_id": req.customer_id,
        "title": req.title,
    }).execute()
    return {"thread": thread.data[0]}


@router.get("/threads/{customer_id}")
def get_threads(customer_id: int):
    threads = supabase_admin.table("thread").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
    return {"threads": threads.data}


@router.get("/messages/{thread_id}")
def get_messages(thread_id: str):
    messages = supabase_admin.table("message").select("*").eq("thread_id", thread_id).order("seq").execute()
    return {"messages": messages.data}
