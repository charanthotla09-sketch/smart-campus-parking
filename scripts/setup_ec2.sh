#!/bin/bash
# ==============================================================================
# AI-Powered Smart Campus Parking System - EC2 Instance Provisioning Script
# Compatible with Ubuntu 22.04 / 24.04 LTS & Amazon Linux 2023
# ==============================================================================

set -e

echo "=== [1/5] Updating system packages ==="
if [ -f /etc/debian_version ]; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git libgl1-mesa-glx libglib2.0-0 awscli
elif [ -f /etc/amazon-linux-release ]; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip git mesa-libGL glib2 awscli
fi

echo "=== [2/5] Setting up Python Virtual Environment ==="
mkdir -p ~/smart_parking && cd ~/smart_parking
python3 -m venv venv
source venv/bin/activate

echo "=== [3/5] Installing Deep Learning, Computer Vision & AWS Dependencies ==="
pip install --upgrade pip
# Ultralytics for YOLOv8, OpenCV for computer vision, Boto3 for AWS SDK, Streamlit for dashboard
pip install boto3 opencv-python-headless pillow numpy ultralytics streamlit

echo "=== [4/5] Downloading YOLOv8 pre-trained weights ==="
python3 -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); print('YOLOv8 Nano model cached successfully!')"

echo "=== [5/5] Setup Complete! ==="
echo "To run detection worker:"
echo "  source ~/smart_parking/venv/bin/activate"
echo "  python3 parking_detector.py --s3-bucket YOUR_S3_BUCKET_NAME --mode simulate"
