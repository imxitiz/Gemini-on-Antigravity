# Gemini on Antigravity

Integrate Google's frontier web models—**Gemini 4 Neon** (`gemini-deeper-analysis`), **Gemini 4 Carbon** (`gemini-code-&-complex-work`), and **Gemini 4 Hydrogen** (`gemini-everyday-help`)—into **Google Antigravity** using your existing Google AI Pro web subscription.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Google Antigravity IDE    |
                      +--------------+--------------+
                                     |
                                     | (MCP Protocol / stdio)
                                     v
                      +-----------------------------+
                      |   gemini_4_mcp Server       |
                      |   - All Thinking Levels     |
                      |   - Auto Catalog Recovery   |
                      +--------------+--------------+
                                     |
                                     | (HTTP 127.0.0.1:28492)
                                     v
                      +-----------------------------+
                      |    Local Web2API Gateway    |
                      |    (go-gemini-web2api)      |
                      +--------------+--------------+
                                     |
                                     | (Google Session Cookies)
                                     v
                      +-----------------------------+
                      |    gemini.google.com        |
                      |   (Google AI Pro Models)    |
                      +-----------------------------+
```

---

## Token Quota & Execution Modes

You can run Gemini 4 in two distinct operating modes:

### Mode 1: Autonomous Agent Loop (100% Web Quota, 0 Antigravity Tokens)
Use `scripts/gemini_agent.py` to run an autonomous agent on your local machine powered entirely by Gemini 4 Neon:
```bash
python3 scripts/gemini_agent.py "Refactor our authentication middleware and test with pytest" --model neon --effort xhigh
```
- **How it works**: Gemini 4 Neon acts as the primary agent brain, autonomously executing local tools (`bash`, `read_file`, `write_file`, `edit_file`, `list_dir`).
- **Quota**: **100% billed to your Google AI Pro web subscription**. Consumes zero Antigravity tokens.

### Mode 2: Native Antigravity MCP Integration (Hybrid Mode)
Call Gemini 4 directly inside Antigravity conversations via MCP tools (`gemini_4_neon`, `gemini_4_carbon`, `gemini_4_hydrogen`):
- Antigravity queries Gemini 4 for architectural blueprints and deep reasoning.
- Neon's response is generated via your Google AI Pro web quota.

---

## Controllable Thinking Effort (All Models)

Thinking effort is fully controllable on **every model tier**:

| Model | Internal Slug | Default Effort | Supported Effort Levels |
|---|---|---|---|
| `gemini_4_neon` | `gemini-deeper-analysis` | `xhigh` | `low`, `medium`, `high`, `xhigh` |
| `gemini_4_carbon` | `gemini-code-&-complex-work` | `high` | `low`, `medium`, `high`, `xhigh` |
| `gemini_4_hydrogen` | `gemini-everyday-help` | `low` | `low`, `medium`, `high`, `xhigh` |
| `gemini_4_auto` | `gemini-auto` | `medium` | `low`, `medium`, `high`, `xhigh` |

### Effort Descriptions:
- **`xhigh`**: Exhaustive first-principles analysis, assumption stress-testing, counter-arguments, and edge-case anticipation.
- **`high`**: Deep multi-step reasoning, trade-off evaluations, and verification.
- **`medium`**: Balanced, structured analytical reasoning.
- **`low`**: Direct and concise output with minimal preamble.

---

## Quickstart

### 1. Automated Setup

Run the automated installer:

```bash
./scripts/setup.sh
```

The script will:
- Check dependencies (`go`, `python3`, `curl`).
- Build the Go gateway binary.
- Create `~/.config/gemini-web2api/` with secure permissions.
- Install and start the user `systemd` daemon on dedicated port `28492`.
- Register `gemini-4-gateway` in Antigravity MCP and global plugins.

### 2. Exporting Google Cookies

1. Open your browser and navigate to [gemini.google.com](https://gemini.google.com) on your Google AI Pro account.
2. Open DevTools (`F12`) -> **Application** -> **Cookies** -> `https://gemini.google.com` and `.google.com`.
3. Export cookies into `~/.config/gemini-web2api/cookie.txt`.
4. Ensure master cookies are present:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`
   - `SAPISID`
   - `SID`
   - `HSID`
   - `SSID`
5. Restart the gateway service:
   ```bash
   systemctl --user restart gemini-web2api.service
   ```

---

## Service Management

- Check gateway status:
  ```bash
  systemctl --user status gemini-web2api.service
  ```
- View service logs:
  ```bash
  journalctl --user -u gemini-web2api.service -f
  ```
- Verify available models:
  ```bash
  curl -s http://127.0.0.1:28492/v1/models | jq .
  ```

---

## Security & Privacy Guidelines

- **Credential Isolation**: Cookies are stored in `~/.config/gemini-web2api/cookie.txt` outside any git repository and protected with `chmod 600`.
- **Session Continuity**: The gateway communicates with Google's cookie rotation endpoint to maintain active sessions.
