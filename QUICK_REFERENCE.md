# ⚡ CloudProof - Quick Reference Card

## 🚀 Quick Start Commands

### Start Everything
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### Generate Test Data
```bash
docker-compose exec backend python generate_sample_data.py 1 90
```

### Access Application
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Health: http://localhost:5000/api/health

---

## 🔧 Common Commands

### Docker Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Rebuild containers
docker-compose up -d --build
```

### Database Access
```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d cloudproof

# Check tables
docker-compose exec postgres psql -U postgres -d cloudproof -c "\dt"

# Count activities
docker-compose exec postgres psql -U postgres -d cloudproof -c "SELECT COUNT(*) FROM activity_logs;"
```

### API Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Create user
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"name\":\"Test\",\"email\":\"test@example.com\",\"role_arn\":\"arn:aws:iam::123456789012:role/TestRole\"}"

# Get activity
curl http://localhost:5000/api/users/1/activity

# List users
curl http://localhost:5000/api/users
```

---

## 📊 Project Structure

```
backend/     → Python Flask API
frontend/    → React Dashboard
infrastructure/ → AWS IAM policies
scripts/     → Setup scripts
*.md         → Documentation
```

---

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `README_NEW.md` | Main documentation |
| `DEPLOYMENT.md` | Deployment guide |
| `PROJECT_SUMMARY.md` | Resume summary |
| `VERIFICATION.md` | Testing checklist |
| `SETUP_COMPLETE.md` | Completion guide |
| `docker-compose.yml` | Container orchestration |
| `backend/app.py` | REST API |
| `frontend/src/App.js` | React app |

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Database Connection Failed
```bash
docker-compose restart postgres
docker-compose logs postgres
```

### Frontend Not Loading
```bash
docker-compose restart backend
curl http://localhost:5000/api/health
```

### Clear Everything and Restart
```bash
docker-compose down -v
docker-compose up -d --build
```

---

## 📝 Resume Bullet Point (Copy-Paste Ready)

**CloudProof - AWS Activity Tracker** | Personal Project | [GitHub Link]

Architected full-stack cloud-native application using Python Flask, React, and PostgreSQL to track AWS hands-on activity through CloudTrail audit logs, implementing secure cross-account IAM role authentication, automated ETL pipeline processing 50+ AWS event types, and GitHub-style contribution heatmap visualization across 8 AWS services.

**Tech**: Python, Flask, React, PostgreSQL, Docker, AWS (CloudTrail, S3, IAM, STS), Boto3

---

## 🎤 30-Second Elevator Pitch

"CloudProof is a full-stack application I built to solve a real problem - verifying AWS hands-on experience. It reads CloudTrail audit logs, processes them through a scoring engine, and displays activity as a GitHub-style heatmap. I used Python Flask for the backend, React for the frontend, PostgreSQL for data storage, and Docker for containerization. The security model uses cross-account IAM roles with temporary credentials, and the system processes logs in batches for efficiency."

---

## 📈 Project Stats

- **Lines of Code**: 2,000+
- **Technologies**: 10+
- **AWS Services**: 8
- **API Endpoints**: 5
- **Containers**: 3
- **Time to Build**: Portfolio-ready
- **Deployment**: One command

---

## ✅ Pre-Interview Checklist

- [ ] Can start project in under 1 minute
- [ ] Can demo heatmap with data
- [ ] Can explain architecture
- [ ] Can discuss security choices
- [ ] Can explain scaling strategy
- [ ] GitHub repo is public
- [ ] README is updated
- [ ] Resume includes project

---

## 🔗 Important URLs

- **Local Frontend**: http://localhost:3000
- **Local Backend**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health
- **GitHub Repo**: [Add your URL]
- **Live Demo**: [Optional - if deployed]

---

## 💡 Interview Questions You Can Answer

✅ "Tell me about a project you're proud of"
✅ "How do you handle AWS security?"
✅ "Explain your experience with Docker"
✅ "How would you scale this application?"
✅ "What's your experience with REST APIs?"
✅ "Tell me about a technical challenge you faced"
✅ "How do you ensure code quality?"
✅ "What's your experience with databases?"

---

## 🎯 Next Actions

1. ✅ Test locally (15 min)
2. ✅ Push to GitHub (10 min)
3. ✅ Update resume (10 min)
4. ✅ Practice demo (15 min)
5. ⭐ Optional: Deploy live (60 min)
6. 🚀 Start applying!

---

**Keep this card handy for quick reference!**
