#!/bin/bash

set -e

echo "🚀 Starting Web Research Assistant with Docker..."

if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file to add your API keys (optional but recommended)"
fi

if [ ! -d searxng-config ]; then
    echo "📁 Creating SearXNG configuration directory..."
    mkdir -p searxng-config
fi

if [ ! -f searxng-config/settings.yml ]; then
    echo "⚠️  Warning: searxng-config/settings.yml not found. SearXNG will use default settings."
    echo "   For optimal performance, copy the settings.yml from this repository."
fi

echo "🏗️  Building Docker images..."
docker-compose build

echo "🌐 Starting services..."
docker-compose up -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "   - SearXNG: http://localhost:2288"
echo "   - Web Research Assistant MCP: Running in container"
echo ""
echo "🔍 Check service status:"
echo "   docker-compose ps"
echo ""
echo "📋 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "🧪 Test SearXNG:"
echo "   curl 'http://localhost:2288/search?q=test&format=json'"
echo ""
