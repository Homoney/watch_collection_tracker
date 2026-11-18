# Watch Collection Tracker

Track a watch collection: specifications, photos, service history, market values, movement accuracy and side-by-side comparisons. Multi-user with an admin role.

**Image:** `dhomoney/watch-tracker` (linux/amd64, linux/arm64). One container serves the web app and the API, with all data in one `/data` volume (SQLite).

## Run

```sh
docker run -d --name watch-tracker --restart unless-stopped \
  -p 8080:8000 -v watch-data:/data \
  -e INITIAL_ADMIN_EMAIL=you@example.com \
  dhomoney/watch-tracker:latest
```

Then create your admin account:

1. Open http://localhost:8080. On a fresh install the sign-in page says **Create the admin account**; click it.
2. Enter the `INITIAL_ADMIN_EMAIL` address and choose a password. No password is set in advance: the one you choose here is the admin password.
3. Click **Create admin account**. You are signed in as the admin.

Public sign-up is off unless `ALLOW_REGISTRATION=true`.

Prefer Compose? Use the `docker-compose.yml` and `.env.example` (saved as `.env`) from the repository or a release, set `INITIAL_ADMIN_EMAIL` in `.env`, run `docker compose up -d`, then do the same three steps. After changing `.env`, run `docker compose up -d --force-recreate`.

## Data

`/data` holds `watch.db`, `uploads/`, `backups/` and a generated `secret_key`. The app makes a daily backup into `/data/backups` (kept 30 days) and one before every migration. On demand:

```sh
docker exec watch-tracker python -m app.cli backup
```

The container runs as UID 1000. For a bind mount, `chown -R 1000` the host folder first. Keep `/data` on a local disk, not network storage.

## Main settings (all optional)

| Variable | Default | |
|---|---|---|
| `INITIAL_ADMIN_EMAIL` | (none) | First admin's email |
| `ALLOW_REGISTRATION` | `false` | Open sign-up |
| `SECRET_KEY` | generated | 32+ characters if set; never change it |
| `TRUSTED_PROXIES` | `127.0.0.1` | Your reverse proxy's address |
| `BACKUP_KEEP_DAYS` | `30` | Backup retention |
| `TZ` | `UTC` | Time zone |

HTTPS: put a reverse proxy (Caddy, Traefik, nginx) in front of port 8000.

## Upgrade

`docker pull dhomoney/watch-tracker:latest`, then recreate the container with the same command. Migrations run on start after an automatic backup.

## Previous images

`dhomoney/watch-tracker-backend` and `dhomoney/watch-tracker-frontend` (versions 1.x, PostgreSQL) are no longer updated.

Source and full documentation: https://github.com/Homoney/watch_collection_tracker
