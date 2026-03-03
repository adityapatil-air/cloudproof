import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import execute_query
from load_sample_data import load_all_sample_logs

print("=" * 50)
print("Clear Database and Load Sample Data")
print("=" * 50)
print()

# Clear existing data
print("Clearing existing data...")
execute_query("DELETE FROM activity_logs")
execute_query("DELETE FROM daily_scores")
print("[OK] Database cleared")
print()

# Load sample data
print("Loading sample data from JSON files...")
print()
total = load_all_sample_logs()

print()
print("=" * 50)
print(f"[DONE] Loaded {total} activities from sample data")
print("=" * 50)
