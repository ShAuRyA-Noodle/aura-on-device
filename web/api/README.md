# Aura — local-network FastAPI bridge

This is the Mac-side daemon the iPhone connects to during development and the
live demo. It runs the full Aura agent stack in-process and streams Reasoning
Trace events to the iOS client over WebSocket.

## Quick start

```bash
# 1. Install (editable).
pip install -e ./web/api/

# 2. Show the QR + start the daemon. The token is generated fresh per session.
aura serve --show-token --host 0.0.0.0 --port 8000
```

The QR encodes `{"url": "http://<lan>:8000", "ws": "ws://<lan>:8000/ws/trace", "token": "..."}`. Scan it from the iOS app's Connect screen.

Without the CLI:

```bash
bash web/run_local.sh                # default 127.0.0.1
AURA_BIND=0.0.0.0 bash web/run_local.sh  # demo mode
```

## Endpoints

| Method | Path                              | Notes                                     |
| ------ | --------------------------------- | ----------------------------------------- |
| GET    | `/`                               | service banner                            |
| GET    | `/health`                         | full subsystem report                     |
| GET    | `/metrics`                        | Prometheus exposition                     |
| GET    | `/openapi.json`, `/docs`          | OpenAPI spec + Swagger UI                 |
| POST   | `/api/comms/triage`               | notif list -> urgent/drafts/muted_count   |
| POST   | `/api/calendar/conflicts`         | events -> conflict spans                  |
| POST   | `/api/finance/parse_sms`          | SMS list -> structured txns               |
| POST   | `/api/finance/categorize`         | merchants -> categories                   |
| POST   | `/api/wellness/load_score`        | features -> score + drivers + intervention|
| POST   | `/api/orchestrator/tick`          | full UserState -> action + trace          |
| POST   | `/api/orchestrator/run_replay`    | named replay -> action + trace            |
| POST   | `/api/memory/add_node`            | typed graph node                          |
| POST   | `/api/memory/search`              | vector + keyword                          |
| DELETE | `/api/memory/by_time_range`       | retention surgery                         |
| GET    | `/api/memory/export`              | JSON Schema export                        |
| GET    | `/api/memory/audit_log`           | tamper-evident hash chain                 |
| WS     | `/ws/trace`                       | live Reasoning Trace stream               |

Every endpoint requires `Authorization: Bearer <token>` unless
`AURA_DISABLE_AUTH=1` is set (used by the test suite).

## CLI

```
aura serve [--host] [--port] [--show-token] [--reload]
aura status
aura replay morning_brief|lecture_focus|spend_anomaly|recovery
aura token [--rotate]
```

## Tests + load

```bash
pytest web/api/ -q
locust -f web/api/load_test.py --host http://localhost:8000 -u 100 -r 20 -t 1m
```

## iOS pairing flow

1. Run `aura serve --show-token --host 0.0.0.0` on the Mac.
2. Mac and iPhone are on the same Wi-Fi.
3. Open the Aura iOS app's Settings -> Connect -> "Scan QR".
4. The app stores `(base_url, ws_url, token)` securely (Keychain) and
   immediately opens `/ws/trace?token=...` for the live trace overlay.

## Troubleshooting

- **"401 invalid token"** — the token rotates every `aura serve`. Re-scan the QR.
- **iPhone can't reach the daemon** — the macOS firewall blocks LAN binds by
  default. *System Settings -> Network -> Firewall -> Options* and allow
  Python. Check `lsof -nP -iTCP:8000` to confirm the bind interface.
- **USB tethering on macOS** — connect the iPhone with a Lightning cable, then
  enable Personal Hotspot. The Mac picks up `bridge100`. `ifconfig bridge100`
  to find the daemon's reachable IP, then bind: `aura serve --host <bridge_ip>`.
- **`websocat`** smoke test:
  ```bash
  websocat "ws://127.0.0.1:8000/ws/trace?token=$(cat ~/.aura/local_auth_token)"
  ```
- **Prometheus** scrape:
  ```bash
  curl -s http://127.0.0.1:8000/metrics | grep aura_
  ```

## Layout

```
web/api/
├── __init__.py        # version
├── main.py            # FastAPI app + endpoints + WS
├── auth.py            # bearer-token auth, ~/.aura/local_auth_token
├── middleware.py      # structlog + request-id + slowapi rate limiter
├── observability.py   # Prometheus registry + helpers
├── health.py          # /health response model
├── trace_bus.py       # in-process pub/sub for trace events
├── cli.py             # `aura` Typer CLI
├── setup.py           # pip install -e ./web/api/
├── Dockerfile         # multi-stage, non-root, healthcheck
├── conftest.py        # pytest fixtures
├── test_api.py        # endpoint suite
├── test_websocket.py  # WS sequence smoke test
├── load_test.py       # locust scenarios
└── requirements.txt
```
