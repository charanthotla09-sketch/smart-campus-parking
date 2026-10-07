#!/usr/bin/env python3
"""
ParkVision AI™ - Amazon DynamoDB Table Creator & Health Verifier
Creates and configures all 5 required DynamoDB tables in AWS Cloud (Region: ap-south-1).
"""

import boto3
import json
from datetime import datetime, timezone

AWS_REGION = "ap-south-1"

# Table Definitions
TABLE_DEFINITIONS = [
    {
        "TableName": "CampusParkingSpots",
        "KeySchema": [{"AttributeName": "SpotId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "SpotId", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
        "Description": "Stores real-time CCTV detection occupancy, parked/non-parked status, vehicle types, and confidence."
    },
    {
        "TableName": "CampusParkingReservations",
        "KeySchema": [{"AttributeName": "ReservationId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "ReservationId", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
        "Description": "Stores student and corporate staff parking reservations, plate numbers, and encrypted QR tokens."
    },
    {
        "TableName": "CampusParkingAuditLogs",
        "KeySchema": [{"AttributeName": "LogId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "LogId", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
        "Description": "Stores security audit logs, CCTV camera telemetry, and capacity alarm events (>= 80%)."
    },
    {
        "TableName": "CampusParkingZones",
        "KeySchema": [{"AttributeName": "ZoneId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "ZoneId", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
        "Description": "Registry of campus parking facilities (Lot A, Lot B, Lot C), GPS locations, and capacities."
    },
    {
        "TableName": "CampusParkingViolations",
        "KeySchema": [{"AttributeName": "ViolationId", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "ViolationId", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
        "Description": "Stores parking violation notices, unauthorized parking records, and fine assessments."
    }
]

def create_and_verify_tables():
    print(f"🚀 Initializing AWS DynamoDB Cloud Service in Region: {AWS_REGION}...")
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    dynamo_res = boto3.resource("dynamodb", region_name=AWS_REGION)
    
    existing_tables = dynamodb.list_tables().get("TableNames", [])
    print(f"Existing tables in AWS: {existing_tables}\n")
    
    for tbl in TABLE_DEFINITIONS:
        name = tbl["TableName"]
        if name not in existing_tables:
            print(f"➕ Creating Table on AWS Cloud: {name}...")
            dynamodb.create_table(
                TableName=name,
                KeySchema=tbl["KeySchema"],
                AttributeDefinitions=tbl["AttributeDefinitions"],
                BillingMode=tbl["BillingMode"]
            )
            print(f"   Waiting for {name} to become ACTIVE...")
            waiter = dynamodb.get_waiter("table_exists")
            waiter.wait(TableName=name)
            print(f"   ✅ Table {name} is now ACTIVE on AWS Cloud!")
        else:
            print(f"✅ Table already exists on AWS Cloud: {name}")

    print("\n" + "="*70)
    print("📊 AWS DYNAMODB CLOUD TABLES SUMMARY:")
    print("="*70)
    
    for tbl in TABLE_DEFINITIONS:
        name = tbl["TableName"]
        desc = dynamodb.describe_table(TableName=name)["Table"]
        print(f"Table Name   : {desc['TableName']}")
        print(f"Table ARN    : {desc['TableArn']}")
        print(f"Status       : {desc['TableStatus']}")
        print(f"Billing Mode : {desc.get('BillingModeSummary', {}).get('BillingMode', 'PAY_PER_REQUEST')}")
        print(f"Description  : {tbl['Description']}")
        print("-" * 70)

if __name__ == "__main__":
    create_and_verify_tables()
