#!/usr/bin/env bash
set -euo pipefail

# Publish both skills to ClawHub (OpenClaw's skill registry)
# Prerequisites: clawhub login

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-1.0.0}"

echo "Publishing escpos-print skill v${VERSION} to ClawHub..."
clawhub publish "$PLUGIN_DIR/skills/escpos-print" \
    --slug escpos-print \
    --name "ESC/POS Printer" \
    --version "$VERSION" \
    --tags latest \
    --changelog "Print to ESC/POS thermal printers over IP, USB, or serial"

echo ""
echo "Publishing print command skill v${VERSION} to ClawHub..."
clawhub publish "$PLUGIN_DIR/skills/print" \
    --slug escpos-print-command \
    --name "ESC/POS /print Command" \
    --version "$VERSION" \
    --tags latest \
    --changelog "/print slash command for ESC/POS thermal printers"

echo ""
echo "Done. Skills published to ClawHub."
