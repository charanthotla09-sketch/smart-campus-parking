#!/bin/bash
# ==============================================================================
# 1-Command Bootstrap for Smart Campus Parking System
# ==============================================================================
set -e

echo "=== [1/4] Installing System Packages ==="
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git unzip libgl1-mesa-glx libglib2.0-0 awscli

echo "=== [2/4] Downloading Latest Project Files from S3 ==="
mkdir -p /home/ubuntu/smart_parking
cd /home/ubuntu/smart_parking
aws s3 cp s3://campus-parking-storage-905223168527-ap-south-1/code/smart_parking.zip /tmp/smart_parking.zip --region ap-south-1
unzip -o /tmp/smart_parking.zip -d /home/ubuntu/smart_parking
chown -R ubuntu:ubuntu /home/ubuntu/smart_parking

echo "=== [3/4] Installing Python Virtual Environment & Packages ==="
sudo -u ubuntu python3 -m venv /home/ubuntu/smart_parking/venv
sudo -u ubuntu /home/ubuntu/smart_parking/venv/bin/pip install --upgrade pip
sudo -u ubuntu /home/ubuntu/smart_parking/venv/bin/pip install boto3 opencv-python-headless pillow numpy streamlit pandas

echo "=== [4/4] Setting Up Systemd Background Services ==="
cat << 'EOF' > /etc/systemd/system/parking-dashboard.service
[Unit]
Description=Campus Smart Parking Streamlit Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/smart_parking
ExecStart=/home/ubuntu/smart_parking/venv/bin/streamlit run /home/ubuntu/smart_parking/dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5
Environment=AWS_DEFAULT_REGION=ap-south-1
Environment=PYTHONPATH=/home/ubuntu/smart_parking:/home/ubuntu/smart_parking/ec2

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/parking-detector.service
[Unit]
Description=Campus Parking CV Detection Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/smart_parking/ec2
ExecStart=/home/ubuntu/smart_parking/venv/bin/python3 /home/ubuntu/smart_parking/ec2/parking_detector.py --s3-bucket campus-parking-storage-905223168527-ap-south-1 --region ap-south-1 --mode simulate
Restart=always
RestartSec=10
Environment=AWS_DEFAULT_REGION=ap-south-1
Environment=PYTHONPATH=/home/ubuntu/smart_parking:/home/ubuntu/smart_parking/ec2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable parking-dashboard
systemctl restart parking-dashboard
systemctl enable parking-detector
systemctl restart parking-detector

echo "=========================================================="
echo "🎉 SUCCESS! The Smart Campus Parking System is now LIVE!"
echo "🌐 Live Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo "=========================================================="
