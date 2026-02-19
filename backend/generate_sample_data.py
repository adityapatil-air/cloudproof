import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import execute_query
from datetime import datetime, timedelta
import random

def generate_sample_data(user_id=1, days=90):
    """Generate sample activity data for testing the heatmap"""
    
    services = ['EC2', 'S3', 'IAM', 'VPC', 'Lambda', 'RDS', 'CloudFormation']
    actions = {
        'EC2': ['RunInstances', 'TerminateInstances', 'StopInstances'],
        'S3': ['CreateBucket', 'PutBucketPolicy'],
        'IAM': ['CreateRole', 'AttachRolePolicy'],
        'VPC': ['CreateVpc', 'CreateSubnet'],
        'Lambda': ['CreateFunction', 'UpdateFunctionCode'],
        'RDS': ['CreateDBInstance'],
        'CloudFormation': ['CreateStack', 'UpdateStack']
    }
    
    scores = {
        'RunInstances': 3,
        'TerminateInstances': 2,
        'StopInstances': 1,
        'CreateBucket': 2,
        'PutBucketPolicy': 2,
        'CreateRole': 2,
        'AttachRolePolicy': 2,
        'CreateVpc': 3,
        'CreateSubnet': 2,
        'CreateFunction': 3,
        'UpdateFunctionCode': 2,
        'CreateDBInstance': 4,
        'CreateStack': 5,
        'UpdateStack': 4
    }
    
    print(f"Generating {days} days of sample data for user {user_id}...")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    total_activities = 0
    
    while current_date <= end_date:
        # Random activity level (some days have more activity)
        if random.random() < 0.7:  # 70% chance of activity on any given day
            num_activities = random.randint(1, 5)
            
            for _ in range(num_activities):
                service = random.choice(services)
                action = random.choice(actions[service])
                score = scores[action]
                
                try:
                    execute_query(
                        "INSERT INTO activity_logs (user_id, date, service, action, score) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, current_date, service, action, score)
                    )
                    
                    execute_query(
                        """
                        INSERT INTO daily_scores (user_id, date, total_score) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, date) 
                        DO UPDATE SET total_score = daily_scores.total_score + EXCLUDED.total_score
                        """,
                        (user_id, current_date, score)
                    )
                    
                    total_activities += 1
                    
                except Exception as e:
                    print(f"Error inserting data: {e}")
        
        current_date += timedelta(days=1)
    
    print(f"✅ Generated {total_activities} sample activities!")
    print(f"View at: http://localhost:3000")

if __name__ == '__main__':
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    
    generate_sample_data(user_id, days)
