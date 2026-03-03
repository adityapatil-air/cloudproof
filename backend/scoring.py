# Production-Level Scoring System v2.0
# Tier 5 (8-10): Critical Infrastructure
# Tier 4 (5-7): High Impact
# Tier 3 (3-4): Medium Impact
# Tier 2 (1-2): Low Impact
# Tier 1 (0): Read-only

SCORING_RULES = {
    # COMPUTE - EC2
    'EC2': {
        'RunInstances': 5,
        'TerminateInstances': 3,
        'StopInstances': 1,
        'StartInstances': 1,
        'RebootInstances': 1,
        'ModifyInstanceAttribute': 3,
        'CreateImage': 4,
        'CreateSnapshot': 3,
        'DeleteSnapshot': 2,
        'AttachVolume': 2,
        'DetachVolume': 2,
        'CreateVolume': 3,
        'DeleteVolume': 2,
        # VPC Actions
        'CreateVpc': 8,
        'DeleteVpc': 6,
        'CreateSubnet': 6,
        'DeleteSubnet': 4,
        'CreateSecurityGroup': 5,
        'DeleteSecurityGroup': 4,
        'AuthorizeSecurityGroupIngress': 4,
        'RevokeSecurityGroupIngress': 3,
        'AuthorizeSecurityGroupEgress': 4,
        'CreateInternetGateway': 7,
        'AttachInternetGateway': 6,
        'CreateNatGateway': 7,
        'CreateRouteTable': 5,
        'CreateRoute': 4,
        'AssociateRouteTable': 4,
    },
    
    # STORAGE - S3
    'S3': {
        'CreateBucket': 4,
        'DeleteBucket': 3,
        'PutBucketPolicy': 5,
        'DeleteBucketPolicy': 4,
        'PutBucketVersioning': 3,
        'PutBucketEncryption': 4,
        'PutBucketLogging': 2,
        'PutBucketCors': 2,
        'PutBucketLifecycle': 3,
        'PutObject': 1,
        'DeleteObject': 1,
        'PutBucketReplication': 5,
    },
    
    # SECURITY - IAM
    'IAM': {
        'CreateRole': 6,
        'DeleteRole': 5,
        'CreateUser': 5,
        'DeleteUser': 4,
        'AttachRolePolicy': 6,
        'DetachRolePolicy': 5,
        'CreatePolicy': 7,
        'DeletePolicy': 5,
        'PutRolePolicy': 6,
        'CreateAccessKey': 4,
        'DeleteAccessKey': 3,
        'AttachUserPolicy': 5,
        'CreateGroup': 4,
        'AddUserToGroup': 3,
    },
    
    # NETWORKING - VPC
    'VPC': {
        'CreateVpc': 8,
        'DeleteVpc': 6,
        'CreateSubnet': 6,
        'DeleteSubnet': 4,
        'CreateSecurityGroup': 5,
        'DeleteSecurityGroup': 4,
        'AuthorizeSecurityGroupIngress': 4,
        'RevokeSecurityGroupIngress': 3,
        'AuthorizeSecurityGroupEgress': 4,
        'CreateInternetGateway': 7,
        'AttachInternetGateway': 6,
        'CreateNatGateway': 7,
        'CreateRouteTable': 5,
        'CreateRoute': 4,
        'AssociateRouteTable': 4,
    },
    
    # SERVERLESS - Lambda
    'LAMBDA': {
        'CreateFunction': 6,
        'DeleteFunction': 4,
        'UpdateFunctionCode': 4,
        'UpdateFunctionConfiguration': 3,
        'PublishVersion': 3,
        'CreateAlias': 2,
        'UpdateAlias': 2,
        'AddPermission': 4,
        'RemovePermission': 3,
        'PutFunctionConcurrency': 3,
        'CreateEventSourceMapping': 5,
    },
    
    # DATABASE - RDS
    'RDS': {
        'CreateDBInstance': 9,
        'DeleteDBInstance': 7,
        'ModifyDBInstance': 5,
        'RebootDBInstance': 3,
        'StartDBInstance': 2,
        'StopDBInstance': 2,
        'CreateDBSnapshot': 4,
        'DeleteDBSnapshot': 3,
        'RestoreDBInstanceFromSnapshot': 7,
        'CreateDBCluster': 10,
        'ModifyDBCluster': 6,
        'CreateDBParameterGroup': 3,
        'ModifyDBParameterGroup': 3,
    },
    
    # INFRASTRUCTURE AS CODE - CloudFormation
    'CLOUDFORMATION': {
        'CreateStack': 10,
        'UpdateStack': 8,
        'DeleteStack': 6,
        'CreateChangeSet': 5,
        'ExecuteChangeSet': 7,
        'CancelUpdateStack': 4,
        'ContinueUpdateRollback': 5,
    },
    
    # CONTAINERS - EKS
    'EKS': {
        'CreateCluster': 10,
        'DeleteCluster': 8,
        'UpdateClusterVersion': 7,
        'UpdateClusterConfig': 6,
        'CreateNodegroup': 8,
        'DeleteNodegroup': 6,
        'UpdateNodegroupConfig': 5,
        'CreateAddon': 4,
        'UpdateAddon': 3,
    },
}

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
