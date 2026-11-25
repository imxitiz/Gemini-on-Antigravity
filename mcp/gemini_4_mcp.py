#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server bridging Google Antigravity to Gemini 4 Models:
- Gemini 4 Neon (Deeper Analysis tier)
- Gemini 4 Carbon (Code & Complex Work tier)
- Gemini 4 Hydrogen (Everyday Help tier)
- Gemini 4 Auto (Adaptive routing tier)

Powered by the local go-gemini-web2api gateway session.
"""

import sys
import json
import urllib.request
import urllib.error
import subprocess
import time

GATEWAY_ENDPOINT = "http://127.0.0.1:28492/v1/chat/completions"

MODEL_MAP = {
    "neon": "gemini-deeper-analysis",          # Gemini 4 Neon (Deeper Analysis)
    "carbon": "gemini-code-&-complex-work",    # Gemini 4 Carbon (Code & Complex Work)
    "hydrogen": "gemini-everyday-help",        # Gemini 4 Hydrogen (Everyday Help)
    "auto": "gemini-auto"                      # Adaptive Routing
}

REASONING_PROMPTS = {
    "xhigh": (
        "[Reasoning Directive: X-HIGH (Maximal Cognitive Depth)]\n"
        "- Deconstruct the task from first principles and evaluate foundational assumptions.\n"
        "- Explore counter-arguments, failure modes, subtle edge cases, and performance bottlenecks.\n"
        "- Validate constraints thoroughly before formulating conclusions.\n"
        "- Provide an exhaustive, step-by-step, production-grade architectural or technical breakdown."
    ),
    "high": (
        "[Reasoning Directive: HIGH]\n"
        "- Perform comprehensive multi-step reasoning.\n"
        "- Analyze alternative approaches, identify edge cases, and justify trade-offs clearly.\n"
        "- Structure the response with clear, rigorous verification."
    ),
    "medium": (
        "[Reasoning Directive: MEDIUM]\n"
        "- Provide balanced, structured analytical reasoning with clear explanations."
    ),
    "low": (
        "[Reasoning Directive: LOW]\n"
        "- Deliver a direct, concise response focused strictly on the final outcome with minimal preamble."
    )
}

def query_gemini(
    model_key: str,
    prompt: str,
    system_prompt: str = "",
    reasoning_effort: str = "default",
    temperature: float = None,
    retry_on_400: bool = True
) -> str:
    upstream_model = MODEL_MAP.get(model_key.lower(), "gemini-deeper-analysis")
    
    # Determine default effort based on model tier
    if reasoning_effort == "default" or not reasoning_effort:
        if model_key.lower() == "neon":
            effort = "xhigh"
        elif model_key.lower() == "carbon":
            effort = "high"
        elif model_key.lower() == "hydrogen":
            effort = "low"
        else:
            effort = "medium"
    else:
        effort = reasoning_effort.lower()

    reasoning_guide = REASONING_PROMPTS.get(effort, REASONING_PROMPTS["high"])

    combined_system_prompt = reasoning_guide
    if system_prompt:
        combined_system_prompt = f"{system_prompt}\n\n{reasoning_guide}"

    messages = [
        {"role": "system", "content": combined_system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": upstream_model,
        "messages": messages
    }
    if temperature is not None:
        payload["temperature"] = temperature

    req = urllib.request.Request(
        GATEWAY_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        # 180s timeout allows deep thinking chains on Neon/Carbon to complete cleanly
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code == 400 and retry_on_400:
            # Model catalog desync (e.g. cold boot before network up).
            # Restart gateway service to trigger fresh otAQ7b model discovery.
            try:
                subprocess.run(
                    ["systemctl", "--user", "restart", "gemini-web2api.service"],
                    check=True,
                    timeout=15
                )
                time.sleep(3)
                return query_gemini(
                    model_key, prompt, system_prompt, reasoning_effort, temperature, retry_on_400=False
                )
            except Exception as restart_err:
                return (
                    f"Error: Gemini Gateway returned 400 (model catalog desync) "
                    f"and service auto-restart failed: {restart_err}"
                )
        error_detail = ""
        try:
            error_detail = e.read().decode("utf-8")
        except Exception:
            pass
        return f"Error connecting to local Gemini Gateway ({GATEWAY_ENDPOINT}): HTTP {e.code} - {e.reason}\n{error_detail}"
    except urllib.error.URLError as e:
        return (
            f"Error connecting to local Gemini Gateway at {GATEWAY_ENDPOINT}: {e}.\n"
            f"Ensure gemini-web2api.service is active: systemctl --user status gemini-web2api.service"
        )
    except Exception as e:
        return f"Error executing Gemini 4 request: {e}"

TOOLS = [
    {
        "name": "gemini_4_neon",
        "description": (
            "Invoke Google's Gemini 4 Neon model (Deeper Analysis tier). "
            "Optimized for deep multi-step architectural planning, research decomposition, "
            "exhaustive hypothesis testing, and maximum reasoning effort (xhigh)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The complex task, query, architectural dilemma, or plan to analyze."
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional persona or specific context guidelines."
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "xhigh"],
                    "description": "Cognitive depth level. Defaults to 'xhigh' for Neon."
                },
                "temperature": {
                    "type": "number",
                    "description": "Optional sampling temperature (0.0 to 1.0)."
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "gemini_4_carbon",
        "description": (
            "Invoke Google's Gemini 4 Carbon model (Code & Complex Work tier). "
            "Optimized for advanced software engineering, repository refactoring, "
            "algorithmic design, and complex algorithmic debugging."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The coding or technical task to execute."
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional system guidelines or coding standards."
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "xhigh"],
                    "description": "Cognitive depth level. Defaults to 'high' for Carbon."
                },
                "temperature": {
                    "type": "number",
                    "description": "Optional sampling temperature (0.0 to 1.0)."
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "gemini_4_hydrogen",
        "description": (
            "Invoke Google's Gemini 4 Hydrogen model (Everyday Help tier). "
            "Supports customizable reasoning effort (low, medium, high, xhigh) for everyday tasks and low-latency workflows."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt or task for Gemini 4 Hydrogen."
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional instructions."
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "xhigh"],
                    "description": "Cognitive depth level (low, medium, high, xhigh). Defaults to 'low'."
                },
                "temperature": {
                    "type": "number",
                    "description": "Optional sampling temperature (0.0 to 1.0)."
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "gemini_4_auto",
        "description": (
            "Invoke Gemini with dynamic tier selection (gemini-auto). "
            "Supports customizable reasoning effort (low, medium, high, xhigh)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to process."
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional system guidelines."
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "xhigh"],
                    "description": "Cognitive depth level (low, medium, high, xhigh). Defaults to 'medium'."
                },
                "temperature": {
                    "type": "number",
                    "description": "Optional sampling temperature (0.0 to 1.0)."
                }
            },
            "required": ["prompt"]
        }
    }
]

def handle_message(msg):
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "gemini-4-gateway",
                    "version": "1.1.0"
                }
            }
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS}
        }
    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        prompt = args.get("prompt", "")
        system_prompt = args.get("system_prompt", "")
        reasoning_effort = args.get("reasoning_effort", "default")
        temperature = args.get("temperature", None)

        if tool_name == "gemini_4_neon":
            res_text = query_gemini("neon", prompt, system_prompt, reasoning_effort, temperature)
        elif tool_name == "gemini_4_carbon":
            res_text = query_gemini("carbon", prompt, system_prompt, reasoning_effort, temperature)
        elif tool_name == "gemini_4_hydrogen":
            res_text = query_gemini("hydrogen", prompt, system_prompt, reasoning_effort=reasoning_effort, temperature=temperature)
        elif tool_name == "gemini_4_auto":
            res_text = query_gemini("auto", prompt, system_prompt, reasoning_effort=reasoning_effort, temperature=temperature)
        else:
            res_text = f"Unknown tool: {tool_name}"

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": res_text}]
            }
        }
    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_message(req)
            if res is not None:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
