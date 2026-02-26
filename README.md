# 🚀 CloudProof — Verified AWS Hands-On Activity Tracker

A platform that tracks and visualizes **real AWS hands-on usage** using CloudTrail audit logs, providing recruiters with a **trusted signal of cloud practice** similar to GitHub's contribution graph.

---

## 🎯 Problem Statement

Recruiters hiring DevOps / Cloud freshers face a major issue:

* Everyone claims "AWS hands-on experience"
* Certificates do not prove practice
* GitHub does not reflect cloud usage
* No standard way to verify real AWS activity

**Solution:** Verified, audit-backed visualization of AWS hands-on activity.

---

## 🧠 Core Concept

CloudTrail logs record all AWS API actions. This system:

1. Reads CloudTrail logs securely
2. Filters meaningful actions
3. Converts them into activity scores
4. Displays a contribution-style heatmap

---

## 🏗️ System Architecture

```
User AWS Account
    |
    | CloudTrail logs AWS actions
    v
Private S3 Bucket (CloudTrail Logs)
    |
    | Cross-account IAM Role (Read-only)
    v
CloudProof Backend
    |
    | Log ingestion + processing
    v
Database (Aggregated Activity)
    |
    | REST API
    v
Frontend Portal (Contribution Graph)
```

---

## 🔐 Security Architecture

### Access Model

Uses AWS **Cross-Account IAM Role**:

* No IAM users
* No long-term credentials
* Temporary STS tokens
* Read-only access

### Data Privacy Rules

The system NEVER exposes:

* Raw CloudTrail logs
* AWS account credentials
* IP addresses
* Full audit metadata

Only stores:

* Service name
* Action type
* Date
* Derived score

---

## 🚀 Quick Start with Docker

### Prerequisites

* Docker Desktop installed and running
* Git (optional, for cloning)

### 1. Start the Application

```bash
# Windows
start.bat

# Or manually with Docker Compose
docker-compose up -d
```

This will start:
* PostgreSQL database (port 5432)
* Backend API (port 5000)
* Frontend UI (port 3000)

### 2. Configure AWS Credentials

Edit `backend/.env` with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### 3. Create a User

```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Your Name\",\"email\":\"your@email.com\",\"role_arn\":\"arn:aws:iam::123456789012:role/CloudProofRole\"}"
```

### 4. Generate Sample Data (Optional)

```bash
docker-compose exec backend python generate_sample_data.py
```

### 5. Access the Application

* Frontend: http://localhost:3000
* Backend API: http://localhost:5000
* Health Check: http://localhost:5000/api/health

---

## 📋 API Endpoints

### Health Check
```
GET /api/health
```

### Create User
```
POST /api/users
Body: {
  "name": "John Doe",
  "email": "john@example.com",
  "role_arn": "arn:aws:iam::123456789012:role/CloudProofRole"
}
```

### Get User Activity
```
GET /api/users/{id}/activity?days=365
```

Returns:
```json
{
  "heatmap": {
    "2026-02-01": 5,
    "2026-02-02": 2
  },
  "services": {
    "EC2": 20,
    "S3": 10
  },
  "recent_actions": [...]
}
```

### List All Users
```
GET /api/users
```

---

## 👤 AWS User Setup (One-Time)

### Step 1 — Enable CloudTrail

Enable CloudTrail with:
* Management events: Read + Write
* All regions
* Log destination: S3 bucket

### Step 2 — Create Private S3 Bucket

Bucket settings:
* Private access only
* No public ACL
* No website hosting

### Step 3 — Create IAM Role

**Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-cloudtrail-bucket",
        "arn:aws:s3:::your-cloudtrail-bucket/*"
      ]
    }
  ]
}
```

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::CLOUDPROOF_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

See `infrastructure/` folder for complete templates.

### Step 4 — Provide Role ARN

Share only the IAM Role ARN when creating your user profile.

---

## 🧮 Activity Scoring Logic

### Ignored Actions

These NEVER count:
* ConsoleLogin
* Describe*
* Get*
* List*
* Read-only queries

### Counted Actions

| Action Type | Score | Examples |
|------------|-------|----------|
| Resource Creation | 3-5 | RunInstances, CreateBucket, CreateVpc |
| Configuration | 2-3 | ModifyInstance, PutBucketPolicy |
| Infrastructure as Code | 5 | CloudFormation CreateStack |

### Anti-Abuse Rules

* Daily score caps
* Per-service limits
* Session grouping
* No scoring for repetitive spam

---

## 🗄️ Database Schema

### users
```sql
id          SERIAL PRIMARY KEY
name        VARCHAR(255)
email       VARCHAR(255) UNIQUE
role_arn    VARCHAR(255)
created_at  TIMESTAMP
```

### activity_logs
```sql
id          SERIAL PRIMARY KEY
user_id     INTEGER REFERENCES users(id)
date        DATE
service     VARCHAR(50)
action      VARCHAR(100)
score       INTEGER
```

### daily_scores
```sql
user_id     INTEGER REFERENCES users(id)
date        DATE
total_score INTEGER
PRIMARY KEY (user_id, date)
```

---

## 🛠️ Technology Stack

**Backend:**
* Python 3.11
* Flask
* PostgreSQL
* boto3 (AWS SDK)

**Frontend:**
* React
* JavaScript

**Infrastructure:**
* Docker & Docker Compose
* AWS CloudTrail
* AWS IAM

---

## 🔧 Development Commands

### View Logs
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
docker-compose restart
docker-compose restart backend
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Access Database
```bash
docker-compose exec postgres psql -U postgres -d cloudproof
```

---

## 📁 Project Structure

```
cloudproof/
├── backend/              # Flask API
│   ├── app.py           # Main API server
│   ├── database.py      # Database connection
│   ├── ingestion.py     # CloudTrail log processor
│   ├── scoring.py       # Activity scoring engine
│   ├── scheduler.py     # Cron job scheduler
│   ├── schema.sql       # Database schema
│   └── Dockerfile
├── frontend/            # React UI
│   ├── src/
│   │   ├── App.js      # Main component
│   │   └── index.js
│   └── Dockerfile
├── infrastructure/      # AWS IAM templates
│   ├── iam-policy.json
│   └── trust-policy.json
├── docker-compose.yml   # Docker orchestration
├── start.bat           # Quick start script
└── README.md           # This file
```

---

## ❌ What the System Does NOT Track

* SSH commands inside EC2
* OS-level activity
* Application logs
* User content data

Only AWS control-plane actions.

---

## 🎯 Target Users

**Primary:**
* DevOps freshers
* Cloud engineering students
* Bootcamp graduates

**Secondary:**
* Recruiters
* Training institutes

---

## ⚠️ Limitations

* Measures activity, not skill
* Cannot detect SSH-level actions
* Requires CloudTrail enabled

---

## 📜 Ethical Disclaimer

This system provides:

> A signal of verified cloud activity derived from audit logs.

It does NOT:
* Assess skill level
* Guarantee job performance

---

## 🔮 Future Enhancements

* Docker activity tracking
* Kubernetes audit integration
* Jenkins CI activity
* Recruiter dashboards
* Activity streak analytics

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**CloudProof** — Verify your cloud practice, not just your claims.
