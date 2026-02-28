"""
AWS client helpers for S3. Uses user-provided credentials:
- Access key + secret: used directly (preferred)
- IAM role ARN: assumed dynamically via STS (requires caller identity with sts:AssumeRole)
"""
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client(access_key=None, secret_key=None, role_arn=None, region=None):
    """
    Return an S3 client using the provided credentials.
    Prefers access_key/secret_key. If only role_arn is provided, assumes the role.
    If no credentials given, uses default boto3 chain (env, instance profile).
    """
    if access_key and secret_key:
        return boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region or "us-east-1",
        )
    if role_arn:
        creds = _assume_role(role_arn, region)
        return boto3.client(
            "s3",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=region or "us-east-1",
        )
    return boto3.client("s3", region_name=region or "us-east-1")


def _assume_role(role_arn, region=None):
    """Assume the given IAM role and return temporary credentials."""
    sts = boto3.client("sts", region_name=region or "us-east-1")
    resp = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="CloudProofS3Session",
        DurationSeconds=3600,
    )
    return resp["Credentials"]


def list_s3_buckets(access_key=None, secret_key=None, role_arn=None, region=None):
    """
    List S3 buckets visible to the provided credentials.
    Returns list of bucket names or raises on error.
    """
    client = get_s3_client(
        access_key=access_key,
        secret_key=secret_key,
        role_arn=role_arn,
        region=region,
    )
    try:
        resp = client.list_buckets()
        return [b["Name"] for b in resp.get("Buckets", [])]
    except ClientError as e:
        logger.error(f"Failed to list S3 buckets: {e}")
        raise
