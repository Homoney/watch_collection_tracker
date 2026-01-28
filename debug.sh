#!/bin/bash

echo "========================================="
echo "COMPREHENSIVE DIAGNOSTICS"
echo "========================================="
echo ""

echo "1. CONTAINER STATUS:"
echo "-------------------"
docker-compose ps
echo ""

echo "2. CHECK FRONTEND BUILD:"
echo "------------------------"
echo "Checking if frontend has built files..."
docker-compose exec frontend ls -la /usr/share/nginx/html/ 2>/dev/null || echo "Frontend container not accessible"
echo ""

echo "3. CHECK FRONTEND INTERNALLY:"
echo "-----------------------------"
echo "Testing frontend container from inside:"
docker-compose exec frontend wget -q -O- http://localhost/ 2>/dev/null | head -20 || echo "Frontend not responding"
echo ""

echo "4. CHECK BACKEND INTERNALLY:"
echo "----------------------------"
echo "Testing backend container from inside:"
docker-compose exec backend curl -s http://localhost:8000/health || echo "Backend not responding"
echo ""

echo "5. NGINX ACCESS TO FRONTEND:"
echo "----------------------------"
echo "Testing if nginx can reach frontend:"
docker-compose exec nginx wget -q -O- http://frontend/ 2>/dev/null | head -20 || echo "Nginx cannot reach frontend"
echo ""

echo "6. NGINX ACCESS TO BACKEND:"
echo "---------------------------"
echo "Testing if nginx can reach backend:"
docker-compose exec nginx wget -q -O- http://backend:8000/health 2>/dev/null || echo "Nginx cannot reach backend"
echo ""

echo "7. EXTERNAL ACCESS:"
echo "-------------------"
echo "Testing from host machine:"
curl -s http://localhost/ | head -20 || echo "No response from localhost"
echo ""

echo "8. NGINX LOGS (last 30 lines):"
echo "-------------------------------"
docker-compose logs --tail=30 nginx
echo ""

echo "9. FRONTEND LOGS (last 30 lines):"
echo "----------------------------------"
docker-compose logs --tail=30 frontend
echo ""

echo "10. BACKEND LOGS (last 30 lines):"
echo "----------------------------------"
docker-compose logs --tail=30 backend
echo ""

echo "11. NETWORK CONNECTIVITY:"
echo "-------------------------"
docker network inspect watch-collection-tracker_watch-tracker-network | grep -A 5 "Containers" || echo "Network not found"
echo ""
