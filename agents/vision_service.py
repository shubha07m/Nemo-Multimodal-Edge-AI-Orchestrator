import time
import threading
import cv2
import numpy as np
from ultralytics import YOLO
from shared_state import state

# --- CONFIGURATION ---
# UPDATED: Pointing to the new NMS-Free YOLO26 model
MODEL_PATH = "../models/yolo26s.onnx" 

# Confidence Thresholds
CONF_RGB = 0.30   
CONF_NOIR = 0.30  

class VisionService(threading.Thread):
    def __init__(self, interval=0.05): # UPDATED: Lower latency (0.05s) because YOLO26 is faster
        super().__init__()
        self.daemon = True
        self.interval = interval
        print(f" [VISION] Loading YOLO26 Eyes ({MODEL_PATH})...", flush=True)
        self.model = YOLO(MODEL_PATH, task='detect')

    def detect_on_image(self, jpg_bytes, conf_threshold):
        if jpg_bytes is None: return []
        
        nparr = np.frombuffer(jpg_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None: return []
        
        t_start = time.time()
        
        # YOLO26 is NMS-free, meaning the model output is cleaner/faster directly
        results = self.model.predict(img, conf=conf_threshold, verbose=False)
        
        t_end = time.time()
        
        # Log if it's struggling (Adjusted threshold for Pi)
        duration = t_end - t_start
        if duration > 0.5:
            print(f" [TIMER] Vision Scan: {duration:.2f}s", flush=True)
        
        detections = []
        for result in results:
            for box in result.boxes:
                try:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    
                    if hasattr(self.model, 'names') and cls_id in self.model.names:
                        name = self.model.names[cls_id]
                    else:
                        name = str(cls_id)
                    
                    detections.append([x1, y1, x2, y2, name])
                except: pass
        return detections

    def run(self):
        print(" [VISION] YOLO26 Sentinel Mode Active.", flush=True)
        
        check_front = True 
        
        while True:
            # Traffic Light Check (Save CPU when speaking)
            if state.is_busy:
                time.sleep(0.5)
                continue

            target_bytes = None
            current_conf = CONF_RGB
            
            with state.lock:
                if check_front:
                    target_bytes = state.frame_rgb
                    current_conf = CONF_RGB
                else:
                    target_bytes = state.frame_noir
                    current_conf = CONF_NOIR 

            if target_bytes:
                boxes = self.detect_on_image(target_bytes, current_conf)
                
                with state.lock:
                    if check_front:
                        state.boxes_rgb = boxes
                    else:
                        state.boxes_noir = boxes
            
            check_front = not check_front
            
            # Faster ping-pong for smoother dual-cam feel
            time.sleep(self.interval)
