# 🚀 CloudProof - Local Development Setup

## Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/)

---

## Quick Start

### 1. Install Dependencies
```cmd
setup-local.bat
```

### 2. Setup Database
```cmd
# Create database
createdb -U postgres cloudproof

# Run schema
psql -U postgres -d cloudproof -f backend\schema.sql
```

### 3. Configure AWS (Optional)
Edit `backend\.env`:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

### 4. Start Services
```cmd
start-local.bat
```

This opens:
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

---

## Manual Start (Alternative)

### Terminal 1 - Backend
```cmd
cd backend
python app.py
```

### Terminal 2 - Frontend
```cmd
cd frontend
npm start
```

---

## Generate Sample Data

```cmd
cd backend
python generate_sample_data.py
```

Then open http://localhost:3000

---

## API Testing

### Health Check
```cmd
curl http://localhost:5000/api/health
```

### Create User
```cmd
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"role_arn\":\"arn:aws:iam::123456789012:role/TestRole\"}"
```

### Get Activity
```cmd
curl http://localhost:5000/api/users/1/activity
```

---

## Project Structure

```
cloudproof/
├── backend/
│   ├── app.py              # Flask API
│   ├── database.py         # DB connection
│   ├── ingestion.py        # CloudTrail processor
│   ├── scoring.py          # Activity scoring
│   ├── scheduler.py        # Cron job
│   ├── schema.sql          # Database schema
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js         # React app
│   │   └── index.js
│   └── package.json
├── infrastructure/
│   ├── iam-policy.json
│   └── trust-policy.json
├── setup-local.bat         # Install dependencies
├── start-local.bat         # Start services
└── README.md              # This file
```

---

## Current Status

### ✅ Working
- Flask API with all endpoints
- React frontend with heatmap
- PostgreSQL database
- Sample data generation
- Activity scoring logic

### ⚠️ Not Implemented Yet
- CloudTrail log ingestion (scheduler not running)
- S3 bucket configuration
- Automatic AWS activity processing

### 🎯 For Testing
Use `generate_sample_data.py` to create test data and view the heatmap.

---

## Next Steps

1. Test with sample data
2. Fix CloudTrail ingestion
3. Add S3 bucket configuration
4. Implement scheduler
5. Deploy to production

---

**Status: Local Development Ready**
