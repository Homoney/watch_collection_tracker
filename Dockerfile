# One image: the web app is built with Node, then served by the FastAPI app.

# --- Stage 1: build the web app -------------------------------------------
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime ------------------------------------------------
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    WEB_DIR=/app/web

# Pick up Debian security fixes released since the base image was built;
# no new packages are added
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Runtime packages only (tests use requirements-dev.txt); setuptools from the
# base image is upgraded for its own security fixes. pip is removed once the
# packages are in: the app never runs it, and it carries its own old copy of
# setuptools code (pkg_resources) that a newer pip does not replace.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip

COPY backend/ ./
COPY --from=web /web/dist /app/web

RUN useradd --uid 1000 --user-group --no-create-home app \
    && mkdir -p /data/uploads /data/backups \
    && chown -R app:app /data
USER app

EXPOSE 8000
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

# Prepares /data, keeps a generated SECRET_KEY, backs up before migrating,
# runs migrations, then starts uvicorn (see backend/app/entrypoint.py)
CMD ["python", "-m", "app.entrypoint"]
