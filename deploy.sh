#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="/app/InvoiceReader"
REPO="https://github.com/leopbar/InvoiceReader.git"

# ── 1. Clone or pull ──────────────────────────────────────────────────────────
if [ -d "$DEPLOY_DIR/.git" ]; then
    git -C "$DEPLOY_DIR" fetch --all
    git -C "$DEPLOY_DIR" reset --hard origin/main
else
    rm -rf "$DEPLOY_DIR"
    git clone "$REPO" "$DEPLOY_DIR"
fi

cd "$DEPLOY_DIR"

# ── 2. Write environment files ────────────────────────────────────────────────
# VPS_ENV is forwarded as an env var from the GitHub Actions step
printf '%s' "$VPS_ENV" > .env

# Extract backend vars (exclude VITE_ prefixed lines)
grep -v '^VITE_' .env | grep -v '^#' | grep -v '^$' > backend/.env

# ── 3. Rebuild and restart containers ────────────────────────────────────────
docker compose pull --quiet 2>/dev/null || true
docker compose build --no-cache
docker compose up -d --remove-orphans

# ── 4. Clean up dangling images ───────────────────────────────────────────────
docker image prune -f

echo "Deploy complete."
