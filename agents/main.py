#!/usr/bin/env python3
import time
import sys
from app import app
from camera_service import CameraService
from vision_service import VisionService
from narrator_service import NarratorService

def main():
    print(" [SYSTEM] Booting Nemo Explorer v1.0...", flush=True)

    # 1. Start NoIR Camera (Picamera2) - Index 0 (Internal)
    # We start this FIRST so it claims the internal hardware.
    cam_noir = CameraService(camera_index=0, camera_type='noir', interval=0.1) 
    cam_noir.start()
    
    # Wait for NoIR to settle
    print(" [SYSTEM] Waiting for NoIR initialization...", flush=True)
    time.sleep(3.0)

    # 2. Start Main Camera (RGB)
    # We ask it to try Index 0. If blocked by NoIR, it will auto-hunt for 1, 2, 3...
    cam_rgb = CameraService(camera_index=0, camera_type='rgb', interval=0.1) 
    cam_rgb.start()
    
    # 3. Start Vision (YOLO11s)
    vision = VisionService(interval=0.1)
    vision.start()

    # 4. Start Narrator (Qwen + KittenTTS)
    narrator = NarratorService(interval=0.1)
    narrator.start()

    # 5. Start Web Interface
    print(" [SYSTEM] Explorer Interface: http://0.0.0.0:5000", flush=True)
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
