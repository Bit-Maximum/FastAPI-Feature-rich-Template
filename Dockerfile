# Start from a slim version of Python 3.13
FROM python:3.14-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.6.4 /uv /uvx /bin/

# Set Envs
ENV APP_HOME=/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    PATH="$APP_HOME/.venv/bin:$PATH" \
    UV_LINK_MODE=copy \
    PYTHONPATH=$APP_HOME

WORKDIR $APP_HOME

# Install in a single layer, and clean up in the same layer to minimize image size
RUN apt-get update \
    && apt-get install -y --no-install-recommends  \
    libpq-dev  \
    curl  \
    ca-certificates  \
    wget \
    && pip install --prefer-binary --no-cache-dir --upgrade pip \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# ===== Prod stage =====
FROM base AS prod

COPY pyproject.toml uv.lock alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

COPY ./app .$APP_HOME

CMD ["python", "-m", "app"]

# ===== Dev stage =====
FROM prod AS dev

RUN uv sync --locked
