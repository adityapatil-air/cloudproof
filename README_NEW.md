# ☁️ CloudProof - AWS Verified Activity Tracker

> **Prove your AWS hands-on experience with audit-backed activity visualization**

A production-ready full-stack application that tracks real AWS usage through CloudTrail logs and displays it as a GitHub-style contribution graph. Perfect for DevOps engineers and cloud practitioners to showcase verified cloud practice to recruiters.

![Tech Stack](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)
![AWS](https://img.shields.io/badge/AWS-CloudTrail-ff9900)

---

## 🎯 Problem Statement

Recruiters hiring DevOps/Cloud engineers face a challenge:
- ❌ Everyone claims "AWS hands-on experience"
- ❌ Certificates don't prove actual practice
- ❌ GitHub doesn't reflect cloud usage
- ❌ No standard way to verify real AWS activity

**CloudProof solves this** by providing:
> ✅ **Verified, audit-backed visualization of AWS hands-on activity**

---

## ✨ Features

### 🔐 Security First
- Cross-account IAM roles (no credentials stored)
- Temporary STS tokens with auto-expiration
- Read-only S3 access
- Privacy-focused (only aggregated data)

### 📊 Visualization
- GitHub-style contribution heatmap
- 365-day activity tracking
- Service-wise breakdown
- Recent activity feed

### ⚡ Performance
- Automated 30-minute sync cycles
- Batch processing for efficiency
- Database connection pooling
- Optimized queries with indexing

### 🛠️ Production Ready
- Comprehensive error handling
- Structured logging
- Health check endpoints
- Docker containerization
- Environment-based configuration

---

## 🏗️ Architecture

```
┌─────────────────┐
│  User AWS       │
│  Account        │
│  (CloudTrail)   │
└────────┬────────┘
         │ Logs to S3
         ▼
┌─────────────────┐
│  S3 Bucket      │
│  (CloudTrail    │
│   Logs)         │
└────────┬────────┘
         │ Cross-Account
         │ IAM Role
         ▼
┌─────────────────┐      ┌──────────────┐
│  CloudProof     │◄────►│  PostgreSQL  │
│  Backend        │      │  Database    │
│  (Python/Flask) │      └──────────────┘
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│  React          │
│  Frontend       │
│  (Dashboard)    │
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS Account (optional for testing)

### 1. Clone & Start

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

### 2. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Health**: http://localhost:5000/api/health

### 3. Create User & Generate Sample Data

```bash
# Windows
test-api.bat

# Linux/Mac
chmod +x test-api.sh
./test-api.sh
```

---

## 📦 Tech Stack

### Backend
- **Python 3.11** - Core language
- **Flask** - REST API framework
- **Boto3** - AWS SDK
- **psycopg2** - PostgreSQL driver
- **Schedule** - Job scheduling

### Frontend
- **React 18** - UI framework
- **Axios** - HTTP client
- **react-calendar-heatmap** - Contribution graph
- **CSS3** - GitHub-inspired styling

### Infrastructure
- **PostgreSQL 15** - Database
- **Docker** - Containerization
- **Docker Compose** - Orchestration

### AWS Services
- **CloudTrail** - Audit logging
- **S3** - Log storage
- **IAM** - Access management
- **STS** - Temporary credentials

---

## 📊 Tracked AWS Services

| Service | Actions Tracked | Max Score |
|---------|----------------|-----------|
| EC2 | RunInstances, Terminate, Stop, Start | 3 |
| S3 | CreateBucket, PutPolicy | 2 |
| IAM | CreateRole, CreateUser, AttachPolicy | 3 |
| VPC | CreateVpc, CreateSubnet, SecurityGroups | 3 |
| Lambda | CreateFunction, UpdateCode | 3 |
| RDS | CreateDBInstance, Modify | 4 |
| CloudFormation | CreateStack, UpdateStack | 5 |
| EKS | CreateCluster, CreateNodegroup | 5 |

---

## 🔧 API Endpoints

### Health Check
```http
GET /api/health
```

### User Management
```http
POST /api/users
GET /api/users
GET /api/users/{id}
```

### Activity Data
```http
GET /api/users/{id}/activity?days=365
```

**Response:**
```json
{
  "heatmap": {
    "2025-01-15": 12,
    "2025-01-16": 8
  },
  "services": {
    "EC2": 45,
    "S3": 23,
    "Lambda": 18
  },
  "recent_actions": [...],
  "total_score": 86
}
```

---

## 🗄️ Database Schema

### users
```sql
id, name, email, role_arn, created_at
```

### activity_logs
```sql
id, user_id, date, service, action, score, created_at
```

### daily_scores
```sql
id, user_id, date, total_score
```

### processing_state
```sql
id, user_id, last_processed_timestamp
```

---

## 🔐 AWS Setup

### Step 1: Enable CloudTrail
1. Go to AWS CloudTrail Console
2. Create trail for all regions
3. Create S3 bucket: `cloudtrail-logs-{user-id}`

### Step 2: Create IAM Role

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::CLOUDPROOF-ACCOUNT:root"
    },
    "Action": "sts:AssumeRole"
  }]
}
```

**Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/*"
    }
  ]
}
```

### Step 3: Register
Share your Role ARN with CloudProof platform.

---

## 🧪 Testing

### Generate Sample Data
```bash
docker-compose exec backend python generate_sample_data.py 1 90
```

### Test API
```bash
# Health check
curl http://localhost:5000/api/health

# Create user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","role_arn":"arn:..."}'

# Get activity
curl http://localhost:5000/api/users/1/activity
```

---

## 📈 Scoring Logic

### Ignored Actions (Score: 0)
- ConsoleLogin
- Describe*
- Get*
- List*
- Read-only queries

### Counted Actions
- **High Impact (3-5)**: Resource creation, infrastructure automation
- **Medium Impact (2)**: Configuration changes
- **Low Impact (1)**: Basic operations

### Anti-Abuse
- Daily score cap: 50 points
- Per-service daily cap: 20 points
- Session grouping
- Spam detection

---

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
```

### Production (AWS)

**Backend:**
- AWS ECS/EKS or EC2
- AWS Lambda + API Gateway (serverless)

**Frontend:**
- S3 + CloudFront
- Vercel / Netlify

**Database:**
- AWS RDS PostgreSQL (db.t3.micro)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 📁 Project Structure

```
cloud proof/
├── backend/
│   ├── app.py                 # Flask REST API
│   ├── database.py            # DB connection & queries
│   ├── ingestion.py           # CloudTrail processor
│   ├── scoring.py             # Event scoring engine
│   ├── scheduler.py           # Cron job scheduler
│   ├── generate_sample_data.py # Test data generator
│   ├── requirements.txt       # Python dependencies
│   ├── schema.sql             # Database schema
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── index.js           # Entry point
│   │   └── index.css          # GitHub-style CSS
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── iam-policy.json        # S3 access policy
│   └── trust-policy.json      # Cross-account trust
├── scripts/
│   └── setup-user.sh          # User onboarding script
├── docker-compose.yml         # Multi-container setup
├── start.bat / start.sh       # Quick start scripts
├── test-api.bat / test-api.sh # API test scripts
├── README.md                  # This file
├── DEPLOYMENT.md              # Deployment guide
└── PROJECT_SUMMARY.md         # Resume summary
```

---

## 🎓 Learning Outcomes

This project demonstrates:
- ✅ AWS service integration (CloudTrail, S3, IAM, STS)
- ✅ Secure cross-account access patterns
- ✅ REST API design and implementation
- ✅ Database design and optimization
- ✅ ETL pipeline development
- ✅ React frontend development
- ✅ Docker containerization
- ✅ Error handling and logging
- ✅ Production-ready code practices

---

## 💰 Cost Estimation

### AWS Free Tier
- CloudTrail: First trail free
- S3: 5GB free
- RDS: db.t3.micro 750 hours/month

### Beyond Free Tier
- RDS PostgreSQL: ~$15/month
- S3 Storage: ~$0.23/month
- **Total: ~$15-20/month**

---

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome!

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

---

## 📝 License

MIT License - See LICENSE file

---

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- Inspired by GitHub's contribution graph
- Built for the DevOps community
- Designed to help freshers prove their skills

---

## 📚 Additional Resources

- [AWS CloudTrail Documentation](https://docs.aws.amazon.com/cloudtrail/)
- [Cross-Account Access Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_common-scenarios_aws-accounts.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)

---

## ⭐ Star This Project

If this project helped you, please give it a star! It helps others discover it.

---

**Built with ❤️ for the DevOps Community**
