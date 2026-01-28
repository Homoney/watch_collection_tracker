#!/bin/bash

set -e

echo "========================================="
echo "Rebuilding Watch Collection Tracker"
echo "========================================="
echo ""

echo "Stopping existing containers..."
docker-compose down -v

echo ""
echo "Rebuilding and starting services..."
if docker-compose up -d --build; then
    echo "✓ Services started successfully"
else
    echo "✗ Failed to start services"
    echo ""
    echo "Checking logs for errors..."
    docker-compose logs
    exit 1
fi

echo ""
echo "Waiting for services to be ready (30 seconds)..."
for i in {1..30}; do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        echo "✓ Application is ready!"
        break
    fi

    if [ $i -eq 30 ]; then
        echo "⚠ Application not responding after 30 seconds"
        echo ""
        echo "Service status:"
        docker-compose ps
        echo ""
        echo "Backend logs:"
        docker-compose logs --tail=30 backend
        echo ""
        echo "Frontend logs:"
        docker-compose logs --tail=30 frontend
        echo ""
        echo "Nginx logs:"
        docker-compose logs --tail=30 nginx
        exit 1
    fi

    echo -n "."
    sleep 1
done

echo ""
echo ""
echo "========================================="
echo "✓ Application is running!"
echo "========================================="
echo ""
echo "Service status:"
docker-compose ps
echo ""
echo "Access the application:"
echo "  Frontend:    http://localhost"
echo "  API Docs:    http://localhost/api/docs"
echo "  Health:      http://localhost/health"
echo ""
echo "View logs:"
echo "  All:         docker-compose logs -f"
echo "  Backend:     docker-compose logs -f backend"
echo "  Frontend:    docker-compose logs -f frontend"
echo ""
