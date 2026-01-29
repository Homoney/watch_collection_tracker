# Claude Context - Watch Collection Tracker

**Last Updated**: 2026-01-29
**Current Phase**: Phase 9 Complete ✓ (Movement Accuracy Tracking)
**Latest Changes**: Comprehensive movement accuracy tracking with atomic clock synchronization, drift calculations, analytics, and visualizations.

---

## Project Overview

Full-stack watch collection management with multi-user support. FastAPI backend, React/TypeScript frontend.

**Tech Stack**:
- Backend: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pillow, Redis
- Frontend: React 18, TypeScript, TanStack Query, React Hook Form, Tailwind CSS, Recharts
- Infrastructure: Docker Compose, Nginx
- Icons: Lucide React

**Access**:
- Application: http://localhost:8080
- Backend API: http://localhost:8080/api
- Health Check: http://localhost:8080/health

---

## Completed Phases

### ✅ Phase 1: Foundation
Docker Compose, PostgreSQL, FastAPI auth (JWT), React frontend, Nginx reverse proxy

### ✅ Phase 2: Core CRUD
Reference data, Collections CRUD, Watches CRUD, filtering/sorting/pagination

### ✅ Phase 3: Image Upload
- File upload with drag-and-drop (JPG, PNG, GIF, WebP, 20MB max)
- Primary image management with auto-promotion
- Full-screen lightbox with keyboard navigation
- Secure storage: `/app/storage/uploads/{watch_id}/`
- Nginx serves from `/uploads/` with caching

### ✅ Phase 4: Service History
- Service records with date, provider, type, cost, next service due
- Document upload (PDF, JPG, PNG, 10MB max)
- Timeline view with overdue alerts
- Cascade delete service → documents
- Storage: `/app/storage/uploads/service-docs/{watch_id}/{service_id}/`

### ✅ Phase 5: Market Value & Analytics
- Historical market values with multiple sources (manual, chrono24, api)
- ROI, total return, annualized return calculations
- Value change tracking (30d, 90d, 1y)
- Smart current value tracking (only updates when newer)
- Watch-level and collection-level analytics
- ValueChart with Recharts LineChart
- CollectionAnalytics dashboard with bar/pie charts
- Brand breakdown and top/worst performers

### ✅ Phase 6: Watch Comparison
- Compare mode toggle in watch list
- Checkbox selection (2-4 watches)
- Floating comparison bar
- URL-based comparison state
- Side-by-side table with 8 sections, 30+ attributes
- Parallel fetching with React Query

### ✅ Phase 7: Production Ready
**Testing**: 55+ backend tests (pytest), frontend tests (Vitest), 48%+ coverage
**Security**: Updated dependencies, security headers (CSP, Permissions Policy), connection pooling, event logging, rate limiting
**Performance**:
- DB query optimization (10-50x faster)
- 12 performance indexes
- Full-text search with GIN indexes (10-100x faster)
- Code splitting (40-60% smaller bundles)
- Redis caching (95% hit rate on reference data)
- API p95 < 200ms
**Documentation**: 60+ pages (API.md, USER_GUIDE.md, ARCHITECTURE.md)
**CI/CD**: 8-job pipeline (tests, security scanning, builds, integration tests)
**Production**: docker-compose.prod.yml, health checks, resource limits, backups

