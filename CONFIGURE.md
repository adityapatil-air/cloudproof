# CloudProof - Quick Configuration Guide

## 🚀 One-Command Setup

```cmd
configure.bat
```

This will:
1. Install Python dependencies
2. Install Node.js dependencies
3. Create PostgreSQL database
4. Run database schema
5. Generate sample data

Then start the app:
```cmd
start-local.bat
```

---

## 📋 Step-by-Step (Manual)

### 1. Verify Prerequisites
```cmd
verify.bat
```

### 2. Install Dependencies
```cmd
setup-local.bat
```

### 3. Setup Database
```cmd
psql -U postgres -c "CREATE DATABASE cloudproof;"
psql -U postgres -d cloudproof -f backend\schema.sql
```

### 4. Generate Sample Data
```cmd
cd backend
python generate_sample_data.py
cd ..
```

### 5. Start Services
```cmd
start-local.bat
```

---

## 🔧 Configuration Files

- `backend\.env` - Database and AWS settings (already created)
- Default PostgreSQL password: `postgres`
- Change in `backend\.env` if different

---

## 🌐 Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Health Check: http://localhost:5000/api/health

---

## ✅ What's Configured

- ✅ Backend `.env` file
- ✅ PostgreSQL connection settings
- ✅ Flask API endpoints
- ✅ React frontend
- ✅ Sample data generator

---

## 🔍 Troubleshooting

**PostgreSQL connection fails?**
- Update `DB_PASSWORD` in `backend\.env`
- Ensure PostgreSQL service is running

**Port already in use?**
- Backend: Change port in `backend\app.py`
- Frontend: Set `PORT=3001` before `npm start`

**Dependencies fail?**
- Python: `pip install --upgrade pip`
- Node: `npm cache clean --force`

---

**Ready to go!** Run `configure.bat` to set everything up.
