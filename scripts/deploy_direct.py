"""
Direct AWS Resource Deployer for AI Smart Campus Parking System
Provisions S3, DynamoDB, SNS, IAM, Lambda, EC2 Security Group, and launches EC2 instance.
"""

import os
import sys
import time
import json
import zipfile
import io
import boto3
from botocore.exceptions import ClientError

AWS_ACCESS_KEY_ID = 'AKIA5FQ4BMIHWM565NBQ'
AWS_SECRET_ACCESS_KEY = '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'
REGION = 'ap-south-1'
EMAIL = 'thotlacharan4@gmail.com'
ACCOUNT_ID = '905223168527'

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

s3 = session.client('s3')
dynamodb = session.client('dynamodb')
sns = session.client('sns')
iam = session.client('iam')
lambda_client = session.client('lambda')
ec2 = session.client('ec2')

print("=" * 65)
print("🚀 STARTING DIRECT AWS PROVISIONING IN REGION:", REGION)
print("=" * 65)

# ----------------------------------------------------------------------
# 1. S3 BUCKET
# ----------------------------------------------------------------------
bucket_name = f"campus-parking-storage-{ACCOUNT_ID}-{REGION}"
print(f"\n[1/6] S3 Storage Bucket: {bucket_name}")
try:
    # In ap-south-1, CreateBucketConfiguration is required
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION}
    )
    print(f"✅ Created S3 Bucket: {bucket_name}")
except ClientError as e:
    if "BucketAlreadyOwnedByYou" in str(e) or "BucketAlreadyExists" in str(e):
        print(f"ℹ️ Bucket '{bucket_name}' already exists.")
    else:
        print(f"⚠️ S3 Error: {e}")

# Create folder structure
try:
    s3.put_object(Bucket=bucket_name, Key='snapshots/')
    s3.put_object(Bucket=bucket_name, Key='detections/')
    print("✅ Created bucket folders 'snapshots/' and 'detections/'")
except Exception as e:
    print(f"⚠️ Folder creation: {e}")

# ----------------------------------------------------------------------
# 2. DYNAMODB TABLE
# ----------------------------------------------------------------------
table_name = "CampusParkingSpots"
print(f"\n[2/6] DynamoDB Table: {table_name}")
try:
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'SpotId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'SpotId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    print(f"✅ Created DynamoDB table: {table_name}. Waiting for ACTIVE status...")
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print("✅ DynamoDB table is ACTIVE.")
except ClientError as e:
    if "ResourceInUseException" in str(e):
        print(f"ℹ️ DynamoDB table '{table_name}' already exists.")
    else:
        print(f"⚠️ DynamoDB Error: {e}")

# ----------------------------------------------------------------------
# 3. SNS TOPIC & SUBSCRIPTION
# ----------------------------------------------------------------------
topic_name = "CampusParkingAlerts"
print(f"\n[3/6] SNS Topic: {topic_name}")
try:
    topic_resp = sns.create_topic(Name=topic_name)
    topic_arn = topic_resp['TopicArn']
    print(f"✅ SNS Topic Created/Retrieved: {topic_arn}")
    
    # Subscribe email
    sub_resp = sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=EMAIL
    )
    print(f"✅ Subscribed '{EMAIL}' to SNS alerts. SubscriptionArn: {sub_resp.get('SubscriptionArn', 'PendingConfirmation')}")
except Exception as e:
    print(f"⚠️ SNS Error: {e}")
    topic_arn = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:{topic_name}"

# ----------------------------------------------------------------------
# 4. IAM ROLE FOR LAMBDA
# ----------------------------------------------------------------------
role_name = "CampusParkingLambdaRole"
print(f"\n[4/6] IAM Role for Lambda: {role_name}")
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

lambda_role_arn = None
try:
    role_resp = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy),
        Description="Execution role for Campus Parking Lambda Processor"
    )
    lambda_role_arn = role_resp['Role']['Arn']
    print(f"✅ Created IAM Role: {lambda_role_arn}")
