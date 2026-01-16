import threading

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        
        # Camera Data (Dual-View System)
        self.frame_rgb = None
        self.boxes_rgb = []
        
        self.frame_noir = None 
        self.boxes_noir = []
        
        # Web UI & Audio Data
        self.caption = "System Initializing..."
        self.last_audio_bytes = None
        self.audio_id = 0
        
        # Traffic Light (Brain Busy Flag)
        self.is_busy = False 

state = SharedState()
