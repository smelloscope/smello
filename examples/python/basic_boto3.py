"""Example: Capture AWS API calls made with boto3.

Assumes AWS credentials are configured (e.g. via AWS_PROFILE, ~/.aws/credentials).
"""

import smello

smello.init(server_url="http://localhost:5110")

import boto3

# S3: List buckets (XML response)
s3 = boto3.client("s3")
buckets = s3.list_buckets()
print(f"S3 buckets: {len(buckets['Buckets'])}")

# STS: Get caller identity (XML response)
sts = boto3.client("sts")
identity = sts.get_caller_identity()
print(f"Account: {identity['Account']}, ARN: {identity['Arn']}")

# Lambda: List functions (JSON response)
lam = boto3.client("lambda")
functions = lam.list_functions()
print(f"Lambda functions: {len(functions['Functions'])}")

# Bedrock: List foundation models (JSON response, larger payload)
bedrock = boto3.client("bedrock", region_name="us-east-1")
models = bedrock.list_foundation_models()
print(f"Bedrock foundation models: {len(models['modelSummaries'])}")

print("\nOpen http://localhost:5110 to see captured requests")

import time

time.sleep(1)
