"""Editable install for `aura` CLI.

    pip install -e ./web/api/

The console script `aura` is wired to ``web.api.cli:main``.
"""

from setuptools import setup

setup(
    name="aura-local-api",
    version="1.1.0",
    description="Aura local-network FastAPI bridge + CLI.",
    packages=["aura_local_api"],
    package_dir={"aura_local_api": "."},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.115",
        "uvicorn[standard]>=0.30",
        "pydantic>=2.7",
        "structlog>=24.0",
        "slowapi>=0.1.9",
        "prometheus-client>=0.20",
        "typer>=0.12",
        "websockets>=12.0",
        "jsonschema>=4.23",
    ],
    entry_points={
        "console_scripts": [
            "aura = web.api.cli:main",
        ],
    },
)
