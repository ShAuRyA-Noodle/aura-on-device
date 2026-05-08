"""Aura CLI — `aura serve`, `aura status`, `aura replay`.

Installable via ``pip install -e ./web/api/``. The Typer app is exposed at
``aura.cli:app`` and bound to the ``aura`` console script in ``setup.py``.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .auth import current_token, init_auth, token_file_path

app = typer.Typer(
    add_completion=False,
    help="Aura local-network daemon CLI.",
    no_args_is_help=True,
)


def _resolve_lan_ip() -> str:
    """Best-effort LAN IP discovery for the QR string."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _print_qr(payload: str) -> None:
    """Render a QR code in the terminal using ``qrcode`` if installed.

    Falls back to printing the payload so the operator can paste it into the
    iOS app's "Connect" field manually.
    """
    try:  # pragma: no cover - optional dep
        import qrcode  # type: ignore

        qr = qrcode.QRCode(border=1)
        qr.add_data(payload)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        typer.secho("(install `qrcode` for an ASCII QR; payload follows)", fg=typer.colors.YELLOW)
    typer.echo(payload)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind address. Use 0.0.0.0 for the LAN demo."),
    port: int = typer.Option(8000, help="HTTP/WS port."),
    show_token: bool = typer.Option(False, "--show-token", help="Print a QR with the token + URL."),
    reload: bool = typer.Option(False, help="Enable uvicorn --reload (dev only)."),
    log_level: str = typer.Option("info"),
) -> None:
    """Start the FastAPI daemon. Token is written to ~/.aura/local_auth_token."""
    token = init_auth()
    lan_ip = _resolve_lan_ip() if host in ("0.0.0.0", "::") else host
    base = f"http://{lan_ip}:{port}"
    payload = json.dumps({"url": base, "ws": f"ws://{lan_ip}:{port}/ws/trace", "token": token})
    if show_token:
        typer.secho(f"Aura local daemon v{__version__}", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"Bind:   {host}:{port}")
        typer.echo(f"LAN IP: {lan_ip}")
        typer.echo(f"Token file: {token_file_path()}")
        typer.echo("--- scan from the iOS app ---")
        _print_qr(payload)
        typer.echo("------------------------------")

    import uvicorn

    uvicorn.run(
        "web.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


@app.command()
def status(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    """Hit /health on a running daemon and pretty-print the result."""
    import urllib.request

    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        typer.echo(json.dumps(data, indent=2))
    except Exception as exc:
        typer.secho(f"daemon not reachable at {url}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def replay(
    name: str = typer.Argument("morning_brief"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    """Run a named replay against a running daemon and print the trace."""
    import urllib.request

    tok = current_token()
    if tok is None:
        path = token_file_path()
        if path.exists():
            tok = path.read_text().strip()
    headers = {"Content-Type": "application/json"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    body = json.dumps({"name": name}).encode("utf-8")
    req = urllib.request.Request(
        f"http://{host}:{port}/api/orchestrator/run_replay",
        data=body, headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        typer.secho(f"replay failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(data["trace"], indent=2))


@app.command()
def token(
    rotate: bool = typer.Option(False, "--rotate", help="Generate a new token."),
) -> None:
    """Print the current token (or rotate it)."""
    if rotate:
        new = init_auth()
        typer.echo(new)
        return
    path = token_file_path()
    if not path.exists():
        typer.secho("no token on disk; run `aura serve` first", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(path.read_text().strip())


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
