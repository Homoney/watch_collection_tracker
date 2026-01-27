#!/bin/bash

echo "========================================="
echo "Watch Collection Tracker - Setup Script"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env

    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -hex 32)

    # Update the .env file with the generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/changeme_long_random_secret_key_at_least_32_characters/$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/changeme_long_random_secret_key_at_least_32_characters/$SECRET_KEY/" .env
    fi

    echo "✓ Created .env file with generated secret key"
    echo ""
    echo "IMPORTANT: Please edit .env and update the following:"
    echo "  - POSTGRES_PASSWORD (set a secure password)"
    echo ""
    read -p "Press Enter to continue after updating .env..."
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Building and starting services..."
docker-compose up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if backend is healthy
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost/health &> /dev/null; then
        echo "✓ Backend is healthy"
        break
    fi

    if [ $i -eq 30 ]; then
        echo "⚠ Backend health check failed. Check logs with: docker-compose logs backend"
    fi

    sleep 2
done

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Your Watch Collection Tracker is ready!"
echo ""
echo "Access the application:"
echo "  Frontend:    http://localhost"
echo "  API Docs:    http://localhost/api/docs"
echo "  Health:      http://localhost/health"
echo ""
echo "Useful commands:"
echo "  View logs:         docker-compose logs -f"
echo "  Stop services:     docker-compose down"
echo "  Restart services:  docker-compose restart"
echo "  View status:       docker-compose ps"
echo ""
echo "Next steps:"
echo "  1. Visit http://localhost"
echo "  2. Click 'Sign up' to create your account"
echo "  3. Start tracking your watch collection!"
echo ""
