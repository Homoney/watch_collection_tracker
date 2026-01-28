#!/bin/bash

echo "========================================="
echo "FULL DIAGNOSTIC FROM 192.168.50.162"
echo "========================================="
echo ""

IP="192.168.50.162"

echo "1. Test main page HTML:"
echo "-----------------------"
curl -s http://$IP/ | head -30
echo ""

echo "2. Test if JavaScript bundle loads:"
echo "------------------------------------"
JS_FILE=$(curl -s http://$IP/ | grep -o '/assets/index-[^"]*\.js' | head -1)
if [ -n "$JS_FILE" ]; then
    echo "JavaScript file: $JS_FILE"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$IP$JS_FILE)
    echo "HTTP Status: $HTTP_CODE"
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ JavaScript loads successfully"
        curl -s http://$IP$JS_FILE | head -5
    else
        echo "✗ JavaScript failed to load"
    fi
else
    echo "✗ No JavaScript file found in HTML"
fi

echo ""
echo "3. Test if CSS bundle loads:"
echo "----------------------------"
CSS_FILE=$(curl -s http://$IP/ | grep -o '/assets/index-[^"]*\.css' | head -1)
if [ -n "$CSS_FILE" ]; then
    echo "CSS file: $CSS_FILE"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$IP$CSS_FILE)
    echo "HTTP Status: $HTTP_CODE"
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ CSS loads successfully"
    else
        echo "✗ CSS failed to load"
    fi
else
    echo "✗ No CSS file found in HTML"
fi

echo ""
echo "4. Test API endpoint:"
echo "---------------------"
curl -s http://$IP/api/v1/auth/me
echo ""

echo ""
echo "5. Check nginx access logs:"
echo "---------------------------"
docker-compose logs nginx 2>&1 | tail -20

echo ""
echo "========================================="
echo "MANUAL BROWSER TEST NEEDED:"
echo "========================================="
echo ""
echo "Please do the following in your browser on the other machine:"
echo ""
echo "1. Open: http://$IP/"
echo "2. Press F12 to open Developer Tools"
echo "3. Go to Console tab - look for errors"
echo "4. Go to Network tab - refresh page"
echo "5. Look for any red/failed requests"
echo ""
echo "Tell me:"
echo "  - What color is the page background?"
echo "  - Do you see any styled content?"
echo "  - What's in the browser Console?"
echo "  - Are there any 404s in the Network tab?"
echo ""
