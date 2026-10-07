# 🚗 AI-Powered Smart Campus Parking System
### End-to-End AWS Deployment Guide & Project Report

---

## 📌 Project Overview
The **AI-Powered Smart Campus Parking System** solves urban campus congestion by combining **IoT Camera Simulation**, **Computer Vision (YOLOv8 / OpenCV)**, and **Serverless AWS Cloud Architecture**.

- **EC2 Instance**: Hosts the computer vision engine, camera stream ingestion, and real-time dashboard.
- **Amazon S3**: Stores raw CCTV frames, annotated detection snapshots, and JSON detection reports.
- **AWS Lambda**: Event-driven serverless compute triggered by S3 uploads to process occupancy metrics.
- **Amazon DynamoDB**: Real-time NoSQL state store tracking individual spot availability (`A-01` to `A-12`) and zone summaries.
- **Amazon SNS**: Sends instant email and SMS notifications when lots exceed capacity thresholds (e.g., >80% full).

```
   ┌────────────────────────────────────────────────────────┐
   │            IoT Camera / Synthetic Feed                 │
   └──────────────────────────┬─────────────────────────────┘
                              │ Real-Time Frames
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │        AWS EC2 (YOLOv8 / OpenCV Inference)             │
   │  • Detects vehicles (Cars, Trucks, Motorcycles)       │
   │  • Maps bounding boxes to Parking Bay Polygons         │
   │  • Overlays HUD (Green = Vacant, Red = Occupied)       │
   └─────────────┬────────────────────────────┬─────────────┘
                 │ Annotated JPGs             │ Detection JSONs
                 ▼                            ▼
   ┌────────────────────────────────────────────────────────┐
   │                    Amazon S3 Bucket                    │
   │  • s3://campus-parking-storage/snapshots/*.jpg         │
   │  • s3://campus-parking-storage/detections/*.json       │
   └──────────────────────────┬─────────────────────────────┘
                              │ S3 PutObject Event Trigger
                              ▼
   ┌────────────────────────────────────────────────────────┐
   │             AWS Lambda (Event Processor)               │
   │  • Parses spot metadata and calculates occupancy %     │
   │  • Formats batch updates                               │
   └─────────────┬────────────────────────────┬─────────────┘
                 │ Batch PutItem              │ Threshold >= 80%
                 ▼                            ▼
   ┌──────────────────────────┐  ┌──────────────────────────┐
   │     Amazon DynamoDB      │  │        Amazon SNS        │
   │  • SpotId (Primary Key)  │  │  • Topic: CampusAlerts   │
   │  • Status, Confidence    │  │  • Mobile / Email Alert  │
   │  • LastUpdated Timestamp │  │  • "Lot A is 92% Full"   │
   └──────────────────────────┘  └──────────────────────────┘
```

---

## 🚀 Deployment Options

You can deploy this project using either:
1. **Option A (Automated CloudFormation)**: Deploy all cloud infrastructure in 2 minutes.
2. **Option B (Step-by-Step Console Guide)**: Detailed manual walkthrough for assignments and exams.

---

## 🛠️ Option A: Automated CloudFormation Deployment (Recommended)

1. Open AWS CloudFormation Console: https://console.aws.amazon.com/cloudformation/
2. Click **Create stack** ➜ **With new resources (standard)**.
3. Under **Template source**, select **Upload a template file** and choose `cloudformation/parking_system_template.yaml`.
4. Enter parameters:
   - **Stack name**: `smart-campus-parking`
   - **AlertEmail**: Your email address (to receive SNS parking notifications).
5. Acknowledge IAM capabilities and click **Submit**.
6. Check your email inbox and click **"Confirm subscription"** in the AWS Notification email.

---

## 📋 Option B: Step-by-Step AWS Console Walkthrough

