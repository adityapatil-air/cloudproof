# CloudProof Scoring System v3.0
#
# Scoring Philosophy:
#   Points = Complexity + Rarity + Skill Required + Infrastructure Impact
#
# Tiers:
#   10    : Elite infrastructure (EKS cluster, RDS cluster, CloudFormation stack)
#   7-9   : High complexity (EC2 VPC setup, RDS instance, EMR, Redshift)
#   5-6   : Medium complexity (Lambda, ECS, IAM policies, API Gateway)
#   3-4   : Standard operations (S3 config, CloudWatch alarms, CodeBuild)
#   1-2   : Simple/common actions (PutObject, Start/Stop, basic tags)
#   0     : Read-only (Describe*, Get*, List*, Head*, AssumeRole)
#
# Key principle:
#   - Creating complex infrastructure = high score
#   - IAM is common/simple = lower scores than RDS/EKS
#   - Deleting = slightly less than creating (less skill needed)
#   - Modifying = slightly less than creating

SCORING_RULES = {

    # ── COMPUTE ───────────────────────────────────────────────────────────────

    # EC2: Medium-high. Running instances requires networking knowledge.
    'EC2': {
        'RunInstances':                  5,
        'TerminateInstances':            2,
        'StopInstances':                 1,
        'StartInstances':                1,
        'RebootInstances':               1,
        'ModifyInstanceAttribute':       3,
        'CreateImage':                   4,
        'CreateSnapshot':                3,
        'DeleteSnapshot':                1,
        'AttachVolume':                  2,
        'DetachVolume':                  1,
        'CreateVolume':                  3,
        'DeleteVolume':                  1,
        # VPC - complex networking, high scores
        'CreateVpc':                     9,
        'DeleteVpc':                     4,
        'CreateSubnet':                  6,
        'DeleteSubnet':                  2,
        'CreateSecurityGroup':           5,
        'DeleteSecurityGroup':           2,
        'AuthorizeSecurityGroupIngress': 4,
        'RevokeSecurityGroupIngress':    2,
        'AuthorizeSecurityGroupEgress':  4,
        'CreateInternetGateway':         7,
        'AttachInternetGateway':         5,
        'CreateNatGateway':              8,
        'CreateRouteTable':              5,
        'CreateRoute':                   4,
        'AssociateRouteTable':           3,
    },

    # VPC: Same as EC2 VPC actions (CloudTrail logs under both)
    'VPC': {
        'CreateVpc':                     9,
        'DeleteVpc':                     4,
        'CreateSubnet':                  6,
        'DeleteSubnet':                  2,
        'CreateSecurityGroup':           5,
        'DeleteSecurityGroup':           2,
        'AuthorizeSecurityGroupIngress': 4,
        'RevokeSecurityGroupIngress':    2,
        'AuthorizeSecurityGroupEgress':  4,
        'CreateInternetGateway':         7,
        'AttachInternetGateway':         5,
        'CreateNatGateway':              8,
        'CreateRouteTable':              5,
        'CreateRoute':                   4,
        'AssociateRouteTable':           3,
    },

    # Lambda: Medium. Serverless is common but requires architecture knowledge.
    'LAMBDA': {
        'CreateFunction':            6,
        'DeleteFunction':            2,
        'UpdateFunctionCode':        4,
        'UpdateFunctionConfiguration': 3,
        'PublishVersion':            3,
        'CreateAlias':               2,
        'UpdateAlias':               2,
        'AddPermission':             4,
        'RemovePermission':          2,
        'PutFunctionConcurrency':    3,
        'CreateEventSourceMapping':  5,
    },

    # ECS: High. Container orchestration requires deep knowledge.
    'ECS': {
        'CreateCluster':             8,
        'DeleteCluster':             3,
        'RegisterTaskDefinition':    7,
        'DeregisterTaskDefinition':  2,
        'CreateService':             8,
        'UpdateService':             5,
        'DeleteService':             3,
        'RunTask':                   4,
        'StopTask':                  1,
        'CreateTaskSet':             5,
        'UpdateTaskSet':             4,
    },

    # EKS: Elite. Kubernetes is the most complex AWS service.
    'EKS': {
        'CreateCluster':         10,
        'DeleteCluster':          5,
        'UpdateClusterVersion':   8,
        'UpdateClusterConfig':    6,
        'CreateNodegroup':        9,
        'DeleteNodegroup':        4,
        'UpdateNodegroupConfig':  6,
        'CreateAddon':            5,
        'UpdateAddon':            3,
    },

    # ECR: Low-medium. Just a container registry.
    'ECR': {
        'CreateRepository':          4,
        'DeleteRepository':          2,
        'PutImage':                  2,
        'SetRepositoryPolicy':       4,
        'DeleteRepositoryPolicy':    2,
        'PutLifecyclePolicy':        3,
        'CreatePullThroughCacheRule': 4,
    },

    # Auto Scaling: Medium. Requires understanding of scaling policies.
    'AUTOSCALING': {
        'CreateAutoScalingGroup':          7,
        'DeleteAutoScalingGroup':          3,
        'UpdateAutoScalingGroup':          4,
        'CreateLaunchConfiguration':       5,
        'DeleteLaunchConfiguration':       2,
        'PutScalingPolicy':                6,
        'DeletePolicy':                    2,
        'AttachLoadBalancerTargetGroups':  4,
        'SetDesiredCapacity':              2,
    },

    # Elastic Beanstalk: Medium. Abstracts EC2 but still requires config knowledge.
    'ELASTICBEANSTALK': {
        'CreateApplication':        5,
        'DeleteApplication':        2,
        'CreateEnvironment':        7,
        'TerminateEnvironment':     3,
        'UpdateEnvironment':        5,
        'CreateApplicationVersion': 4,
        'DeleteApplicationVersion': 2,
        'SwapEnvironmentCNAMEs':    4,
    },

    # App Runner: Low-medium. Simplified container deployment.
    'APPRUNNER': {
        'CreateService':                   5,
        'DeleteService':                   2,
        'UpdateService':                   4,
        'PauseService':                    1,
        'ResumeService':                   1,
        'CreateConnection':                3,
        'CreateAutoScalingConfiguration':  3,
    },

    # Lightsail: Low. Simplified VPS, less skill required.
    'LIGHTSAIL': {
        'CreateInstances':           3,
        'DeleteInstance':            1,
        'CreateRelationalDatabase':  6,
        'DeleteRelationalDatabase':  3,
        'CreateLoadBalancer':        5,
        'CreateDisk':                3,
        'CreateDomainEntry':         3,
    },

    # ── STORAGE ───────────────────────────────────────────────────────────────

    # S3: Low-medium. Common service, but security config requires knowledge.
    'S3': {
        'CreateBucket':          3,
        'DeleteBucket':          2,
        'PutBucketPolicy':       5,
        'DeleteBucketPolicy':    2,
        'PutBucketVersioning':   3,
        'PutBucketEncryption':   4,
        'PutBucketLogging':      3,
        'PutBucketCors':         3,
        'PutBucketLifecycle':    3,
        'PutObject':             1,
        'DeleteObject':          1,
        'PutBucketReplication':  6,
    },

    # EFS: Medium. Shared file system requires networking setup.
    'ELASTICFILESYSTEM': {
        'CreateFileSystem':    6,
        'DeleteFileSystem':    3,
        'CreateMountTarget':   5,
        'DeleteMountTarget':   2,
        'PutFileSystemPolicy': 5,
        'CreateAccessPoint':   4,
        'PutBackupPolicy':     3,
    },

    # Backup: Medium. Requires understanding of backup strategies.
    'BACKUP': {
        'CreateBackupPlan':      5,
        'DeleteBackupPlan':      2,
        'CreateBackupSelection': 4,
        'StartBackupJob':        3,
        'StartRestoreJob':       6,
        'CreateBackupVault':     5,
        'DeleteBackupVault':     2,
    },

    # ── DATABASE ──────────────────────────────────────────────────────────────

    # RDS: High. Database setup requires networking, security, parameter tuning.
    'RDS': {
        'CreateDBInstance':              9,
        'DeleteDBInstance':              4,
        'ModifyDBInstance':              6,
        'RebootDBInstance':              2,
        'StartDBInstance':               1,
        'StopDBInstance':                1,
        'CreateDBSnapshot':              4,
        'DeleteDBSnapshot':              2,
        'RestoreDBInstanceFromSnapshot': 8,
        'CreateDBCluster':              10,
        'ModifyDBCluster':               6,
        'CreateDBParameterGroup':        4,
        'ModifyDBParameterGroup':        4,
    },

    # DynamoDB: Medium-high. NoSQL design requires different thinking.
    'DYNAMODB': {
        'CreateTable':                       7,
        'DeleteTable':                       3,
        'UpdateTable':                       5,
        'PutItem':                           1,
        'DeleteItem':                        1,
        'UpdateItem':                        1,
        'CreateBackup':                      4,
        'RestoreTableFromBackup':            6,
        'CreateGlobalTable':                 9,
        'UpdateGlobalTable':                 6,
        'EnableKinesisStreamingDestination': 5,
    },

    # ElastiCache: High. Caching layer requires architecture knowledge.
    'ELASTICACHE': {
        'CreateCacheCluster':      8,
        'DeleteCacheCluster':      3,
        'ModifyCacheCluster':      5,
        'CreateReplicationGroup':  9,
        'DeleteReplicationGroup':  4,
        'ModifyReplicationGroup':  6,
        'CreateCacheSubnetGroup':  5,
        'CreateSnapshot':          4,
        'RestoreFromSnapshot':     7,
    },

    # Redshift: Elite. Data warehouse setup is very complex.
    'REDSHIFT': {
        'CreateCluster':                10,
        'DeleteCluster':                 4,
        'ModifyCluster':                 6,
        'CreateClusterSnapshot':         4,
        'RestoreFromClusterSnapshot':    8,
        'CreateClusterSubnetGroup':      5,
        'CreateEventSubscription':       4,
        'EnableLogging':                 3,
    },

    # OpenSearch/Elasticsearch: High. Search cluster setup is complex.
    'ES': {
        'CreateDomain':              9,
        'DeleteDomain':              4,
        'UpdateDomainConfig':        6,
        'CreateOutboundConnection':  5,
        'AddTags':                   1,
    },

    # ── SECURITY ──────────────────────────────────────────────────────────────

    # IAM: Medium. Common but important. Not as complex as infra services.
    'IAM': {
        'CreateRole':          5,
        'DeleteRole':          2,
        'CreateUser':          4,
        'DeleteUser':          2,
        'AttachRolePolicy':    4,
        'DetachRolePolicy':    2,
        'CreatePolicy':        6,
        'DeletePolicy':        2,
        'PutRolePolicy':       5,
        'CreateAccessKey':     3,
        'DeleteAccessKey':     2,
        'AttachUserPolicy':    4,
        'CreateGroup':         3,
        'AddUserToGroup':      2,
    },

    # KMS: Medium-high. Key management requires security expertise.
    'KMS': {
        'CreateKey':           7,
        'ScheduleKeyDeletion': 4,
        'EnableKey':           2,
        'DisableKey':          2,
        'CreateAlias':         3,
        'DeleteAlias':         2,
        'PutKeyPolicy':        6,
        'EnableKeyRotation':   5,
        'CreateGrant':         4,
    },

    # Secrets Manager: Medium. Requires understanding of secret rotation.
    'SECRETSMANAGER': {
        'CreateSecret':    5,
        'DeleteSecret':    2,
        'UpdateSecret':    4,
        'RotateSecret':    6,
        'PutSecretValue':  3,
        'TagResource':     1,
    },

    # WAF: High. Web security rules require deep knowledge.
    'WAFV2': {
        'CreateWebACL':    8,
        'DeleteWebACL':    3,
        'UpdateWebACL':    6,
        'CreateRuleGroup': 7,
        'DeleteRuleGroup': 3,
        'CreateIPSet':     4,
        'AssociateWebACL': 5,
    },

    # GuardDuty: Medium. Threat detection setup.
    'GUARDDUTY': {
        'CreateDetector':              6,
        'DeleteDetector':              3,
        'CreateFilter':                4,
        'CreateIPSet':                 4,
        'CreateThreatIntelSet':        4,
        'ArchiveFindings':             2,
        'CreatePublishingDestination': 4,
    },

    # Config: Medium. Compliance rules require policy knowledge.
    'CONFIG': {
        'PutConfigRule':                   6,
        'DeleteConfigRule':                2,
        'PutConfigurationRecorder':        5,
        'StartConfigurationRecorder':      3,
        'StopConfigurationRecorder':       2,
        'PutDeliveryChannel':              4,
        'PutRemediationConfigurations':    6,
    },

    # ── NETWORKING ────────────────────────────────────────────────────────────

    # CloudFront: Medium-high. CDN config requires understanding of caching.
    'CLOUDFRONT': {
        'CreateDistribution':        7,
        'DeleteDistribution':        3,
        'UpdateDistribution':        5,
        'CreateInvalidation':        2,
        'CreateCachePolicy':         5,
        'CreateOriginAccessControl': 5,
        'AssociateAlias':            4,
    },

    # Route53: Medium. DNS management requires networking knowledge.
    'ROUTE53': {
        'CreateHostedZone':            6,
        'DeleteHostedZone':            3,
        'ChangeResourceRecordSets':    4,
        'CreateHealthCheck':           5,
        'DeleteHealthCheck':           2,
        'CreateTrafficPolicy':         6,
        'AssociateVPCWithHostedZone':  5,
    },

    # ELB: Medium-high. Load balancer setup requires networking knowledge.
    'ELASTICLOADBALANCING': {
        'CreateLoadBalancer':          8,
        'DeleteLoadBalancer':          3,
        'CreateTargetGroup':           5,
        'DeleteTargetGroup':           2,
        'CreateListener':              5,
        'DeleteListener':              2,
        'RegisterTargets':             3,
        'DeregisterTargets':           2,
        'ModifyLoadBalancerAttributes': 4,
        'CreateRule':                  4,
    },

    # Direct Connect: Elite. Dedicated network connection is very complex.
    'DIRECTCONNECT': {
        'CreateConnection':           10,
        'DeleteConnection':            5,
        'CreateVirtualInterface':      9,
        'DeleteVirtualInterface':      4,
        'CreateDirectConnectGateway':  9,
        'AssociateVirtualInterface':   7,
    },

    # ── MESSAGING ─────────────────────────────────────────────────────────────

    # SNS: Low. Simple notification service.
    'SNS': {
        'CreateTopic':               3,
        'DeleteTopic':               1,
        'Subscribe':                 2,
        'Unsubscribe':               1,
        'Publish':                   1,
        'SetTopicAttributes':        2,
        'CreatePlatformApplication': 4,
    },

    # SQS: Low. Simple queue service.
    'SQS': {
        'CreateQueue':        3,
        'DeleteQueue':        1,
        'SendMessage':        1,
        'SetQueueAttributes': 3,
        'AddPermission':      3,
        'RemovePermission':   1,
    },

    # Kinesis: Medium-high. Streaming data requires architecture knowledge.
    'KINESIS': {
        'CreateStream':              7,
        'DeleteStream':              3,
        'MergeShards':               5,
        'SplitShard':                5,
        'AddTagsToStream':           1,
        'EnableEnhancedMonitoring':  4,
        'StartStreamEncryption':     5,
    },

    # Firehose: Medium. Data delivery streams.
    'FIREHOSE': {
        'CreateDeliveryStream':  6,
        'DeleteDeliveryStream':  2,
        'UpdateDestination':     4,
        'TagDeliveryStream':     1,
    },

    # ── DEVOPS / CI-CD ────────────────────────────────────────────────────────

    # CodePipeline: Medium-high. CI/CD pipelines require workflow knowledge.
    'CODEPIPELINE': {
        'CreatePipeline':          7,
        'DeletePipeline':          2,
        'UpdatePipeline':          5,
        'StartPipelineExecution':  3,
        'StopPipelineExecution':   2,
        'PutApprovalResult':       2,
        'CreateCustomActionType':  5,
    },

    # CodeBuild: Medium. Build configuration requires knowledge of build systems.
    'CODEBUILD': {
        'CreateProject':      6,
        'DeleteProject':      2,
        'UpdateProject':      4,
        'StartBuild':         3,
        'StopBuild':          1,
        'CreateReportGroup':  4,
        'BatchDeleteBuilds':  2,
    },

    # CodeDeploy: Medium. Deployment strategies require knowledge.
    'CODEDEPLOY': {
        'CreateApplication':      5,
        'DeleteApplication':      2,
        'CreateDeploymentGroup':  7,
        'DeleteDeploymentGroup':  3,
        'CreateDeployment':       5,
        'StopDeployment':         2,
        'CreateDeploymentConfig': 5,
    },

    # CodeCommit: Low. Just a Git repository.
    'CODECOMMIT': {
        'CreateRepository':              4,
        'DeleteRepository':              2,
        'CreateBranch':                  2,
        'DeleteBranch':                  1,
        'MergeBranchesByFastForward':    2,
        'CreatePullRequest':             2,
        'MergePullRequestBySquash':      2,
    },

    # ── MONITORING ────────────────────────────────────────────────────────────

    # CloudWatch: Low-medium. Monitoring setup is straightforward.
    'CLOUDWATCH': {
        'PutMetricAlarm':        4,
        'DeleteAlarms':          1,
        'CreateDashboard':       3,
        'DeleteDashboards':      1,
        'PutDashboard':          3,
        'EnableAlarmActions':    2,
        'PutMetricData':         1,
        'PutAnomalyDetector':    5,
    },

    # CloudWatch Logs: Low.
    'LOGS': {
        'CreateLogGroup':          2,
        'DeleteLogGroup':          1,
        'CreateLogStream':         1,
        'PutLogEvents':            1,
        'PutSubscriptionFilter':   4,
        'DeleteSubscriptionFilter': 2,
        'PutRetentionPolicy':      2,
        'CreateExportTask':        3,
    },

    # ── INFRASTRUCTURE AS CODE ────────────────────────────────────────────────

    # CloudFormation: Elite. IaC requires deep multi-service knowledge.
    'CLOUDFORMATION': {
        'CreateStack':           10,
        'UpdateStack':            8,
        'DeleteStack':            4,
        'CreateChangeSet':        6,
        'ExecuteChangeSet':       8,
        'CancelUpdateStack':      3,
        'ContinueUpdateRollback': 4,
    },

    # SSM: Medium. Parameter store and automation.
    'SSM': {
        'PutParameter':              3,
        'DeleteParameter':           1,
        'AddTagsToResource':         1,
        'CreateDocument':            5,
        'DeleteDocument':            2,
        'CreateAssociation':         4,
        'StartAutomationExecution':  5,
        'SendCommand':               3,
    },

    # ── DATA & ANALYTICS ──────────────────────────────────────────────────────

    # Glue: High. ETL pipelines require data engineering knowledge.
    'GLUE': {
        'CreateDatabase':  5,
        'DeleteDatabase':  2,
        'CreateTable':     4,
        'DeleteTable':     2,
        'CreateJob':       7,
        'DeleteJob':       2,
        'StartJobRun':     4,
        'CreateCrawler':   6,
        'StartCrawler':    3,
        'CreateTrigger':   5,
        'CreateWorkflow':  6,
    },

    # Athena: Medium. SQL queries on S3.
    'ATHENA': {
        'CreateWorkGroup':        5,
        'DeleteWorkGroup':        2,
        'StartQueryExecution':    2,
        'CreateDataCatalog':      5,
        'CreateNamedQuery':       3,
        'CreatePreparedStatement': 3,
    },

    # EMR: Elite. Big data clusters are very complex.
    'EMR': {
        'RunJobFlow':                  10,
        'TerminateJobFlows':            4,
        'AddJobFlowSteps':              6,
        'CreateSecurityConfiguration':  6,
        'AddInstanceGroups':            7,
        'ModifyInstanceGroups':         5,
    },

    # ── ML ────────────────────────────────────────────────────────────────────

    # SageMaker: Elite. ML infrastructure is highly complex.
    'SAGEMAKER': {
        'CreateNotebookInstance':  7,
        'DeleteNotebookInstance':  3,
        'CreateTrainingJob':       9,
        'CreateModel':             7,
        'CreateEndpoint':          9,
        'DeleteEndpoint':          3,
        'CreateEndpointConfig':    6,
        'CreatePipeline':          8,
        'CreateDomain':            9,
        'CreateFeatureGroup':      7,
    },

    # ── WORKFLOW ──────────────────────────────────────────────────────────────

    # Step Functions: Medium-high. State machines require workflow design.
    'STATES': {
        'CreateStateMachine':  8,
        'DeleteStateMachine':  3,
        'UpdateStateMachine':  6,
        'StartExecution':      3,
        'StopExecution':       1,
        'CreateActivity':      4,
    },

    # ── API ───────────────────────────────────────────────────────────────────

    # API Gateway: Medium-high. REST API design requires architecture knowledge.
    'APIGATEWAY': {
        'CreateRestApi':    7,
        'DeleteRestApi':    3,
        'CreateDeployment': 6,
        'CreateStage':      5,
        'DeleteStage':      2,
        'CreateResource':   4,
        'DeleteResource':   2,
        'PutMethod':        4,
        'PutIntegration':   5,
        'CreateApiKey':     3,
        'CreateUsagePlan':  4,
    },

    # ── OTHER ─────────────────────────────────────────────────────────────────

    # Amplify: Low-medium. Frontend deployment.
    'AMPLIFY': {
        'CreateApp':               4,
        'DeleteApp':               2,
        'CreateBranch':            3,
        'DeleteBranch':            1,
        'CreateDeployment':        4,
        'StartDeployment':         3,
        'CreateDomainAssociation': 5,
    },

    # Transfer Family: Medium. SFTP/FTP server setup.
    'TRANSFER': {
        'CreateServer':       6,
        'DeleteServer':       3,
        'CreateUser':         4,
        'DeleteUser':         2,
        'ImportSshPublicKey': 3,
    },

    # IoT: High. IoT infrastructure requires specialized knowledge.
    'IOT': {
        'CreateThing':                4,
        'DeleteThing':                2,
        'CreatePolicy':               5,
        'CreateTopicRule':            6,
        'DeleteTopicRule':            2,
        'CreateCertificateFromCsr':   5,
        'CreateProvisioningTemplate': 6,
    },
}

IGNORED_ACTIONS = [
    'ConsoleLogin', 'Describe', 'Get', 'List', 'Head', 'AssumeRole'
]

DAILY_SCORE_CAP    = 100
SERVICE_DAILY_CAP  = 30
ACTION_DAILY_CAP   = 15


def should_ignore_action(action):
    for ignored in IGNORED_ACTIONS:
        if action.startswith(ignored):
            return True
    return False


def calculate_score(service, action):
    if should_ignore_action(action):
        return 0
    return SCORING_RULES.get(service, {}).get(action, 0)
