# Tadabbur backend
#
#   docker build --target production -t tadabbur-backend .
#
# The production image contains the application and its Python dependencies
# only: no compiler, no torch, no model weights, no secrets. All AI inference
# runs on Hugging Face Inference Providers; configuration (including HF_TOKEN)
# is supplied as environment variables at run time.

ARG PYTHON_IMAGE=python:3.11-slim-bookworm

# ---------------------------------------------------------------- builder
FROM ${PYTHON_IMAGE} AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /src
# Resolve and install the declared dependencies (non-editable). The app
# package itself is then removed from the venv: the runtime image runs the
# code from /app so there is exactly one copy of it.
COPY pyproject.toml ./
COPY app ./app
# Optional build secret "extra_ca": a CA bundle for builds behind a TLS-
# intercepting proxy. It is mounted only for this step and never stored in a layer.
RUN --mount=type=secret,id=extra_ca \
    if [ -s /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
    pip install --upgrade pip && pip install . && pip uninstall -y tadabbur-ai

# ------------------------------------------------------------ development
# Used by docker-compose.portable.yml for local work only (auto-reload).
FROM ${PYTHON_IMAGE} AS development
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN --mount=type=secret,id=extra_ca \
    if [ -s /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
    pip install -e ".[dev]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ------------------------------------------------------------- production
FROM ${PYTHON_IMAGE} AS production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    ENVIRONMENT=production \
    WORKERS=2 \
    PORT=8000 \
    FORWARDED_ALLOW_IPS=127.0.0.1 \
    TASMEE_AUDIO_DIR=/tmp/tasmee_audio \
    REVIEW_STATE_DIR=/var/lib/tadabbur

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app \
 && install -d -o app -g app /var/lib/tadabbur

COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
# Application code is owned by root and read-only for the runtime user.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=4).status == 200 else 1)"]

# No --reload. Proxy headers are trusted only from FORWARDED_ALLOW_IPS
# (the reverse proxy); WORKERS sizes the process pool.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\" --workers \"$WORKERS\" --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\" --no-server-header --timeout-graceful-shutdown 30"]
