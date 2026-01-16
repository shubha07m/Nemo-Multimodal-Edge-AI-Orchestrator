import sys
import time
import threading
import cv2
import numpy as np
from shared_state import state

# --- BRIDGE FIX FOR CONDAS ---
sys.path.append('/usr/lib/python3/dist-packages')

try:
    from picamera2 import Picamera2
    HAS_PICAM = True
    print(" [SYSTEM] Native Picamera2 driver loaded.", flush=True)
except ImportError:
    HAS_PICAM = False
    print(" [WARN] Picamera2 not found.", flush=True)

class CameraService(threading.Thread):
    def __init__(self, camera_index=0, camera_type='rgb', interval=0.1):
        super().__init__()
        self.daemon = True
        self.camera_index = camera_index
        self.camera_type = camera_type # 'rgb' or 'noir'
        self.interval = interval
        self.picam = None
        self.cap = None

        print(f" [{camera_type.upper()}] Service initializing...", flush=True)
        
        if self.camera_type == 'noir':
            self._init_picamera()
        else:
            self._init_opencv()

    def _init_picamera(self):
        if not HAS_PICAM: return
        try:
            # NoIR always uses the ribbon cable (internal), index 0 usually works for libcamera
            self.picam = Picamera2(camera_num=0) 
            config = self.picam.create_preview_configuration(main={"size": (640, 480), "format": "XRGB8888"})
            self.picam.configure(config)
            self.picam.start()
            print(" [NOIR] Picamera2 Stream Active!", flush=True)
        except Exception as e:
            print(f" [NOIR] Init Failed: {e}", flush=True)

    def _init_opencv(self):
        # HUNTING LOGIC: Try the requested index, then scan neighbors
        indices_to_try = [self.camera_index, 0, 1, 2, 3, 4]
        # Remove duplicates while preserving order
        indices_to_try = sorted(list(set(indices_to_try)), key=indices_to_try.index)

        print(f" [RGB] Hunting for USB Camera in: {indices_to_try}", flush=True)

        for idx in indices_to_try:
            try:
                temp_cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                # Force MJPEG (Fixes bandwidth/busy issues)
                temp_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                if temp_cap.isOpened():
                    # Read one frame to prove it's real
                    ret, _ = temp_cap.read()
                    if ret:
                        print(f" [RGB] Success! Connected to Index {idx}", flush=True)
                        self.cap = temp_cap
                        return # Stop hunting
                    else:
                        temp_cap.release()
            except:
                pass
        
        print(" [RGB] CRITICAL: Could not find any working USB Camera.", flush=True)

    def run(self):
        while True:
            frame = None
            
            # --- NOIR (Picamera2) ---
            if self.camera_type == 'noir' and self.picam:
                try:
                    frame = self.picam.capture_array("main")
                    if frame is not None:
                        # Convert colors
                        if frame.ndim == 3:
                            if frame.shape[2] == 4: frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                            elif frame.shape[2] == 3: frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                except: pass

            # --- RGB (OpenCV) ---
            elif self.cap and self.cap.isOpened():
                ret, frame_read = self.cap.read()
                if ret:
                    frame = frame_read

            # --- PROCESS & SAVE ---
            if frame is not None:
                # Draw boxes if available
                with state.lock:
                    boxes = state.boxes_rgb if self.camera_type == 'rgb' else state.boxes_noir
                
                for (x1, y1, x2, y2, label) in boxes:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    jpg_bytes = buffer.tobytes()
                    with state.lock:
                        if self.camera_type == 'rgb': state.frame_rgb = jpg_bytes
                        elif self.camera_type == 'noir': state.frame_noir = jpg_bytes
            else:
                time.sleep(1.0) # Sleep if camera broken

            time.sleep(self.interval)
