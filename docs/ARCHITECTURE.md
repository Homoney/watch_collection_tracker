# Watch Collection Tracker - Architecture Documentation

This document describes the system architecture, design decisions, and technical implementation of the Watch Collection Tracker.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Layers](#architecture-layers)
4. [Database Design](#database-design)
5. [API Architecture](#api-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [File Storage](#file-storage)
8. [Security Architecture](#security-architecture)
9. [Performance Optimizations](#performance-optimizations)
10. [Scalability Considerations](#scalability-considerations)

---

## System Overview

The Watch Collection Tracker is a full-stack web application built with modern technologies, following a client-server architecture with clear separation of concerns.

### High-Level Architecture

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │ HTTP/HTTPS
       ↓
┌─────────────┐
│    Nginx    │ ← Reverse Proxy + Static Files
└──────┬──────┘
       │
    ┌──┴───┬────────────┐
    ↓      ↓            ↓
┌────────┐ ┌──────────┐ ┌──────────┐
│Frontend│ │ Backend  │ │  Uploads │
│ (SPA)  │ │  (API)   │ │ (Static) │
└────────┘ └────┬─────┘ └──────────┘
                │
          ┌─────┴──────┬────────┐
          ↓            ↓        ↓
     ┌──────────┐ ┌──────┐ ┌──────┐
     │PostgreSQL│ │Redis │ │ File │
     │          │ │Cache │ │System│
     └──────────┘ └──────┘ └──────┘
```

### Request Flow

1. **User Request** → Browser sends HTTP request
2. **Nginx** → Routes request to appropriate service
3. **API Processing**:
   - Backend validates authentication (JWT)
   - Checks cache (Redis) if applicable
   - Queries database (PostgreSQL)
   - Processes business logic
   - Returns JSON response
4. **Response** → Nginx adds cache headers and returns to browser
5. **Frontend** → React renders UI with data

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.109.0 | Web framework |
| Language | Python | 3.11 | Programming language |
| ASGI Server | Uvicorn | 0.27.0 | Production server |
| ORM | SQLAlchemy | 2.0.25 | Database abstraction |
| Migrations | Alembic | 1.13.1 | Database migrations |
| Validation | Pydantic | 2.5.3 | Data validation |
| Authentication | python-jose | 3.3.0 | JWT tokens |
| Password Hashing | bcrypt | 4.1.2 | Secure hashing |
| Image Processing | Pillow | 10.2.0 | Image manipulation |
| Web Scraping | BeautifulSoup4 | 4.12.3 | HTML parsing |
| HTTP Client | httpx | 0.26.0 | Async HTTP |
| Caching | redis | 5.0.1 | Cache layer |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18.2.0 | UI library |
| Language | TypeScript | 5.3.3 | Type-safe JavaScript |
| Build Tool | Vite | 5.0.11 | Fast build system |
| Routing | React Router | 6.21.1 | Client-side routing |
| State Management | TanStack Query | 5.17.9 | Server state |
| State Management | Zustand | 4.4.7 | Client state |
| Forms | React Hook Form | 7.49.3 | Form handling |
| HTTP Client | Axios | 1.7.7 | API requests |
| Styling | Tailwind CSS | 3.4.1 | Utility-first CSS |
| Icons | Lucide React | 0.309.0 | Icon library |
| Charts | Recharts | 2.10.3 | Data visualization |
| Date Handling | date-fns | 2.30.0 | Date utilities |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Database | PostgreSQL | 16 | Relational database |
| Cache | Redis | 7 | In-memory cache |
| Reverse Proxy | Nginx | Latest | Load balancing |
| Container Runtime | Docker | Latest | Containerization |
| Orchestration | Docker Compose | Latest | Multi-container apps |

---

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Responsibility**: User interface and user experience

**Components**:
- **Pages**: Top-level route components (Login, Dashboard, WatchList, etc.)
- **Components**: Reusable UI components (WatchCard, ImageGallery, etc.)
- **Hooks**: Custom React hooks (useWatches, useAuth, etc.)
- **Contexts**: Global state providers (AuthContext, ComparisonContext)
- **Services**: API client (axios wrapper)

**Key Patterns**:
- **Component Composition**: Small, reusable components
- **Custom Hooks**: Encapsulate business logic
- **React Query**: Server state caching and synchronization
- **Code Splitting**: Lazy loading for better performance

### 2. API Layer (Backend)

**Responsibility**: Business logic and data access

**Structure**:
```
backend/app/
├── api/v1/           # API endpoints
│   ├── auth.py       # Authentication
│   ├── watches.py    # Watch CRUD
│   └── ...
├── core/             # Core functionality
│   ├── security.py   # JWT, password hashing
│   └── deps.py       # Dependencies
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── utils/            # Utilities
│   ├── file_upload.py
│   ├── cache.py
│   └── logging.py
└── middleware/       # Middleware
    └── cache.py
```

**Key Patterns**:
- **Dependency Injection**: FastAPI's Depends system
- **Repository Pattern**: Database access through ORM
- **DTO Pattern**: Pydantic schemas for validation
- **Middleware**: Cross-cutting concerns (caching, logging)

### 3. Data Layer

**Responsibility**: Data persistence and retrieval

**Components**:
- **PostgreSQL**: Relational data storage
- **Redis**: Caching layer
- **File System**: Static file storage (images, documents)

**Key Patterns**:
- **ORM**: SQLAlchemy for database abstraction
- **Migrations**: Alembic for schema versioning
- **Indexes**: Optimized query performance
- **Connection Pooling**: Efficient database connections

---

## Database Design

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
- Source tracking (user upload, Google, URL)

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

### Indexes for Performance

```sql
-- Watch indexes
CREATE INDEX ix_watches_brand_id ON watches(brand_id);
CREATE INDEX ix_watches_collection_id ON watches(collection_id);
CREATE INDEX ix_watches_condition ON watches(condition);
CREATE INDEX ix_watches_purchase_date ON watches(purchase_date);

-- Full-text search
CREATE INDEX ix_watches_model_search
  ON watches USING gin(to_tsvector('english', model));

-- Service history indexes
CREATE INDEX ix_service_history_watch_id ON service_history(watch_id);
CREATE INDEX ix_service_history_service_date ON service_history(service_date);

-- Market value indexes
CREATE INDEX ix_market_values_watch_id ON market_values(watch_id);
CREATE INDEX ix_market_values_recorded_at ON market_values(recorded_at);

-- Image indexes
CREATE INDEX ix_watch_images_watch_id ON watch_images(watch_id);
CREATE INDEX ix_watch_images_is_primary ON watch_images(is_primary);
```

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
┌────────┐                  ┌────────┐
│ Client │                  │  API   │
└───┬────┘                  └───┬────┘
    │                           │
    │  POST /auth/register      │
    │  (email, password)        │
    ├──────────────────────────>│
    │                           │
    │  201 Created              │
    │  (access_token,           │
    │   refresh_token)          │
    │<──────────────────────────┤
    │                           │
    │  GET /watches             │
    │  (Bearer access_token)    │
    ├──────────────────────────>│
    │                           │
    │  200 OK                   │
    │  (watches data)           │
    │<──────────────────────────┤
    │                           │
    │  (access_token expires)   │
    │                           │
    │  POST /auth/refresh       │
    │  (refresh_token)          │
    ├──────────────────────────>│
    │                           │
    │  200 OK                   │
    │  (new access_token)       │
    │<──────────────────────────┤
```

**Token Expiry**:
- Access token: 30 minutes
- Refresh token: 7 days

**Security**:
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens signed with HS256
- Secret key from environment variable

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

**Server State** (TanStack Query):
- API data caching
- Automatic refetching
- Optimistic updates
- Loading/error states

```typescript
const { data: watches, isLoading } = useQuery({
  queryKey: ['watches', filters],
  queryFn: () => fetchWatches(filters),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

**Client State** (Zustand):
- UI state (modals, sidebars)
- User preferences
- Temporary selections

**Context API**:
- Authentication state (AuthContext)
- Comparison selections (ComparisonContext)

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
storage/
├── uploads/
│   ├── {watch_id}/
│   │   ├── image1.jpg
│   │   └── image2.png
│   └── service-docs/
│       └── {watch_id}/
│           └── {service_id}/
│               ├── receipt.pdf
│               └── certificate.jpg
└── backups/
    └── {date}/
        └── backup.sql
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

### Security

**File Validation**:
- MIME type checking
- File extension whitelist
- Size limits (images: 20MB, documents: 10MB)
- Filename sanitization (prevent path traversal)

**Storage Security**:
- Isolated directories per watch
- Nginx serves with read-only mount
- UUID-based paths (non-guessable)

---

## Security Architecture

### Defense in Depth

**Layer 1: Network**
- Nginx reverse proxy
- Rate limiting (5 req/min auth, 10 req/sec API)
- HTTPS support (production)

**Layer 2: Application**
- JWT authentication
- CORS configuration
- Security headers (CSP, X-Frame-Options, etc.)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (React escaping)

**Layer 3: Data**
- Password hashing (bcrypt)
- Database connection pooling
- Entity ownership verification
- File path validation

**Layer 4: Monitoring**
- Security event logging
- Failed login tracking
- Audit trails

### Authentication Security

**Password Requirements**:
- Minimum 8 characters
- Hashed with bcrypt (cost 12)
- Never stored in plain text
- Never logged

**Token Security**:
- Short-lived access tokens (30 min)
- Longer-lived refresh tokens (7 days)
- Signed with HMAC-SHA256
- Stored client-side (localStorage)

**Session Management**:
- Stateless (JWT)
- No server-side session storage
- Token revocation via expiry

---

## Performance Optimizations

### Database

**Query Optimization**:
- SQL aggregation instead of Python loops (10-50x faster)
- Strategic indexes on foreign keys and filter fields
- PostgreSQL full-text search with GIN indexes
- Connection pooling (pool_size=20, max_overflow=10)

**Example**:
```python
# Before: O(n) in Python
total = sum(watch.current_market_value for watch in watches)

# After: O(1) in SQL
total = db.query(func.sum(Watch.current_market_value)).scalar()
```

### Caching

**HTTP Caching**:
- Reference data: 1 hour (`Cache-Control: public, max-age=3600`)
- Static uploads: Forever (`Cache-Control: public, max-age=31536000, immutable`)
- API responses: No-cache (dynamic data)

**Redis Caching**:
- Application-level cache
- Graceful fallback if unavailable
- TTL-based expiration

### Frontend

**Code Splitting**:
```typescript
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
// Result: ~40-60% smaller initial bundle
```

**React Optimizations**:
- `React.memo()` for expensive components
- `useCallback()` for stable function references
- Image lazy loading (`loading="lazy"`)

**Bundle Optimization**:
- Manual chunks for vendor libraries
- Tree shaking (Vite)
- Minification (production builds)

### Nginx

**Static File Serving**:
- Gzip compression (level 6)
- Browser caching headers
- Direct file serving (bypass backend)

**Load Balancing** (future):
- Multiple backend instances
- Health checks
- Failover support

---

## Scalability Considerations

### Horizontal Scaling

**Stateless Design**:
- JWT tokens (no session state)
- Redis for shared cache
- Database connection pooling

**Containerization**:
- Docker for easy deployment
- Docker Compose for orchestration
- Kubernetes-ready architecture

### Vertical Scaling

**Database**:
- PostgreSQL supports large datasets
- Indexes optimize query performance
- Read replicas (future)

**Caching**:
- Redis reduces database load
- Can scale to Redis Cluster

### Future Enhancements

**CDN Integration**:
- Static assets (images, JS, CSS)
- Reduced latency
- Lower bandwidth costs

**Message Queue**:
- Background jobs (image processing, emails)
- Asynchronous processing
- Better resource utilization

**Microservices** (if needed):
- Image service (upload, resize, optimize)
- Analytics service (calculations, reports)
- Notification service (emails, alerts)

---

## Monitoring & Observability

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

### Health Checks

**Endpoints**:
- `/health` - Overall health
- `/api/health` - API health

**Checks**:
- Database connectivity
- Redis availability (optional)
- Disk space (upload directory)

### Metrics (Future)

**Application Metrics**:
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Active users

**Infrastructure Metrics**:
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

---

## Deployment Architecture

### Development

```
┌─────────────────────┐
│   docker-compose    │
├─────────────────────┤
│ - postgres          │
│ - redis             │
│ - backend (dev)     │
│ - frontend (dev)    │
│ - nginx             │
└─────────────────────┘
```

### Production

```
┌──────────────────────┐
│     Cloud Provider   │
├──────────────────────┤
│  ┌────────────────┐  │
│  │ Load Balancer  │  │
│  └───────┬────────┘  │
│          │           │
│  ┌───────┴────────┐  │
│  │  nginx (HTTPS) │  │
│  └───┬────────┬───┘  │
│      │        │      │
│  ┌───┴───┐ ┌─┴────┐ │
│  │Backend│ │Redis │ │
│  └───┬───┘ └──────┘ │
│      │              │
│  ┌───┴───────────┐  │
│  │  PostgreSQL   │  │
│  │  (with backup)│  │
│  └───────────────┘  │
└──────────────────────┘
```

---

**Last Updated**: 2026-01-28
**Version**: 1.0.0
