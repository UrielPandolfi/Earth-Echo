FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    libeccodes0 \
    libnetcdf19 \
    libhdf5-103-1 \
    libgdal32 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Earth_Echo_Catalogo.json Earth_Echo_Especificacion.md /app/
COPY data /app/data
COPY services/api /app/services/api

ENV EARTH_ECHO_ROOT=/app \
    EARTH_ECHO_REFRESH_ENABLED=0 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy

WORKDIR /app/services/api
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["sh", "-c", "uv run uvicorn earth_echo.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
