import json
from openai import OpenAI
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.agents.loan_agent import LoanAgent
from app.agents.account_agent import AccountAgent
from app.agents.card_agent import CardAgent
from app.agents.complaint_agent import ComplaintAgent
from app.database import supabase_admin

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

AGENTS = {
    "loan_agent": LoanAgent(),
    "account_agent": AccountAgent(),
    "card_agent": CardAgent(),
    "complaint_agent": ComplaintAgent(),
}

ROUTER_SYSTEM_PROMPT = """You are the SuperAgent — the intelligent router for SmartBank's AI assistant.

Your job is to analyze the customer's message and route it to the correct specialist agent.

Available agents:
- loan_agent: Handles loan eligibility, EMI calculations, loan applications, loan status
- account_agent: Handles account balance, transactions, statements, customer profile
- card_agent: Handles credit/debit card queries, blocking/unblocking cards, card statements
- complaint_agent: Handles filing complaints, checking complaint status, escalating issues

For general greetings or questions that don't clearly fit one agent, respond directly with a helpful message and list what you can help with.

Respond ONLY with a JSON object in this exact format:
{"route_to": "agent_name", "reason": "brief reason"}

Or for general/greeting messages:
{"route_to": "self", "reply": "your direct response"}
"""


class SuperAgent:
    name = "super_agent"

    def route_and_execute(self, user_message: str, history: list[dict], customer_id: int, thread_id: str, run_id: str) -> dict:
        """Route the user's message to the appropriate agent and execute."""
        self._log(thread_id, run_id, "routing", {"message": user_message[:200]})

        routing_messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        ]
        for msg in history[-6:]:
            routing_messages.append({"role": msg["role"], "content": msg["content"]})
        routing_messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=routing_messages,
            temperature=0,
            max_tokens=200,
        )
        raw = response.choices[0].message.content.strip()

        try:
            raw_clean = raw
            if raw_clean.startswith("```"):
                raw_clean = raw_clean.split("\n", 1)[1].rsplit("```", 1)[0]
            decision = json.loads(raw_clean)
        except (json.JSONDecodeError, IndexError):
            decision = {"route_to": "self", "reply": raw}

        route_to = decision.get("route_to", "self")

        if route_to == "self":
            reply = decision.get("reply", "Hello! I'm SmartBank's AI assistant. I can help you with accounts, loans, cards, and complaints. What would you like to know?")
            self._log(thread_id, run_id, "self_reply", {"reply_length": len(reply)})

            supabase_admin.table("run").update({"routed_to": "super_agent"}).eq("id", run_id).execute()
            return {"agent": "super_agent", "reply": reply, "routed_to": "super_agent"}

        agent = AGENTS.get(route_to)
        if not agent:
            self._log(thread_id, run_id, "unknown_route", {"attempted": route_to})
            return {
                "agent": "super_agent",
                "reply": "I'm sorry, I couldn't determine the right department. Could you rephrase your question?",
                "routed_to": "super_agent",
            }

        self._log(thread_id, run_id, "routed", {
            "target": route_to, "reason": decision.get("reason", ""),
        })

        supabase_admin.table("run").update({"routed_to": route_to}).eq("id", run_id).execute()

        agent_messages = []
        for msg in history:
            agent_messages.append({"role": msg["role"], "content": msg["content"]})
        agent_messages.append({"role": "user", "content": user_message})

        result = agent.run(agent_messages, customer_id, thread_id, run_id)
        result["routed_to"] = route_to
        return result

    def _log(self, thread_id: str, run_id: str, action: str, detail: dict):
        supabase_admin.table("agent_log").insert({
            "thread_id": thread_id,
            "run_id": run_id,
            "agent_name": self.name,
            "action": action,
            "detail": detail,
        }).execute()
