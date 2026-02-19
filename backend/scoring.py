SCORING_RULES = {
    'EC2': {
        'RunInstances': 3,
        'TerminateInstances': 2,
        'StopInstances': 1,
        'StartInstances': 1,
        'ModifyInstanceAttribute': 2,
    },
    'S3': {
        'CreateBucket': 2,
        'DeleteBucket': 2,
        'PutBucketPolicy': 2,
        'PutBucketVersioning': 1,
    },
    'IAM': {
        'CreateRole': 2,
        'CreateUser': 2,
        'AttachRolePolicy': 2,
        'CreatePolicy': 3,
    },
    'VPC': {
        'CreateVpc': 3,
        'CreateSubnet': 2,
        'CreateSecurityGroup': 2,
        'AuthorizeSecurityGroupIngress': 1,
    },
    'CloudFormation': {
        'CreateStack': 5,
        'UpdateStack': 4,
        'DeleteStack': 3,
    },
    'Lambda': {
        'CreateFunction': 3,
        'UpdateFunctionCode': 2,
    },
    'RDS': {
        'CreateDBInstance': 4,
        'ModifyDBInstance': 2,
    },
    'EKS': {
        'CreateCluster': 5,
        'CreateNodegroup': 4,
    },
}

IGNORED_ACTIONS = [
    'ConsoleLogin', 'Describe', 'Get', 'List', 'Head'
]

DAILY_SCORE_CAP = 50
SERVICE_DAILY_CAP = 20

def should_ignore_action(action):
    for ignored in IGNORED_ACTIONS:
        if action.startswith(ignored):
            return True
    return False

def calculate_score(service, action):
    if should_ignore_action(action):
        return 0
    return SCORING_RULES.get(service, {}).get(action, 0)
