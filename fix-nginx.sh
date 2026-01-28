#!/bin/bash

echo "========================================="
echo "Nginx Configuration Fix"
echo "========================================="
echo ""

echo "1. Checking current nginx config in container..."
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep -A 3 "server {" | head -15

echo ""
echo "2. Stopping nginx..."
docker-compose stop nginx

echo ""
echo "3. Removing nginx container..."
docker-compose rm -f nginx

echo ""
echo "4. Rebuilding nginx with NO CACHE..."
docker-compose build --no-cache nginx

echo ""
echo "5. Starting nginx..."
docker-compose up -d nginx

echo ""
echo "6. Waiting for nginx to start..."
sleep 3

echo ""
echo "7. Verifying new config..."
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep -A 3 "server {" | head -15

echo ""
echo "8. Testing from localhost..."
curl -s http://localhost/ | head -5

echo ""
echo "9. Testing from 192.168.50.162..."
curl -s http://192.168.50.162/ | head -5

echo ""
echo "10. Checking nginx error logs..."
docker-compose logs nginx 2>&1 | grep -i error | tail -10

echo ""
echo "Done!"
