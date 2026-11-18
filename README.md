# Watch Collection Tracker

A modern web application for watch collectors to track their collections with multi-user support, authentication, image management, service history, and market value tracking.

## Features

- **Multi-User Support**: Secure authentication with JWT tokens, isolated user data
- **User Management**: Role-based access control with admin panel for managing users
- **Watch Management**: Track brand, model, reference numbers, purchase info, specifications
- **Image Management**: Multiple images per watch with drag-and-drop upload, full-screen lightbox
- **Collections**: Organize watches into multiple collections (Current, Wishlist, Sold, etc.)
- **Search & Filter**: Filter by brand, collection, movement type, condition, price and value; save searches
- **Service History**: Track maintenance records, costs, schedule future services, attach documents
- **Market Value Tracking**: Historical value tracking, ROI calculations, appreciation/depreciation analytics
- **Performance Analytics**: Watch-level and collection-level analytics with trend indicators
- **Interactive Dashboards**: Recharts visualizations with line charts, bar charts, and pie charts
- **Collection Analytics**: Brand value breakdown, top/worst performers, distribution percentages
- **Movement Accuracy Tracking**: Track watch accuracy with atomic clock synchronization, drift calculations in seconds per day, analytics and visualizations
- **Multi-Currency Support**: USD, EUR, GBP, CHF, JPY, AUD, CAD
- **Document Management**: Upload service receipts, warranties, certificates (PDF, JPG, PNG)
- **Export & Backup**: PDF export of one watch or the whole collection, QR codes, automatic daily database backups
- **Dark Mode**: Full dark mode support with proper contrast ratios
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy, Alembic, SQLite, Pillow, JWT authentication
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, React Hook Form, Recharts, Lucide React
- **Packaging**: one Docker image (amd64 and arm64). The FastAPI app serves the API, the web app and uploaded files from a single process, and keeps everything in one `/data` volume.

## Install

The [deployment guide](docs/DEPLOYMENT.md) covers HTTPS, backups, upgrades and moving from 1.x in more detail.

You need Docker.

### With `docker run`

1. Start the container, with your own email address:

   ```sh
   docker run -d --name watch-tracker --restart unless-stopped \
     -p 8080:8000 -v watch-data:/data \
     -e INITIAL_ADMIN_EMAIL=you@example.com \
     dhomoney/watch-tracker:latest
   ```

2. Create your admin account:
   1. Open http://localhost:8080. On a fresh install the sign-in page says **Create the admin account**; click it.
   2. Enter the email address you set in `INITIAL_ADMIN_EMAIL` and choose a password. No password is set in advance: the one you choose here is the admin password.
   3. Click **Create admin account**. You are signed in, and this first account is the admin.

To change `INITIAL_ADMIN_EMAIL` later, remove the container (`docker rm -f watch-tracker`) and run the command again; your data stays in the `watch-data` volume.

Public sign-up is off: create other accounts with the command below, or set `ALLOW_REGISTRATION=true`. You can also create any account, the admin included, from the command line:

```sh
docker exec -it watch-tracker python -m app.cli create-user you@example.com --admin
```

### With Docker Compose

1. Download [`docker-compose.yml`](docker-compose.yml), and [`.env.example`](.env.example) saved as `.env` in the same folder.
2. In `.env`, set your email address: `INITIAL_ADMIN_EMAIL=you@example.com`.
3. Start it:

   ```sh
   docker compose up -d
   ```

4. Create your admin account:
   1. Open http://localhost:8080. On a fresh install the sign-in page says **Create the admin account**; click it.
   2. Enter the email address you set in `INITIAL_ADMIN_EMAIL` and choose a password. No password is set in advance: the one you choose here is the admin password.
   3. Click **Create admin account**. You are signed in, and this first account is the admin.

Changed `.env` after the container started (for example `INITIAL_ADMIN_EMAIL` was empty the first time)? Run `docker compose up -d --force-recreate` so the container picks up the new values.

### What is in `/data`

| Path | Contents |
|---|---|
| `watch.db` | the SQLite database |
| `uploads/` | watch images and service documents |
| `backups/` | daily database backups |
| `secret_key` | the signing key, generated on first start (if `SECRET_KEY` is not set) |

Copying this folder while the container is stopped is a full backup. Keep `/data` on a local disk; SQLite should not live on network storage (NFS or SMB).

The container runs as user ID 1000. A named volume (as above) works without changes. For a bind mount (`-v /srv/watch:/data`), run `chown -R 1000 /srv/watch` first, or start the container with `--user` set to your own user ID.

