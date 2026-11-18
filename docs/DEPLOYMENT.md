# Deployment Guide

Watch Collection Tracker 2.x ships as **one Docker image**, `dhomoney/watch-tracker`.
One container runs the API, the web app and the uploaded files. Everything it
keeps is in **one volume, `/data`**. There is no separate database server,
cache or web server to run.

```
Browser ──HTTP──▶ host port 8080 ──▶ container port 8000 (FastAPI + Uvicorn)
                                         │
                                         └── /data  (SQLite database, uploads, backups, secret key)
```

The [README](../README.md#install) has the short version. This guide adds the
details: HTTPS, backups, upgrades, and moving from 1.x.

---

## 1. Requirements

- Docker (any host that runs Linux containers; the image is built for amd64 and arm64)
- A local disk for `/data`. SQLite must not live on network storage (NFS or SMB).
- Disk space for your photos, documents and backups

## 2. First start

### docker run

```sh
docker run -d --name watch-tracker --restart unless-stopped \
  -p 8080:8000 -v watch-data:/data \
  -e INITIAL_ADMIN_EMAIL=you@example.com \
  dhomoney/watch-tracker:latest
```

### Docker Compose

Use [`docker-compose.yml`](../docker-compose.yml) from the repository, and
[`.env.example`](../.env.example) copied to `.env` next to it. Set
`INITIAL_ADMIN_EMAIL=you@example.com` in `.env`, then:

```sh
docker compose up -d
```

`HTTP_PORT` in `.env` changes the host port (default `8080`). `VERSION` pins an
image tag instead of `latest`.

Compose reads `.env` only when it creates the container. After you change
`.env` (for example you set `INITIAL_ADMIN_EMAIL` after the first start), run
`docker compose up -d --force-recreate`. With `docker run`, remove the
container and run it again with the new `-e` values; data in the volume stays.

### Create your admin account

Do this right after the first start, with either install:

1. Open http://localhost:8080. While no account exists, the sign-in page says
   **Create the admin account**. Click it.
2. Enter the address you set in `INITIAL_ADMIN_EMAIL` and choose a password.
   No password is set in advance: the one you choose here is the admin
   password.
3. Click **Create admin account**. You are signed in as the admin.

Any other address is refused until the admin exists. Public sign-up stays off
unless you set `ALLOW_REGISTRATION=true`. The Admin
page manages existing accounts (roles, password resets, deletion) but does not
create them.

Create accounts from the command line, with `--admin` for an admin (this is
also the way to make the first admin without `INITIAL_ADMIN_EMAIL`). The
password is prompted for, or read from `WATCH_USER_PASSWORD`:

```sh
docker exec -it watch-tracker python -m app.cli create-user you@example.com --admin
```

### Check it is up

```sh
curl http://localhost:8080/health      # {"status":"healthy"}
docker logs watch-tracker
```

The image has a Docker health check on `/health`, so `docker ps` shows
`healthy` once the app is ready.

## 3. Ports and addresses

| Address | What it serves |
|---|---|
| `/` and any other path | the web app |
| `/api/v1/...` | the REST API |
| `/api` | API name and version |
| `/docs`, `/redoc` | interactive API documentation |
| `/uploads/...` | photos and documents, only through signed links that expire |
| `/health` | health check |

The container listens on port **8000**, plain HTTP. The examples publish it on
host port **8080**.

## 4. What is in `/data`

| Path | Contents |
|---|---|
| `watch.db` | the SQLite database |
| `uploads/` | watch images and service documents |
| `backups/` | database backups (daily, and before every migration) |
| `secret_key` | the signing key, generated on first start when `SECRET_KEY` is not set |

The container runs as user ID **1000**. A named volume works as is. For a bind
mount (`-v /srv/watch:/data`), run `chown -R 1000 /srv/watch` first, or start
the container with `--user` set to the owner of that folder. If the folder is
not writable the container stops at once with an "is not writable" message.

Keep `secret_key` (or your `SECRET_KEY`) with the data. If it changes, everyone
has to sign in again and old file links stop working.

## 5. Settings

All settings are optional environment variables. The full table is in the
[README](../README.md#settings). The ones most installs touch:

- `INITIAL_ADMIN_EMAIL`, `ALLOW_REGISTRATION`: who can create accounts
- `SECRET_KEY`: if you set it, 32 or more random characters (the app refuses
  to start with a shorter one), and never change it
- `TRUSTED_PROXIES`: the address of your reverse proxy (see below)
- `BACKUP_KEEP_DAYS`, `BACKUP_INTERVAL_HOURS`: backup retention and frequency
- `TZ`: time zone for log times

## 6. HTTPS with a reverse proxy

The container does not do TLS. Put a reverse proxy in front of it, for example
Caddy, Traefik or nginx, and set `TRUSTED_PROXIES` to the proxy's address.
Without that, every request seems to come from the proxy: rate limits then
apply to all users together, and the login cookie may not get its `Secure`
flag.

Caddy example (gets a certificate automatically):

```
watches.example.com {
    reverse_proxy watch-tracker:8000
}
```

When Caddy runs in the same Compose project, `TRUSTED_PROXIES` is the Docker
network range, for example `172.16.0.0/12`. When it runs on the host, publish
the container only on the loopback address (`-p 127.0.0.1:8080:8000`) and keep
the default `TRUSTED_PROXIES=127.0.0.1`.

Run **one** container per data volume. Rate limits are kept in the app's
memory, and SQLite expects a single writer.

## 7. Backups and restore

- The app copies the database to `/data/backups` once a day and deletes copies
  older than `BACKUP_KEEP_DAYS` (default 30).
- It also takes a copy before it runs a database migration.
- Back up now: `docker exec watch-tracker python -m app.cli backup`

The database backups do not contain the photos and documents. For a full
backup, copy the whole `/data` folder, ideally while the container is stopped:

```sh
docker stop watch-tracker
docker run --rm -v watch-data:/data -v "$PWD":/out alpine \
  tar czf /out/watch-data.tgz -C /data .
docker start watch-tracker
```

To restore the database: stop the container, copy a file from
`/data/backups/` over `/data/watch.db`, and start the container again.

## 8. Upgrading within 2.x

```sh
docker pull dhomoney/watch-tracker:latest
docker rm -f watch-tracker
# then the same docker run command as in section 2
```

With Compose: `docker compose pull && docker compose up -d`.

On start the container backs up the database, runs any new migrations, and
then starts the app. `docker exec watch-tracker alembic current` shows the
schema version.

## 9. Upgrading from 1.x (PostgreSQL)

**Your 1.x data is not migrated.** Version 2.0 is a new install:

| 1.x | 2.x |
|---|---|
| Several containers: PostgreSQL, Redis, backend, frontend, nginx | One container |
| Images `dhomoney/watch-tracker-backend` and `dhomoney/watch-tracker-frontend` | Image `dhomoney/watch-tracker` |
| PostgreSQL database | SQLite file `/data/watch.db` |
| Uploads in `./storage/uploads` on the host | Uploads in `/data/uploads` |

2.x does not read the PostgreSQL database or the old uploads folder, and there
is no conversion tool. Starting 2.x does not touch the 1.x containers or
volumes either. Before you switch:

1. Keep a copy of your 1.x data. With the 1.x stack still running, dump the
   database and copy the uploads folder, for example:
   ```sh
   docker compose exec -T postgres pg_dump -U <user> <database> > watch-1x.sql
   cp -r storage/uploads uploads-1x
   ```
   (Use the user and database names from your 1.x `.env`.)
2. Stop the 1.x stack (`docker compose down`, **without** `-v`, so its volumes stay).
3. Start 2.x as in section 2. It may use the same port, 8080.
4. Re-create your account and enter the collection again. The 1.x stack and
   your dump stay available as the reference, and you can start 1.x again to
   look something up.

Remove the old volumes only when you no longer need the 1.x data.
