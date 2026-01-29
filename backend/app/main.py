from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    collections,
    images,
    market_values,
    movement_accuracy,
    reference,
    saved_searches,
    service_history,
    users,
    watches,
)
from app.config import settings
from app.middleware.cache import CacheMiddleware

app = FastAPI(
    title="Watch Collection Tracker API",
    description="""
# Watch Collection Tracker API

A comprehensive API for managing watch collections with multi-user support.

## Features

* **Authentication**: JWT-based authentication with access and refresh tokens
* **Watch Management**: Full CRUD operations for watches with detailed specifications
* **Collections**: Organize watches into color-coded collections
* **Image Upload**: Upload and manage watch images with primary designation
* **Service History**: Track maintenance records with document attachments
* **Market Values**: Track historical market values and performance analytics
* **Comparison**: Compare multiple watches side-by-side
* **Reference Data**: Brands, movement types, and complications

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Rate Limiting

* Authentication endpoints: 5 requests per minute
* General API endpoints: 10 requests per second
* Image upload endpoints: 10 uploads per minute

## Caching

* Reference data endpoints: Cached for 1 hour
* Static uploads: Cached with immutable headers
* API responses: No-cache by default
    """,
    version="1.0.0",
    contact={
        "name": "Watch Collection Tracker Support",
        "url": "https://github.com/Homoney/watch_collection_tracker",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and registration",
        },
        {
            "name": "Reference Data",
            "description": "Brands, movement types, and complications",
        },
        {"name": "Collections", "description": "Watch collection management"},
        {"name": "Watches", "description": "Watch CRUD operations and search"},
        {"name": "Images", "description": "Watch image upload and management"},
        {"name": "Service History", "description": "Maintenance records and documents"},
        {"name": "Market Values", "description": "Market value tracking and analytics"},
        {"name": "Analytics", "description": "Collection-wide performance analytics"},
        {"name": "Saved Searches", "description": "Save and manage watch searches"},
        {"name": "User Management", "description": "Admin-only user management"},
        {
            "name": "Movement Accuracy",
            "description": "Watch movement accuracy tracking and drift calculations",
        },
    ],
)

# Cache middleware (must be before CORS)
app.add_middleware(CacheMiddleware, cache_time=300)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(
    reference.router, prefix="/api/v1/reference", tags=["Reference Data"]
)
app.include_router(
    collections.router, prefix="/api/v1/collections", tags=["Collections"]
)
app.include_router(watches.router, prefix="/api/v1/watches", tags=["Watches"])
app.include_router(images.router, prefix="/api/v1/watches", tags=["Images"])
app.include_router(
    service_history.router, prefix="/api/v1/watches", tags=["Service History"]
)
# Market values - register collection analytics separately to avoid path conflicts
import app.api.v1.market_values as mv

app.include_router(mv.collection_analytics_router, prefix="/api/v1", tags=["Analytics"])
app.include_router(mv.router, prefix="/api/v1/watches", tags=["Market Values"])
app.include_router(
    saved_searches.router, prefix="/api/v1/saved-searches", tags=["Saved Searches"]
)
app.include_router(users.router, prefix="/api/v1/users", tags=["User Management"])
# Movement accuracy - atomic-time is public (no auth), watch-specific routes require auth
app.include_router(
    movement_accuracy.atomic_time_router, prefix="/api/v1", tags=["Movement Accuracy"]
)
app.include_router(
    movement_accuracy.router, prefix="/api/v1/watches", tags=["Movement Accuracy"]
)


@app.get("/")
async def root():
    return {"message": "Watch Collection Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
