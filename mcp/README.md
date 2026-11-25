# Gemini 4 Gateway MCP Server

This directory contains the Model Context Protocol (MCP) server that connects Google Antigravity to your local Gemini 4 gateway.

## Tools Exposed

| Tool Name | Upstream Model | Target Use Case | Default Effort |
|---|---|---|---|
| `gemini_4_neon` | `gemini-deeper-analysis` | Architectural planning, deep reasoning, first-principles logic | `xhigh` |
| `gemini_4_carbon` | `gemini-code-&-complex-work` | Advanced software engineering, heavy refactoring, debugging | `high` |
| `gemini_4_hydrogen` | `gemini-everyday-help` | Rapid execution, low-latency tasks | `low` |
| `gemini_4_auto` | `gemini-auto` | Adaptive dynamic tier | `medium` |

## Tool Parameters

- `prompt` (*string, required*): The prompt, code, or task description.
- `system_prompt` (*string, optional*): Custom instructions or persona definitions.
- `reasoning_effort` (*string, optional*): One of `["low", "medium", "high", "xhigh"]`.
- `temperature` (*number, optional*): Sampling temperature between 0.0 and 1.0.

## Antigravity Configuration

Add this entry to `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "gemini-4-gateway": {
      "command": "python3",
      "args": [
        "/path/to/Gemini-on-Antigravity/mcp/gemini_4_mcp.py"
      ]
    }
  }
}
```
