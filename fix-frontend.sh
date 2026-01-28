#!/bin/bash

echo "========================================="
echo "Frontend Rebuild & Fix"
echo "========================================="
echo ""

echo "Step 1: Stop and remove frontend container..."
docker-compose stop frontend
docker-compose rm -f frontend

echo ""
echo "Step 2: Rebuild frontend with no cache (verbose)..."
docker-compose build --no-cache --progress=plain frontend

echo ""
echo "Step 3: Start frontend..."
docker-compose up -d frontend

echo ""
echo "Step 4: Wait for frontend to start..."
sleep 5

echo ""
echo "Step 5: Check if files were built..."
echo "Files in /usr/share/nginx/html:"
docker-compose exec frontend ls -lah /usr/share/nginx/html/

echo ""
echo "Step 6: Check if index.html exists and has content..."
docker-compose exec frontend cat /usr/share/nginx/html/index.html 2>/dev/null | head -20

echo ""
echo "Step 7: Test frontend internally..."
docker-compose exec frontend wget -q -O- http://localhost/ 2>/dev/null | head -10

echo ""
echo "Step 8: Restart nginx to pick up any changes..."
docker-compose restart nginx

echo ""
echo "Step 9: Test from host..."
sleep 2
curl -s http://localhost/ | head -20

echo ""
echo "Done!"
