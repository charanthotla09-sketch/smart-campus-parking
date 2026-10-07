"""
ParkVision AI™ - Enterprise CCTV Parking Detection Engine
Processes RTSP streams, IP Cameras, Video Files, Webcams, and Synthetic CCTV feeds.
"""

import os
import sys
import json
import cv2
import numpy as np
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_SNAPSHOT_PATH = os.path.join(DATA_DIR, "latest_snapshot.jpg")

class EnterpriseParkingDetector:
    def __init__(self, s3_bucket=None, aws_region="ap-south-1", use_yolo=True):
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.yolo_model = None
        self.s3_client = None
        
        try:
            self.s3_client = boto3.client("s3", region_name=aws_region)
        except Exception:
            pass

        if use_yolo:
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO("yolov8n.pt")
                print("[ParkVision AI] YOLOv8 Nano Neural Network loaded.")
            except Exception as e:
                print(f"[ParkVision AI] YOLO fallback to optical variance analyzer: {e}")

    def compute_iou(self, boxA, boxB):
        """Calculates Intersection over Union / coverage between vehicle and bay."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]

        if boxBArea == 0:
            return 0.0
        return interArea / float(boxBArea)

    def analyze_spot_optical(self, frame, spot_bbox):
        """Optical texture, edge density, and color variance spot classifier."""
        x, y, w, h = spot_bbox
        # Inset margin to avoid pavement lines
        mx = int(w * 0.15)
        my = int(h * 0.15)
        crop = frame[max(0, y + my): min(frame.shape[0], y + h - my), max(0, x + mx): min(frame.shape[1], x + w - mx)]
        
        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return "VACANT", 0.90, "none"

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray)
        edges = cv2.Canny(gray, 40, 120)
        edge_density = np.count_nonzero(edges) / float(crop.shape[0] * crop.shape[1])
        
        b, g, r = cv2.split(crop)
        color_diff = np.mean(np.abs(r.astype(int) - b.astype(int)))

        is_occupied = (edge_density > 0.038) or (std_dev > 26.0) or (color_diff > 16.0)
        conf = min(0.99, max(0.70, (std_dev / 38.0) * 0.88)) if is_occupied else min(0.99, max(0.75, 1.0 - edge_density * 8))
        return ("OCCUPIED" if is_occupied else "VACANT"), round(conf, 2), ("sedan" if is_occupied else "none")

    def process_cctv_frame(self, frame, zone_config):
        """Processes an enterprise CCTV camera frame against defined parking bays."""
        annotated = frame.copy()
        spot_results = []
        occupied_count = 0
        violations = []

        detected_vehicles = []
        if self.yolo_model is not None:
            results = self.yolo_model(frame, verbose=False, classes=[2, 3, 5, 7]) # car, motorcycle, bus, truck
            for r in results:
                for box in r.boxes:
                    bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    detected_vehicles.append({
                        "bbox": [int(bx1), int(by1), int(bx2 - bx1), int(by2 - by1)],
                        "confidence": conf,
                        "type": self.yolo_model.names.get(cls_id, "car")
                    })

        for spot in zone_config["spots"]:
            spot_id = spot["spot_id"]
            x, y, w, h = spot["bbox"]
            spot_type = spot.get("type", "standard") # standard, ev_charging, handicap, vip, faculty

            status = "VACANT"
            confidence = 0.95
            vehicle_type = "none"

            if self.yolo_model is not None:
                best_match = None
                best_iou = 0.0
                for veh in detected_vehicles:
                    iou = self.compute_iou(veh["bbox"], [x, y, w, h])
                    if iou > 0.30 and iou > best_iou:
                        best_iou = iou
                        best_match = veh
                
                if best_match:
                    status = "OCCUPIED"
                    confidence = round(best_match["confidence"], 2)
                    vehicle_type = best_match["type"]
                else:
                    status = "VACANT"
                    confidence = 0.94
            else:
                status, confidence, vehicle_type = self.analyze_spot_optical(frame, [x, y, w, h])

            if status == "OCCUPIED":
                occupied_count += 1
                color_bgr = (40, 40, 240) # Neon Crimson Red
                badge_bg = (20, 20, 180)
            else:
                color_bgr = (50, 220, 50) # Emerald Neon Green
                badge_bg = (20, 140, 20)
                
            # Check for parking violations (e.g., unauthorized parking in EV / Handicap / VIP)
            if status == "OCCUPIED" and spot_type in ["handicap", "vip"]:
                if confidence > 0.85:
                    violations.append(f"Special Access Bay {spot_id} ({spot_type.upper()}) is occupied.")

            # Draw glowing bay bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color_bgr, 2)
            
            # Semi-transparent spot fill
            overlay = annotated.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color_bgr, -1)
            cv2.addWeighted(overlay, 0.16, annotated, 0.84, 0, annotated)

            # Spot header badge
            badge_h = 22
            cv2.rectangle(annotated, (x, y - badge_h), (x + w, y), badge_bg, -1)
            label = f"{spot_id}: {status}"
            cv2.putText(annotated, label, (x + 6, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

            spot_results.append({
                "spot_id": spot_id,
                "status": status,
                "confidence": confidence,
                "vehicle_type": vehicle_type,
                "spot_type": spot_type,
                "bbox": [x, y, w, h]
            })

        total_spots = len(zone_config["spots"])
        vacant_count = total_spots - occupied_count
        occ_rate = (occupied_count / total_spots * 100) if total_spots > 0 else 0.0

        # CCTV On-Screen HUD Overlay
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.rectangle(annotated, (15, 15), (480, 80), (15, 20, 25), -1)
        hud_border = (0, 0, 255) if occ_rate >= 80 else (0, 255, 150)
        cv2.rectangle(annotated, (15, 15), (480, 80), hud_border, 2)
        
        cv2.putText(annotated, f"PARKVISION AI | {zone_config.get('zone_id', 'ZONE-A')} | {now_str}",
                    (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(annotated, f"OCCUPANCY: {occupied_count}/{total_spots} ({occ_rate:.1f}%) | VACANT: {vacant_count}",
                    (25, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.52, hud_border, 2, cv2.LINE_AA)

        summary = {
            "zone_id": zone_config.get("zone_id", "ZONE-A"),
            "zone_name": zone_config.get("zone_name", "Enterprise Parking Facility"),
            "camera_id": zone_config.get("camera_id", "CCTV-CAM-01"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_spots": total_spots,
            "occupied_count": occupied_count,
            "vacant_count": vacant_count,
            "occupancy_rate_pct": round(occ_rate, 1),
            "spots": spot_results,
            "violations": violations
        }

        return annotated, summary

    def upload_to_aws(self, annotated_frame, summary, local_path=DEFAULT_SNAPSHOT_PATH):
        """Uploads snapshot and triggers Lambda/DynamoDB/SNS via S3."""
        if not self.s3_bucket:
            return False
            
        cv2.imwrite(local_path, annotated_frame)
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        img_key = f"snapshots/{summary['zone_id']}_{ts_str}.jpg"
        latest_key = f"snapshots/latest_{summary['zone_id']}.jpg"
        json_key = f"detections/{summary['zone_id']}_{ts_str}.json"
        
        summary["image_s3_url"] = f"s3://{self.s3_bucket}/{img_key}"
        
        try:
            if not self.s3_client:
                self.s3_client = boto3.client("s3", region_name=self.aws_region)
                
            self.s3_client.upload_file(local_path, self.s3_bucket, img_key, ExtraArgs={'ContentType': 'image/jpeg'})
            self.s3_client.upload_file(local_path, self.s3_bucket, latest_key, ExtraArgs={'ContentType': 'image/jpeg'})
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=json_key,
                Body=json.dumps(summary, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"[AWS Sync Error] {e}")
            return False

ParkingDetector = EnterpriseParkingDetector
