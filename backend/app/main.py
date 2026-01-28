from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, reference, collections, watches, images, service_history, market_values, saved_searches

app = FastAPI(
    title="Watch Collection Tracker API",
    description="API for managing watch collections with multi-user support",
    version="1.0.0"
)

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
app.include_router(reference.router, prefix="/api/v1/reference", tags=["Reference Data"])
app.include_router(collections.router, prefix="/api/v1/collections", tags=["Collections"])
app.include_router(watches.router, prefix="/api/v1/watches", tags=["Watches"])
app.include_router(images.router, prefix="/api/v1/watches", tags=["Images"])
app.include_router(service_history.router, prefix="/api/v1/watches", tags=["Service History"])
# Market values - register collection analytics separately to avoid path conflicts
import app.api.v1.market_values as mv
app.include_router(mv.collection_analytics_router, prefix="/api/v1", tags=["Analytics"])
app.include_router(mv.router, prefix="/api/v1/watches", tags=["Market Values"])
app.include_router(saved_searches.router, prefix="/api/v1/saved-searches", tags=["Saved Searches"])


@app.get("/")
async def root():
    return {"message": "Watch Collection Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
