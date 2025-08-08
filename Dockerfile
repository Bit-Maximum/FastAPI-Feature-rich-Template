# Start from a slim version of Python 3.13
FROM python:3.13-slim AS base

# Set Python Envs
ENV APP_HOME=/app/ PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1

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
    && rm -rf /var/lib/apt/lists/* \

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH" UV_LINK_MODE=copy PYTHONPATH=$APP_HOME

# ===== Prod stage =====
FROM base AS prod

# Install base dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY ./pyproject.toml ./uv.lock $APP_HOME

COPY ./src $APP_HOME/src

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Run app - exec form (doesn’t start a shell on its own)
CMD ["/usr/local/bin/python", "-m", "main.py"]

# ===== Dev stage =====
FROM prod AS dev

RUN uv sync --locked