### ✅ Phase 8: User Management & UI Fixes
**User Management**:
- Role-based access control (admin/user roles)
- First registered user automatically becomes admin
- Admin panel for user management
- Promote/demote users between roles
- Reset user passwords (admin only)
- Delete user accounts (admin only)
- Self-protection (admins can't demote/delete themselves)
- Security event logging for all admin actions
- Admin-only API endpoints with 403 Forbidden protection

**UI Fixes**:
- Fixed dark mode text readability in input fields and select boxes
- Fixed dark mode text readability in watch detail sections
- Proper contrast colors for light and dark modes

### ✅ Phase 9: Movement Accuracy Tracking
**Overview**: Track watch movement accuracy over time by comparing against atomic clock reference.

**Features**:
- Real-time atomic clock display (WorldTimeAPI integration with fallback)
- Second mark recording (0, 15, 30, 45) to eliminate human reaction time errors
- Drift calculation in seconds per day (positive = fast, negative = slow)
- Initial readings for baseline/reset points (after regulation, service, etc.)
- Subsequent readings to measure drift since last initial
- Automatic pairing of readings (finds most recent initial within 90 days)
- Validation: minimum 6 hours between initial and subsequent, maximum 90 days
- Analytics: current drift, average drift, best/worst accuracy, time-based trends (7d/30d/90d)
- Recharts visualization showing drift over time with reference line at zero
- Timeline view of all readings with drift calculations
- Notes field for context (position, temperature, etc.)
- Dark mode support with AppLayout integration

**Technical Details**:
- Backend: WorldTimeAPI for atomic time, graceful fallback to server time
- Database: movement_accuracy_readings table with 4 indexes
- API: 7 endpoints (atomic-time, CRUD operations, analytics)
- Frontend: 6 new components (AtomicClock, Form, List, Analytics, Chart, Page)
- React Query hooks with 1-second refresh for atomic time
- Drift calculation: `((watch_elapsed - reference_elapsed) / hours_elapsed) * 24`
- Color-coded accuracy indicators: green ≤5 spd, yellow ≤10 spd, red >10 spd

**Access**: Watch Detail Page → "Movement Accuracy" button

---

## Architecture

### Database Schema
- **Users**: Email/password auth, JWT tokens, role (admin/user)
- **Brands, MovementTypes, Complications**: Reference data
- **Collections**: User collections with color coding
- **Watches**: Specs, purchase info, current market value
- **WatchImages**: Images with primary designation
- **ServiceHistory**: Service records with dates/costs
- **ServiceDocument**: Receipts/certificates
- **MarketValue**: Historical values for appreciation tracking

### Key Directories
```
backend/app/
  ├── api/v1/          # auth, reference, collections, watches, images, service_history, market_values, users
  ├── core/            # security, deps (includes get_current_admin)
  ├── models/          # SQLAlchemy models
  ├── schemas/         # Pydantic schemas
  └── utils/           # file_upload

frontend/src/
  ├── components/
  │   ├── common/      # ImageLightbox
  │   ├── analytics/   # CollectionAnalytics
  │   └── watches/     # Image*, Service*, MarketValue*, WatchAnalytics, ValueChart, Comparison*
  ├── contexts/        # ComparisonContext
  ├── hooks/           # useWatches, useWatchImages, useServiceHistory, useMarketValues, useCompareWatches
  ├── pages/           # WatchDetailPage, AnalyticsPage, ComparePage, AdminPage
  └── lib/api.ts       # API client

storage/
  └── uploads/
      ├── {watch_id}/                    # Watch images
      └── service-docs/{watch_id}/{service_id}/  # Service documents
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register|login|refresh`
- `GET /api/v1/auth/me`

### Reference Data
- `GET /api/v1/reference/brands|movement-types|complications`

### Collections
- `GET|POST /api/v1/collections/`
- `GET|PUT|DELETE /api/v1/collections/{id}`

### Watches
- `GET|POST /api/v1/watches/`
- `GET|PUT|DELETE /api/v1/watches/{id}`

### Images
- `POST|GET /api/v1/watches/{watch_id}/images`
- `PATCH|DELETE /api/v1/watches/{watch_id}/images/{image_id}`
- URLs: `/uploads/{watch_id}/{filename}`

### Service History
- `POST|GET /api/v1/watches/{watch_id}/service-history`
- `GET|PUT|DELETE /api/v1/watches/{watch_id}/service-history/{service_id}`
- `POST|GET /api/v1/watches/{watch_id}/service-history/{service_id}/documents`
- `DELETE /api/v1/watches/{watch_id}/service-history/{service_id}/documents/{doc_id}`
- URLs: `/uploads/service-docs/{watch_id}/{service_id}/{filename}`

### Market Values
- `POST|GET /api/v1/watches/{watch_id}/market-values`
- `GET|PUT|DELETE /api/v1/watches/{watch_id}/market-values/{value_id}`
- `GET /api/v1/watches/{watch_id}/analytics` - Watch performance
- `GET /api/v1/collection-analytics` - Collection-wide analytics

### User Management (Admin Only)
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{user_id}` - Get user details
- `PATCH /api/v1/users/{user_id}` - Update user role
- `POST /api/v1/users/{user_id}/reset-password` - Reset user password
- `DELETE /api/v1/users/{user_id}` - Delete user

---

## Testing Credentials

**User**: `imagetest@example.com` / `testpass123`
**Test Watch ID**: `f98edb57-b35c-4b7e-846f-b04bd95ceb75`
- Model: "Test Model" (Rolex)
- Purchase: $5,000 → Current: $15,000 (200% ROI)
- 2 images, 2 service records, 4 market values

---

## Key Technical Details

### Image Upload
- Types: JPG, PNG, GIF, WebP (20MB max)
- Dimensions extracted via Pillow
- Primary image logic: first uploaded = primary, delete auto-promotes next
- Security: filename sanitization, ownership verification, isolated directories

### Service History
- Required: service_date, provider
- Optional: service_type, description, cost, next_service_due
- Documents: PDF, JPG, PNG (10MB max)
- Overdue alerts when next_service_due < today
- Cascade delete service → documents

### Market Value
- Fields: value, currency, source, notes, recorded_at
- Current value only updates if recorded_at >= last_value_update
- Update/delete triggers recalculation
- Analytics: ROI %, total return, annualized return, value changes (30d/90d/1y)
- Same-currency comparisons only (no auto exchange rates)

### Database Enum Fix
SQLAlchemy enum issue fixed with `values_callable`:
```python
source = Column(
    Enum(ImageSourceEnum, values_callable=lambda x: [e.value for e in x]),
    default=ImageSourceEnum.USER_UPLOAD,
    nullable=False
)
```

### Frontend State
- React Query for server state (caching, refetching, optimistic updates)
- Cache invalidation: upload/delete → invalidate images, watch detail, watch list
- ComparisonContext for global selection state (2-4 watches)

---

## Docker Commands

```bash
# Start/stop
docker-compose up -d
docker-compose down

# Rebuild
docker-compose build backend|frontend --no-cache
docker-compose up -d backend|frontend

# Logs
docker-compose logs -f backend|frontend|nginx

# Database
docker-compose exec postgres psql -U watchuser -d watch_tracker
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "description"

# Backend shell
docker-compose exec backend bash

# Health check
curl http://localhost:8080/health

# Fix 502 errors (when container IPs change)
docker-compose restart nginx
```

---

## Common Tasks

### View Files
```bash
ls -lh storage/uploads/{watch_id}/
ls -lh storage/uploads/service-docs/{watch_id}/{service_id}/
```

### Test API (curl)
```bash
TOKEN="your_jwt_token"
WATCH_ID="watch_uuid"

# Upload image
curl -X POST "http://localhost:8080/api/v1/watches/$WATCH_ID/images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"

# Create service record
curl -X POST "http://localhost:8080/api/v1/watches/$WATCH_ID/service-history" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"service_date":"2025-01-15","provider":"Rolex","cost":850,"cost_currency":"USD"}'

