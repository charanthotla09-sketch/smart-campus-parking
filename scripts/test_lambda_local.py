"""
Local test runner for Lambda handler (simulates S3 event or direct JSON payload)
"""

import sys
import json
from decimal import Decimal

# Add lambda path
sys.path.append("/home/user/lambda")

# Mock boto3 resources if running locally without AWS credentials
class MockDynamoTable:
    def __init__(self, name):
        self.name = name
        self.items = {}
    
    def batch_writer(self):
        return self
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def put_item(self, Item):
        print(f"[MOCK DYNAMODB] PutItem: {Item['SpotId']} -> Status: {Item.get('Status')} (LastUpdated: {Item.get('LastUpdated')})")
        self.items[Item['SpotId']] = Item

class MockSNS:
    def publish(self, TopicArn, Subject, Message):
        print(f"\n[MOCK SNS DISPATCH] TOPIC: {TopicArn}\nSUBJECT: {Subject}\nMESSAGE:\n{Message}\n")

# Patch Lambda module clients
import lambda_function
lambda_function.dynamodb = type('MockDynamoResource', (), {'Table': lambda self, name: MockDynamoTable(name)})()
lambda_function.sns_client = MockSNS()
lambda_function.SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:CampusParkingAlerts"
lambda_function.OCCUPANCY_ALERT_THRESHOLD = 80.0

# Sample Event (High Occupancy - 11/12 spots taken = 91.7%)
sample_detection_event = {
    "zone_id": "ZONE-A",
    "zone_name": "North Campus Academic Lot A",
    "camera_id": "CAM-LOT-A-NORTH",
    "timestamp": "2026-10-06T12:00:00Z",
    "image_s3_url": "s3://campus-parking-storage-123456789012-us-east-1/snapshots/ZONE-A_20261006_120000.jpg",
    "spots": [
        {"spot_id": "A-01", "status": "OCCUPIED", "confidence": 0.95, "vehicle_type": "car"},
        {"spot_id": "A-02", "status": "OCCUPIED", "confidence": 0.92, "vehicle_type": "car"},
        {"spot_id": "A-03", "status": "OCCUPIED", "confidence": 0.88, "vehicle_type": "truck"},
        {"spot_id": "A-04", "status": "OCCUPIED", "confidence": 0.96, "vehicle_type": "car"},
        {"spot_id": "A-05", "status": "OCCUPIED", "confidence": 0.91, "vehicle_type": "car"},
        {"spot_id": "A-06", "status": "OCCUPIED", "confidence": 0.89, "vehicle_type": "car"},
        {"spot_id": "A-07", "status": "OCCUPIED", "confidence": 0.94, "vehicle_type": "car"},
        {"spot_id": "A-08", "status": "OCCUPIED", "confidence": 0.97, "vehicle_type": "car"},
        {"spot_id": "A-09", "status": "OCCUPIED", "confidence": 0.93, "vehicle_type": "car"},
        {"spot_id": "A-10", "status": "OCCUPIED", "confidence": 0.90, "vehicle_type": "car"},
        {"spot_id": "A-11", "status": "OCCUPIED", "confidence": 0.85, "vehicle_type": "car"},
        {"spot_id": "A-12", "status": "VACANT", "confidence": 0.99, "vehicle_type": "none"},
    ]
}

print("=== RUNNING LOCAL TEST OF LAMBDA HANDLER ===")
result = lambda_function.lambda_handler(sample_detection_event, None)
print("Lambda Result:")
print(json.dumps(result, indent=2))
