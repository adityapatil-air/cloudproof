#!/bin/bash

echo "CloudProof User Setup Script"
echo "=============================="
echo ""

read -p "Enter your AWS Account ID: " AWS_ACCOUNT_ID
read -p "Enter CloudTrail S3 Bucket Name: " BUCKET_NAME
read -p "Enter CloudProof Account ID: " CLOUDPROOF_ACCOUNT_ID

echo ""
echo "Creating IAM Role..."

ROLE_NAME="CloudProofAccessRole"

cat > trust-policy-temp.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${CLOUDPROOF_ACCOUNT_ID}:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://trust-policy-temp.json

cat > permissions-policy-temp.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::${BUCKET_NAME}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name CloudProofS3Access \
  --policy-document file://permissions-policy-temp.json

ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Your Role ARN:"
echo "$ROLE_ARN"
echo ""
echo "Share this ARN with CloudProof to complete registration."

rm trust-policy-temp.json permissions-policy-temp.json
