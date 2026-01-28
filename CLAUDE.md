# Claude Context - Watch Collection Tracker

**Last Updated**: 2026-01-27
**Current Phase**: Phase 3 Complete ✓
**Commit**: `e0942bf` - Implement Phase 3 image upload and management system

---

## Project Overview

A full-stack watch collection management application with multi-user support, built with FastAPI (Python) and React (TypeScript). Users can track their watch collections with detailed specifications, images, and metadata.

**Tech Stack**:
- Backend: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pillow
- Frontend: React 18, TypeScript, TanStack Query, React Hook Form, Tailwind CSS
- Infrastructure: Docker Compose, Nginx (reverse proxy + static files)
- Icons: Lucide React

**Access**:
- Application: http://localhost:8080
- Backend API: http://localhost:8080/api
- Health Check: http://localhost:8080/health

---

## What We've Completed

### ✅ Phase 1: Foundation (Complete)
- Docker Compose infrastructure
- PostgreSQL database with migrations
- FastAPI backend with authentication (JWT)
- React frontend with routing
- Nginx reverse proxy + static file serving
- User registration and login

### ✅ Phase 2: Core CRUD Operations (Complete)
- Reference data (Brands, Movement Types, Complications)
- Collections CRUD with color coding
- Watches CRUD with full specifications
- Filtering, sorting, and pagination
- Watch cards UI with collections integration

### ✅ Phase 3: Image Upload and Management (Complete - Just Finished!)
**Backend**:
- File upload utilities with validation (`backend/app/utils/file_upload.py`)
- Image CRUD API endpoints (`backend/app/api/v1/images.py`)
- Image schemas with computed URLs (`backend/app/schemas/watch_image.py`)
- Watch endpoints updated to eager load images
- Primary image management (auto-promotion on delete)
- Secure file storage in `/app/storage/uploads/{watch_id}/`

**Frontend**:
- ImageUpload component with drag-and-drop (`frontend/src/components/watches/ImageUpload.tsx`)
- ImageGallery component with grid layout (`frontend/src/components/watches/ImageGallery.tsx`)
- ImageLightbox component for full-screen viewing (`frontend/src/components/common/ImageLightbox.tsx`)
- React Query hooks for image operations (`frontend/src/hooks/useWatchImages.ts`)
- Updated WatchCard to display primary images
- Integrated image management into WatchDetailPage

**Features**:
- ✓ Upload images (JPG, PNG, GIF, WebP, max 20MB)
- ✓ Extract and store dimensions using Pillow
- ✓ Set primary image (only one per watch)
- ✓ Delete images (removes database record + physical file)
- ✓ Full-screen lightbox with keyboard navigation
- ✓ Nginx serves images from `/uploads/` with caching

---

## Current Architecture

### Database Schema

**Users**: Email/password authentication, JWT tokens
**Brands**: Reference data for watch manufacturers
**MovementTypes**: Reference data for watch movements
**Complications**: Reference data for watch features
**Collections**: User-created collections with color coding
**Watches**: Main entity with specifications, purchase info, market value
**WatchImages**: Images linked to watches with primary designation

### File Structure

