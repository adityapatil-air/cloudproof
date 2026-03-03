import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import execute_query
from scoring import calculate_score
from datetime import datetime

def track_resource(user_id, service, event_name, record, event_time):
    """Track resource state for all services"""
    
    if service == 'EC2':
        if event_name == 'RunInstances':
            instances = record.get('responseElements', {}).get('instancesSet', {}).get('items', [])
            for instance in instances:
                instance_id = instance.get('instanceId')
                vpc_id = instance.get('vpcId')
                if instance_id:
                    execute_query(
                        "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, parent_resource_id, state, created_at, last_updated) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (user_id, 'EC2_INSTANCE', instance_id, vpc_id, 'running', event_time, event_time)
                    )
        elif event_name == 'TerminateInstances':
            instances = record.get('requestParameters', {}).get('instancesSet', {}).get('items', [])
            for instance in instances:
                instance_id = instance.get('instanceId')
                if instance_id:
                    # Get created_at to calculate runtime
                    result = execute_query(
                        "SELECT created_at FROM resource_state WHERE resource_id = %s AND user_id = %s",
                        (instance_id, user_id), fetch=True
                    )
                    runtime_hours = 0
                    if result:
                        created_at = result[0]['created_at']
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        runtime_hours = (event_time - created_at).total_seconds() / 3600
                    
                    execute_query(
                        "UPDATE resource_state SET state = %s, last_updated = %s, metadata = %s WHERE resource_id = %s AND user_id = %s",
                        ('terminated', event_time, f'Runtime: {runtime_hours:.1f}h', instance_id, user_id)
                    )
        elif event_name == 'CreateVpc':
            vpc_id = record.get('responseElements', {}).get('vpc', {}).get('vpcId')
            if vpc_id:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'VPC', vpc_id, 'available', event_time)
                )
        elif event_name == 'CreateSubnet':
            subnet = record.get('responseElements', {}).get('subnet', {})
            subnet_id = subnet.get('subnetId')
            vpc_id = subnet.get('vpcId')
            if subnet_id and vpc_id:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, parent_resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, 'SUBNET', subnet_id, vpc_id, 'available', event_time)
                )
        elif event_name == 'CreateRouteTable':
            route_table = record.get('responseElements', {}).get('routeTable', {})
            route_table_id = route_table.get('routeTableId')
            vpc_id = route_table.get('vpcId')
            if route_table_id and vpc_id:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, parent_resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, 'ROUTE_TABLE', route_table_id, vpc_id, 'available', event_time)
                )
        elif event_name == 'CreateInternetGateway':
            igw_id = record.get('responseElements', {}).get('internetGateway', {}).get('internetGatewayId')
            if igw_id:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'INTERNET_GATEWAY', igw_id, 'available', event_time)
                )
        elif event_name == 'AttachInternetGateway':
            igw_id = record.get('requestParameters', {}).get('internetGatewayId')
            vpc_id = record.get('requestParameters', {}).get('vpcId')
            if igw_id and vpc_id:
                execute_query(
                    "UPDATE resource_state SET parent_resource_id = %s WHERE resource_id = %s AND user_id = %s",
                    (vpc_id, igw_id, user_id)
                )
    
    elif service == 'S3':
        if event_name == 'CreateBucket':
            bucket_name = record.get('requestParameters', {}).get('bucketName')
            if bucket_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'S3_BUCKET', bucket_name, 'active', event_time)
                )
        elif event_name == 'DeleteBucket':
            bucket_name = record.get('requestParameters', {}).get('bucketName')
            if bucket_name:
                execute_query(
                    "UPDATE resource_state SET state = %s, last_updated = %s WHERE resource_id = %s AND user_id = %s",
                    ('deleted', event_time, bucket_name, user_id)
                )
    
    elif service == 'IAM':
        if event_name == 'CreateRole':
            role_name = record.get('requestParameters', {}).get('roleName')
            if role_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'IAM_ROLE', role_name, 'active', event_time)
                )
        elif event_name == 'CreateUser':
            user_name = record.get('requestParameters', {}).get('userName')
            if user_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'IAM_USER', user_name, 'active', event_time)
                )
        elif event_name == 'AttachRolePolicy':
            role_name = record.get('requestParameters', {}).get('roleName')
            policy_arn = record.get('requestParameters', {}).get('policyArn')
            if role_name and policy_arn:
                policy_name = policy_arn.split('/')[-1]
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, parent_resource_id, state, metadata, last_updated) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (user_id, 'IAM_POLICY_ATTACHMENT', f'{role_name}/{policy_name}', role_name, 'attached', policy_arn, event_time)
                )
    
    elif service == 'LAMBDA':
        if event_name == 'CreateFunction':
            function_name = record.get('requestParameters', {}).get('functionName')
            if function_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'LAMBDA_FUNCTION', function_name, 'active', event_time)
                )
        elif event_name == 'DeleteFunction':
            function_name = record.get('requestParameters', {}).get('functionName')
            if function_name:
                execute_query(
                    "UPDATE resource_state SET state = %s, last_updated = %s WHERE resource_id = %s AND user_id = %s",
                    ('deleted', event_time, function_name, user_id)
                )
    
    elif service == 'RDS':
        if event_name == 'CreateDBInstance':
            db_instance = record.get('requestParameters', {}).get('dBInstanceIdentifier')
            vpc_id = record.get('requestParameters', {}).get('dBSubnetGroupName')
            if db_instance:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, parent_resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, 'RDS_INSTANCE', db_instance, vpc_id, 'creating', event_time)
                )
        elif event_name == 'DeleteDBInstance':
            db_instance = record.get('requestParameters', {}).get('dBInstanceIdentifier')
            if db_instance:
                execute_query(
                    "UPDATE resource_state SET state = %s, last_updated = %s WHERE resource_id = %s AND user_id = %s",
                    ('deleting', event_time, db_instance, user_id)
                )
    
    elif service == 'CLOUDFORMATION':
        if event_name == 'CreateStack':
            stack_name = record.get('requestParameters', {}).get('stackName')
            if stack_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'CFN_STACK', stack_name, 'creating', event_time)
                )
        elif event_name == 'DeleteStack':
            stack_name = record.get('requestParameters', {}).get('stackName')
            if stack_name:
                execute_query(
                    "UPDATE resource_state SET state = %s, last_updated = %s WHERE resource_id = %s AND user_id = %s",
                    ('deleting', event_time, stack_name, user_id)
                )
    
    elif service == 'EKS':
        if event_name == 'CreateCluster':
            cluster_name = record.get('requestParameters', {}).get('name')
            if cluster_name:
                execute_query(
                    "INSERT OR REPLACE INTO resource_state (user_id, resource_type, resource_id, state, last_updated) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, 'EKS_CLUSTER', cluster_name, 'creating', event_time)
                )
        elif event_name == 'DeleteCluster':
            cluster_name = record.get('requestParameters', {}).get('name')
            if cluster_name:
                execute_query(
                    "UPDATE resource_state SET state = %s, last_updated = %s WHERE resource_id = %s AND user_id = %s",
                    ('deleting', event_time, cluster_name, user_id)
                )


