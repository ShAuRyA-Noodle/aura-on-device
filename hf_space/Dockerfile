# Optional Docker build for the Aura HuggingFace Space.
# HF Spaces accepts either a Gradio SDK config or a Dockerfile; this is the
# Dockerfile path for teams that want full control of the runtime.

FROM python:3.12-slim

# System deps stay tiny: sqlite is shipped with Python; no GPU drivers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the agent stack alongside the Space app so imports resolve cleanly.
COPY agents     /app/agents
COPY orchestrator /app/orchestrator
COPY memory     /app/memory
COPY hf_space   /app/hf_space

RUN pip install --no-cache-dir -r /app/hf_space/requirements.txt

ENV PYTHONPATH=/app
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

EXPOSE 7860

CMD ["python", "/app/hf_space/app.py"]
