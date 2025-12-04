#!/bin/bash

echo "🚀 Deploying AI Gateway locally with Docker Compose..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your API keys if needed."
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "🧹 Cleaning up old containers..."
docker-compose down -v

echo ""
echo "🏗️  Building containers..."
docker-compose build

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "📊 Service URLs:"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Frontend UI:    http://localhost:80"
echo "  • PostgreSQL:     localhost:5432"
echo "  • Redis:          localhost:6379"

echo ""
echo "📝 Useful Commands:"
echo "  • View logs:           docker-compose logs -f"
echo "  • View backend logs:   docker-compose logs -f backend"
echo "  • Stop services:       docker-compose down"
echo "  • Restart services:    docker-compose restart"
echo "  • Enter backend shell: docker-compose exec backend bash"

echo ""
echo "🧪 Test the API:"
echo "  curl http://localhost:8000/health"

echo ""
echo "✅ Deployment complete! Access the gateway at http://localhost:8000/docs"
