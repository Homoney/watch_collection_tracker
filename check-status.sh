#!/bin/bash

echo "========================================="
echo "Watch Collection Tracker - Status Check"
echo "========================================="
echo ""

echo "Container Status:"
docker-compose ps
echo ""

echo "----------------------------------------"
echo "Testing Endpoints:"
echo "----------------------------------------"
echo ""

echo "1. Nginx (main entry point):"
curl -s -o /dev/null -w "   http://localhost/ -> HTTP %{http_code}\n" http://localhost/ || echo "   FAILED"

echo "2. Nginx health:"
curl -s -o /dev/null -w "   http://localhost/health -> HTTP %{http_code}\n" http://localhost/health || echo "   FAILED"

echo "3. Backend API (direct):"
docker-compose exec -T backend curl -s -o /dev/null -w "   http://localhost:8000/health -> HTTP %{http_code}\n" http://localhost:8000/health 2>/dev/null || echo "   FAILED"

echo "4. Backend API (via nginx):"
curl -s -o /dev/null -w "   http://localhost/api/v1/auth/me -> HTTP %{http_code}\n" http://localhost/api/v1/auth/me || echo "   FAILED"

echo "5. Frontend (direct):"
docker-compose exec -T frontend wget -q -O /dev/null --server-response http://localhost/ 2>&1 | grep "HTTP/" | awk '{print "   http://localhost/ (inside frontend) -> " $2}' || echo "   FAILED"

echo ""
echo "----------------------------------------"
echo "Recent Logs:"
echo "----------------------------------------"
echo ""
echo "=== NGINX ==="
docker-compose logs --tail=10 nginx
echo ""
echo "=== BACKEND ==="
docker-compose logs --tail=10 backend
echo ""
echo "=== FRONTEND ==="
docker-compose logs --tail=10 frontend
echo ""