```
watch-collection-tracker/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py           # User authentication
│   │   │   ├── reference.py      # Reference data (brands, etc.)
│   │   │   ├── collections.py    # Collections CRUD
│   │   │   ├── watches.py        # Watches CRUD
│   │   │   └── images.py         # Image upload/management (NEW)
│   │   ├── core/
│   │   │   ├── security.py       # JWT & password hashing
│   │   │   └── deps.py           # Dependencies (auth)
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   │   └── watch_image.py    # Image schemas (NEW)
│   │   ├── utils/
│   │   │   └── file_upload.py    # File handling utilities (NEW)
│   │   ├── config.py             # Settings
│   │   ├── database.py           # DB connection
│   │   └── main.py               # FastAPI app
│   ├── alembic/                  # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── ImageLightbox.tsx  # Full-screen viewer (NEW)
│   │   │   ├── watches/
│   │   │   │   ├── ImageUpload.tsx    # Upload component (NEW)
│   │   │   │   ├── ImageGallery.tsx   # Gallery component (NEW)
│   │   │   │   ├── WatchCard.tsx      # Updated with images
│   │   │   │   └── WatchForm.tsx
│   │   │   └── layout/
│   │   ├── hooks/
│   │   │   ├── useWatches.ts
│   │   │   └── useWatchImages.ts      # Image hooks (NEW)
│   │   ├── lib/
│   │   │   └── api.ts                 # API client (updated)
│   │   ├── pages/
│   │   │   └── WatchDetailPage.tsx    # Updated with image section
│   │   ├── types/index.ts             # TypeScript types (updated)
│   │   └── App.tsx
│   └── package.json                   # Added lucide-react
├── nginx/
│   └── nginx.conf                # Reverse proxy + static files
├── storage/
│   ├── uploads/                  # User-uploaded images (watch_id subdirs)
│   └── backups/                  # Database backups
└── docker-compose.yml
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Reference Data
- `GET /api/v1/reference/brands` - List brands
- `GET /api/v1/reference/movement-types` - List movement types
- `GET /api/v1/reference/complications` - List complications

### Collections
- `GET /api/v1/collections/` - List user collections
- `POST /api/v1/collections/` - Create collection
- `GET /api/v1/collections/{id}` - Get collection
- `PUT /api/v1/collections/{id}` - Update collection
- `DELETE /api/v1/collections/{id}` - Delete collection

### Watches
- `GET /api/v1/watches/` - List watches (paginated, filterable)
- `POST /api/v1/watches/` - Create watch
- `GET /api/v1/watches/{id}` - Get watch with images
- `PUT /api/v1/watches/{id}` - Update watch
- `DELETE /api/v1/watches/{id}` - Delete watch (cascades to images)

### Images (NEW - Phase 3)
- `POST /api/v1/watches/{watch_id}/images` - Upload image
- `GET /api/v1/watches/{watch_id}/images` - List watch images
- `PATCH /api/v1/watches/{watch_id}/images/{image_id}` - Update metadata
- `DELETE /api/v1/watches/{watch_id}/images/{image_id}` - Delete image

**Image URLs**: `/uploads/{watch_id}/{filename}` (served by Nginx)

---

## Testing Credentials

**Test User** (created during Phase 3 testing):
- Email: `imagetest@example.com`
- Password: `testpass123`

**Test Watch** (has 2 uploaded images):
- Watch ID: `f98edb57-b35c-4b7e-846f-b04bd95ceb75`
- Model: "Test Model"
- Brand: Rolex
- Images: test_img1.jpg, test_img2.jpg (600x400px)

---

## Key Technical Details

### Image Upload System

**File Validation**:
- Allowed types: JPG, PNG, GIF, WebP
- Max size: 20MB (configurable via `MAX_UPLOAD_SIZE`)
- Client-side validation in ImageUpload component
- Server-side validation in file_upload.py

**Storage Structure**:
```
/app/storage/uploads/
  ├── {watch_id_1}/
  │   ├── image1.jpg
  │   └── image2.png
  └── {watch_id_2}/
      └── image.jpg
```

**Image Metadata**:
- File path (relative to upload dir)
- File name (sanitized to prevent attacks)
- File size (bytes)
- MIME type
- Dimensions (width/height extracted via Pillow)
- Primary flag (boolean)
- Sort order (integer)
- Source (user_upload, google_images, url_import)

**Primary Image Logic**:
- First uploaded image automatically set as primary
- Only one primary image per watch
- Setting new primary automatically unsets previous
- Deleting primary auto-promotes next by sort_order

**Security**:
- Filename sanitization prevents directory traversal
- Watch ownership verified on all operations
- Files stored in isolated watch-specific directories
- Delete operations verify paths are within upload directory

### Database Enum Issue (Fixed)

**Problem**: SQLAlchemy enum was sending Python enum names (e.g., "USER_UPLOAD") instead of values ("user_upload").

**Solution**: Added `values_callable` to Enum column definition:
```python
source = Column(
    Enum(ImageSourceEnum, values_callable=lambda x: [e.value for e in x]),
    default=ImageSourceEnum.USER_UPLOAD,
    nullable=False
)
```

### Frontend State Management

**React Query** for server state:
- Automatic caching and refetching
- Optimistic updates
- Cache invalidation on mutations
- Loading/error states

**Image Hooks**:
- `useWatchImages(watchId)` - Fetch images
- `useUploadImage()` - Upload mutation
- `useUpdateImage()` - Update mutation (set primary)
- `useDeleteImage()` - Delete mutation

**Cache Invalidation Strategy**:
- After upload/delete: invalidate watch images, watch detail, and watch list
- Ensures primary image updates across all views

---

## Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Rebuild Specific Service
```bash
docker-compose build backend
docker-compose up -d backend

