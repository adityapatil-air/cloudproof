#!/bin/bash

echo "========================================"
echo "CloudProof - Quick Start Script"
echo "========================================"
echo ""

echo "[1/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Please install Docker and try again"
    exit 1
fi
echo "✓ Docker is installed"

echo ""
echo "[2/5] Creating environment file..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env - Please edit with your AWS credentials"
else
    echo "✓ backend/.env already exists"
fi

echo ""
echo "[3/5] Starting services with Docker Compose..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start services"
    exit 1
fi
echo "✓ Services started"

echo ""
echo "[4/5] Waiting for database to be ready..."
sleep 10
echo "✓ Database should be ready"

echo ""
echo "[5/5] Initializing database schema..."
docker-compose exec -T postgres psql -U postgres -d cloudproof < backend/schema.sql
if [ $? -ne 0 ]; then
    echo "WARNING: Database initialization may have failed"
    echo "You may need to run it manually"
fi

echo ""
echo "========================================"
echo "✅ CloudProof is ready!"
echo "========================================"
echo ""
echo "Services running at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:5000"
echo "  Database: localhost:5432"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your AWS credentials"
echo "2. Create a user:"
echo "   curl -X POST http://localhost:5000/api/users -H 'Content-Type: application/json' -d '{\"name\":\"Your Name\",\"email\":\"your@email.com\",\"role_arn\":\"your-role-arn\"}'"
echo "3. Generate sample data:"
echo "   docker-compose exec backend python generate_sample_data.py"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo ""
