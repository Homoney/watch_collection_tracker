# Changelog

Versions follow [Semantic Versioning](https://semver.org/). Patch releases (x.y.Z) are fixes and maintenance only.

## [2.1.3] - 2026-11-19

Fixes only. No upgrade steps.

### Fixed
- Pop-ups with a form (add and edit watch, collections, accuracy reading, password reset) no longer close on a click outside. Escape, X and Cancel ask "Discard changes?" when something was typed. The Add watch form keeps a draft in the browser through a reload or crash.

## [2.1.2] - 2026-11-19

Fixes and a lookup improvement. No upgrade steps.

### Added
- New outgoing host: `www.grand-seiko.com`. Grand Seiko watches missing from WatchBase (for example SBGE253) are now filled from grand-seiko.com, with the official photo offered as a private reference photo.
- Look up shows Caliber Corner movement facts when WatchBase does not have the watch.

### Fixed
- Look up finds references typed with spaces, dashes or a suffix.
- A "not found" result is no longer remembered for 24 hours.

## [2.1.1] - 2026-11-19

Fixes only. No upgrade steps.

### Fixed
- Phone layout: the Look up button stays on one line, the Primary and Reference photo badges no longer overlap, the photo caption is no longer cut off, and the watch page no longer scrolls sideways at phone width.

## [2.1.0] - 2026-11-19

Feature release. Database migration 0002 runs automatically on start (a backup is taken first). No other upgrade steps.

### Added
- Look up specs and a reference photo from the reference number: pick a match and the form fills in caliber, movement facts, crystal, case material and complications, and a reference photo is available to save.
- New watch fields: caliber, crystal and case material.
- WatchBase API key is optional. Set it on the Admin page or with `WATCHBASE_API_KEY`; without a key, Look up still works and returns links only.

### Removed
- The Google image fetch (scraper) is removed; reference photos now come from WatchBase (closes #205).

## [2.0.4] - 2026-11-18

Fixes and maintenance only. No upgrade steps.

### Fixed
- Dark mode readability: text, chart labels, disabled buttons and placeholders are now readable (#210).
- Fetch images shows a message instead of an error when the search finds nothing (part of #205).

## [2.0.3] - 2026-11-18

Fixes and maintenance only. No upgrade steps.

### Fixed
- First sign-up on a fresh install is now clear: the login page leads to "Create the admin account" when `INITIAL_ADMIN_EMAIL` is set, and a wrong email gets a hint instead of a bare error. Without `INITIAL_ADMIN_EMAIL` the page no longer promises an admin account.
- Docs (README, Docker Hub page, deployment and user guides) now list the first-admin step in every install path.

### Added
- Public `GET /api/v1/auth/setup-status` endpoint (`setup_required`, `admin_signup`; never returns the admin address).

## [2.0.2] - 2026-11-18

Fixes and maintenance only. No upgrade steps.

### Fixed
- Fixes #201 and #202.

### Added
- LICENSE and SECURITY.md. Private vulnerability reporting is turned on for the repository.

### Removed
- `github-sync.sh` and `mcp.json` (unused housekeeping files).

## [2.0.1] - 2026-11-18

Fixes and maintenance only. No upgrade steps.

### Fixed
- Saved searches list no longer returns 404 (API paths work with or without a trailing slash).

### Changed
- Updated backend and frontend dependencies to current security releases.
- Slimmer runtime image with current security fixes.

## [2.0.0] - 2026-11-18

Single-image release: the whole app now ships as one container. **Breaking.** Read "Upgrade notes" before deploying.

### Upgrade notes (breaking changes)
- **New image: `dhomoney/watch-tracker`** (linux/amd64 and linux/arm64). It serves the web app and the API from one container on one port. The old `watch-tracker-backend` and `watch-tracker-frontend` images no longer update.
- **SQLite only.** PostgreSQL support and Redis are gone. **Data from a 1.x PostgreSQL install is not migrated.**
- **Port 8080:** the container listens on 8000 inside; publish it with `-p 8080:8000`.
- **Data lives in one volume mounted at `/data`** (`watch.db`, `uploads/`, `backups/`, and a generated `secret_key` if `SECRET_KEY` is not set). A bind-mounted host folder must be owned by UID 1000.
- **API docs moved from `/api/docs` to `/docs`.** The API info response moved from `GET /` to `GET /api` (`/` is now the web app).
- **Removed:** `nginx/`, `docker-compose.prod.yml`, `docker-compose.test.yml`, the `POSTGRES_*`, `REDIS_*` and `ALLOWED_ORIGINS` settings (old `.env` files are ignored, not rejected). The QR-code `base_url` must be this site.
- Install: `docker run -p 8080:8000 -v watch-data:/data -e INITIAL_ADMIN_EMAIL=you@example.com dhomoney/watch-tracker`.

### Added
- App-served signed, expiring upload links and in-app rate limits (same limits as the old nginx config; over the limit returns 429 with `Retry-After`).
- Container start-up: creates `/data` folders, generates and keeps a secret key, copies the database before a pending migration, then runs migrations.
- Daily online database backups (`BACKUP_INTERVAL_HOURS`, default 24; `python -m app.cli backup` on demand).
- Docker health check; `TRUSTED_PROXIES` for running behind a reverse proxy.

### Changed
- Search matches substrings (case-insensitive) instead of whole stemmed words.
- Single Alembic baseline migration.
- Security headers, gzip and the web app are served by the backend.

## [1.2.0] - 2026-11-18

Hardening release (sessions, uploads, configuration, deployment). Read "Upgrade notes" before deploying.

### Upgrade notes (behaviour changes)
- **Run database migrations** (`alembic upgrade head`; the backend container does this on start). Migration `005` adds session and login-guard columns.
- **`SECRET_KEY` must be at least 32 characters** and not the `.env.example` placeholder, or the backend will not start. Generate one with `openssl rand -hex 32`. Changing it signs everyone out.
- **Everyone signs in again once** after upgrading. The refresh token now lives in an `HttpOnly` cookie and the access token in memory only.
- **Logout ends the user's sessions on all devices.** Changing a password keeps the current browser signed in and ends other sessions.
- **Login lockout:** 5 wrong passwords lock the account for 15 minutes (`LOGIN_MAX_FAILURES`, `LOGIN_LOCKOUT_MINUTES`). An admin password reset clears the lock.
- **Behind a TLS proxy** that does not send `X-Forwarded-Proto`, set `COOKIE_SECURE=true`.
- **Uploads are validated:** files must be real images (JPEG/PNG/GIF/WebP) or PDFs; defaults of 50 images per watch and 20 documents per service record (`MAX_IMAGES_PER_WATCH`, `MAX_DOCUMENTS_PER_SERVICE`, `MAX_DOCUMENT_SIZE`).
- **Production compose requires `REDIS_PASSWORD`**; set it before `docker compose up`.
- **QR codes:** `base_url` must be this site or an entry in `ALLOWED_ORIGINS`.
- **Very common passwords are refused** on sign-up, change and reset.
- The reference-time endpoint now requires sign-in.
- HTTPS server block and HSTS are ready to enable in `nginx/nginx.conf` (opt-in); the production nginx config mount was corrected.

### Changed
- CORS is handled by the backend (`ALLOWED_ORIGINS`) only; nginx security headers apply to all locations.
- Rate limits added for password change, token refresh and uploads.
- Error responses no longer include internal error text; logging replaces `print()`.
- Search treats `%` and `_` literally.
- CI workflow permissions are least-privilege; the Trivy action is pinned.

## [1.1.0] - 2026-11-18

Upgrade and hardening release. Read "Upgrade notes" before deploying.

### Upgrade notes (behaviour changes)
- **Sign-up is closed by default.** Public registration is off unless `ALLOW_REGISTRATION=true`.
- **First admin is set explicitly.** Set `INITIAL_ADMIN_EMAIL` in `.env` (register with that email on an empty database), or create accounts from the command line: `docker compose exec backend python -m app.cli create-user EMAIL --admin`.
- **Old `/uploads/...` links stop working.** Images and documents are now served through signed, expiring file URLs; bookmarked or shared direct links must be re-generated by opening the item in the app.
- Review `.env.example` for new settings before upgrading.

### Changed
- Upgraded FastAPI to 0.164.0 and Starlette to 1.10.0; cleared the deprecations the upgrade surfaced.
- Tightened how remote images are fetched.
- CI: the release job now has the permissions it needs to create the GitHub release (v1.0.1's release step failed without them); other jobs are read-only.

## [1.0.1] - 2026-11-18

Maintenance release: CI, dependency and container fixes since 1.0.0. No feature changes.

### Security
- Containers (backend, frontend, nginx) now run as a non-root user.
- Updated vulnerable dependencies: FastAPI, Pillow, python-multipart, python-dotenv, and frontend packages via `npm audit` fixes; backend dependencies are pinned to exact versions.
- Replaced `python-jose` with `PyJWT` for token handling (removes the ecdsa, cryptography and pyasn1 transitive dependencies).

### Fixed
- CI pipeline: backend tests, linting (flake8, black, isort, ESLint), TypeScript compilation, integration tests under Docker Compose V2, and CodeQL action upgraded to v4.
- Tests expect `401` for unauthenticated requests.
- Duplicate database indexes; `package-lock.json` added.
- Frontend image builds on `node:20-slim` with `npm ci`.

### Changed
- Backend test coverage raised to 83.5%.

## [1.0.0] - 2026-01-29

Initial release: collections, watches, images, service history, market values and analytics, comparison, user management, movement accuracy tracking.