docker-compose build frontend
docker-compose up -d frontend
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### Database Access
```bash
docker-compose exec postgres psql -U watchuser -d watch_tracker
```

### Backend Shell
```bash
docker-compose exec backend bash
```

### Check Health
```bash
curl http://localhost:8080/health
```

---

## Common Development Tasks

### Run Database Migration
```bash
docker-compose exec backend alembic upgrade head
```

### Create New Migration
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Clear Frontend Build Cache
```bash
docker-compose build --no-cache frontend
```

### View Uploaded Images
```bash
ls -lh storage/uploads/{watch_id}/
```

### Test Image Upload (curl)
```bash
TOKEN="your_jwt_token"
WATCH_ID="watch_uuid"

curl -X POST "http://localhost:8080/api/v1/watches/$WATCH_ID/images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"
```

---

## Known Issues & Limitations

### Current Limitations (Future Enhancements)
1. **No Image Optimization**: Images stored as-is, no thumbnails or compression
2. **No Drag-to-Reorder**: Can't reorder images via drag-and-drop
3. **No Batch Operations**: Can't select multiple images for deletion
4. **No Image Editing**: No crop, rotate, or filters
5. **No Google Images Integration**: Schema supports it, not implemented

### Potential Improvements
- Add image thumbnails (100x100, 400x400) for faster loading
- Implement lazy loading for image gallery
- Add WebP conversion for smaller file sizes
- Add progress bar for large uploads
- Support for image captions/descriptions

---

## Next Steps (Phases 4-6)

### Phase 4: Service History & Maintenance Tracking
- Service records linked to watches
- Maintenance schedules and reminders
- Service cost tracking
- Service provider management

### Phase 5: Market Value Tracking & Analytics
- Manual market value updates
- Historical value tracking over time
- Price appreciation/depreciation analytics
- Collection value summaries
- Charts and graphs for trends

### Phase 6: Advanced Features
- PDF export of collection
- QR code generation for watches
- Google Images auto-fetch
- Advanced search and filtering
- Watch comparison views
- Public collection sharing (optional)

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
MAX_UPLOAD_SIZE=20971520  # 20MB in bytes

# Frontend
VITE_API_URL=/api

# Server
HTTP_PORT=8080
```

---

## Troubleshooting

### Backend Won't Start
1. Check logs: `docker-compose logs backend`
2. Verify database is healthy: `docker-compose ps`
3. Run migrations: `docker-compose exec backend alembic upgrade head`

### Frontend Build Errors
1. Rebuild with no cache: `docker-compose build --no-cache frontend`
2. Check package.json for missing dependencies
3. Verify TypeScript compilation: `docker-compose exec frontend npm run build`

### Images Not Accessible
1. Verify file exists: `ls storage/uploads/{watch_id}/`
2. Check Nginx configuration: `docker-compose exec nginx cat /etc/nginx/conf.d/default.conf`
3. Verify Nginx volume mount in docker-compose.yml
4. Test direct URL: `curl http://localhost:8080/uploads/{watch_id}/{filename}`

### Database Migration Issues
1. Check current revision: `docker-compose exec backend alembic current`
2. View history: `docker-compose exec backend alembic history`
3. Downgrade if needed: `docker-compose exec backend alembic downgrade -1`

### Token Expired Errors
- Access tokens expire after 30 minutes
- Frontend should auto-refresh using refresh token
- If refresh fails, user must log in again

---

## Testing

### Manual Testing Checklist (Phase 3)
- [ ] Upload image via drag-and-drop
- [ ] Upload multiple images at once
- [ ] Set image as primary
- [ ] Delete image
- [ ] View image in lightbox
- [ ] Navigate between images with arrow keys
- [ ] Verify primary image shows on watch card
- [ ] Test file validation (wrong type, too large)
- [ ] Verify physical file deletion

### API Testing (curl examples)
See "Test Image Upload" section above for curl commands.

### Browser Testing
1. Open http://localhost:8080
2. Register/login
3. Create a watch
4. Navigate to watch detail page
5. Upload images
6. Test all image management features

---

## Performance Considerations

### Current Performance
- Images loaded on-demand (not all at once)
- Nginx serves static files with caching headers
- React Query caches API responses
- Database queries use eager loading to avoid N+1

### Future Optimizations
- Implement image thumbnails for faster gallery loading
- Add pagination to image list (if >50 images)
- Implement CDN for image delivery
- Add image lazy loading with intersection observer
- Compress images on upload

