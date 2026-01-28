#!/bin/bash

echo "Checking frontend assets..."
echo ""

echo "1. List all files in /usr/share/nginx/html/assets:"
docker-compose exec frontend ls -lah /usr/share/nginx/html/assets/

echo ""
echo "2. Test asset loading from inside frontend:"
docker-compose exec frontend wget -q -O- http://localhost/assets/index-CptHi2a2.js 2>/dev/null | head -5

echo ""
echo "3. Test asset loading from nginx:"
docker-compose exec nginx wget -q -O- http://frontend/assets/index-CptHi2a2.js 2>/dev/null | head -5

echo ""
echo "4. Test asset loading from host:"
curl -s http://localhost/assets/index-CptHi2a2.js | head -5

echo ""
echo "5. Test CSS loading from host:"
curl -s http://localhost/assets/index-BjUkVnMX.css | head -5

echo ""
echo "6. Check browser console for errors:"
echo "Open http://localhost in your browser"
echo "Press F12 to open Developer Tools"
echo "Check the Console and Network tabs for 404 errors"
