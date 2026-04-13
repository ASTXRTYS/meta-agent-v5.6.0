#!/bin/bash
set -e

cd /Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Install dependencies (idempotent)
.venv/bin/pip install -e ".[dev]" --quiet 2>/dev/null || true

# Ensure test directories exist
mkdir -p tests/contract tests/integration tests/tui

# Ensure .env exists
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || true
fi

echo "Meta Harness environment ready."
