# Gemini 4 Agent Rules

When using the `gemini-4` plugin or MCP tools:
1. **Architectural Decisions**: Route high-level planning, structural design, and long-horizon tasks to `gemini_4_neon` (or the `gemini-4-architect` subagent) with `reasoning_effort: xhigh`.
2. **Code & Complex Engineering**: Route complex refactoring, compiler diagnostics, and algorithmic implementation to `gemini_4_carbon` with `reasoning_effort: high`.
3. **Execution Safety**: Execute bash and file operations on the laptop using Antigravity's native tools only after verifying the proposed plan.
