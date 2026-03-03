import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import execute_query
from generate_sample_data import generate_sample_data

print("Setting up CloudProof database...")

# Create test user
try:
    execute_query(
        "INSERT INTO users (name, email, role_arn) VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING",
        ("Test User", "test@example.com", "arn:aws:iam::123456789012:role/TestRole")
    )
    print("[OK] User created")
except Exception as e:
    print(f"User creation: {e}")

# Get user ID
user = execute_query("SELECT id FROM users WHERE email = %s", ("test@example.com",), fetch=True)
if user:
    user_id = user[0]['id']
    print(f"[OK] User ID: {user_id}")
    
    # Generate sample data
    generate_sample_data(user_id, 90)
else:
    print("[ERROR] Failed to create user")
