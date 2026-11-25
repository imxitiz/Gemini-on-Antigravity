#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.config/systemd/user"
SERVICE_NAME="gemini-web2api.service"

mkdir -p "${TARGET_DIR}"
cp "${SCRIPT_DIR}/${SERVICE_NAME}" "${TARGET_DIR}/${SERVICE_NAME}"

echo "==> Reloading user systemd daemon..."
systemctl --user daemon-reload

echo "==> Enabling and starting ${SERVICE_NAME}..."
systemctl --user enable "${SERVICE_NAME}"
systemctl --user restart "${SERVICE_NAME}"

echo "==> Service installed and started successfully!"
systemctl --user status "${SERVICE_NAME}" --no-pager
