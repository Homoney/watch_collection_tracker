# Watch Collection Tracker API Documentation

**Version**: 1.0.0
**Base URL**: `http://localhost:8080/api/v1`
**Interactive Docs**: `http://localhost:8080/api/docs`

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

---

## Authentication

All endpoints except `/auth/register` and `/auth/login` require authentication using JWT tokens.

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
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

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
Authorization: Bearer <access_token>

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
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
  "is_active": true,
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
    "sort_order": 0,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
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
  "case_material": "Stainless Steel",
  "case_diameter": 40.0,
  "water_resistance": 300,
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
  ?skip=0
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
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (default: 20)
- `search` (string): Search in model, brand, reference number, serial number
- `brand_id` (uuid): Filter by brand
- `collection_id` (uuid): Filter by collection
- `condition` (string): Filter by condition (mint, excellent, good, fair, poor)
- `min_value`, `max_value` (number): Filter by current market value range
- `purchase_date_from`, `purchase_date_to` (date): Filter by purchase date range
- `sort_by` (string): Sort field (created_at, purchase_date, purchase_price, model)
- `sort_order` (string): Sort direction (asc, desc)

**Response** (200 OK):
```json
{
  "items": [ ... ],
  "total": 45,
  "skip": 0,
  "limit": 20
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
  "url": "/uploads/watch_id/image.jpg"
}
```

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

**Response** (201 Created):
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
  "url": "/uploads/service-docs/watch_id/service_id/receipt.pdf"
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

Rate limits are enforced by Nginx:

| Endpoint Pattern | Limit | Burst |
|-----------------|-------|-------|
| `/api/v1/auth/login` | 5 req/min | 3 |
| `/api/v1/auth/register` | 5 req/min | 3 |
| `/api/*` (general) | 10 req/sec | 20 |

When rate limit is exceeded, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
```

---

## Interactive API Documentation

For interactive API exploration, visit:

- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc

These provide:
- Complete endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Authentication support

---

## SDK Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8080/api/v1/auth/login",
    data={"username": "user@example.com", "password": "password123"}
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
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'user@example.com',
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

**Last Updated**: 2026-01-28
**API Version**: 1.0.0
