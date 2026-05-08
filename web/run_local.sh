#!/usr/bin/env bash
# Aura — local-network daemon runner (Mac-side).
#
#   bash web/run_local.sh                 # 127.0.0.1 only (default, safe)
#   AURA_BIND=0.0.0.0 bash web/run_local.sh   # LAN demo
#
# Boots:
#   - FastAPI + WebSocket on :8000 (the agent stack)
#   - Static React frontend on :8080
# Then opens http://localhost:8080/index.html.
#
# A per-session token is generated and written to ~/.aura/local_auth_token.
# The same token is passed to the static frontend via a tiny ?token= query
# string so the in-page WebSocket overlay can authenticate.
#
# Works offline. No CDN, no internet egress.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"

API_PORT="${AURA_API_PORT:-8000}"
WEB_PORT="${AURA_WEB_PORT:-8080}"
BIND="${AURA_BIND:-127.0.0.1}"

echo "==> Aura local daemon"
echo "    repo root : $REPO_ROOT"
echo "    bind      : $BIND"
echo "    API       : :$API_PORT"
echo "    web       : :$WEB_PORT"

# Pick a Python — prefer venv if present, else system python3.
PY="python3"
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
fi
echo "    python    : $PY"

# Best-effort dependency check.
if ! "$PY" -c "import fastapi, uvicorn, structlog, slowapi, prometheus_client, typer" 2>/dev/null; then
  echo "==> installing FastAPI bridge deps from web/api/requirements.txt"
  "$PY" -m pip install -r "$HERE/api/requirements.txt"
fi

# Generate a fresh per-session token via the Aura auth module.
TOKEN="$(
  PYTHONPATH="$REPO_ROOT" "$PY" - <<'PY'
from web.api.auth import init_auth
print(init_auth())
PY
)"
echo "    token file: ${HOME}/.aura/local_auth_token"

# Boot FastAPI in the background.
echo "==> launching uvicorn on $BIND:$API_PORT"
PYTHONPATH="$REPO_ROOT" "$PY" -m uvicorn web.api.main:app \
  --host "$BIND" --port "$API_PORT" \
  --log-level warning &
API_PID=$!

# Boot static server in the background.
echo "==> launching static server on $BIND:$WEB_PORT"
"$PY" -m http.server "$WEB_PORT" --directory "$HERE/web" --bind "$BIND" &
WEB_PID=$!

URL="http://localhost:$WEB_PORT/index.html?api=http://localhost:$API_PORT&token=$TOKEN"

# Open the browser (best-effort across macOS / Linux).
sleep 1
if command -v open >/dev/null 2>&1; then
  open "$URL" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" || true
fi

echo ""
echo "==> Aura local daemon is live."
echo "    Frontend : $URL"
echo "    API health : http://localhost:$API_PORT/health"
echo "    Trace WS   : ws://localhost:$API_PORT/ws/trace?token=$TOKEN"
echo "    Stop       : Ctrl-C"

trap 'echo "==> shutting down"; kill -TERM "$API_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM

# Bash 3.2 (macOS default) doesn't support `wait -n`; poll both PIDs.
while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do
  sleep 1
done