def load_sample_data_from_json(json_file_path, user_id=1):
    """Load sample data from CloudTrail JSON file"""
    
    print(f"Loading sample data from: {json_file_path}")
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {json_file_path}")
        return 0
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return 0
    
    records = data.get('Records', [])
    if not records:
        print("No records found in JSON file")
        return 0
    
    activities_added = 0
    daily_scores = {}
    
    for record in records:
        try:
            read_only = record.get('readOnly')
            if read_only == True or read_only == 'true':
                continue
            
            event_time_str = record.get('eventTime')
            event_source = record.get('eventSource', '')
            event_name = record.get('eventName', '')
            
            if not event_time_str or not event_source or not event_name:
                continue
            
            event_time = datetime.strptime(event_time_str, '%Y-%m-%dT%H:%M:%SZ')
            date = event_time.date()
            
            service = event_source.split('.')[0].upper()
            action = event_name
            
            score = calculate_score(service, action)
            
            # Track resources regardless of score
            track_resource(user_id, service, event_name, record, event_time)
            
            if score > 0:
                execute_query(
                    "INSERT INTO activity_logs (user_id, date, service, action, score, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, date, service, action, score, event_time)
                )
                
                if date not in daily_scores:
                    daily_scores[date] = 0
                daily_scores[date] += score
                
                activities_added += 1
                print(f"  [OK] {date} | {service} | {action} | +{score} points")
        
        except Exception as e:
            print(f"  [ERROR] Error processing record: {str(e)}")
            continue
    
    for date, total_score in daily_scores.items():
        execute_query(
            """
            INSERT INTO daily_scores (user_id, date, total_score) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, date) 
            DO UPDATE SET total_score = daily_scores.total_score + EXCLUDED.total_score
            """,
            (user_id, date, total_score)
        )
    
    print(f"\n[OK] Loaded {activities_added} activities from sample data")
    print(f"[OK] Updated {len(daily_scores)} days")
    
    return activities_added


def load_all_sample_logs(user_id=1):
    """Load all JSON files from sample_logs directory"""
    
    sample_logs_dir = os.path.join(os.path.dirname(__file__), 'sample_logs')
    
    if not os.path.exists(sample_logs_dir):
        print(f"Error: Directory not found - {sample_logs_dir}")
        return 0
    
    total_activities = 0
    json_files = [f for f in os.listdir(sample_logs_dir) if f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found in sample_logs directory")
        return 0
    
    print(f"Found {len(json_files)} JSON file(s) in sample_logs/\n")
    
    for json_file in json_files:
        file_path = os.path.join(sample_logs_dir, json_file)
        count = load_sample_data_from_json(file_path, user_id)
        total_activities += count
        print()
    
    return total_activities


if __name__ == '__main__':
    user = execute_query("SELECT id FROM users WHERE id = 1", fetch=True)
    
    if not user:
        print("Creating test user...")
        execute_query(
            "INSERT INTO users (name, email, role_arn) VALUES (%s, %s, %s)",
            ("Test User", "test@example.com", "arn:aws:iam::123456789012:role/TestRole")
        )
        print("[OK] User created\n")
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        load_sample_data_from_json(json_file, user_id)
    else:
        load_all_sample_logs()