---

## Security Checklist

### Implemented ✓
- [x] JWT authentication on all protected routes
- [x] Watch ownership verification
- [x] File type validation (MIME type + extension)
- [x] File size limits enforced
- [x] Filename sanitization (prevents directory traversal)
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS prevention (React escapes by default)
- [x] CORS configured for specific origins
- [x] Password hashing (bcrypt)

### To Consider Later
- [ ] Rate limiting on upload endpoint
- [ ] File virus scanning
- [ ] CSP headers
- [ ] HTTPS in production
- [ ] Image file content verification (not just extension)

---

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- Feature branches for new phases (optional)

### Commit Message Format
```
Brief summary line

Detailed description:
- Bullet points for changes
- Organized by component (Backend/Frontend)

Features:
- User-facing feature list

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Recent Commits
- `e0942bf` - Phase 3: Image upload and management
- `b16c7d5` - Phase 2: Core CRUD operations
- `a733703` - Configure HTTP port to 8080
- `9181e47` - Fix backend auth and DB compatibility

---

## Important Code Locations

### Backend
- **Main router registration**: `backend/app/main.py`
- **Authentication logic**: `backend/app/core/security.py`
- **Database models**: `backend/app/models/`
- **API schemas**: `backend/app/schemas/`
- **File upload utilities**: `backend/app/utils/file_upload.py`
- **Image endpoints**: `backend/app/api/v1/images.py`

### Frontend
- **API client**: `frontend/src/lib/api.ts`
- **Type definitions**: `frontend/src/types/index.ts`
- **React Query hooks**: `frontend/src/hooks/`
- **Reusable components**: `frontend/src/components/common/`
- **Watch components**: `frontend/src/components/watches/`
- **Pages**: `frontend/src/pages/`

### Infrastructure
- **Docker config**: `docker-compose.yml`
- **Nginx config**: `nginx/nginx.conf`
- **Database migrations**: `backend/alembic/versions/`

---

## Quick Reference

### Watch Image Fields
```typescript
interface WatchImage {
  id: string
  watch_id: string
  file_path: string          // "watch_id/filename.jpg"
  file_name: string          // "filename.jpg"
  file_size: number          // bytes
  mime_type: string          // "image/jpeg"
  width: number | null       // pixels
  height: number | null      // pixels
  is_primary: boolean        // only one true per watch
  sort_order: number         // display order
  source: 'user_upload' | 'google_images' | 'url_import'
  created_at: string         // ISO timestamp
  url: string                // "/uploads/watch_id/filename.jpg"
}
```

### API Response Format
```json
{
  "id": "uuid",
  "watch_id": "uuid",
  "file_path": "watch_id/image.jpg",
  "file_name": "image.jpg",
  "file_size": 20236,
  "mime_type": "image/jpeg",
  "width": 800,
  "height": 600,
  "is_primary": true,
  "sort_order": 0,
  "source": "user_upload",
  "created_at": "2026-01-28T00:00:00",
  "url": "/uploads/watch_id/image.jpg"
}
```

---

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React Query: https://tanstack.com/query/latest
- SQLAlchemy: https://www.sqlalchemy.org/
- Tailwind CSS: https://tailwindcss.com/
- Lucide Icons: https://lucide.dev/

### Repository
- GitHub: https://github.com/Homoney/watch_collection_tracker

---

## Session Summary (2026-01-27)

**What We Did**:
1. Implemented complete Phase 3 image upload and management
2. Created backend file upload utilities with security
3. Built image CRUD API endpoints
4. Added frontend components (upload, gallery, lightbox)
5. Integrated image management into watch detail page
6. Fixed database enum issue
7. Tested all functionality end-to-end
8. Committed and pushed to GitHub

**Files Created** (16 total):
- 3 backend files (images.py, watch_image.py, file_upload.py)
- 4 frontend components (ImageUpload, ImageGallery, ImageLightbox, useWatchImages)
- 9 modified files (watches.py, WatchCard, WatchDetailPage, types, api.ts, etc.)

**Test Results**: ✅ All tests passed
- Image upload: ✓
- File storage: ✓
- Primary image management: ✓
- Image deletion: ✓
- Nginx static serving: ✓
- Frontend build: ✓

**Ready for**: Phase 4 (Service History) or Phase 5 (Market Value Tracking)

---

**End of Context Document**
