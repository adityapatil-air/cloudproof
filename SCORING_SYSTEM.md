# CloudProof Scoring System v2.0

## Overview
Production-level scoring system for AWS CloudTrail activity tracking across 8 core services with 100+ actions.

---

## Scoring Tiers

### Tier 5 (8-10 points) - Critical Infrastructure
- RDS CreateDBCluster: 10
- CloudFormation CreateStack: 10
- EKS CreateCluster: 10
- RDS CreateDBInstance: 9

### Tier 4 (5-7 points) - High Impact
- VPC CreateVpc: 8
- EKS CreateNodegroup: 8
- CloudFormation UpdateStack: 8
- IAM CreatePolicy: 7
- VPC CreateNatGateway: 7

### Tier 3 (3-4 points) - Medium Impact
- EC2 RunInstances: 5
- Lambda CreateFunction: 6
- IAM CreateRole: 6
- S3 PutBucketPolicy: 5

### Tier 2 (1-2 points) - Low Impact
- EC2 StopInstances: 1
- S3 PutObject: 1
- RDS StartDBInstance: 2

### Tier 1 (0 points) - Read-Only
- All Describe* actions
- All Get* actions
- All List* actions
- ConsoleLogin

---

## Services Covered

### 1. EC2 (Compute)
- 13 actions tracked
- Range: 1-5 points
- Focus: Instance lifecycle, volumes, snapshots

### 2. S3 (Storage)
- 12 actions tracked
- Range: 1-5 points
- Focus: Bucket operations, policies, encryption

### 3. IAM (Security)
- 14 actions tracked
- Range: 3-7 points
- Focus: Roles, users, policies (security critical)

### 4. VPC (Networking)
- 15 actions tracked
- Range: 3-8 points
- Focus: Network infrastructure, security groups

### 5. Lambda (Serverless)
- 11 actions tracked
- Range: 2-6 points
- Focus: Function management, permissions

### 6. RDS (Database)
- 13 actions tracked
- Range: 2-10 points
- Focus: Database instances, clusters, snapshots

### 7. CloudFormation (IaC)
- 7 actions tracked
- Range: 4-10 points
- Focus: Stack operations (highest complexity)

### 8. EKS (Containers)
- 9 actions tracked
- Range: 3-10 points
- Focus: Kubernetes cluster management

---

## Daily Caps (Anti-Gaming)

```python
DAILY_SCORE_CAP = 100      # Max 100 points per day
SERVICE_DAILY_CAP = 30     # Max 30 points per service per day
ACTION_DAILY_CAP = 15      # Max 15 points per action per day
```

### Why Caps?
- Prevents score inflation
- Encourages service diversity
- Rewards consistent activity over bulk operations

---

## Scoring Logic

### Read-Only Actions (0 points)
```
DescribeInstances
GetObject
ListBuckets
HeadBucket
ConsoleLogin
AssumeRole
```

### Write Operations (Scored)
```
CREATE → Full points
UPDATE → 80% of create
DELETE → 60% of create
MODIFY → 50% of create
```

---

## Examples

### High-Value Day (100 points cap)
```
CreateDBCluster (RDS): 10
CreateStack (CloudFormation): 10
CreateVpc (VPC): 8
CreateCluster (EKS): 10
RunInstances (EC2): 5
CreateFunction (Lambda): 6
CreateRole (IAM): 6
CreateBucket (S3): 4
... more actions up to 100 total
```

### Typical Development Day (35 points)
```
RunInstances (EC2): 5
UpdateFunctionCode (Lambda): 4
CreateBucket (S3): 4
AttachRolePolicy (IAM): 6
CreateSecurityGroup (VPC): 5
CreateSnapshot (EC2): 3
PutBucketPolicy (S3): 5
StopInstances (EC2): 1
DeleteSnapshot (EC2): 2
```

---

## Implementation Details

### File: `backend/scoring.py`
- 8 service dictionaries
- 100+ action mappings
- 3 cap constants
- Ignore list for read operations

### Integration Points
1. `ingestion.py` - Applies scores during log processing
2. `generate_sample_data.py` - Uses rules for test data
3. `app.py` - Returns scores via API
4. Database - Stores scored activities

---

## Maintenance

### Adding New Actions
```python
'SERVICE': {
    'NewAction': points,  # 1-10 based on tier
}
```

### Adjusting Caps
```python
DAILY_SCORE_CAP = 150      # Increase for power users
SERVICE_DAILY_CAP = 40     # Allow more per service
ACTION_DAILY_CAP = 20      # Allow repeated actions
```

---

## Version History

**v2.0** (Current)
- 8 services, 100+ actions
- 3-tier cap system
- Production-ready

**v1.0** (Previous)
- 8 services, 30 actions
- 2-tier cap system
- Basic implementation

---

**Status: Production Ready ✓**