### Settings

All settings are optional environment variables.

| Variable | Default | What it does |
|---|---|---|
| `INITIAL_ADMIN_EMAIL` | (none) | Signing up with this email on an empty database creates the admin; you choose the password when you sign up |
| `ALLOW_REGISTRATION` | `false` | Let anyone with the address create an account |
| `SECRET_KEY` | generated | Signs logins and file links. If you set it: 32+ random characters, never change it |
| `TRUSTED_PROXIES` | `127.0.0.1` | Address of your reverse proxy, so rate limits see real client addresses |
| `BACKUP_KEEP_DAYS` | `30` | Days to keep the daily backups |
| `BACKUP_INTERVAL_HOURS` | `24` | Hours between automatic backups (`0` turns them off) |
| `UPLOAD_URL_TTL_SECONDS` | `3600` | Lifetime of the signed links to uploaded files |
| `MAX_UPLOAD_SIZE` | `20971520` | Largest image upload in bytes (20 MB) |
| `MAX_DOCUMENT_SIZE` | `10485760` | Largest service document in bytes (10 MB) |
| `LOGIN_MAX_FAILURES` / `LOGIN_LOCKOUT_MINUTES` | `5` / `15` | Lock an account after repeated wrong passwords |
| `COOKIE_SECURE` | auto | Force the `Secure` flag on the login cookie |
| `RATE_LIMIT_ENABLED` | `true` | Per-address request limits (keep on unless your proxy does this) |
| `DATA_DIR` | `/data` | Folder for the database, uploads, backups and the generated key |
| `TZ` | `UTC` | Time zone for log times |
| `WATCHBASE_API_KEY` | (none) | Key for automatic reference look-up; an admin can also set it on the Admin page (see the [user guide](docs/USER_GUIDE.md#reference-look-up-key-watchbase)) |
| `SPEC_LOOKUP_CACHE_DAYS` | `90` | Days a reference look-up answer is reused |

With Compose, `.env` also sets `HTTP_PORT` (host port, default `8080`) and `VERSION` (image tag, default `latest`).

### Backups and restore

The app backs up the database once a day into `/data/backups` and deletes backups older than `BACKUP_KEEP_DAYS`. It also takes a backup before it runs a database migration. To back up now:

```sh
docker exec watch-tracker python -m app.cli backup
```

To restore: stop the container, copy a backup over `/data/watch.db`, then start the container again.

Uploaded files are not inside the database. Back up the whole `/data` folder to keep them.

### Upgrade

```sh
docker pull dhomoney/watch-tracker:latest
docker rm -f watch-tracker
# then the same docker run command as above
```

With Compose, run `docker compose pull && docker compose up -d`. Migrations run on start, after an automatic backup.

**Coming from 1.x (PostgreSQL)?** 2.x is a new install and does not migrate 1.x data. Read [Upgrading from 1.x](docs/DEPLOYMENT.md#9-upgrading-from-1x-postgresql) before you switch.

### HTTPS and reverse proxies

The container speaks plain HTTP on port 8000. For HTTPS, put a reverse proxy in front of it, for example Caddy, Traefik or nginx. Set `TRUSTED_PROXIES` to the proxy's address so that rate limits and the secure login cookie work correctly.

## Development

```sh
# Backend (http://localhost:8000)
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt   # app + test tools
export DATA_DIR=$PWD/../.data SECRET_KEY=$(openssl rand -hex 32)
python -m app.entrypoint     # creates .data, migrates, starts uvicorn

# Frontend (http://localhost:3000; /api and /uploads go to the backend)
cd frontend
npm install
npm run dev
```

Tests:

```sh
cd backend && pytest          # uses a temporary SQLite database
cd frontend && npm test
```

Build the image from a checkout with `docker build -t watch-tracker .`.

New migration: `cd backend && alembic revision --autogenerate -m "describe change"` (Alembic runs in batch mode, so `ALTER TABLE` works on SQLite).

## API Documentation

Once the application is running, visit http://localhost:8080/docs for interactive API documentation powered by Swagger UI (ReDoc at `/redoc`). [docs/API.md](docs/API.md) has examples, rate limits and the full endpoint list; the list below is the most used part.

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/setup-status` - `setup_required` is true until the first account exists
- `GET /api/v1/spec-lookup?reference=...` - Specs for a reference number (see API.md)
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/logout` - Logout

#### Reference Data
- `GET /api/v1/reference/brands` - List brands
- `GET /api/v1/reference/movement-types` - List movement types
- `GET /api/v1/reference/complications` - List complications

#### Collections
- `GET /api/v1/collections/` - List collections
- `POST /api/v1/collections/` - Create collection
- `GET /api/v1/collections/{id}` - Get collection details
- `PUT /api/v1/collections/{id}` - Update collection
- `DELETE /api/v1/collections/{id}` - Delete collection

#### Watches
- `GET /api/v1/watches/` - List watches with filters (paginated)
- `POST /api/v1/watches/` - Add new watch
- `GET /api/v1/watches/{id}` - Get watch details with images
- `PUT /api/v1/watches/{id}` - Update watch
- `DELETE /api/v1/watches/{id}` - Delete watch (cascades to images and service records)

#### Images
- `POST /api/v1/watches/{watch_id}/images` - Upload image
- `GET /api/v1/watches/{watch_id}/images` - List watch images
- `PATCH /api/v1/watches/{watch_id}/images/{image_id}` - Update metadata (set primary)
- `DELETE /api/v1/watches/{watch_id}/images/{image_id}` - Delete image

#### Service History
- `POST /api/v1/watches/{watch_id}/service-history` - Create service record
- `GET /api/v1/watches/{watch_id}/service-history` - List service records
- `GET /api/v1/watches/{watch_id}/service-history/{service_id}` - Get service record
- `PUT /api/v1/watches/{watch_id}/service-history/{service_id}` - Update service record
- `DELETE /api/v1/watches/{watch_id}/service-history/{service_id}` - Delete service record
- `POST /api/v1/watches/{watch_id}/service-history/{service_id}/documents` - Upload document
- `DELETE /api/v1/watches/{watch_id}/service-history/{service_id}/documents/{doc_id}` - Delete document

#### Market Values
- `POST /api/v1/watches/{watch_id}/market-values` - Create market value record
- `GET /api/v1/watches/{watch_id}/market-values` - List market values (sorted by date)
- `GET /api/v1/watches/{watch_id}/market-values/{value_id}` - Get market value
- `PUT /api/v1/watches/{watch_id}/market-values/{value_id}` - Update market value
- `DELETE /api/v1/watches/{watch_id}/market-values/{value_id}` - Delete market value
- `GET /api/v1/watches/{watch_id}/analytics` - Get watch performance analytics (ROI, returns, value changes)
- `GET /api/v1/collection-analytics` - Get collection-wide analytics (total value, brand breakdown, top performers)

#### User Management (Admin Only)
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{user_id}` - Get user details
- `PATCH /api/v1/users/{user_id}` - Update user role (promote/demote)
- `POST /api/v1/users/{user_id}/reset-password` - Reset user password
- `DELETE /api/v1/users/{user_id}` - Delete user account

## Database Schema

### Core Tables
- **users** - User accounts, preferences, and roles (admin/user)
- **collections** - User-defined watch collections
- **watches** - Watch details and specifications
- **watch_images** - Multiple images per watch
- **service_history** - Maintenance records
- **service_documents** - Service receipts and documents
- **market_values** - Historical market value tracking
- **movement_accuracy_readings** - Movement accuracy readings
- **saved_searches** - Saved watch list filters

### Reference Tables (Pre-seeded)
- **brands** - Watch brands (Rolex, Omega, Seiko, etc.)
- **movement_types** - Movement types (Automatic, Hand-wound, Quartz, etc.)
- **complications** - Watch complications (Chronograph, GMT, Date, etc.)

## Security

- **Passwords**: bcrypt; common passwords are refused; accounts lock after repeated failures
- **Sessions**: short-lived access tokens; the refresh token sits in an HttpOnly, SameSite=Strict cookie; logout and password changes end all sessions
- **Uploaded files**: served only through signed, expiring links; contents are checked to be real images or PDFs
- **Rate limits**: per-address limits on sign-in, account changes, uploads and the API
- **Headers**: Content Security Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **Input validation**: Pydantic schemas; SQLAlchemy ORM with bound parameters
- **Container**: runs as a non-root user

## Troubleshooting

- **Container exits at start with "is not writable"**: the `/data` bind mount belongs to another user. Run `chown -R 1000 <folder>`.
- **Logs**: `docker logs watch-tracker`
- **Health**: `curl http://localhost:8080/health`, or check `docker ps` (healthy/unhealthy)
- **Migration state**: `docker exec watch-tracker alembic current`
- **Locked out of the admin account**: `docker exec -it watch-tracker python -m app.cli create-user you@example.com --admin` promotes an existing account

## Versioning and releases

Versions follow [Semantic Versioning](https://semver.org/) as `x.y.z`: patch (`z`) for fixes, security and dependency updates; minor (`y`) for new features or changes in behaviour; major (`x`) for breaking changes. The version is set in `frontend/package.json` and `backend/app/main.py`, and each release has a git tag `vX.Y.Z`, a [CHANGELOG](CHANGELOG.md) entry and a GitHub release.

Every merge to `main` publishes `dhomoney/watch-tracker:latest` (and `:main`); a `vX.Y.Z` tag publishes `X.Y.Z`, `X.Y` and `X`. To stay on a release, pin a version tag (`VERSION` in `.env` for Compose). See [DOCKER_HUB_SETUP.md](DOCKER_HUB_SETUP.md) for the publishing workflow.

## Security scanning

Every pull request and push to `main`, and a weekly scheduled run, scan the code, dependencies and the built image (Trivy, Gitleaks, plus CodeQL and Dependabot alerts). Results go to the repository's Security tab and are triaged weekly. Found a security problem? Please report it privately through the repository's Security tab (**Report a vulnerability**), not in a public issue. See [SECURITY.md](SECURITY.md) for supported versions and what to expect.

## Development History

The phases below record how the app was built. Phases 1 to 10 ran on the 1.x stack (separate backend and frontend images, PostgreSQL, Redis and nginx); version 2.0 replaced that stack with the single image and SQLite described above. Numbers (tests, timings) are from that time.

### ✅ Phase 1: Foundation (COMPLETED)
- Docker Compose infrastructure
- PostgreSQL database with migrations
- FastAPI backend with authentication (JWT)
- React frontend with routing
- Nginx reverse proxy + static file serving
- User registration and login

### ✅ Phase 2: Core CRUD Operations (COMPLETED)
- Reference data (Brands, Movement Types, Complications)
- Collections CRUD with color coding
- Watches CRUD with full specifications
- Filtering, sorting, and pagination
- Watch cards UI with collections integration

### ✅ Phase 3: Image Upload and Management (COMPLETED)
- File upload utilities with validation
- Image CRUD API endpoints
- Image schemas with computed URLs
- Primary image management
- ImageUpload component with drag-and-drop
- ImageGallery component with grid layout
- ImageLightbox component for full-screen viewing
- Secure file storage and Nginx static serving

### ✅ Phase 4: Service History & Maintenance Tracking (COMPLETED)
- Service history schemas and API endpoints
- Service document upload/management (PDF, JPG, PNG)
- ServiceHistoryList component with timeline view
- ServiceHistoryForm component with date pickers
- ServiceDocuments component for document management
- Overdue service alerts
- Cascade delete: service → documents

### ✅ Phase 5: Market Value Tracking & Analytics (COMPLETED)
- Market value schemas and CRUD API endpoints
- Watch-level analytics endpoint (ROI, returns, value changes)
- Collection-level analytics endpoint with brand breakdown
- MarketValueHistory component with timeline view
- MarketValueForm component with date pickers
- WatchAnalytics component with performance metrics
- ValueChart component with Recharts LineChart (historical trends)
- CollectionAnalytics component with comprehensive dashboard
  - Total collection value and watch count cards
  - Average ROI with color-coded trend indicators
  - Top/worst performer identification
  - Bar chart for value distribution by brand
  - Pie chart for collection distribution percentages
  - Brand performance table with detailed metrics
- AnalyticsPage with dedicated dashboard view
  - Currency selector for multi-currency support
  - Integrated navigation menu access
- Historical value tracking over time
- ROI and annualized return calculations
- 30-day, 90-day, 1-year value change tracking
- Smart current value management (date-aware updates)
- Multi-currency support (USD, EUR, GBP, CHF, JPY, AUD, CAD)

### ✅ Phase 6: Watch Comparison Views (COMPLETED)
- ComparisonContext for global selection state management
- Compare mode toggle with checkbox overlays
- ComparisonBar component for floating action bar
- ComparisonTable component for side-by-side comparison
- useCompareWatches hook for parallel watch fetching
- URL-based comparison state (/compare?ids=...)
- 8 comparison sections with 30+ attributes
- Responsive design with dark mode support

### ✅ Phase 7: Production Ready (COMPLETED)
**Sprint 1: Testing Infrastructure + Critical Security**
- Backend testing framework with pytest (55+ test cases)
- Frontend testing framework with Vitest
- Updated critical dependencies (axios 1.7.7, bcrypt 4.1.2)
- Security headers (CSP, Permissions Policy)
- Database connection pooling
- Security event logging
- Docker test environment

**Sprint 2: Performance Optimization + Security Hardening**
- Database query optimization (10-50x faster)
- 12 performance indexes
- PostgreSQL full-text search (10-100x faster)
- Frontend code splitting (40-60% smaller bundle)
- React.memo and useCallback optimizations
- Image lazy loading
- Bundle size optimization
- HTTP caching middleware

**Sprint 3: Documentation + Deployment Preparation**
- Comprehensive API documentation (8,500+ words, 50+ endpoints)
- User guide with tutorials (6,000+ words)
- Architecture documentation (5,500+ words)
- CI/CD pipeline with 8 automated jobs
- Production Docker Compose configuration
- Environment templates
- Health checks, resource limits, automated backups

**Performance Improvements**:
- Collection analytics: 1-2s → <150ms (10-13x faster)
- Search: 300ms → <50ms (6x faster)
- Initial load: ~3s → <1.5s (50% faster)
- Bundle size: 240KB → <200KB (17% smaller)

**Production Ready**: ✅ Application is ready for deployment with comprehensive testing, security hardening, performance optimization, and documentation.

### ✅ Phase 8: User Management & UI Fixes (COMPLETED)
**User Management**:
- Role-based access control (admin/user roles)
- The first admin is set up with `INITIAL_ADMIN_EMAIL` (register with that email on an empty database) or `docker exec -it watch-tracker python -m app.cli create-user EMAIL --admin`; public registration is off unless `ALLOW_REGISTRATION=true`
- Admin panel at `/admin` for user management
- Promote/demote users between admin and regular user roles
- Reset user passwords (admin only)
- Delete user accounts with confirmation (admin only)
- Self-protection: admins cannot demote or delete themselves
- Security event logging for all admin operations
- Admin-only API endpoints with 403 Forbidden protection
- Role badges in user list (visual distinction)
- Admin link in navigation bar (visible only to admins)

**UI Fixes**:
- Fixed dark mode text readability in input fields and select boxes
- Fixed dark mode text readability in watch detail page sections
- Proper contrast colors for both light and dark modes
- All text now meets WCAG accessibility standards

### ✅ Phase 9: Movement Accuracy Tracking (COMPLETED)
- Atomic clock synchronization with WorldTimeAPI integration
- Second mark recording (0, 15, 30, 45) to eliminate human error
- Drift calculation in seconds per day (positive = fast, negative = slow)
- Initial and subsequent reading types for baseline tracking
- Automatic reading pairing with validation (6 hours minimum, 90 days maximum)
- Analytics: current drift, average drift, best/worst accuracy, time-based trends
- Recharts visualization with drift over time
- Timeline view of all readings with drift calculations
- Notes field for context (position, temperature, etc.)
- Full dark mode support

### ✅ Phase 10: Comprehensive Test Coverage (COMPLETED)
**Test Infrastructure**:
- 233 comprehensive backend tests (up from 55)
- Coverage increased from 54.39% to 83.50% (target: 80%)
- 178 new test cases across 8 new test files
- 100% coverage on critical APIs (Images, Service History, Market Values, Saved Searches, Users)

**Test Files Created**:
- test_images.py (23 tests) → Images API: 98% coverage
- test_service_history.py (28 tests) → Service History API: 100% coverage
- test_market_values.py (32 tests) → Market Values API: 98% coverage
- test_movement_accuracy.py (28 tests) → Movement Accuracy API: 90% coverage
- test_saved_searches.py (17 tests) → Saved Searches API: 100% coverage
- test_users.py (15 tests) → Users API: 100% coverage
- test_qr_code.py (14 tests) → QR Code Utils: 100% coverage
- test_pdf_export.py (22 tests) → PDF Export Utils: 86% coverage

**Quality Improvements**:
- All 233 tests passing
- Comprehensive CRUD operation testing
- Security and authorization testing
- Edge case and validation testing
- Database constraint verification
- File upload and image processing testing
- Multi-currency and calculation testing

### 🎯 Post-Production Enhancements
- Email notifications and price alerts
- Mobile app development
- Chrono24 API integration
- Public collection sharing
- Multi-language support
- Advanced analytics with ML price predictions

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

MIT License, see [LICENSE](LICENSE). Feel free to use this for your own watch collection tracking needs.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with FastAPI and React
- Inspired by the watch collecting community
- Database schema based on common watch specification standards
