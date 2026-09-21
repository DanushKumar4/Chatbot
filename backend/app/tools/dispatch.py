import json
import inspect
from typing import Any


def get_openai_tools(tool_instance: Any) -> list[dict]:
    """Convert a tool class's methods into OpenAI function-calling tool definitions."""
    tools = []
    for name, method in inspect.getmembers(tool_instance, predicate=inspect.ismethod):
        if name.startswith("_"):
            continue
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or ""

        params = {}
        required = []
        for pname, param in sig.parameters.items():
            if pname == "self":
                continue
            ptype = param.annotation
            json_type = "string"
            if ptype in (int, float):
                json_type = "number"
            elif ptype == bool:
                json_type = "boolean"
            params[pname] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(pname)

        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": required,
                },
            },
        })
    return tools


def dispatch_tool_call(tool_instance: Any, function_name: str, arguments: dict) -> str:
    """Call a method on a tool instance by name, coercing argument types."""
    method = getattr(tool_instance, function_name, None)
    if method is None:
        return json.dumps({"error": f"Unknown tool: {function_name}"})

    sig = inspect.signature(method)
    coerced = {}
    for pname, param in sig.parameters.items():
        if pname == "self" or pname not in arguments:
            continue
        val = arguments[pname]
        if param.annotation == int and isinstance(val, (float, str)):
            val = int(float(val))
        elif param.annotation == float and isinstance(val, (int, str)):
            val = float(val)
        coerced[pname] = val

    result = method(**coerced)
    return json.dumps(result, default=str)
