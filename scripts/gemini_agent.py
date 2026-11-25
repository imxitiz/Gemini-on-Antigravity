#!/usr/bin/env python3
"""
Autonomous Gemini 4 Agent Runner (A2A / Local Autonomous Loop)
Executes tasks on your local machine using Google's Gemini 4 models (Neon, Carbon, Hydrogen)
directly via the local go-gemini-web2api gateway (100% Google AI Pro web quota, 0 Antigravity tokens).
"""

import os
import sys
import json
import argparse
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any

GATEWAY_URL = "http://127.0.0.1:28492/v1/chat/completions"

MODEL_MAP = {
    "neon": "gemini-deeper-analysis",
    "carbon": "gemini-code-&-complex-work",
    "hydrogen": "gemini-everyday-help",
    "auto": "gemini-auto"
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash shell command in the local workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command line string to run."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative or absolute path to the file."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional 1-based start line."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional 1-based end line."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write."
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace exact target string with replacement in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to edit."
                    },
                    "target": {
                        "type": "string",
                        "description": "Exact text to find and replace."
                    },
                    "replacement": {
                        "type": "string",
                        "description": "New text to insert."
                    }
                },
                "required": ["path", "target", "replacement"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories in a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (defaults to current dir)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Signal that the task is complete and provide the final report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Comprehensive summary of actions taken and final result."
                    }
                },
                "required": ["summary"]
            }
        }
    }
]

def execute_tool(name: str, args: Dict[str, Any], cwd: str) -> str:
    try:
        if name == "bash":
            cmd = args.get("command", "")
            print(f"  \033[33m$ {cmd}\033[0m")
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=120
            )
            out = res.stdout + ("\nSTDERR:\n" + res.stderr if res.stderr else "")
            return out.strip() if out.strip() else "(command completed with no output)"

        elif name == "read_file":
            path = os.path.expanduser(args.get("path", ""))
            if not os.path.isabs(path):
                path = os.path.join(cwd, path)
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist."
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            start = args.get("start_line", 1) or 1
            end = args.get("end_line", len(lines)) or len(lines)
            selected = lines[max(0, start - 1):end]
            return "".join(selected)

        elif name == "write_file":
            path = os.path.expanduser(args.get("path", ""))
            if not os.path.isabs(path):
                path = os.path.join(cwd, path)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(args.get("content", ""))
            return f"Successfully wrote {len(args.get('content', ''))} bytes to '{path}'."

        elif name == "edit_file":
            path = os.path.expanduser(args.get("path", ""))
            if not os.path.isabs(path):
                path = os.path.join(cwd, path)
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist."
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            target = args.get("target", "")
            replacement = args.get("replacement", "")
            if target not in content:
                return f"Error: Target text not found in '{path}'."
            new_content = content.replace(target, replacement, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"Successfully replaced target in '{path}'."

        elif name == "list_dir":
            path = os.path.expanduser(args.get("path", ".") or ".")
            if not os.path.isabs(path):
                path = os.path.join(cwd, path)
            entries = os.listdir(path)
            return "\n".join(sorted(entries))

        elif name == "finish":
            return args.get("summary", "Task completed.")

        return f"Unknown tool: {name}"

    except Exception as e:
        return f"Tool execution error: {e}"

def call_gemini(model: str, messages: List[Dict[str, Any]], effort: str) -> Dict[str, Any]:
    upstream_model = MODEL_MAP.get(model.lower(), "gemini-deeper-analysis")
    payload = {
        "model": upstream_model,
        "messages": messages,
        "tools": TOOLS
    }
    req = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_agent(goal: str, model: str = "neon", effort: str = "xhigh", max_turns: int = 25, cwd: str = None):
    if not cwd:
        cwd = os.getcwd()

    print("======================================================================")
    print(f"\033[1;36mGemini Autonomous Agent (Backend: Google AI Pro Web / {model.upper()})\033[0m")
    print(f"Workspace: {cwd}")
    print(f"Reasoning Effort: {effort.upper()}")
    print(f"Goal: {goal}")
    print("======================================================================\n")

    system_prompt = (
        f"You are Gemini 4 Autonomous Agent running with {effort.upper()} reasoning depth on Linux.\n"
        f"Working directory: {cwd}\n"
        f"You have local tools to read/write files and execute bash commands.\n"
        f"Use tools methodically to inspect, plan, test, and implement what is asked.\n"
        f"When finished, call the 'finish' tool with a clear summary."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": goal}
    ]

    for turn in range(1, max_turns + 1):
        print(f"\033[1;34m[Turn {turn}/{max_turns}] Consulting Gemini {model.upper()}...\033[0m")
        try:
            resp = call_gemini(model, messages, effort)
        except Exception as e:
            print(f"\033[1;31mError communicating with gateway: {e}\033[0m")
            break

        choice = resp.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        if content:
            print(f"\033[32mAgent Thoughts:\033[0m\n{content}\n")

        messages.append(message)

        if not tool_calls:
            print("\033[1;32mTask concluded (no further tool calls).\033[0m")
            break

        finished = False
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            raw_args = func.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except Exception:
                args = {}

            print(f"\033[1;33mTool Call:\033[0m {name}({json.dumps(args, indent=2)})")
            result = execute_tool(name, args, cwd)
            print(f"\033[1;30mResult ({len(str(result))} chars)\033[0m\n")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", "call_1"),
                "content": str(result)
            })

            if name == "finish":
                finished = True
                print("======================================================================")
                print(f"\033[1;32mAGENT TASK FINISHED:\033[0m\n{result}")
                print("======================================================================")
                break

        if finished:
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run autonomous Gemini 4 agent via local gateway.")
    parser.add_argument("goal", help="The goal or instruction for the autonomous agent.")
    parser.add_argument("--model", choices=["neon", "carbon", "hydrogen", "auto"], default="neon", help="Model tier.")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh"], default="xhigh", help="Reasoning depth.")
    parser.add_argument("--turns", type=int, default=25, help="Maximum agent turns.")
    parser.add_argument("--cwd", default=None, help="Working directory path.")

    args = parser.parse_args()
    run_agent(args.goal, args.model, args.effort, args.turns, args.cwd)
