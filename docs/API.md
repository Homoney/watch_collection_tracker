# Watch Collection Tracker API Documentation

**Applies to**: 2.x (checked against 2.0.1)
**Base URL**: `http://localhost:8080/api/v1`
**Interactive Docs**: `http://localhost:8080/docs`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Reference Data](#reference-data)
3. [Collections](#collections)
4. [Watches](#watches)
5. [Images](#images)
6. [Service History](#service-history)
7. [Market Values](#market-values)
8. [Analytics](#analytics)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)
11. [Other Endpoints](#other-endpoints)
12. [Reference Look-up](#reference-look-up)

---

## Authentication

All endpoints except `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/setup-status` and the reference data require a JWT access token in the `Authorization: Bearer <access_token>` header.

Registration is closed unless `ALLOW_REGISTRATION=true`. On an empty database the address in `INITIAL_ADMIN_EMAIL` may always register and becomes the admin; any other refused registration returns `403`.

Login, registration and refresh also set the refresh token in an HttpOnly cookie. The web app relies on the cookie; other clients can send the refresh token in the body instead.

### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

After `LOGIN_MAX_FAILURES` wrong passwords (default 5) the account is locked for `LOGIN_LOCKOUT_MINUTES` (default 15).

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

The body is optional: without it the refresh token is read from the cookie.

**Response** (200 OK): a new access token, and a new refresh token (in the cookie, and in the body only when the request sent one in the body):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Setup Status

```http
GET /api/v1/auth/setup-status
```

Public. `setup_required` is `true` only while the database has no accounts. `admin_signup` is `true` when, in addition, signing up creates the admin (`INITIAL_ADMIN_EMAIL` is set); the web app then shows "Create the admin account" on the sign-in page. Neither reveals the address.

**Response** (200 OK):
```json
{
  "setup_required": false,
  "admin_signup": false
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "default_currency": "USD",
  "theme": "light",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

## Reference Data

Reference data endpoints return brands, movement types, and complications. These are cached for 1 hour.

### List Brands

```http
GET /api/v1/reference/brands
Cache-Control: public, max-age=3600
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "name": "Rolex",
    "sort_order": 0
  }
]
```

### List Movement Types

```http
GET /api/v1/reference/movement-types
```

### List Complications

```http
GET /api/v1/reference/complications
```

---

## Collections

Manage color-coded watch collections.

### Create Collection

```http
POST /api/v1/collections/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Dive Watches",
  "description": "My collection of dive watches",
  "color": "#0066CC"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "name": "Dive Watches",
  "description": "My collection of dive watches",
  "color": "#0066CC",
  "user_id": "uuid",
  "is_default": false,
  "watch_count": 0,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### List Collections

```http
GET /api/v1/collections/
Authorization: Bearer <access_token>
```

### Get Collection

```http
GET /api/v1/collections/{collection_id}
Authorization: Bearer <access_token>
```

### Update Collection

```http
PUT /api/v1/collections/{collection_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "color": "#FF0000"
}
```

### Delete Collection

```http
DELETE /api/v1/collections/{collection_id}
Authorization: Bearer <access_token>
```

**Response** (204 No Content)

---

## Watches

Full CRUD operations for watches with filtering and search.

### Create Watch

```http
POST /api/v1/watches/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "model": "Submariner Date",
  "brand_id": "uuid",
  "collection_id": "uuid",
  "reference_number": "116610LN",
  "serial_number": "ABC12345",
  "movement_type_id": "uuid",
  "retailer": "Authorized dealer",
  "case_diameter": 40.0,
  "water_resistance": 300,
  "caliber": "3135",
  "crystal": "Sapphire",
  "case_material": "Stainless steel",
  "complications": ["Date", "Dive Bezel"],
  "purchase_date": "2020-01-15T00:00:00",
  "purchase_price": 9000.00,
  "purchase_currency": "USD",
  "condition": "excellent"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "model": "Submariner Date",
  "brand": {
    "id": "uuid",
    "name": "Rolex"
  },
  "collection": { ... },
  "reference_number": "116610LN",
  ...
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### List Watches

```http
GET /api/v1/watches/
  ?offset=0
  &limit=20
  &search=submariner
  &brand_id=uuid
  &collection_id=uuid
  &condition=excellent
  &min_value=5000
  &max_value=15000
  &purchase_date_from=2020-01-01
  &purchase_date_to=2024-12-31
  &sort_by=created_at
  &sort_order=desc
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `offset` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (default: 20, maximum 100)
- `search` (string): Case-insensitive search in model, brand, reference number, serial number and notes
- `brand_id` (uuid): Filter by brand
- `collection_id` (uuid): Filter by collection
- `movement_type_id` (uuid): Filter by movement type
- `condition` (string): Filter by condition (mint, excellent, good, fair, poor)
- `min_price`, `max_price` (number): Filter by purchase price range
- `min_value`, `max_value` (number): Filter by current market value range
- `purchase_date_from`, `purchase_date_to` (date): Filter by purchase date range
- `sort_by` (string): Sort field (created_at, purchase_date, purchase_price, model)
- `sort_order` (string): Sort direction (asc, desc)

**Response** (200 OK):
```json
{
  "items": [ ... ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

### Get Watch

```http
GET /api/v1/watches/{watch_id}
Authorization: Bearer <access_token>
```

### Update Watch

```http
PUT /api/v1/watches/{watch_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "model": "Updated Model Name"
}
```

### Delete Watch

```http
DELETE /api/v1/watches/{watch_id}
Authorization: Bearer <access_token>
```

**Response** (204 No Content)

---

## Images

Upload and manage watch images.

### Upload Image

```http
POST /api/v1/watches/{watch_id}/images
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=@/path/to/image.jpg
```

**Constraints**:
- Allowed types: JPG, PNG, GIF, WebP
- Max size: 20MB
- Automatically extracts dimensions using Pillow

**Response** (201 Created):
```json
{
  "id": "uuid",
  "watch_id": "uuid",
  "file_path": "watch_id/image.jpg",
  "file_name": "image.jpg",
  "file_size": 1048576,
  "mime_type": "image/jpeg",
  "width": 1920,
  "height": 1080,
  "is_primary": true,
  "sort_order": 0,
  "source": "user_upload",
  "created_at": "2024-01-15T10:30:00",
  "url": "/uploads/watch_id/image.jpg?expires=1735689600&sig=..."
}
```

`url` is a signed link that expires (see `UPLOAD_URL_TTL_SECONDS`). Fetch the record again for a fresh link; do not store the URL.

### List Images

```http
GET /api/v1/watches/{watch_id}/images
Authorization: Bearer <access_token>
```

### Update Image

```http
PATCH /api/v1/watches/{watch_id}/images/{image_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_primary": true
}
```

### Delete Image

```http
DELETE /api/v1/watches/{watch_id}/images/{image_id}
Authorization: Bearer <access_token>
```

**Response** (204 No Content)

---

## Service History

Track maintenance records and upload service documents.

### Create Service Record

```http
POST /api/v1/watches/{watch_id}/service-history
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service_date": "2024-01-15T00:00:00",
  "provider": "Rolex Service Center",
  "service_type": "Full Service",
  "description": "Complete overhaul",
  "cost": 850.00,
  "cost_currency": "USD",
  "next_service_due": "2029-01-15T00:00:00"
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "watch_id": "uuid",
  "service_date": "2024-01-15T00:00:00",
  "provider": "Rolex Service Center",
  "service_type": "Full Service",
  "description": "Complete overhaul",
  "cost": "850.00",
  "cost_currency": "USD",
  "next_service_due": "2029-01-15T00:00:00",
  "documents": [],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Upload Service Document

```http
POST /api/v1/watches/{watch_id}/service-history/{service_id}/documents
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=@/path/to/receipt.pdf
```

**Constraints**:
- Allowed types: PDF, JPG, PNG
- Max size: 10MB

**Response** (201 Created):
```json
{
  "id": "uuid",
  "service_history_id": "uuid",
  "file_path": "watch_id/service_id/receipt.pdf",
  "file_name": "receipt.pdf",
  "file_size": 524288,
  "mime_type": "application/pdf",
  "created_at": "2024-01-15T10:30:00",
  "url": "/uploads/service-docs/watch_id/service_id/receipt.pdf?expires=1735689600&sig=..."
}
```

---

## Market Values

Track historical market values and view performance analytics.

### Create Market Value

```http
POST /api/v1/watches/{watch_id}/market-values
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "value": 15000.00,
  "currency": "USD",
  "source": "manual",
  "notes": "Current market estimate",
  "recorded_at": "2024-01-15T00:00:00"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "watch_id": "uuid",
  "value": "15000.00",
  "currency": "USD",
  "source": "manual",
  "notes": "Current market estimate",
  "recorded_at": "2024-01-15T00:00:00"
}
```

### Get Watch Analytics

```http
GET /api/v1/watches/{watch_id}/analytics
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "watch_id": "uuid",
  "current_value": "15000.00",
  "current_currency": "USD",
  "purchase_price": "9000.00",
  "purchase_currency": "USD",
  "total_return": "6000.00",
  "roi_percentage": 66.67,
  "annualized_return": 13.2,
  "value_change_30d": "500.00",
  "value_change_90d": "1200.00",
  "value_change_1y": "3000.00",
  "total_valuations": 5,
  "first_valuation_date": "2023-01-15T00:00:00",
  "latest_valuation_date": "2024-01-15T00:00:00"
}
```

---

## Analytics

Collection-wide performance analytics.

### Get Collection Analytics

```http
GET /api/v1/collection-analytics?currency=USD
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "total_watches": 45,
  "total_current_value": "450000.00",
  "total_purchase_price": "300000.00",
  "currency": "USD",
  "total_return": "150000.00",
  "average_roi": 50.0,
  "top_performers": [
    {
      "watch_id": "uuid",
      "model": "Daytona",
      "brand": "Rolex",
      "roi": 120.5,
      "current_value": 35000.00,
      "purchase_price": 15000.00
    }
  ],
  "worst_performers": [ ... ],
  "value_by_brand": {
    "Rolex": 250000.00,
    "Omega": 150000.00
  },
  "value_by_collection": {
    "Dive Watches": 200000.00,
    "Dress Watches": 250000.00
  },
  "total_valuations": 225
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Errors

**Authentication Required**:
```json
{
  "detail": "Not authenticated"
}
```

**Invalid Token**:
```json
{
  "detail": "Could not validate credentials"
}
```

**Resource Not Found**:
```json
{
  "detail": "Watch not found"
}
```

**Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

The app enforces rate limits per client address (`backend/app/middleware/rate_limit.py`). The first matching rule applies:

| Endpoint Pattern | Limit | Burst |
|-----------------|-------|-------|
| `/api/v1/auth/login`, `/api/v1/auth/register` | 5 req/min | 3 |
| `/api/v1/auth/change-password`, `/api/v1/auth/refresh` | 10 req/min | 5 |
| `POST` uploads (`/images`, `/reference-photo`, service documents) | 10 req/min | 10 |
| `/api/v1/spec-lookup` | 20 req/min | 10 |
| `/api/*` (general) | 10 req/sec | 20 |

When a limit is exceeded, you'll receive `429 Too Many Requests` with a `Retry-After` header.

Behind a reverse proxy, set `TRUSTED_PROXIES` to the proxy's address so limits apply to each client and not to the proxy (see [DEPLOYMENT.md](DEPLOYMENT.md#6-https-with-a-reverse-proxy)).

Separately, an account is locked for 15 minutes after 5 wrong passwords.

---

## Other Endpoints

The sections above show request and response bodies for the most used calls. These endpoints exist as well; `/docs` has their full schemas.

| Method and path | What it does |
|---|---|
| `POST /api/v1/auth/logout` | End every session of the current user and clear the cookie (204) |
| `PUT /api/v1/auth/me` | Update `full_name`, `default_currency`, `theme` |
| `POST /api/v1/auth/change-password` | Body `current_password`, `new_password` (204); ends other sessions |
| `GET`, `PUT`, `DELETE /api/v1/watches/{watch_id}/service-history/{service_id}` | One service record; `GET /api/v1/watches/{watch_id}/service-history` lists them |
| `GET /api/v1/watches/{watch_id}/service-history/{service_id}/documents` | List a record's documents |
| `DELETE /api/v1/watches/{watch_id}/service-history/{service_id}/documents/{doc_id}` | Delete a document |
| `GET /api/v1/watches/{watch_id}/market-values` | List a watch's valuations |
| `GET`, `PUT`, `DELETE /api/v1/watches/{watch_id}/market-values/{value_id}` | One valuation |
| `GET /api/v1/watches/{watch_id}/qr-code?base_url=...` | PNG QR code linking to the watch page; `base_url` must be this site |
| `GET /api/v1/watches/{watch_id}/export/pdf` | One watch as a PDF |
| `GET /api/v1/watches/export/pdf?collection_id=...` | All watches (or one collection) as a PDF |
| `POST /api/v1/watches/{watch_id}/reference-photo` | Save WatchBase's photo of the watch as a reference photo; optional body `{"watchbase_id": 123}` (from Look up), otherwise the watch's reference number is used. 201 with `image` when saved; 200 with `status`, `message` and `image: null` otherwise (no key, not found, several matches, no photo, source down, already has one). Upload rate limit applies |
| `GET /api/v1/atomic-time` | Reference time for accuracy readings |
| `POST`, `GET /api/v1/watches/{watch_id}/accuracy-readings` | Record a movement accuracy reading; list readings with drift |
| `GET`, `PUT`, `DELETE /api/v1/watches/{watch_id}/accuracy-readings/{reading_id}` | One reading |
| `GET /api/v1/watches/{watch_id}/accuracy-analytics` | Drift statistics for a watch |
| `GET`, `POST /api/v1/saved-searches/` | List or create saved watch searches |
| `GET`, `PUT`, `DELETE /api/v1/saved-searches/{search_id}` | One saved search |
| `GET /api/v1/users/`, `GET /api/v1/users/{user_id}` | Admin only: list or show users |
| `PATCH /api/v1/users/{user_id}` | Admin only: change a user's role |
| `POST /api/v1/users/{user_id}/reset-password` | Admin only: set a new password |
| `DELETE /api/v1/users/{user_id}` | Admin only: delete a user |
| `GET /api` | API name and version |
| `GET /health` | Health check, `{"status": "healthy"}` |

A collection path sent without its trailing slash (for example `/api/v1/watches`) is redirected (307) to the slashed form.

---

## Interactive API Documentation

For interactive API exploration, visit:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

These provide:
- Complete endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Authentication support

---

## Reference Look-up

### Look up a reference number

```http
GET /api/v1/spec-lookup?reference=126610LN&brand_id=<uuid>&caliber=3235
Authorization: Bearer <access_token>
```

`reference` is required (2-100 characters). `brand_id` and `caliber` are optional hints. After the user picks from `choices`, call again with `watchbase_id=<id>`.

Always answers **200**; `status` says what happened:

| `status` | Meaning |
|---|---|
| `ok` | `fields` holds values to fill, `sources` says where each came from |
| `choices` | Several watches match; `choices` lists them (no paid call made yet) |
| `not_found` | WatchBase has no watch for this reference |
| `links_only` | No WatchBase key is set; only `links` (and Caliber Corner facts when `caliber` and the brand are given) |
| `bad_key` | WatchBase refused the key (wrong key or no credits) |
| `unavailable` | A source is down or answered something unexpected |

```json
{
  "status": "ok",
  "message": "Filled the empty fields we found. Check them before saving.",
  "reference": "126610LN",
  "fields": {
    "brand_name": "Rolex",
    "model": "Submariner Date 41 Steel / Black / Black",
    "movement_type_name": "Automatic",
    "case_diameter": 41.0,
    "lug_width": 21.0,
    "water_resistance": 300,
    "power_reserve": 70,
    "caliber": "3235",
    "crystal": "Sapphire",
    "case_material": "Stainless Steel",
    "complications": ["Dive Bezel", "Date"]
  },
  "sources": {
    "caliber": {"name": "WatchBase", "url": "https://watchbase.com/rolex/submariner/126610ln-0001"}
  },
  "choices": [],
  "movement": {
    "caliber": "3235", "jewels": 31, "frequency": "28,800 bph (4Hz)", "power_reserve": 70,
    "source": {"name": "Caliber Corner", "url": "https://calibercorner.com/rolex-caliber-3235/"}
  },
  "links": [
    {"label": "WatchBase", "url": "https://duckduckgo.com/?q=site%3Awatchbase.com+Rolex+126610LN"},
    {"label": "Caliber Corner", "url": "https://calibercorner.com/rolex-caliber-3235/"},
    {"label": "Rolex website", "url": "https://duckduckgo.com/?q=site%3Arolex.com+126610LN"}
  ]
}
```

`fields` uses names (`brand_name`, `movement_type_name`, complication names) rather than IDs; the web app matches them to the reference data. Answers are cached on the server for `SPEC_LOOKUP_CACHE_DAYS` (default 90).

### WatchBase key (admin only)

| Method and path | What it does |
|---|---|
| `GET /api/v1/settings/watchbase-key` | `{"configured": bool, "from_environment": bool}`; never the key |
| `PUT /api/v1/settings/watchbase-key` | Body `{"api_key": "..."}` (8-200 characters, no spaces); saves it |
| `DELETE /api/v1/settings/watchbase-key` | Removes the saved key |

---

## SDK Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8080/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# Create watch
headers = {"Authorization": f"Bearer {token}"}
watch_data = {
    "model": "Submariner",
    "brand_id": "brand-uuid",
    "purchase_price": 9000.00,
    "purchase_currency": "USD"
}
response = requests.post(
    "http://localhost:8080/api/v1/watches/",
    headers=headers,
    json=watch_data
)
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('http://localhost:8080/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// Create watch
const watchResponse = await fetch('http://localhost:8080/api/v1/watches/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'Submariner',
    brand_id: 'brand-uuid',
    purchase_price: 9000.00,
    purchase_currency: 'USD'
  })
});
```

---

## Webhooks (Future)

Webhook support is planned for future releases to notify external systems of events like:
- New watch added
- Market value updated
- Service due reminder

---

**Last Updated**: 2026-11-18
**Applies to**: 2.x
