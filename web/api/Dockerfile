# Aura local-network FastAPI bridge — production-grade Docker image.
#
# Multi-stage build keeps the runtime layer small. Phase 2 ships this to a
# lightweight VM behind Tailscale; the on-device Mac flow uses run_local.sh.

FROM python:3.11-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY web/api/requirements.txt /build/requirements.txt
RUN pip install --user --prefix=/install -r /build/requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AURA_BIND=0.0.0.0 \
    AURA_PORT=8000

# Non-root user.
RUN groupadd --system aura \
 && useradd --system --gid aura --home /home/aura --create-home aura

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=aura:aura . /app

USER aura

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; \
    urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()" || exit 1

CMD ["python", "-m", "uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
