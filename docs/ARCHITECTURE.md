# Watch Collection Tracker - Architecture

How the application is built and how the parts fit together. For installing
and running it, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Layout](#backend-layout)
4. [Database Design](#database-design)
5. [API Architecture](#api-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [File Storage](#file-storage)
8. [Security Architecture](#security-architecture)
9. [Performance](#performance)
10. [Scaling Limits](#scaling-limits)
11. [Monitoring](#monitoring)
12. [Build and Deployment](#build-and-deployment)

---

## System Overview

Since 2.0 the whole application is **one Docker image** running **one
process**: FastAPI under Uvicorn. That process serves the REST API, the built
React web app and the uploaded files. All state lives in **one volume,
`/data`**: a SQLite database, the uploads, the backups and the signing key.

```
┌─────────────┐
│   Browser   │  React single-page app
└──────┬──────┘
       │ HTTP (HTTPS via your own reverse proxy)
       ↓ host port 8080 → container port 8000
┌──────────────────────────────────────────────┐
│  watch-tracker container (user 1000)         │
│                                              │
│  Uvicorn → FastAPI                           │
│   ├─ middleware: gzip, security headers,     │
│   │   rate limits, cache headers             │
│   ├─ /api/v1/...   REST API                  │
│   ├─ /uploads/...  files, signed links only  │
│   ├─ /docs /redoc  API documentation         │
│   ├─ /health       health check              │
│   └─ everything else → web app (dist/)       │
│                                              │
│  /data (volume)                              │
│   ├─ watch.db     SQLite database            │
│   ├─ uploads/     images, service documents  │
│   ├─ backups/     database copies            │
│   └─ secret_key   generated signing key      │
└──────────────────────────────────────────────┘
```

There is no separate database server, cache or web server. Versions 1.x used
PostgreSQL, Redis and nginx; 2.0 removed them (see
[DEPLOYMENT.md](DEPLOYMENT.md#9-upgrading-from-1x-postgresql)).

### Request Flow

1. The browser sends a request to the container.
2. Middleware runs in this order: gzip, security headers, rate limits, cache headers.
3. FastAPI routes the request:
   - `/api/v1/...`: checks the JWT access token, validates input with
     Pydantic, reads and writes SQLite through SQLAlchemy, returns JSON.
   - `/uploads/...`: checks the link's signature and expiry, then sends the file.
   - `/assets/...`: content-hashed web app files, cached for a year.
   - any other path: a file from the web app build, or `index.html` so the
     React router can handle the address.
4. React renders the page with the data.

### Start-up

`python -m app.entrypoint` is the container's command. It:

1. checks that `/data` is writable and creates its folders,
2. reads `SECRET_KEY`, or generates `/data/secret_key` on first start,
3. backs up the database, then runs Alembic migrations,
4. replaces itself with Uvicorn (one process; proxy headers trusted only from
   `TRUSTED_PROXIES`).

A background task in the app takes the daily backup.

---

## Technology Stack

Exact versions are pinned in `backend/requirements.txt` (runtime),
`backend/requirements-dev.txt` (tests) and
`frontend/package-lock.json`.

### Backend

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Starlette) |
| Language | Python 3.11 |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2 |
| Database | SQLite (file in `/data`) |
| Migrations | Alembic (batch mode, so `ALTER TABLE` works on SQLite) |
| Validation | Pydantic 2 |
| Authentication | PyJWT (HS256), bcrypt |
| Images | Pillow |
| HTML parsing | BeautifulSoup4 (image search) |
| HTTP client | httpx |

### Frontend

| Component | Technology |
|-----------|-----------|
| Framework | React 18, TypeScript |
| Build tool | Vite |
| Routing | React Router 7 |
| Server state | TanStack Query |
| Forms | React Hook Form |
| HTTP client | Axios |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Charts | Recharts |
| Dates | date-fns |

### Packaging

| Component | Technology |
|-----------|-----------|
| Image | multi-stage `Dockerfile` at the repository root: Node builds the web app, a slim Python image runs it |
| Platforms | linux/amd64, linux/arm64 |
| Compose | `docker-compose.yml`: one service, one volume |
| CI | GitHub Actions (`.github/workflows/ci.yml`), including a smoke test that starts the built image |

---

## Backend Layout

```
backend/app/
├── main.py            # FastAPI app, middleware, routers, health check
├── entrypoint.py      # container start-up (data dir, secret, migrate, uvicorn)
├── web.py             # serves the built web app
├── backup.py          # SQLite backups and retention
├── cli.py             # create-user, backup
├── config.py          # settings from environment variables
├── database.py        # SQLAlchemy engine and sessions (SQLite)
├── db_types.py        # portable column types (UUID, JSON)
├── api/v1/            # API routes, plus uploads.py for /uploads/
├── core/              # security (JWT, bcrypt), deps, passwords, signed file URLs
├── middleware/        # cache headers, rate limits, security headers
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
├── services/          # business logic shared by routes
└── utils/             # file upload, image search, PDF export, QR codes, logging
```

**Patterns**: FastAPI dependency injection (`Depends`) for the database
session and the current user; Pydantic schemas at the API boundary; ownership
checks on every watch-scoped route.

---

## Database Design

SQLite, in `/data/watch.db`. The schema is created by one baseline migration,
`backend/alembic/versions/0001_baseline.py`; later changes are new Alembic
revisions. Foreign keys are switched on for every connection.

### Entity Relationship Diagram

```
┌─────────┐
│  Users  │
└────┬────┘
     │
     │ 1:N
     ↓
┌────────────┐
│ Collections│
└─────┬──────┘
      │ 1:N
      ↓
┌───────────────┐       ┌─────────┐
│    Watches    │──N:1──│ Brands  │
└───┬───┬───┬───┘       └─────────┘
    │   │   │
    │   │   └──N:1──┌────────────────┐
    │   │           │ MovementTypes  │
    │   │           └────────────────┘
    │   │
    │   └──N:N──┌───────────────┐
    │           │ Complications │
    │           └───────────────┘
    │
    ├──1:N──┌─────────────┐
    │       │ WatchImages │
    │       └─────────────┘
    │
    ├──1:N──┌────────────────┐       ┌──────────────────┐
    │       │ ServiceHistory │──1:N──│ ServiceDocuments │
    │       └────────────────┘       └──────────────────┘
    │
    └──1:N──┌──────────────┐
            │ MarketValues │
            └──────────────┘
```

### Core Tables

**users**
- Primary identity table
- Email-based authentication
- Password hashed with bcrypt

**brands, movement_types, complications**
- Reference data tables
- Seeded with common values
- Sortable for UI display

**collections**
- User-owned groups of watches
- Color-coded for visual identification
- Soft relationship (watches not deleted with collection)

**watches**
- Main entity with detailed specifications
- Foreign keys to brands, movement types, collections
- Stores current market value (denormalized for performance)
- Many-to-many with complications via association table

**watch_images**
- Stores image metadata
- Primary image designation
- Sort order for gallery display
- Source tracking (user upload, URL import, WatchBase reference photo with its source page)

**service_history**
- Maintenance records
- Cost tracking with currency
- Next service due date for reminders
- One-to-many with service documents

**service_documents**
- Attachments for service records
- PDF, JPG, PNG support
- Secure file paths

**market_values**
- Historical valuation records
- Multiple currency support
- Source tracking (manual, Chrono24, API)
- Used for analytics and ROI calculations

### Indexes

The baseline creates indexes on every foreign key and on the common filter
and sort fields, for example:

```sql
CREATE INDEX ix_watches_user_id ON watches(user_id);
CREATE INDEX ix_watches_brand_id ON watches(brand_id);
CREATE INDEX ix_watches_collection_id ON watches(collection_id);
CREATE INDEX ix_watches_purchase_date ON watches(purchase_date);
CREATE INDEX ix_service_history_watch_id ON service_history(watch_id);
CREATE INDEX ix_market_values_watch_id ON market_values(watch_id);
CREATE INDEX ix_market_values_recorded_at ON market_values(recorded_at);
CREATE INDEX ix_watch_images_watch_id ON watch_images(watch_id);
```

### Search

Watch search is a case-insensitive substring match (`LIKE`) on the model
name, brand name and reference number. 1.x used PostgreSQL full-text search;
for one person's collection a substring match is fast enough and finds
partial words.

---

## API Architecture

### RESTful Design

**Resource Naming**:
- Plural nouns for collections: `/watches`, `/collections`
- Nested resources: `/watches/{id}/images`
- No verbs in URLs (use HTTP methods)

**HTTP Methods**:
- `GET` - Retrieve resources
- `POST` - Create resources
- `PUT` - Full update
- `PATCH` - Partial update
- `DELETE` - Remove resources

**Status Codes**:
- `200 OK` - Success with response body
- `201 Created` - Resource created
- `204 No Content` - Success without response body
- `400 Bad Request` - Client error
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Authentication Flow

```
┌────────┐                          ┌────────┐
│ Client │                          │  API   │
└───┬────┘                          └───┬────┘
    │  POST /api/v1/auth/login          │
    ├──────────────────────────────────>│
    │  200: access_token (JSON)         │
    │       refresh token (HttpOnly     │
    │       cookie)                     │
    │<──────────────────────────────────┤
    │                                   │
    │  GET /api/v1/watches/             │
    │  Authorization: Bearer <access>   │
    ├──────────────────────────────────>│
    │  200 OK                           │
    │<──────────────────────────────────┤
    │                                   │
    │  (access token expires)           │
    │  POST /api/v1/auth/refresh        │
    │  (cookie sent by the browser)     │
    ├──────────────────────────────────>│
    │  200: new access_token            │
    │<──────────────────────────────────┤
```

- Access token: 30 minutes, kept only in the web app's memory.
- Refresh token: 7 days, in an HttpOnly cookie that page scripts cannot read.
- Every token carries the user's token version. Logging out or changing the
  password raises it, which ends all of that user's sessions.

### Data Validation

**Pydantic Schemas**:
```python
class WatchCreate(BaseModel):
    model: str = Field(..., min_length=1, max_length=200)
    brand_id: UUID
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    # ... other fields with validation
```

**Benefits**:
- Automatic validation
- Type safety
- OpenAPI schema generation
- Clear error messages

---

## Frontend Architecture

### State Management

**Server state** (TanStack Query): API data caching, refetching, optimistic
updates, loading and error states.

```typescript
const { data: watches, isLoading } = useQuery({
  queryKey: ['watches', filters],
  queryFn: () => fetchWatches(filters),
});
```

**Context**: authentication (`AuthContext`) and the comparison selection
(`ComparisonContext`).

**Tokens**: `src/lib/tokenStore.ts` keeps the access token in memory. On a
reload the app gets a new one with the refresh cookie.

### Component Architecture

**Atomic Design**:
```
components/
├── common/           # Atoms (Button, Input, Card)
├── watches/          # Molecules (WatchCard, WatchForm)
├── layout/           # Organisms (Navbar, Sidebar)
└── pages/            # Templates (WatchListPage)
```

**Key Principles**:
- Single Responsibility
- Props for configuration
- Composition over inheritance
- Memoization for performance

### Routing

**React Router v6**:
```typescript
<Routes>
  <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
  <Route path="/watches" element={<ProtectedRoute><WatchListPage /></ProtectedRoute>} />
  <Route path="/watches/:id" element={<ProtectedRoute><WatchDetailPage /></ProtectedRoute>} />
</Routes>
```

**Features**:
- Protected routes with authentication check
- Lazy loading for code splitting
- URL-based state (filters, search)

---

## File Storage

### Directory Structure

```
/data/
├── watch.db
├── secret_key
├── backups/
│   └── watch-<timestamp>.db
└── uploads/
    ├── {watch_id}/
    │   ├── <uuid>.jpg
    │   └── <uuid>.png
    └── service-docs/
        └── {watch_id}/
            └── {service_id}/
                ├── <uuid>.pdf
                └── <uuid>.jpg
```

### Upload Flow

```
Client                Backend              FileSystem
  │                      │                     │
  │  POST /images        │                     │
  │  (multipart/form)    │                     │
  ├──────────────────────>│                     │
  │                      │                     │
  │                      │  Validate file      │
  │                      │  (type, size)       │
  │                      │                     │
  │                      │  Generate UUID      │
  │                      │  Sanitize filename  │
  │                      │                     │
  │                      │  Write file         │
  │                      ├─────────────────────>│
  │                      │                     │
  │                      │  Extract metadata   │
  │                      │  (Pillow for dims)  │
  │                      │                     │
  │                      │  Save to database   │
  │                      │                     │
  │  201 Created         │                     │
  │  (image metadata)    │                     │
  │<──────────────────────┤                     │
```

### Serving Files

Browsers load images with plain `<img>` tags, which cannot send a Bearer
token. So the API returns **signed links**: `/uploads/<path>?expires=...&sig=...`.
The signature is an HMAC over the path and expiry, with a key derived from
`SECRET_KEY`. `GET /uploads/...` checks the signature and expiry, refuses any
path outside the uploads folder, and sends the file with `nosniff` and
`private` cache headers. Links last `UPLOAD_URL_TTL_SECONDS` (default one hour);
the expiry is rounded so a link stays the same for a while and browsers can
cache it.

### Upload Checks

- File type checked by content and by extension (images: JPG, PNG, GIF, WebP;
  documents: PDF, JPG, PNG)
- Size limits: images 20 MB, documents 10 MB (`MAX_UPLOAD_SIZE`, `MAX_DOCUMENT_SIZE`)
- Count limits: 50 photos per watch, 20 documents per service record
- Stored under a generated UUID name; the original name is only kept as data

---

## Security Architecture

**Network edge** (your reverse proxy, if you use one)
- HTTPS
- `TRUSTED_PROXIES` tells the app which proxy may set `X-Forwarded-For`

**Application**
- JWT authentication on every protected route; admin routes require the admin role
- Rate limits per client address, in the app (`middleware/rate_limit.py`):
  sign-in and sign-up 5 per minute, password change and refresh 10 per minute,
  uploads 10 per minute, other API calls 10 per second (each with a burst allowance)
- Account lockout after 5 wrong passwords for 15 minutes
  (`LOGIN_MAX_FAILURES`, `LOGIN_LOCKOUT_MINUTES`)
- Security headers on every response (`middleware/security_headers.py`):
  Content-Security-Policy, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy
- Input validation with Pydantic; SQL through the SQLAlchemy ORM; React escapes output
- Outgoing fetches (image search, image import) go through `utils/safe_fetch.py`,
  which refuses private and local addresses

**Data**
- Passwords hashed with bcrypt; minimum 8 characters; common passwords refused
- `SECRET_KEY` must be 32+ characters, or is generated (64 hex characters)
  into `/data/secret_key` with owner-only permissions
- Ownership checked on every watch, collection and file
- The container runs as an unprivileged user (UID 1000)

**Monitoring**
- Security events (sign-ins, failures, lockouts, admin actions) are logged

---

## Performance

- **SQL aggregation** for collection analytics instead of Python loops
- **Indexes** on foreign keys and filter fields (see above)
- **HTTP caching**: web app assets cached for a year (content-hashed names);
  `index.html` is `no-cache`; reference data `public, max-age=3600`; other API
  responses are not cached; uploads are `private, max-age=3600`
- **Gzip** for responses over 1 KB
- **Frontend**: route-level code splitting (`React.lazy`), `React.memo`,
  lazy-loaded images, vendor chunks

---

## Scaling Limits

The 2.x design is for one household or one collector, on one machine.

- **One process per data volume.** Rate limit counters and login lockouts live
  in the process's memory, and SQLite allows one writer at a time. Do not run
  two containers on the same `/data`.
- SQLite handles thousands of watches and many reads per second without
  trouble. Writes are short and rare in this app.
- `/data` must be on a local disk; SQLite file locking is unreliable on
  network file systems.

If the app ever needs several servers, the database and the rate limit store
would have to move to shared services again.

---

## Monitoring

### Logging

**Structured Logging**:
```python
log_security_event(
    "login_success",
    user_id=user.id,
    email=user.email
)
```

**Log Levels**:
- ERROR: System errors
- WARNING: Potential issues
- INFO: Security events, significant actions
- DEBUG: Detailed diagnostics (development only)

### Health Check

`GET /health` returns `{"status": "healthy"}`. The image's Docker
`HEALTHCHECK` calls it every 30 seconds.

---

## Build and Deployment

- **Image**: `docker build -t watch-tracker .` from the repository root.
  Stage 1 runs `npm ci` and `npm run build`; stage 2 applies Debian
  security updates, installs the runtime Python requirements (not the test
  tools) and copies the backend and the built `dist/`.
- **CI** (`.github/workflows/ci.yml`): backend tests (pytest on SQLite),
  frontend tests and build, lint and format checks, a dependency audit, a
  security scan, and a smoke test that builds the image, starts it and waits
  for `/health`. These jobs are required checks for merging to `main`.
- **Security scanning** (`.github/workflows/security-scanning.yml`): Trivy
  (files, dependencies and the built image) and Gitleaks on pull requests,
  pushes to `main` and weekly; CodeQL runs through GitHub's default setup.
  Results go to the repository's Security tab and are triaged weekly.
- **Publishing** (`.github/workflows/docker-publish.yml`): on pushes to `main`
  and on `v*.*.*` tags, builds amd64 and arm64 and pushes `dhomoney/watch-tracker`
  (`latest` and `main` from `main`; `X.Y.Z`, `X.Y`, `X` from a tag). Tags follow
  the `x.y.z` versioning rule in the [README](../README.md#versioning-and-releases).
- **Running it**: see [DEPLOYMENT.md](DEPLOYMENT.md).

---

**Last Updated**: 2026-11-18
**Applies to**: 2.x (single image)
