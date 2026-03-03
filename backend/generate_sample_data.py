import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import execute_query
from datetime import datetime, timedelta
import random
from scoring import SCORING_RULES

def generate_sample_data(user_id=1, days=90):
    """Generate sample activity data for testing the heatmap"""
    
    # Use actual services and actions from scoring system
    services_actions = {
        'EC2': list(SCORING_RULES['EC2'].keys()),
        'S3': list(SCORING_RULES['S3'].keys()),
        'IAM': list(SCORING_RULES['IAM'].keys()),
        'VPC': list(SCORING_RULES['VPC'].keys()),
        'LAMBDA': list(SCORING_RULES['LAMBDA'].keys()),
        'RDS': list(SCORING_RULES['RDS'].keys()),
        'CLOUDFORMATION': list(SCORING_RULES['CLOUDFORMATION'].keys()),
        'EKS': list(SCORING_RULES['EKS'].keys()),
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
                service = random.choice(list(services_actions.keys()))
                action = random.choice(services_actions[service])
                score = SCORING_RULES[service][action]
                
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
    
    print(f"[OK] Generated {total_activities} sample activities!")
    print(f"View at: http://localhost:3000")

if __name__ == '__main__':
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    
    generate_sample_data(user_id, days)
