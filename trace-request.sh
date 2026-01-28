#!/bin/bash

echo "========================================="
echo "Tracing Request Path"
echo "========================================="
echo ""

# Clear logs
docker-compose logs --tail=0 -f nginx > /tmp/nginx-trace.log 2>&1 &
TAIL_PID=$!

sleep 1

echo "Making request to 192.168.50.162..."
curl -v http://192.168.50.162/ 2>&1 | grep -E "^> |^< |^HTTP"

sleep 2

kill $TAIL_PID 2>/dev/null

echo ""
echo "Nginx access log:"
cat /tmp/nginx-trace.log

echo ""
echo "========================================="
echo "Testing Host Header Override"
echo "========================================="
echo ""

echo "Request with Host: localhost header:"
curl -H "Host: localhost" http://192.168.50.162/ | head -5

echo ""
echo "Request with Host: 192.168.50.162 header:"
curl -H "Host: 192.168.50.162" http://192.168.50.162/ | head -5

echo ""
echo "Request with no Host header (HTTP/1.0):"
curl -0 http://192.168.50.162/ | head -5

echo ""
echo "========================================="
echo "Check Frontend Container Response"
echo "========================================="
echo ""

echo "Direct request to frontend container:"
docker-compose exec nginx wget -q -O- http://frontend/ | head -5

echo ""
echo "Request to frontend with Host: 192.168.50.162:"
docker-compose exec nginx sh -c 'echo -e "GET / HTTP/1.1\r\nHost: 192.168.50.162\r\n\r" | nc frontend 80' | head -20
