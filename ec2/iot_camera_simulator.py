"""
AI-Powered Smart Campus Parking System - Real-Time IoT Camera & Vehicle Dynamics Simulator
Generates synthetic high-fidelity CCTV camera frames with realistic vehicle physics, lighting, and bay coordinates.
"""

import cv2
import numpy as np
import random
import time
from datetime import datetime, timezone

# Multi-Zone Campus Parking Definitions
CAMPUS_ZONES = {
    "ZONE-A": {
        "zone_id": "ZONE-A",
        "zone_name": "North Academic Lot A (Engineering & Science)",
        "camera_id": "CAM-LOT-A-NORTH",
        "capacity": 12,
        "spots": [
            {"spot_id": "A-01", "bbox": [120, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-02", "bbox": [250, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-03", "bbox": [380, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-04", "bbox": [510, 180, 110, 190], "type": "ev_charging"},
            {"spot_id": "A-05", "bbox": [660, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-06", "bbox": [790, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-07", "bbox": [920, 180, 110, 190], "type": "standard"},
            {"spot_id": "A-08", "bbox": [1050, 180, 110, 190], "type": "handicap"},
            {"spot_id": "A-09", "bbox": [120, 440, 110, 190], "type": "standard"},
            {"spot_id": "A-10", "bbox": [250, 440, 110, 190], "type": "standard"},
            {"spot_id": "A-11", "bbox": [380, 440, 110, 190], "type": "standard"},
            {"spot_id": "A-12", "bbox": [510, 440, 110, 190], "type": "faculty"},
        ]
    },
    "ZONE-B": {
        "zone_id": "ZONE-B",
        "zone_name": "South Campus Lot B (Library & Student Center)",
        "camera_id": "CAM-LOT-B-SOUTH",
        "capacity": 8,
        "spots": [
            {"spot_id": "B-01", "bbox": [150, 200, 120, 200], "type": "standard"},
            {"spot_id": "B-02", "bbox": [300, 200, 120, 200], "type": "standard"},
            {"spot_id": "B-03", "bbox": [450, 200, 120, 200], "type": "ev_charging"},
            {"spot_id": "B-04", "bbox": [600, 200, 120, 200], "type": "standard"},
            {"spot_id": "B-05", "bbox": [750, 200, 120, 200], "type": "standard"},
            {"spot_id": "B-06", "bbox": [900, 200, 120, 200], "type": "handicap"},
            {"spot_id": "B-07", "bbox": [150, 450, 120, 200], "type": "standard"},
            {"spot_id": "B-08", "bbox": [300, 450, 120, 200], "type": "standard"},
        ]
    }
}

CAMPUS_PARKING_CONFIG = CAMPUS_ZONES["ZONE-A"]

CAR_PRESETS = [
    {"name": "sedan", "color": (40, 40, 210), "label": "Sedan (Red)"},
    {"name": "suv", "color": (210, 210, 215), "label": "SUV (White)"},
    {"name": "sedan", "color": (25, 25, 25), "label": "Sedan (Black)"},
    {"name": "hatchback", "color": (210, 110, 25), "label": "Hatchback (Blue)"},
    {"name": "suv", "color": (45, 130, 45), "label": "SUV (Green)"},
    {"name": "sedan", "color": (160, 160, 60), "label": "Sedan (Cyan)"},
    {"name": "truck", "color": (80, 80, 120), "label": "Pickup (Grey)"},
]

def draw_realistic_car(image, bbox, preset=None):
    """Draws a vehicle inside a spot bounding box with windshield and roof detail."""
    x, y, w, h = bbox
    car = preset if preset else random.choice(CAR_PRESETS)
    car_color = car["color"]
    
    margin_x = 10
    margin_y = 12
    cx = x + margin_x
    cy = y + margin_y
    cw = w - (margin_x * 2)
    ch = h - (margin_y * 2)
    
    # Car body (rounded rect)
    cv2.rectangle(image, (cx, cy), (cx + cw, cy + ch), car_color, -1)
    cv2.rectangle(image, (cx, cy), (cx + cw, cy + ch), (15, 15, 15), 2)
    
    # Windshields
    window_color = (60, 60, 70)
    front_glass_y = cy + int(ch * 0.22)
    rear_glass_y = cy + int(ch * 0.70)
    
    cv2.rectangle(image, (cx + 6, front_glass_y - 12), (cx + cw - 6, front_glass_y), window_color, -1)
    cv2.rectangle(image, (cx + 6, rear_glass_y), (cx + cw - 6, rear_glass_y + 12), window_color, -1)
    
    # Roof
    roof_color = (max(0, car_color[0]-30), max(0, car_color[1]-30), max(0, car_color[2]-30))
    cv2.rectangle(image, (cx + 8, front_glass_y + 2), (cx + cw - 8, rear_glass_y - 2), roof_color, -1)
    
    # Headlights & Taillights
    cv2.rectangle(image, (cx + 4, cy), (cx + 14, cy + 4), (200, 255, 255), -1)
    cv2.rectangle(image, (cx + cw - 14, cy), (cx + cw - 4, cy + 4), (200, 255, 255), -1)
    cv2.rectangle(image, (cx + 4, cy + ch - 4), (cx + 14, cy + ch), (30, 30, 220), -1)
    cv2.rectangle(image, (cx + cw - 14, cy + ch - 4), (cx + cw - 4, cy + ch), (30, 30, 220), -1)

    return car.get("name", "car")

def generate_parking_frame(occupied_spot_ids=None, zone_key="ZONE-A"):
    """Generates a complete CCTV frame with campus background, marked bays and parked vehicles."""
    zone_config = CAMPUS_ZONES.get(zone_key, CAMPUS_ZONES["ZONE-A"])
    width, height = 1280, 720
    
    # Asphalt background
    frame = np.full((height, width, 3), (72, 75, 78), dtype=np.uint8)
    
    # Add texture noise
    noise = np.random.normal(0, 3, (height, width, 3)).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Sidewalk / Campus curb
    cv2.rectangle(frame, (0, 0), (width, 100), (50, 105, 50), -1) # Green lawn
    cv2.rectangle(frame, (0, 95), (width, 120), (135, 135, 135), -1) # Sidewalk curb
    
    # Center driving lane dividers
    for x in range(50, width - 50, 60):
        cv2.line(frame, (x, 400), (x + 35, 400), (0, 215, 255), 3)

    if occupied_spot_ids is None:
        num_occupied = random.randint(7, 11)
        occupied_spot_ids = set(random.sample([s["spot_id"] for s in zone_config["spots"]], num_occupied))
    else:
        occupied_spot_ids = set(occupied_spot_ids)
        
    vehicle_map = {}
    for spot in zone_config["spots"]:
        x, y, w, h = spot["bbox"]
        spot_id = spot["spot_id"]
        spot_type = spot.get("type", "standard")
        
        # Bay outline
        bay_line_color = (230, 230, 230)
        if spot_type == "ev_charging":
            bay_line_color = (0, 200, 255) # Yellow/Cyan for EV
        elif spot_type == "handicap":
            bay_line_color = (255, 180, 50) # Blue for Accessible
            
        cv2.rectangle(frame, (x, y), (x + w, y + h), bay_line_color, 2)
        
        # Spot ID label
        cv2.putText(frame, spot_id, (x + 24, y + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        if spot_type != "standard":
            cv2.putText(frame, spot_type.upper(), (x + 10, y + h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, bay_line_color, 1)

        # Draw vehicle
        if spot_id in occupied_spot_ids:
            v_type = draw_realistic_car(frame, spot["bbox"])
            vehicle_map[spot_id] = v_type

    # CCTV HUD Header
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cv2.rectangle(frame, (0, 0), (width, 40), (20, 20, 20), -1)
    cctv_text = f"CAMPUS CCTV | {zone_config['camera_id']} | {zone_config['zone_name']} | {now} | 30 FPS"
    cv2.putText(frame, cctv_text, (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)
    
    cv2.circle(frame, (width - 40, 20), 7, (0, 0, 255), -1)
    cv2.putText(frame, "LIVE", (width - 85, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return frame, occupied_spot_ids, zone_config

if __name__ == "__main__":
    frame, occupied, conf = generate_parking_frame()
    print(f"Generated frame for {conf['zone_name']}. Occupied: {occupied}")
