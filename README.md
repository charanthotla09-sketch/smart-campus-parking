# 🛡️ ParkVision AI™ Enterprise - Smart Campus Parking System

[![AWS Architecture](https://img.shields.io/badge/AWS-Cloud%20Native-orange?logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer%20Vision-00FFFF?logo=ultralytics)](https://ultralytics.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, cloud-native IoT and Computer Vision Smart Campus Parking Intelligence System built on **Amazon Web Services (AWS)** and **YOLOv8**. Detects both parked (occupied) and vacant spaces from physical CCTV camera feeds, RTSP video streams, or mobile uploads, and synchronizes real-time occupancy across Amazon DynamoDB, AWS Lambda, S3, and Amazon SNS.

---

## 🌟 Key Features

- **📹 Autonomous Multi-Angle Optical CCTV Stream Analysis**:
  - Dynamically detects **🔴 Parked (Occupied)** and **🟢 Non-Parked (Vacant)** parking spaces.
  - Supports arbitrary CCTV camera angles (*Angled Perspective*, *Bird's Eye 90°*, *Ground / Street Level*, *Wide Angle*).
  - Works with real CCTV cameras, RTSP streams, phone uploads, and synthetic campus lot simulators.

- **📱 Smart Mobile GPS Navigator & Digital Parking Pass**:
  - Live turn-by-turn routing to the nearest available vacant bay.
  - Holographic Digital Campus Parking Pass with encrypted QR security tokens.
  - 1-tap spot reservation with instant database sync.

- **⚡ Amazon DynamoDB Serverless Architecture (5 Core Tables)**:
  - `CampusParkingSpots`: Real-time parking bay state, vehicle classification, and confidence.
  - `CampusParkingReservations`: Student & corporate staff reservation registry.
  - `CampusParkingAuditLogs`: High-occupancy alarms (≥80%) and CCTV telemetry.
  - `CampusParkingZones`: Campus parking lot registries and GPS coordinates.
  - `CampusParkingViolations`: Unauthorized parking detection and infraction tracking.

- **🔔 Automated Incident Alarms (Amazon SNS)**:
  - Real-time SMS and email broadcasts to campus security when capacity reaches critical thresholds (≥80%).

- **🌌 Next-Gen Midnight Obsidian & Aurora Cyber Design**:
  - Executive command center dashboard with frosted glassmorphism containers and PyDeck 3D geographic satellite maps.
  - Role-segregated portals for **Students**, **Corporate Employees**, and **Security Admins**.

---

## 🏗️ System Architecture

```text
[ Physical CCTV / IP RTSP / Upload ]
                 │
                 ▼
      [ AWS EC2 Instance (t3.small) ]
   (YOLOv8 / OpenCV Computer Vision Detector)
                 │
                 ├──────────────────────────────┐
                 ▼                              ▼
  [ Amazon S3 (Raw & Annotated Frames) ]  [ Streamlit Web Command Center ]
                 │
                 ▼ (S3 Event Notification)
       [ AWS Lambda Processor ]
                 │
        ┌────────┴────────┐
        ▼                 ▼
[ Amazon DynamoDB ] [ Amazon SNS (Email/SMS Alerts) ]
(Real-Time NoSQL)   (Dispatched to Campus Officers & Drivers)
```

---

## 📁 Repository Structure

```text
├── cloudformation/
│   └── parking_system_template.yaml  # Complete AWS CloudFormation IaC Blueprint
├── dashboard/
│   └── app.py                        # Streamlit Executive Dark Command Center UI
├── ec2/
│   ├── parking_detector.py           # YOLOv8 / OpenCV Dynamic Vision Engine
│   └── iot_camera_simulator.py       # Multi-Zone Camera Frame Generator
├── lambda/
│   └── lambda_function.py            # Serverless Event Handler & SNS Dispatcher
├── scripts/
│   ├── setup_dynamodb.py             # DynamoDB 5-Table Provisioner & Health Check
│   ├── setup_ec2.sh                  # Ubuntu / Amazon Linux System Provisioning
│   ├── deploy_direct.py              # Automated Boto3 Cloud Provisioner
│   └── bootstrap.sh                  # 1-Command EC2 Systemd Setup Script
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git exclusion rules
├── DEPLOYMENT_GUIDE.md               # Complete Step-by-Step AWS Setup Guide
└── README.md                         # Project Documentation
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/smart-campus-parking.git
cd smart-campus-parking
```

### 2. Install Dependencies
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # On Linux/macOS
# .\venv\Scripts\activate      # On Windows PowerShell

# Install Python packages
pip install -r requirements.txt
```

### 3. Provision DynamoDB Tables on AWS
Ensure your AWS credentials are configured (`aws configure`):
```bash
python scripts/setup_dynamodb.py
```

### 4. Launch the Web Dashboard
```bash
streamlit run dashboard/app.py
```
Open **`http://localhost:8501`** in your browser.

---

## ☁️ Deployment on AWS EC2

Run this 1-line command on your EC2 instance (`Ubuntu 22.04 LTS`):
```bash
cd ~/smart_parking && source venv/bin/activate && streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🛡️ License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
