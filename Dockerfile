# --- Stage 1: Build Base ---
FROM python:3.11-slim as base

# Common environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONMALLOC=malloc \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# --- Stage 2: Builder ---
FROM base as builder

# Build configuration
ENV POETRY_VERSION=2.0.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system build dependencies using BuildKit cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install dependencies into project's .venv
RUN --mount=type=cache,target=/root/.cache/pip \
    poetry install --no-root --only main

# --- Stage 3: Runner ---
FROM base as runner

LABEL org.opencontainers.image.title="BMO Assistant" \
    org.opencontainers.image.description="Modular AI Assistant API Environment" \
    org.opencontainers.image.version="0.1.0"

# Install runtime dependencies and tini for signal handling
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    tini \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a secure non-root user
RUN addgroup --system --gid 1001 bmo && \
    adduser --system --uid 1001 --gid 1001 --home /app bmo

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder --chown=bmo:bmo /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY --chown=bmo:bmo src ./src

# Persistence setup
RUN mkdir -p persistence && chown -R bmo:bmo persistence && chmod 700 persistence

USER bmo

# Runtime Configuration
ENV PORT=8000 \
    PYTHONPATH="/app"

EXPOSE 8000

# Healthcheck to ensure API is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Use tini as init to handle signals correctly (SIGTERM, SIGINT)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start the uvicorn server in optimized production mode
CMD ["uvicorn", "src.BMO.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