### Step 1: Create Amazon S3 Bucket
1. Go to **S3 Console** ➜ Click **Create bucket**.
2. **Bucket name**: `campus-parking-storage-<your-aws-account-id>` (must be globally unique).
3. **AWS Region**: `us-east-1` (or your preferred region).
4. Keep **Block all public access** checked (Private bucket).
5. Click **Create bucket**.
6. Inside your bucket, create two folders:
   - `snapshots/`
   - `detections/`

---

### Step 2: Create Amazon DynamoDB Table
1. Go to **DynamoDB Console** ➜ Click **Create table**.
2. **Table name**: `CampusParkingSpots`
3. **Partition key (Hash key)**: `SpotId` (Type: `String`)
4. **Table class**: DynamoDB Standard
5. **Capacity mode**: `On-demand` (Pay per request - Free tier friendly).
6. Click **Create table**.

---

### Step 3: Create Amazon SNS Topic & Subscription
1. Go to **SNS Console** ➜ **Topics** ➜ Click **Create topic**.
2. **Type**: `Standard`.
3. **Name**: `CampusParkingAlerts`.
4. **Display name**: `Campus Parking Alerts`.
5. Click **Create topic** and copy the **Topic ARN** (e.g. `arn:aws:sns:us-east-1:123456789012:CampusParkingAlerts`).
6. Click **Create subscription**:
   - **Protocol**: `Email`
   - **Endpoint**: `<your-email-address@domain.com>`
   - Click **Create subscription**.
7. Open your email inbox and click **Confirm subscription**.

---

### Step 4: Create IAM Roles for Lambda & EC2

#### 4.1 Lambda Role:
1. Go to **IAM Console** ➜ **Roles** ➜ **Create role**.
2. **Trusted entity**: `AWS service` ➜ Use case: `Lambda`.
3. Attach policies:
   - `AWSLambdaBasicExecutionRole` (AWS managed)
4. Add Inline Policy (`CampusParkingLambdaPolicy`):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::campus-parking-storage-*", "arn:aws:s3:::campus-parking-storage-*/*"]
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem", "dynamodb:BatchWriteItem", "dynamodb:GetItem", "dynamodb:Scan"],
      "Resource": "arn:aws:dynamodb:*:*:table/CampusParkingSpots"
    },
    {
      "Effect": "Allow",
      "Action": ["sns:Publish"],
      "Resource": "arn:aws:sns:*:*:CampusParkingAlerts"
    }
  ]
}
```
5. Name role: `CampusParkingLambdaRole` and click **Create role**.

#### 4.2 EC2 Role & Instance Profile:
1. Create role with trusted entity `EC2`.
2. Attach policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::campus-parking-storage-*", "arn:aws:s3:::campus-parking-storage-*/*"]
    }
  ]
}
```
3. Name role: `CampusParkingEC2Role`.

---

### Step 5: Create AWS Lambda Function & S3 Event Trigger
1. Go to **Lambda Console** ➜ Click **Create function**.
2. **Function name**: `CampusParkingProcessor`
3. **Runtime**: `Python 3.11` (or Python 3.10/3.12).
4. **Execution role**: Choose existing role ➜ Select `CampusParkingLambdaRole`.
5. Click **Create function**.
6. In **Code Source**, copy & paste the content from `lambda/lambda_function.py`.
7. Go to **Configuration** ➜ **Environment variables** ➜ Add:
   - `DYNAMODB_TABLE`: `CampusParkingSpots`
   - `SNS_TOPIC_ARN`: `<Your-SNS-Topic-ARN>`
   - `OCCUPANCY_ALERT_THRESHOLD`: `80`
8. Click **Deploy**.
9. Click **Add trigger** ➜ Select **S3**:
   - **Bucket**: `campus-parking-storage-<id>`
   - **Event types**: `All object create events` (`s3:ObjectCreated:*`)
   - **Prefix**: `detections/`
   - **Suffix**: `.json`
   - Check confirmation and click **Add**.

---

### Step 6: Launch EC2 Instance & Run Computer Vision Engine
1. Go to **EC2 Console** ➜ Click **Launch Instance**.
2. **Name**: `SmartCampusParking-CV-Server`.
3. **AMI**: Ubuntu 22.04 LTS or Amazon Linux 2023.
4. **Instance Type**: `t3.medium` (recommended) or `t2.micro` (free tier).
5. **Key pair**: Select or create key pair.
6. **Network Settings / Security Group**:
   - Inbound SSH (Port `22`) from your IP.
   - Inbound Custom TCP (Port `8501`) from `0.0.0.0/0` (Streamlit Dashboard).
   - Inbound HTTP (Port `80`) from `0.0.0.0/0`.
7. **Advanced Details** ➜ **IAM instance profile**: Select `CampusParkingEC2Role`.
8. Click **Launch Instance**.

---

### Step 7: Configure and Run Detection on EC2
Connect to your EC2 instance via SSH:
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

Clone or transfer the project files and run setup:
```bash
# 1. Update and install dependencies
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git libgl1 libglib2.0-0

