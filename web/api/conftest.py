"""Pytest fixtures for the FastAPI bridge tests.

Auth is disabled via ``AURA_DISABLE_AUTH=1`` so endpoint tests don't have to
juggle bearer tokens. Token auth is exercised explicitly in
``test_api.py::test_auth_required``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the repo root importable.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(scope="session", autouse=True)
def _disable_auth_for_tests() -> None:
    os.environ.setdefault("AURA_DISABLE_AUTH", "1")


@pytest.fixture()
def client():
    from web.api.main import app

    with TestClient(app) as c:
        yield c
