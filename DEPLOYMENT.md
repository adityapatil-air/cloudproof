# 🚀 CloudProof - Deployment Guide

## Prerequisites

- Docker & Docker Compose
- AWS Account with CloudTrail enabled
- PostgreSQL (or use Docker)
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

---

## Quick Start (Docker)

### 1. Clone and Setup

```bash
cd "cloud proof"
cp backend/.env.example backend/.env
```

### 2. Configure Environment

Edit `backend/.env`:

```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=cloudproof
DB_USER=postgres
DB_PASSWORD=your_secure_password

AWS_REGION=us-east-1
CLOUDPROOF_ACCOUNT_ID=your_aws_account_id
```

### 3. Start Services

```bash
docker-compose up -d
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- PostgreSQL: localhost:5432

### 4. Initialize Database

```bash
docker-compose exec postgres psql -U postgres -d cloudproof -f /docker-entrypoint-initdb.d/schema.sql
```

### 5. Create First User

```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Name",
    "email": "your.email@example.com",
    "role_arn": "arn:aws:iam::ACCOUNT_ID:role/CloudProofAccessRole"
  }'
```

---

## Local Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## AWS Setup for Users

### Step 1: Enable CloudTrail

1. Go to AWS CloudTrail Console
2. Create a trail
3. Enable for all regions
4. Create new S3 bucket: `cloudtrail-logs-YOUR-USER-ID`

### Step 2: Create IAM Role

```bash
cd scripts
chmod +x setup-user.sh
./setup-user.sh
```

Or manually:

1. Create IAM Role: `CloudProofAccessRole`
2. Attach trust policy from `infrastructure/trust-policy.json`
3. Attach permissions from `infrastructure/iam-policy.json`
4. Note the Role ARN

### Step 3: Register with CloudProof

Share your Role ARN with the CloudProof platform.

---

## API Endpoints

### Health Check
```
GET /api/health
```

### Create User
```
POST /api/users
Body: {
  "name": "string",
  "email": "string",
  "role_arn": "string"
}
```

### Get User Activity
```
GET /api/users/{id}/activity?days=365
```

### Get User Details
```
GET /api/users/{id}
```

### List All Users
```
GET /api/users
```

---

## Running the Ingestion Scheduler

### With Docker

```bash
docker-compose exec backend python scheduler.py
```

### Standalone

```bash
cd backend
python scheduler.py
```

The scheduler runs every 30 minutes automatically.

---

## Production Deployment

### AWS Lambda Deployment

1. Package backend code
2. Create Lambda function with Python 3.11 runtime
3. Set environment variables
4. Configure EventBridge rule for scheduling
5. Attach IAM role with RDS and STS permissions

### Frontend Deployment

#### Option 1: AWS S3 + CloudFront

```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-bucket-name
```

#### Option 2: Vercel/Netlify

```bash
cd frontend
npm run build
# Deploy build folder
```

### Database

Use AWS RDS PostgreSQL:
- Instance type: db.t3.micro (free tier)
- Enable automated backups
- Set up security groups
- Update backend .env with RDS endpoint

---

## Monitoring & Logs

### View Backend Logs

```bash
docker-compose logs -f backend
```

### View Scheduler Logs

```bash
docker-compose logs -f backend | grep scheduler
```

### Database Queries

```bash
docker-compose exec postgres psql -U postgres -d cloudproof
```

Useful queries:

```sql
-- Check user count
SELECT COUNT(*) FROM users;

-- Check total activities
SELECT COUNT(*) FROM activity_logs;

-- Top services
SELECT service, SUM(score) as total 
FROM activity_logs 
GROUP BY service 
ORDER BY total DESC;
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres
```

### AWS Permission Errors

- Verify IAM role trust policy
- Check S3 bucket permissions
- Ensure CloudTrail is logging to correct bucket

### Frontend Not Loading Data

- Check backend is running: `curl http://localhost:5000/api/health`
- Verify CORS settings in backend
- Check browser console for errors

---

## Security Best Practices

1. **Never commit .env files**
2. **Use strong database passwords**
3. **Enable SSL for production**
4. **Rotate AWS credentials regularly**
5. **Use AWS Secrets Manager for production**
6. **Enable CloudTrail log file validation**
7. **Set up CloudWatch alarms**

---

## Backup & Recovery

### Backup Database

```bash
docker-compose exec postgres pg_dump -U postgres cloudproof > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U postgres cloudproof < backup.sql
```

---

## Performance Optimization

1. **Database Indexing**: Already configured in schema.sql
2. **Caching**: Add Redis for API responses
3. **CDN**: Use CloudFront for frontend
4. **Connection Pooling**: Implemented in database.py
5. **Batch Processing**: Implemented in ingestion.py

---

## Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Create test user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","role_arn":"arn:aws:iam::123456789012:role/TestRole"}'

# Get user activity
curl http://localhost:5000/api/users/1/activity
```

---

## Scaling Considerations

### Horizontal Scaling

- Use AWS ECS/EKS for container orchestration
- Add Application Load Balancer
- Use RDS Read Replicas

### Vertical Scaling

- Increase container resources in docker-compose.yml
- Upgrade RDS instance type
- Add more worker processes

---

## Cost Estimation

### AWS Free Tier
- CloudTrail: First trail free
- S3: 5GB free
- RDS: db.t3.micro 750 hours/month

### Estimated Monthly Cost (Beyond Free Tier)
- RDS PostgreSQL (db.t3.micro): ~$15
- S3 Storage (10GB): ~$0.23
- CloudTrail: Free (first trail)
- Lambda (if used): ~$0.20
- **Total: ~$15-20/month**

---

## Support & Contribution

For issues and contributions, please refer to the main README.md

---

## License

MIT License - See LICENSE file for details
