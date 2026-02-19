#!/bin/bash

echo "========================================"
echo "CloudProof - API Test Script"
echo "========================================"
echo ""

echo "Testing Backend Health..."
curl -s http://localhost:5000/api/health
echo ""
echo ""

echo "Creating Test User..."
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@cloudproof.dev","role_arn":"arn:aws:iam::123456789012:role/CloudProofTestRole"}'
echo ""
echo ""

echo "Generating Sample Data..."
docker-compose exec -T backend python generate_sample_data.py 1 90
echo ""

echo "Fetching User Activity..."
curl -s http://localhost:5000/api/users/1/activity | python -m json.tool
echo ""
echo ""

echo "========================================"
echo "✅ Tests Complete!"
echo "========================================"
echo ""
echo "Open http://localhost:3000 to view the dashboard"
echo ""
