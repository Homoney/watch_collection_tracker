#!/bin/bash

echo "========================================="
echo "Browser Compatibility Test"
echo "========================================="
echo ""

echo "1. Testing if assets are accessible:"
echo "------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/assets/index-CptHi2a2.js)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✓ JavaScript bundle: HTTP $HTTP_CODE (OK)"
else
    echo "✗ JavaScript bundle: HTTP $HTTP_CODE (FAILED)"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/assets/index-BjUkVnMX.css)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✓ CSS bundle: HTTP $HTTP_CODE (OK)"
else
    echo "✗ CSS bundle: HTTP $HTTP_CODE (FAILED)"
fi

echo ""
echo "2. Testing main page:"
echo "---------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$HTTP_CODE" == "200" ]; then
    echo "✓ Main page: HTTP $HTTP_CODE (OK)"
else
    echo "✗ Main page: HTTP $HTTP_CODE (FAILED)"
fi

echo ""
echo "3. Testing API endpoints:"
echo "-------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/auth/me)
echo "GET /api/v1/auth/me: HTTP $HTTP_CODE (expected 403 when not logged in)"

echo ""
echo "4. Creating test HTML file:"
echo "---------------------------"
cat > /tmp/test-watch-app.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Watch Tracker Test</title>
</head>
<body>
    <h1>Connection Test</h1>
    <p>If you see this, basic serving works!</p>
    <div id="results"></div>
    <script>
        console.log('Test page loaded successfully');

        // Test asset loading
        fetch('/assets/index-CptHi2a2.js')
            .then(r => {
                document.getElementById('results').innerHTML +=
                    `<p>✓ JavaScript asset: ${r.status}</p>`;
            })
            .catch(e => {
                document.getElementById('results').innerHTML +=
                    `<p>✗ JavaScript asset failed: ${e}</p>`;
            });

        fetch('/assets/index-BjUkVnMX.css')
            .then(r => {
                document.getElementById('results').innerHTML +=
                    `<p>✓ CSS asset: ${r.status}</p>`;
            })
            .catch(e => {
                document.getElementById('results').innerHTML +=
                    `<p>✗ CSS asset failed: ${e}</p>`;
            });
    </script>
</body>
</html>
EOF

echo "Test HTML created at /tmp/test-watch-app.html"
echo ""
echo "To use it:"
echo "1. Copy to container: docker cp /tmp/test-watch-app.html watch-tracker-frontend:/usr/share/nginx/html/test.html"
echo "2. Visit: http://localhost/test.html"
echo ""
echo "========================================="
echo "NEXT STEPS:"
echo "========================================="
echo ""
echo "Please open http://localhost in your browser and:"
echo "1. Press F12 to open Developer Tools"
echo "2. Go to the 'Console' tab"
echo "3. Refresh the page"
echo "4. Look for any red error messages"
echo "5. Go to the 'Network' tab"
echo "6. Refresh the page"
echo "7. Look for any red/failed requests"
echo ""
echo "Then report back what you see!"
echo ""
