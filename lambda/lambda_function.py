"""
AWS Lambda Function: CampusParkingProcessor
Triggered by S3 PutObject event on 'detections/*.json' or direct invocation.
Updates DynamoDB table 'CampusParkingSpots' and triggers SNS alerts if parking is nearing capacity.
"""

import json
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal

# AWS Resource Clients
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)

# Configuration from Environment Variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'CampusParkingSpots')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
OCCUPANCY_ALERT_THRESHOLD = float(os.environ.get('OCCUPANCY_ALERT_THRESHOLD', '80'))

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    try:
        # 1. Parse Event Payload (S3 Event Trigger or Direct Payload)
        data = None
        if 'Records' in event and len(event['Records']) > 0 and 's3' in event['Records'][0]:
            record = event['Records'][0]
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            print(f"Processing S3 event from bucket '{bucket_name}', key '{object_key}'")
            
            # Only process JSON detection reports
            if not object_key.endswith('.json'):
                print(f"Skipping non-JSON file: {object_key}")
                return {'statusCode': 200, 'body': 'Skipping non-JSON object'}
                
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            file_content = response['Body'].read().decode('utf-8')
            data = json.loads(file_content)
        else:
            # Direct invocation (via CLI, test console, or API)
            data = event

        if not data:
            raise ValueError("No valid payload found in event")

        # 2. Extract Parking Detection Data
        zone_id = data.get('zone_id', 'ZONE-A')
        zone_name = data.get('zone_name', 'Campus Parking Lot')
        camera_id = data.get('camera_id', 'CAM-01')
        spots = data.get('spots', [])
        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        image_s3_url = data.get('image_s3_url', '')

        total_spots = len(spots)
        occupied_count = 0
        vacant_spots_list = []
        occupied_spots_list = []

        # 3. Update DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        
        with table.batch_writer() as batch:
            for spot in spots:
                spot_id = spot.get('spot_id')
                status = spot.get('status', 'VACANT').upper() # 'OCCUPIED' or 'VACANT'
                confidence = Decimal(str(round(spot.get('confidence', 0.90), 2)))
                vehicle_type = spot.get('vehicle_type', 'none')
                
                if status == 'OCCUPIED':
                    occupied_count += 1
                    occupied_spots_list.append(spot_id)
                else:
                    vacant_spots_list.append(spot_id)

                # Write individual spot record
                batch.put_item(
                    Item={
                        'SpotId': spot_id,
                        'ZoneId': zone_id,
                        'Status': status,
                        'Confidence': confidence,
                        'VehicleType': vehicle_type,
                        'LastUpdated': timestamp,
                        'CameraId': camera_id,
                        'ImageS3Url': image_s3_url
                    }
                )

        vacant_count = total_spots - occupied_count
        occupancy_rate = (occupied_count / total_spots * 100) if total_spots > 0 else 0.0

        # Save Zone-level aggregated summary item
        table.put_item(
            Item={
                'SpotId': f"SUMMARY_{zone_id}",
                'ZoneId': zone_id,
                'ZoneName': zone_name,
                'Status': 'FULL' if occupancy_rate >= OCCUPANCY_ALERT_THRESHOLD else 'AVAILABLE',
                'TotalSpots': total_spots,
                'OccupiedCount': occupied_count,
                'VacantCount': vacant_count,
                'OccupancyRatePct': Decimal(str(round(occupancy_rate, 1))),
                'VacantSpotIds': vacant_spots_list,
                'LastUpdated': timestamp
            }
        )

        print(f"[SUMMARY] Zone: {zone_id} | Total: {total_spots} | Occupied: {occupied_count} | Vacant: {vacant_count} | Occupancy: {occupancy_rate:.1f}%")

        # 4. Trigger SNS Mobile / Email Alert if Threshold Exceeded
        alert_sent = False
        if occupancy_rate >= OCCUPANCY_ALERT_THRESHOLD and SNS_TOPIC_ARN:
            alert_subject = f"🚨 Campus Parking Alert: {zone_id} is {occupancy_rate:.0f}% FULL"
            alert_body = (
                f"=========================================\n"
                f" CAMPUS SMART PARKING SYSTEM ALERT       \n"
                f"=========================================\n\n"
                f"📍 Zone: {zone_name} ({zone_id})\n"
                f"📊 Occupancy Rate: {occupancy_rate:.1f}%\n"
                f"🚗 Occupied Spots: {occupied_count} / {total_spots}\n"
                f"🟢 Available Spots Left: {vacant_count} ({', '.join(vacant_spots_list) if vacant_spots_list else 'None'})\n"
                f"🕒 Timestamp: {timestamp}\n"
                f"📷 Camera ID: {camera_id}\n\n"
                f"⚠️ ADVISORY:\n"
                f"Parking capacity in {zone_id} has crossed {OCCUPANCY_ALERT_THRESHOLD}%. Students and staff are advised to proceed to alternative lots.\n\n"
                f"-- Powered by AWS EC2 (YOLOv8 CV) + S3 + Lambda + DynamoDB + SNS"
            )
            
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=alert_subject,
                Message=alert_body
            )
            alert_sent = True
            print(f"[SNS] Published alert notification to {SNS_TOPIC_ARN}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'zone_id': zone_id,
                'total_spots': total_spots,
                'occupied_count': occupied_count,
                'vacant_count': vacant_count,
                'occupancy_rate_pct': occupancy_rate,
                'alert_triggered': alert_sent,
                'timestamp': timestamp
            })
        }

    except Exception as e:
        print(f"[ERROR] Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error_message': str(e)
            })
        }