# Create market value
curl -X POST "http://localhost:8080/api/v1/watches/$WATCH_ID/market-values" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value":15000,"currency":"USD","source":"manual","recorded_at":"2026-01-28"}'

# Get analytics
curl -X GET "http://localhost:8080/api/v1/watches/$WATCH_ID/analytics" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Environment Variables

Required in `.env`:
```bash
# Database
POSTGRES_DB=watch_tracker
POSTGRES_USER=watchuser
POSTGRES_PASSWORD=your_password

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost

# Storage
MAX_UPLOAD_SIZE=20971520  # 20MB

# Frontend
VITE_API_URL=/api

# Server
HTTP_PORT=8080
```

---

## Troubleshooting

### Backend Won't Start
1. Check logs: `docker-compose logs backend`
2. Verify DB: `docker-compose ps`
3. Run migrations: `docker-compose exec backend alembic upgrade head`

### Frontend Build Errors
1. Rebuild: `docker-compose build --no-cache frontend`
2. Check package.json dependencies
3. Test build: `docker-compose exec frontend npm run build`

### 502 Bad Gateway
- Container IPs changed after restart
- Fix: `docker-compose restart nginx`

### Images Not Accessible
1. Verify file: `ls storage/uploads/{watch_id}/`
2. Check nginx config: `docker-compose exec nginx cat /etc/nginx/conf.d/default.conf`
3. Test URL: `curl http://localhost:8080/uploads/{watch_id}/{filename}`

### Database Migration Issues
1. Current revision: `docker-compose exec backend alembic current`
2. History: `docker-compose exec backend alembic history`
3. Downgrade: `docker-compose exec backend alembic downgrade -1`

### Token Expired
- Access tokens expire after 30 min
- Frontend auto-refreshes with refresh token (7 days)
- Re-login if refresh fails

---

## Security

### Implemented ✓
- JWT authentication on all protected routes
- Watch ownership verification
- File type/size validation (MIME + extension)
- Filename sanitization (directory traversal prevention)
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (React auto-escaping)
- CORS configured
- Password hashing (bcrypt)
- Security headers (CSP, Permissions Policy)
- Rate limiting (Nginx + per-user)
- Connection pooling with health checks
- Security event logging

**Security Score**: 8/10 (Production Ready)

### Future Considerations
- Rate limiting on upload endpoint
- File virus scanning
- HTTPS in production
- Image content verification

---

## Performance

### Current Metrics
- Collection analytics: 1-2s → <150ms (10-13x)
- Search: 300ms → <50ms (6x)
- Initial load: ~3s → <1.5s (50%)
- Bundle size: 240KB → <200KB (17%)
- Cache hit rate: ~95% (reference data)
- API p95: <200ms

### Optimizations Applied
- Database query optimization with SQL aggregation
- 12 performance indexes
- PostgreSQL full-text search with GIN indexes
- Frontend code splitting (React.lazy)
- React.memo and useCallback
- Image lazy loading
- Redis caching with graceful fallback
- HTTP caching middleware (Cache-Control headers)

