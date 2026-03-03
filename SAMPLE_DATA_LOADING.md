# 📥 Sample Data Loading Feature

## Overview
Load real CloudTrail JSON data into CloudProof instead of generating random data.

---

## Usage

### **Load All Sample Files**
```bash
cd backend
python load_sample_data.py
```
This loads all `.json` files from `sample_logs/` directory.

### **Load Specific File**
```bash
python load_sample_data.py path/to/cloudtrail.json
```

### **Load for Specific User**
```bash
python load_sample_data.py path/to/cloudtrail.json 2
```

---

## Sample Data Format

Place CloudTrail JSON files in `backend/sample_logs/`:

```json
{
  "Records": [
    {
      "eventTime": "2026-03-01T10:15:30Z",
      "eventSource": "ec2.amazonaws.com",
      "eventName": "RunInstances",
      "readOnly": false,
      "userIdentity": {
        "type": "IAMUser",
        "userName": "dev-user"
      }
    }
  ]
}
```

---

## Features

✅ **Automatic Scoring** - Uses production scoring system  
✅ **Skip Read-Only** - Ignores Describe/Get/List actions  
✅ **Daily Aggregation** - Automatically updates daily_scores  
✅ **Multiple Files** - Loads all JSON files in directory  
✅ **Error Handling** - Continues on errors, shows summary  

---

## Examples

### **Example 1: Load Recent Activity**
```bash
# Create file: sample_logs/march_2026.json
python load_sample_data.py
```

### **Example 2: Load Historical Data**
```bash
# Download CloudTrail logs from AWS
aws cloudtrail lookup-events --max-results 100 > sample_logs/my_activity.json
python load_sample_data.py
```

### **Example 3: Test Scoring System**
```bash
# Create test file with specific actions
python load_sample_data.py sample_logs/test_data.json
```

---

## Output

```
Found 2 JSON file(s) in sample_logs/

Loading sample data from: sample_data_march.json
  [OK] 2026-02-28 | EC2 | RunInstances | +5 points
  [OK] 2026-02-28 | S3 | CreateBucket | +4 points
  [OK] 2026-03-01 | RDS | CreateDBInstance | +9 points

[OK] Loaded 8 activities from sample data
[OK] Updated 3 days
```

---

## Comparison

| Feature | generate_sample_data.py | load_sample_data.py |
|---------|------------------------|---------------------|
| Data Source | Random generation | Real CloudTrail JSON |
| Dates | Random 90 days | Actual event dates |
| Actions | Random selection | Real AWS actions |
| Use Case | Testing/Demo | Real data import |

---

## Tips

1. **Get Real Data**: Download from AWS CloudTrail console
2. **Multiple Days**: Create separate JSON files for different dates
3. **Test Scoring**: Use to verify scoring system works correctly
4. **Incremental Load**: Run multiple times to add more data

---

**Now you can use REAL CloudTrail data instead of fake generated data!** 🎯