# 2. Setup Virtual Environment
mkdir -p ~/smart_parking && cd ~/smart_parking
python3 -m venv venv
source venv/bin/activate

# 3. Install required libraries
pip install boto3 opencv-python-headless pillow numpy ultralytics streamlit pandas

# 4. Run single detection test
python3 parking_detector.py --s3-bucket campus-parking-storage-<id> --mode once

# 5. Run continuous simulation worker
python3 parking_detector.py --s3-bucket campus-parking-storage-<id> --mode simulate
```

---

### Step 8: Launch the Live Web Dashboard
On the EC2 instance, start the Streamlit UI:
```bash
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```
Open your browser and navigate to:
```
http://<EC2-PUBLIC-IP>:8501
```

---

## 🧪 Testing & Verification Checklist

| Test Case | Procedure | Expected Outcome |
| :--- | :--- | :--- |
| **1. Spot Detection** | Run `parking_detector.py --mode once` | Generates `latest_snapshot.jpg` with Green boxes for free spots & Red boxes for occupied spots. |
| **2. S3 Upload** | Verify S3 Bucket via Console or CLI | New files appear in `snapshots/*.jpg` and `detections/*.json`. |
| **3. Lambda Execution** | Check Lambda CloudWatch Logs (`/aws/lambda/CampusParkingProcessor`) | Log shows spot parsing and successful batch write to DynamoDB. |
| **4. DynamoDB State** | Query `CampusParkingSpots` table in DynamoDB | Spots `A-01` to `A-12` contain current `Status`, `Confidence`, and `LastUpdated`. |
| **5. SNS Alert** | Simulate >80% occupancy (e.g. 10/12 spots occupied) | Instant Email / SMS alert received with zone occupancy & vacancy details! |

---

## 💰 Cost Optimization & Free Tier Guidelines
- **EC2**: 750 hours/month of `t2.micro` or `t3.micro` are free under AWS Free Tier.
- **S3**: 5 GB of standard storage and 20,000 GET / 2,000 PUT requests are free.
- **Lambda**: 1,000,000 free requests per month.
- **DynamoDB**: 25 GB free storage & 25 read/write capacity units under Free Tier.
- **SNS**: 1,000,000 free Amazon SNS publishes/month; first 100 SMS are free (varies by country) and unlimited email notifications.
- **Cleanup**: Delete the CloudFormation stack or terminate EC2 when finished to avoid charges.

---

## 🎓 Academic Presentation Tips
1. **Highlight Architecture Synergy**: Emphasize how EC2 offloads heavy edge AI inference while Lambda + DynamoDB handle high-velocity asynchronous state updates.
2. **Show Live Alert Demonstration**: Trigger high-occupancy simulation in the UI and show the AWS SNS alert email landing in your inbox live!
3. **Edge-to-Cloud Discussion**: Explain how this model scales to hundreds of campus cameras using AWS IoT Greengrass on edge devices with centralized DynamoDB aggregation.
