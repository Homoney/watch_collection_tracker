# Watch Collection Tracker - Docker Hub Deployment

This guide explains how to deploy the Watch Collection Tracker using pre-built images from Docker Hub.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 2GB of free disk space
- Ports 8080 available (or configure a different port)

### Installation

1. **Download the docker-compose file**:
   ```bash
   curl -O https://raw.githubusercontent.com/Homoney/watch_collection_tracker/main/docker-compose.hub.yml
   curl -O https://raw.githubusercontent.com/Homoney/watch_collection_tracker/main/.env.example
   curl -O https://raw.githubusercontent.com/Homoney/watch_collection_tracker/main/nginx/nginx.conf
   mkdir -p nginx && mv nginx.conf nginx/
   ```

2. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set required values**:
   ```bash
   nano .env  # or use your preferred editor
   ```

   **Required changes**:
   - `POSTGRES_PASSWORD`: Set a secure password
   - `SECRET_KEY`: Generate a secure key (32+ characters)

   **Optional changes**:
   - `HTTP_PORT`: Change if 8080 is already in use
   - `VERSION`: Specify a version tag (default: latest)

4. **Generate a secure SECRET_KEY** (if needed):
   ```bash
   # Using OpenSSL
   openssl rand -hex 32

   # Using Python
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **Create storage directory**:
   ```bash
   mkdir -p storage/uploads
   ```

6. **Start the application**:
   ```bash
   docker-compose -f docker-compose.hub.yml up -d
   ```

7. **Check the status**:
   ```bash
   docker-compose -f docker-compose.hub.yml ps
   ```

8. **Access the application**:
   - Web UI: http://localhost:8080
   - API: http://localhost:8080/api
   - Health: http://localhost:8080/health

### First Time Setup

1. Open http://localhost:8080
2. Click "Register" to create your account
3. The first user to register automatically becomes an admin

## Available Images

- **Backend**: `dhomoney/watch-tracker-backend`
- **Frontend**: `dhomoney/watch-tracker-frontend`

### Tags
- `latest`: Latest stable release from main branch
- `v1.0.0`, `v1.0`, `v1`: Semantic version tags
- `main`: Latest commit to main branch

### Supported Architectures
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | watch_tracker | Database name |
| `POSTGRES_USER` | watchuser | Database user |
| `POSTGRES_PASSWORD` | *required* | Database password |
| `SECRET_KEY` | *required* | JWT secret key (32+ chars) |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `ALLOWED_ORIGINS` | http://localhost:3000 | CORS origins |
| `MAX_UPLOAD_SIZE` | 20971520 | Max upload size (20MB) |
| `HTTP_PORT` | 8080 | HTTP port to expose |
| `VERSION` | latest | Docker image version tag |

### Using a Specific Version

To use a specific version, set the `VERSION` environment variable:

```bash
# In .env file
VERSION=v1.0.0
```

Or specify inline:
```bash
VERSION=v1.0.0 docker-compose -f docker-compose.hub.yml up -d
```

## Upgrading

To upgrade to a new version:

1. **Pull the latest images**:
   ```bash
   docker-compose -f docker-compose.hub.yml pull
   ```

2. **Restart the services**:
   ```bash
   docker-compose -f docker-compose.hub.yml up -d
   ```

3. **Database migrations** are applied automatically on startup.

## Backup and Restore

### Backup Database
```bash
docker-compose -f docker-compose.hub.yml exec postgres pg_dump -U watchuser watch_tracker > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose -f docker-compose.hub.yml exec -T postgres psql -U watchuser watch_tracker
```

### Backup Uploads
```bash
tar -czf uploads_backup.tar.gz storage/uploads/
```

## Troubleshooting

### View Logs
```bash
# All services
docker-compose -f docker-compose.hub.yml logs -f

# Specific service
docker-compose -f docker-compose.hub.yml logs -f backend
```

### Check Service Health
```bash
curl http://localhost:8080/health
```

### Reset Everything
```bash
docker-compose -f docker-compose.hub.yml down -v
rm -rf storage/uploads/*
docker-compose -f docker-compose.hub.yml up -d
```

### Common Issues

**Port 8080 already in use**:
- Change `HTTP_PORT` in `.env` to a different port

**502 Bad Gateway**:
- Wait 30 seconds for services to start
- Check backend health: `docker-compose -f docker-compose.hub.yml logs backend`

**Images not loading**:
- Ensure `storage/uploads` directory exists and has proper permissions
- Check nginx logs: `docker-compose -f docker-compose.hub.yml logs nginx`

## Production Deployment

For production, consider:

1. **Use HTTPS**: Put nginx behind a reverse proxy (Traefik, Caddy, etc.)
2. **Secure secrets**: Use Docker secrets or a secrets manager
3. **Database backups**: Set up automated backups
4. **Resource limits**: Add resource constraints to docker-compose
5. **Monitoring**: Set up health checks and monitoring
6. **Volumes**: Use named volumes or external storage for data

See `docker-compose.prod.yml` in the repository for a production-ready example.

## Support

- **Documentation**: https://github.com/Homoney/watch_collection_tracker
- **Issues**: https://github.com/Homoney/watch_collection_tracker/issues
- **Discussions**: https://github.com/Homoney/watch_collection_tracker/discussions

## License

See LICENSE file in the repository.