---

## Next Steps (Post-Production)

### Short Term (1-3 Months)
- Deploy to production
- Configure SSL/monitoring
- Increase test coverage to 80%
- Email notifications
- Price alerts
- Data export (CSV/PDF)

### Medium Term (3-6 Months)
- Chrono24 API integration
- Public collection sharing
- QR code generation
- Exchange rate support
- Watchlist feature

### Long Term (6-12 Months)
- Multi-language support
- ML price predictions
- Marketplace integration
- Native mobile apps
- Advanced search with saved filters

---

## Important Code Locations

### Backend
- Main: `backend/app/main.py`
- Security: `backend/app/core/security.py`
- Models: `backend/app/models/`
- Schemas: `backend/app/schemas/`
- File upload: `backend/app/utils/file_upload.py`
- API routes: `backend/app/api/v1/`

### Frontend
- API client: `frontend/src/lib/api.ts`
- Types: `frontend/src/types/index.ts`
- Hooks: `frontend/src/hooks/`
- Components: `frontend/src/components/`
- Pages: `frontend/src/pages/`

### Infrastructure
- Docker: `docker-compose.yml`, `docker-compose.prod.yml`
- Nginx: `nginx/nginx.conf`
- Migrations: `backend/alembic/versions/`
- Tests: `backend/tests/`, `frontend/src/__tests__/`
- CI/CD: `.github/workflows/ci.yml`

---

## Quick Reference - TypeScript Interfaces

### WatchImage
```typescript
interface WatchImage {
  id: string
  watch_id: string
  file_path: string          // "watch_id/filename.jpg"
  file_name: string
  file_size: number          // bytes
  mime_type: string
  width: number | null
  height: number | null
  is_primary: boolean
  sort_order: number
  source: 'user_upload' | 'google_images' | 'url_import'
  created_at: string
  url: string                // "/uploads/watch_id/filename.jpg"
}
```

### ServiceHistory
```typescript
interface ServiceHistory {
  id: string
  watch_id: string
  service_date: string       // ISO datetime
  provider: string           // Required, max 200 chars
  service_type: string | null
  description: string | null
  cost: number | null        // >= 0
  cost_currency: string      // 3 chars, default "USD"
  next_service_due: string | null
  created_at: string
  updated_at: string
  documents: ServiceDocument[]
}

interface ServiceDocument {
  id: string
  service_history_id: string
  file_path: string
  file_name: string
  file_size: number
  mime_type: string
  created_at: string
  url: string
}
```

### MarketValue
```typescript
interface MarketValue {
  id: string
  watch_id: string
  value: string              // Decimal as string
  currency: string           // 3 chars
  source: 'manual' | 'chrono24' | 'api'
  notes: string | null
  recorded_at: string        // ISO datetime
}

interface WatchAnalytics {
  watch_id: string
  current_value: string | null
  current_currency: string
  purchase_price: string | null
  purchase_currency: string
  total_return: string | null
  roi_percentage: number | null
  annualized_return: number | null
  value_change_30d: string | null
  value_change_90d: string | null
  value_change_1y: string | null
  total_valuations: number
  first_valuation_date: string | null
  latest_valuation_date: string | null
}
```

---

## Session History Summary

**Phases 4-7 Completed (2026-01-28)**:

**Phase 4**: Service history CRUD with document upload, timeline view, overdue alerts, cascade delete
**Phase 5**: Market value tracking, ROI analytics, ValueChart visualization, CollectionAnalytics dashboard with currency selector
**Phase 6**: Watch comparison with selection UI, ComparisonBar, side-by-side table (8 sections, 30+ attributes), URL-based state
**Phase 7**: Testing (55+ tests, 48% coverage), security hardening (8/10 score), performance optimization (10-100x improvements), documentation (60+ pages), CI/CD pipeline (8 jobs)

**Bug Fixes**:
- Enum serialization (ValueSourceEnum, ImageSourceEnum) - fixed with `values_callable`
- Collection analytics 422 error - route conflict fixed by separating routers
- 502 Bad Gateway - nginx IP resolution fixed with restart

**Production Ready**: ✅ Testing, Security, Performance, Documentation, CI/CD, Deployment

---

## Known Limitations

1. No image optimization (thumbnails/compression)
2. No drag-to-reorder images
3. No batch operations
4. No image editing (crop/rotate)
5. No Google Images integration (schema ready)

---

## Resources

- FastAPI: https://fastapi.tiangolo.com/
- React Query: https://tanstack.com/query/latest
- SQLAlchemy: https://www.sqlalchemy.org/
- Tailwind CSS: https://tailwindcss.com/
- Lucide Icons: https://lucide.dev/
- Recharts: https://recharts.org/
- Repository: https://github.com/Homoney/watch_collection_tracker

---

**End of Context Document**
