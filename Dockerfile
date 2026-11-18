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
    UPLOAD_DIR=/data/uploads \
    BACKUP_DIR=/data/backups \
    WEB_DIR=/app/web

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=web /web/dist /app/web

RUN useradd --uid 1000 --user-group --no-create-home app \
    && mkdir -p /data/uploads /data/backups \
    && chown -R app:app /data
USER app

EXPOSE 8000
# X-Forwarded-For/-Proto are trusted only from TRUSTED_PROXIES
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"${TRUSTED_PROXIES:-127.0.0.1}\""]
