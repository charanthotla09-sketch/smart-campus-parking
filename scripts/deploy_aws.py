"""
Automated 1-Click AWS Deployer for Smart Campus Parking System
Deploys CloudFormation stack (S3, DynamoDB, Lambda, SNS, IAM, Security Groups) and verifies resources.
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

def deploy_stack(region="us-east-1", alert_email="student@example.com", stack_name="smart-campus-parking"):
    print("=" * 65)
    print("🚀 SMART CAMPUS PARKING SYSTEM - AUTOMATED AWS DEPLOYER")
    print("=" * 65)
    
    cf_client = boto3.client("cloudformation", region_name=region)
    sts_client = boto3.client("sts", region_name=region)
    
    # Verify AWS Identity
    try:
        identity = sts_client.get_caller_identity()
        print(f"✅ Authenticated AWS Account: {identity['Account']}")
        print(f"✅ IAM Principal ARN: {identity['Arn']}")
        print(f"✅ Region: {region}")
    except Exception as e:
        print(f"❌ Failed to authenticate with AWS credentials: {e}")
        return False

    template_path = "/home/user/cloudformation/parking_system_template.yaml"
    with open(template_path, "r") as f:
        template_body = f.read()

    print(f"\n📦 Deploying CloudFormation Stack: '{stack_name}'...")
    print(f"📧 Notification Email: {alert_email}")
    
    # Check if stack already exists
    stack_exists = False
    try:
        cf_client.describe_stacks(StackName=stack_name)
        stack_exists = True
        print(f"ℹ️ Stack '{stack_name}' already exists. Updating stack...")
    except ClientError as e:
        if "does not exist" in str(e):
            stack_exists = False
        else:
            print(f"❌ Error checking stack: {e}")
            return False

    params = [
        {"ParameterKey": "AlertEmail", "ParameterValue": alert_email},
        {"ParameterKey": "Environment", "ParameterValue": "dev"}
    ]

    try:
        if stack_exists:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=params,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        else:
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=params,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        print(f"✅ Stack operation initiated! StackId: {response['StackId']}")
    except ClientError as e:
        if "No updates are to be performed" in str(e):
            print("ℹ️ Stack is already up to date!")
        else:
            print(f"❌ CloudFormation Error: {e}")
            return False

    # Wait for completion
    print("\n⏳ Waiting for AWS CloudFormation to provision S3, DynamoDB, Lambda, SNS, and IAM roles...")
    waiter = cf_client.get_waiter("stack_create_complete" if not stack_exists else "stack_update_complete")
    
    try:
        waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
        print("🎉 CloudFormation Stack successfully deployed!")
    except Exception as e:
        print(f"⚠️ Waiter notification: {e}")

    # Describe stack outputs
    describe_resp = cf_client.describe_stacks(StackName=stack_name)
    outputs = describe_resp['Stacks'][0].get('Outputs', [])
    
    print("\n" + "=" * 65)
    print("📋 PROVISIONED AWS RESOURCES")
    print("=" * 65)
    output_dict = {}
    for out in outputs:
        key = out['OutputKey']
        val = out['OutputValue']
        output_dict[key] = val
        print(f"• {key:25}: {val}")

    print("=" * 65)
    print("⚠️ IMPORTANT NEXT STEPS:")
    print(f"1. Check your email ({alert_email}) and click 'Confirm subscription' in the AWS SNS email.")
    print("2. Launch your EC2 instance attaching the IAM profile:")
    print(f"   Profile: {output_dict.get('EC2InstanceProfileName', 'CampusParkingEC2InstanceProfile')}")
    print(f"3. Run detector on EC2 with S3 bucket:")
    print(f"   python3 parking_detector.py --s3-bucket {output_dict.get('BucketName', '')} --mode simulate")
    print("=" * 65)
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="us-east-1", help="AWS Region (e.g. us-east-1)")
    parser.add_argument("--email", default="student@example.com", help="Email for SNS parking capacity alerts")
    parser.add_argument("--stack-name", default="smart-campus-parking", help="CloudFormation Stack Name")
    args = parser.parse_args()

    deploy_stack(region=args.region, alert_email=args.email, stack_name=args.stack_name)
