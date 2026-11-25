#!/usr/bin/env bash
# ==============================================================================
# Gemini 4 on Antigravity - Automated Setup Script
# Bridges Google AI Pro Web models (Neon, Carbon, Hydrogen) into Google Antigravity
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY_DIR="${REPO_DIR}/go-gemini-web2api"
CONFIG_DIR="${HOME}/.config/gemini-web2api"
COOKIE_FILE="${CONFIG_DIR}/cookie.txt"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
MCP_CONFIG_FILE="${HOME}/.gemini/config/mcp_config.json"

echo "=========================================================="
echo "   Setting up Gemini 4 Gateway for Google Antigravity    "
echo "=========================================================="

# 1. Check prerequisites
echo "--> Checking dependencies..."
for cmd in go python3 curl git; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: Required dependency '$cmd' is not installed." >&2
        exit 1
    fi
done

# 2. Build or update Go gateway
if [ ! -d "${GATEWAY_DIR}" ]; then
    echo "--> Cloning go-gemini-web2api..."
    git clone https://github.com/n0madic/go-gemini-web2api.git "${GATEWAY_DIR}"
fi

echo "--> Compiling go-gemini-web2api static binary..."
(
    cd "${GATEWAY_DIR}"
    go build -o go-gemini-web2api .
)

# 3. Configure secure cookie directory
mkdir -p "${CONFIG_DIR}"
chmod 700 "${CONFIG_DIR}"

if [ ! -f "${COOKIE_FILE}" ]; then
    echo "----------------------------------------------------------"
    echo "ACTION REQUIRED: Missing Google Session Cookies!"
    echo "Please export your cookies from gemini.google.com and save them to:"
    echo "   ${COOKIE_FILE}"
    echo "Required cookies: __Secure-1PSID, __Secure-1PSIDTS, SAPISID, SID, HSID, SSID"
    echo "----------------------------------------------------------"
    touch "${COOKIE_FILE}"
    chmod 600 "${COOKIE_FILE}"
fi

# 4. Install systemd user service
echo "--> Installing systemd user service..."
mkdir -p "${SYSTEMD_USER_DIR}"
sed "s|%h|${HOME}|g" "${REPO_DIR}/systemd/gemini-web2api.service" > "${SYSTEMD_USER_DIR}/gemini-web2api.service"
systemctl --user daemon-reload
systemctl --user enable gemini-web2api.service
systemctl --user restart gemini-web2api.service

# 5. Register in Antigravity MCP Config & Plugins
echo "--> Configuring Antigravity MCP Server and Plugins..."
mkdir -p "${HOME}/.gemini/config/plugins/gemini-4/agents"
mkdir -p "${HOME}/.gemini/config/plugins/gemini-4/skills"
mkdir -p "${HOME}/.gemini/config/plugins/gemini-4/rules"
cp "${REPO_DIR}/plugin.json" "${HOME}/.gemini/config/plugins/gemini-4/"
cp "${REPO_DIR}/agents/gemini-4-architect.md" "${HOME}/.gemini/config/plugins/gemini-4/agents/"
cp -r "${REPO_DIR}/skills/gemini-4-agent" "${HOME}/.gemini/config/plugins/gemini-4/skills/"
cp "${REPO_DIR}/rules/AGENTS.md" "${HOME}/.gemini/config/plugins/gemini-4/rules/"

mkdir -p "$(dirname "${MCP_CONFIG_FILE}")"
python3 - <<EOF
import json
import os

config_path = "${MCP_CONFIG_FILE}"
script_path = "${REPO_DIR}/mcp/gemini_4_mcp.py"

data = {"mcpServers": {}}
if os.path.exists(config_path):
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except Exception:
        pass

if "mcpServers" not in data:
    data["mcpServers"] = {}

data["mcpServers"]["gemini-4-gateway"] = {
    "command": "python3",
    "args": [script_path]
}

with open(config_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Registered gemini-4-gateway in {config_path}")
EOF

echo "=========================================================="
echo " Setup complete! Testing gateway connectivity..."
sleep 2

if curl -s http://127.0.0.1:28492/v1/models | grep -q "gemini"; then
    echo " SUCCESS: Gemini Gateway is online and responding on 127.0.0.1:28492!"
    echo " Available models:"
    curl -s http://127.0.0.1:28492/v1/models | python3 -m json.tool || true
else
    echo " Note: Gateway started, but model list not active yet."
    echo " Ensure ${COOKIE_FILE} contains valid Google session cookies."
fi
echo "=========================================================="
