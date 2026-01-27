# Watch Collection Tracker

A modern web application for watch collectors to track their collections with multi-user support, authentication, image management, service history, and market value tracking.

## Features

- **Multi-User Support**: Secure authentication with JWT tokens, isolated user data
- **Watch Management**: Track brand, model, reference numbers, purchase info, specifications
- **Image Management**: Multiple images per watch, auto-source from Google Images
- **Collections**: Organize watches into multiple collections (Current, Wishlist, Sold, etc.)
- **Search & Filter**: Advanced filtering by brand, price, movement type, complications
- **Statistics Dashboard**: Total value, average price, brand breakdown
- **Service History**: Track maintenance, costs, and schedule future services
- **Market Value Tracking**: Monitor watch values over time
- **Multi-Currency Support**: USD, EUR, GBP, CHF
- **Export & Backup**: Full database dumps and JSON exports
- **Dark Mode**: Complete theme support
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

### Backend
- **FastAPI** (Python 3.11+) - Modern async web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL 16** - Relational database
- **JWT Authentication** - Secure token-based auth
- **Pillow** - Image processing

### Frontend
- **React 18** + **TypeScript** - Modern UI framework
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first CSS
- **TanStack Query** - Data fetching and caching
- **React Router** - Client-side routing
- **React Hook Form** - Form management
- **Zustand** - Lightweight state management

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and static file serving
- **Let's Encrypt** - SSL/TLS certificates (optional)

## Project Structure

```
watch-collection-tracker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # Security, dependencies
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── contexts/      # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # API client, utilities
│   │   ├── pages/         # Page components
│   │   └── types/         # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── nginx/                  # Nginx reverse proxy
│   ├── Dockerfile
│   └── nginx.conf
├── storage/               # Persistent storage
│   ├── uploads/          # Watch images
│   └── backups/          # Export files
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd watch-collection-tracker
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Edit `.env` file**

Generate a secure secret key:
```bash
openssl rand -hex 32
```

Update the following in `.env`:
```
SECRET_KEY=<your-generated-secret-key>
POSTGRES_PASSWORD=<your-secure-password>
```

4. **Start the application**
```bash
docker-compose up -d
```

5. **Wait for services to be ready**
```bash
docker-compose logs -f
```

6. **Access the application**
- Frontend: http://localhost
- API Docs: http://localhost/api/docs
- Health Check: http://localhost/health

### First Time Setup

1. Visit http://localhost
2. Click "Sign up" to create your account
3. Start adding watches to your collection!

## Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Access Python shell with app context
python -c "from app.database import SessionLocal; db = SessionLocal()"
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend sh

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U watchuser -d watch_tracker

# Backup database
docker-compose exec postgres pg_dump -U watchuser watch_tracker > backup.sql

# Restore database
docker-compose exec -T postgres psql -U watchuser watch_tracker < backup.sql
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f nginx
```

## API Documentation

Once the application is running, visit http://localhost/api/docs for interactive API documentation powered by Swagger UI.

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/logout` - Logout

#### Collections (Coming in Phase 2)
- `GET /api/v1/collections` - List collections
- `POST /api/v1/collections` - Create collection
- `GET /api/v1/collections/:id` - Get collection details
- `PUT /api/v1/collections/:id` - Update collection
- `DELETE /api/v1/collections/:id` - Delete collection

#### Watches (Coming in Phase 2)
- `GET /api/v1/watches` - List watches with filters
- `POST /api/v1/watches` - Add new watch
- `GET /api/v1/watches/:id` - Get watch details
- `PUT /api/v1/watches/:id` - Update watch
- `DELETE /api/v1/watches/:id` - Delete watch

## Database Schema

### Core Tables
- **users** - User accounts and preferences
- **collections** - User-defined watch collections
- **watches** - Watch details and specifications
- **watch_images** - Multiple images per watch
- **service_history** - Maintenance records
- **service_documents** - Service receipts and documents
- **market_values** - Historical market value tracking

### Reference Tables (Pre-seeded)
- **brands** - Watch brands (Rolex, Omega, Seiko, etc.)
- **movement_types** - Movement types (Automatic, Hand-wound, Quartz, etc.)
- **complications** - Watch complications (Chronograph, GMT, Date, etc.)

## Security

- **Password Hashing**: bcrypt with 12 rounds
- **JWT Tokens**: 30-minute access tokens, 7-day refresh tokens
- **CORS**: Configured whitelist for allowed origins
- **Rate Limiting**: API endpoint rate limiting via Nginx
- **HTTPS**: SSL/TLS support (configure in production)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **Input Validation**: Pydantic schemas, file type/size validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## Production Deployment

### Prerequisites
- Domain name
- SSL certificate (Let's Encrypt recommended)
- Server with Docker and Docker Compose

### Steps

1. **Update environment variables**
```bash
ALLOWED_ORIGINS=https://yourdomain.com
VITE_API_URL=https://yourdomain.com/api
```

2. **Configure SSL in nginx**

Uncomment HTTPS configuration in `nginx/nginx.conf` and add SSL certificates to `./ssl/` directory.

3. **Build and deploy**
```bash
docker-compose -f docker-compose.yml up -d --build
```

4. **Set up automatic SSL renewal** (if using Let's Encrypt)
```bash
# Add cron job for certificate renewal
0 0 * * * docker-compose exec nginx nginx -s reload
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from app.database import engine; engine.connect()"

# Rebuild container
docker-compose up -d --build backend
```

### Frontend build fails
```bash
# Check Node version
docker-compose exec frontend node --version

# Clear node_modules and reinstall
docker-compose exec frontend rm -rf node_modules package-lock.json
docker-compose exec frontend npm install
```

### Database migration issues
```bash
# Check migration status
docker-compose exec backend alembic current

# Downgrade and re-upgrade
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

### Port conflicts
```bash
# Change ports in .env
HTTP_PORT=8080
FRONTEND_PORT=3001
BACKEND_PORT=8001

# Restart services
docker-compose down
docker-compose up -d
```

## Development Roadmap

### ✅ Phase 1: Foundation (COMPLETED)
- Project structure and Docker setup
- Authentication (register, login, JWT tokens)
- Basic frontend with login/register pages
- Database schema and migrations

### 🚧 Phase 2: Core CRUD (In Progress)
- Collection management
- Watch CRUD operations
- Watch list/grid with filters
- Watch detail page

### 📋 Phase 3: Images
- File upload and validation
- Image gallery component
- Google Images integration
- Image optimization

### 📋 Phase 4: Statistics
- Dashboard with charts
- Currency conversion
- Value tracking visualization
- Brand distribution

### 📋 Phase 5: Service History
- Service records management
- Document uploads
- Service reminders
- Timeline view

### 📋 Phase 6: Advanced Features
- Export (JSON, CSV, full backup)
- Social sharing
- Dark mode
- Mobile responsiveness

### 📋 Phase 7: Production Ready
- Unit and integration tests
- Security audit
- Performance optimization
- Documentation

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

MIT License - feel free to use this for your own watch collection tracking needs.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with FastAPI and React
- Inspired by the watch collecting community
- Database schema based on common watch specification standards
