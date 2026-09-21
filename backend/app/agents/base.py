import json
from openai import OpenAI
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.tools.dispatch import get_openai_tools, dispatch_tool_call
from app.database import supabase_admin

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


class BaseAgent:
    """Base class for all specialized agents."""

    name: str = "base"
    system_prompt: str = "You are a helpful banking assistant."
    tool_instance = None

    def run(self, messages: list[dict], customer_id: int, thread_id: str, run_id: str) -> dict:
        """Execute the agent's turn with tool calling loop."""
        tools = get_openai_tools(self.tool_instance) if self.tool_instance else []

        system_msg = self.system_prompt.format(customer_id=customer_id)
        full_messages = [{"role": "system", "content": system_msg}] + messages

        self._log(thread_id, run_id, "started", {"messages_count": len(messages)})

        max_iterations = 10
        for _ in range(max_iterations):
            kwargs = {"model": LLM_MODEL, "messages": full_messages, "max_tokens": 500}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
                assistant_msg = {"role": "assistant", "content": choice.message.content or ""}
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]
                full_messages.append(assistant_msg)
                for tc in choice.message.tool_calls:
                    fn_name = tc.function.name
                    fn_args = json.loads(tc.function.arguments)
                    if "customer_id" not in fn_args and "customer_id" in self._get_tool_params(fn_name):
                        fn_args["customer_id"] = customer_id

                    result = dispatch_tool_call(self.tool_instance, fn_name, fn_args)
                    self._log(thread_id, run_id, "tool_call", {
                        "tool": fn_name, "args": fn_args, "result": result[:500],
                    })
                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                continue

            reply = choice.message.content or ""
            self._log(thread_id, run_id, "completed", {"reply_length": len(reply)})
            return {"agent": self.name, "reply": reply}

        return {"agent": self.name, "reply": "I apologize, but I'm having trouble processing your request. Please try again."}

    def _get_tool_params(self, fn_name: str) -> list[str]:
        if not self.tool_instance:
            return []
        import inspect
        method = getattr(self.tool_instance, fn_name, None)
        if not method:
            return []
        return list(inspect.signature(method).parameters.keys())

    def _log(self, thread_id: str, run_id: str, action: str, detail: dict):
        supabase_admin.table("agent_log").insert({
            "thread_id": thread_id,
            "run_id": run_id,
            "agent_name": self.name,
            "action": action,
            "detail": detail,
        }).execute()