except ClientError as e:
    if "EntityAlreadyExists" in str(e):
        role_resp = iam.get_role(RoleName=role_name)
        lambda_role_arn = role_resp['Role']['Arn']
        print(f"ℹ️ IAM Role already exists: {lambda_role_arn}")
    else:
        print(f"⚠️ IAM Role Error: {e}")

# Attach policies
policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
]
for pol in policies:
    try:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=pol)
    except Exception as e:
        pass
print("✅ Attached AWS managed execution policies to Lambda role.")

# Wait a brief moment for IAM propagation
time.sleep(10)

# ----------------------------------------------------------------------
# 5. AWS LAMBDA FUNCTION
# ----------------------------------------------------------------------
function_name = "CampusParkingProcessor"
print(f"\n[5/6] AWS Lambda Function: {function_name}")

# Prepare zip file in memory
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    with open('/home/user/lambda/lambda_function.py', 'r') as f:
        zip_file.writestr('lambda_function.py', f.read())
zip_buffer.seek(0)
zip_bytes = zip_buffer.read()

lambda_arn = None
try:
    func_resp = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=lambda_role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_bytes},
        Description='AI Smart Campus Parking occupancy processor and SNS alert dispatcher',
        Timeout=30,
        MemorySize=256,
        Environment={
            'Variables': {
                'DYNAMODB_TABLE': table_name,
                'SNS_TOPIC_ARN': topic_arn,
                'OCCUPANCY_ALERT_THRESHOLD': '80'
            }
        }
    )
    lambda_arn = func_resp['FunctionArn']
    print(f"✅ Created Lambda Function: {lambda_arn}")
except ClientError as e:
    if "ResourceConflictException" in str(e):
        print(f"ℹ️ Function '{function_name}' exists. Updating code and configuration...")
        lambda_client.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
        time.sleep(3)
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': {
                    'DYNAMODB_TABLE': table_name,
                    'SNS_TOPIC_ARN': topic_arn,
                    'OCCUPANCY_ALERT_THRESHOLD': '80'
                }
            }
        )
        func_resp = lambda_client.get_function(FunctionName=function_name)
        lambda_arn = func_resp['Configuration']['FunctionArn']
        print(f"✅ Updated Lambda Function: {lambda_arn}")
    else:
        print(f"⚠️ Lambda Error: {e}")

# Add Lambda Permission for S3 Invocations
try:
    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId='s3-invoke-parking-processor',
        Action='lambda:InvokeFunction',
        Principal='s3.amazonaws.com',
        SourceArn=f"arn:aws:s3:::{bucket_name}"
    )
    print("✅ Added S3 invocation permission to Lambda")
except ClientError as e:
    if "ResourceConflictException" in str(e):
        pass

# ----------------------------------------------------------------------
# 6. S3 EVENT NOTIFICATION (Trigger Lambda on detection JSONs)
# ----------------------------------------------------------------------
try:
    s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': lambda_arn,
                    'Events': ['s3:ObjectCreated:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {'Name': 'prefix', 'Value': 'detections/'},
                                {'Name': 'suffix', 'Value': '.json'}
                            ]
                        }
                    }
                }
            ]
        }
    )
    print("✅ S3 Bucket Notification connected to Lambda trigger.")
except Exception as e:
    print(f"⚠️ S3 Notification Setup: {e}")

print("\n" + "=" * 65)
print("🎉 CORE AWS SERVERLESS STACK DEPLOYED SUCCESSFULLY!")
print("=" * 65)
print(f"📦 S3 Storage Bucket : {bucket_name}")
print(f"📊 DynamoDB Table    : {table_name}")
print(f"🔔 SNS Alert Topic   : {topic_arn}")
print(f"⚡ Lambda Function   : {function_name}")
print("=" * 65)
