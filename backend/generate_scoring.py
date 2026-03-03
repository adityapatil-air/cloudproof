import boto3
import json

def get_service_operations():
    """Extract all operations from boto3 services"""
    
    services = {
        'ec2': 'EC2',
        's3': 'S3',
        'iam': 'IAM',
        'lambda': 'LAMBDA',
        'rds': 'RDS',
        'cloudformation': 'CLOUDFORMATION',
        'eks': 'EKS',
        'dynamodb': 'DYNAMODB',
        'sns': 'SNS',
        'sqs': 'SQS',
    }
    
    scoring_rules = {}
    
    for service_name, service_key in services.items():
        try:
            client = boto3.client(service_name, region_name='us-east-1')
            operations = client._service_model.operation_names
            
            service_actions = {}
            for op in operations:
                # Auto-assign scores based on operation type
                score = assign_score(op)
                if score > 0:
                    service_actions[op] = score
            
            scoring_rules[service_key] = service_actions
            print(f"{service_key}: {len(service_actions)} actions")
            
        except Exception as e:
            print(f"Error with {service_name}: {e}")
    
    return scoring_rules

def assign_score(operation):
    """Auto-assign score based on operation name"""
    
    # Tier 5 (8-10): Critical Infrastructure
    if any(x in operation for x in ['CreateCluster', 'CreateStack', 'CreateDBInstance', 'CreateVpc']):
        return 10
    
    # Tier 4 (5-7): High Impact
    if any(x in operation for x in ['Create', 'Delete', 'Launch', 'Terminate']):
        if 'Cluster' in operation or 'Stack' in operation or 'Instance' in operation:
            return 7
        return 5
    
    # Tier 3 (3-4): Medium Impact
    if any(x in operation for x in ['Update', 'Modify', 'Put', 'Attach', 'Detach']):
        return 3
    
    # Tier 2 (1-2): Low Impact
    if any(x in operation for x in ['Start', 'Stop', 'Reboot', 'Enable', 'Disable']):
        return 1
    
    # Tier 1 (0): Read-only
    if any(x in operation for x in ['Describe', 'Get', 'List', 'Head']):
        return 0
    
    return 0

def generate_scoring_file(scoring_rules):
    """Generate Python scoring file"""
    
    output = """# Auto-Generated Scoring System from boto3
# Generated using all available AWS service operations

SCORING_RULES = {
"""
    
    for service, actions in sorted(scoring_rules.items()):
        output += f"    '{service}': {{\n"
        for action, score in sorted(actions.items()):
            output += f"        '{action}': {score},\n"
        output += "    },\n\n"
    
    output += """}\n
IGNORED_ACTIONS = [
    'ConsoleLogin', 'Describe', 'Get', 'List', 'Head', 'AssumeRole'
]

DAILY_SCORE_CAP = 100
SERVICE_DAILY_CAP = 30
ACTION_DAILY_CAP = 15

def should_ignore_action(action):
    for ignored in IGNORED_ACTIONS:
        if action.startswith(ignored):
            return True
    return False

def calculate_score(service, action):
    if should_ignore_action(action):
        return 0
    return SCORING_RULES.get(service, {}).get(action, 0)
"""
    
    return output

if __name__ == '__main__':
    print("Extracting AWS service operations from boto3...\n")
    
    scoring_rules = get_service_operations()
    
    total_actions = sum(len(actions) for actions in scoring_rules.values())
    print(f"\nTotal actions: {total_actions}")
    
    output = generate_scoring_file(scoring_rules)
    
    with open('scoring_auto.py', 'w') as f:
        f.write(output)
    
    print("\nGenerated scoring_auto.py with all AWS operations!")
    print("Review and replace scoring.py if needed.")
