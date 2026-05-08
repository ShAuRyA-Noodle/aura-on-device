"""Local-network token auth.

The Mac daemon binds to 127.0.0.1 by default. For the live demo the operator
flips a config flag to bind on the LAN IP — but every request must still carry
the per-session token. The token rotates each time `aura serve` starts and is
written to ~/.aura/local_auth_token (mode 600). The iOS app picks it up via a
one-time QR code that `aura serve --show-token` displays.

Auth header (preferred):  Authorization: Bearer <token>
Query fallback (WebSocket): ?token=<token>
"""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path
from typing import Optional

from fastapi import Header, HTTPException, Query, Request, WebSocket, status

# Module-global token. Initialised at process start by `init_auth()`.
_TOKEN: Optional[str] = None
_TOKEN_FILE_ENV = "AURA_TOKEN_FILE"


def _default_token_path() -> Path:
    return Path(os.path.expanduser("~/.aura/local_auth_token"))


def token_file_path() -> Path:
    """Resolve the token file path. Override with AURA_TOKEN_FILE for tests."""
    override = os.environ.get(_TOKEN_FILE_ENV)
    return Path(override) if override else _default_token_path()


def init_auth(token: Optional[str] = None, *, persist: bool = True) -> str:
    """Generate (or accept) a session token and persist it to disk.

    Returns the active token. Subsequent calls without ``token`` rotate the
    value — the previous token becomes invalid immediately.
    """
    global _TOKEN
    _TOKEN = token or secrets.token_urlsafe(32)
    if persist:
        path = token_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_TOKEN, encoding="utf-8")
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except (OSError, PermissionError):  # pragma: no cover - non-POSIX FS
            pass
    return _TOKEN


def current_token() -> Optional[str]:
    """The active session token, or None if auth is uninitialised."""
    return _TOKEN


def auth_disabled() -> bool:
    """Test / dev override. Setting AURA_DISABLE_AUTH=1 turns off enforcement."""
    return os.environ.get("AURA_DISABLE_AUTH", "").strip() in ("1", "true", "yes")


def _extract_bearer(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return auth_header.strip() or None


async def require_token(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_aura_token: Optional[str] = Header(default=None, alias="X-Aura-Token"),
) -> str:
    """FastAPI dependency: enforce the per-session token on HTTP routes."""
    if auth_disabled():
        return "disabled"
    expected = current_token()
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth not initialised",
        )
    candidate = (
        _extract_bearer(authorization)
        or (x_aura_token.strip() if x_aura_token else None)
        or request.query_params.get("token")
    )
    if not candidate or not secrets.compare_digest(candidate, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return candidate


async def require_token_ws(websocket: WebSocket, token: Optional[str] = Query(default=None)) -> str:
    """WebSocket variant. Accepts ?token= or the Sec-WebSocket-Protocol header."""
    if auth_disabled():
        return "disabled"
    expected = current_token()
    if expected is None:
        await websocket.close(code=1011, reason="auth not initialised")
        raise HTTPException(status_code=503, detail="auth not initialised")
    candidate = token or _extract_bearer(websocket.headers.get("authorization"))
    if not candidate or not secrets.compare_digest(candidate, expected):
        await websocket.close(code=4401, reason="invalid token")
        raise HTTPException(status_code=401, detail="invalid token")
    return candidate
