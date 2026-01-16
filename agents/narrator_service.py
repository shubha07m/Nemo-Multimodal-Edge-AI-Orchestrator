import time
import threading
import ollama
import io
import numpy as np
import sounddevice as sd
import soundfile as sf
from kittentts import KittenTTS
from shared_state import state

# --- CONFIGURATION ---
MODEL_LLM = "qwen2.5:0.5b"
MODEL_TTS = "KittenML/kitten-tts-nano-0.2"
TTS_VOICE = "expr-voice-3-f"
TTS_RATE = 25000

class NarratorService(threading.Thread):
    def __init__(self, interval=1.0):
        super().__init__()
        self.daemon = True
        self.interval = interval
        self.last_spoken_hash = "" 
        
        print(f" [NARRATOR] Loading Voice ({MODEL_TTS})...", flush=True)
        try:
            self.tts = KittenTTS(MODEL_TTS)
            print(" [NARRATOR] Voice Loaded.", flush=True)
        except Exception as e:
            print(f" [NARRATOR] CRITICAL VOICE ERROR: {e}", flush=True)

    def generate_thought(self, obj_str):
        prompt = (f"You are Nemo. You see: {obj_str}. "
                  "Describe it in exactly 5 words.")
        
        t_start = time.time()
        try:
            response = ollama.generate(model=MODEL_LLM, prompt=prompt, keep_alive=-1)
            result = response['response'].strip()
            if len(result.split()) > 12:
                result = " ".join(result.split()[:12])
        except Exception as e:
            print(f" [NARRATOR] Brain Freeze: {e}", flush=True)
            return None
        t_end = time.time()
        print(f" [TIMER] LLM Think: {t_end - t_start:.2f}s", flush=True)
        return result

    def speak(self, text):
        t_start = time.time()
        try:
            audio = self.tts.generate(text, voice=TTS_VOICE)
            audio_int16 = (audio * 32767).astype(np.int16)
            buffer = io.BytesIO()
            sf.write(buffer, audio_int16, TTS_RATE, format='WAV')
            buffer.seek(0)
            
            with state.lock:
                state.caption = f"Nemo: {text}"
                state.last_audio_bytes = buffer.getvalue()
                state.audio_id += 1
                
        except Exception as e:
            print(f" [NARRATOR] Vocal Error: {e}", flush=True)
            return

        t_end = time.time()
        print(f" [TIMER] TTS Gen: {t_end - t_start:.2f}s", flush=True)
        print(f" [NARRATOR] Spoke: '{text}'", flush=True)

    def run(self):
        print(" [NARRATOR] Dual-View Controller Active...", flush=True)
        while True:
            # 1. Get Detections from BOTH eyes
            front_objs = []
            back_objs = []
            
            with state.lock:
                if state.boxes_rgb:
                    # FIX: Use sorted() to prevent random order changes triggering speech
                    front_objs = sorted(list(set([b[4] for b in state.boxes_rgb])))
                if state.boxes_noir:
                    # FIX: Use sorted()
                    back_objs = sorted(list(set([b[4] for b in state.boxes_noir])))

            # 2. Construct the "Scene String"
            scene_desc = ""
            
            if front_objs and back_objs:
                f_str = ", ".join(front_objs)
                b_str = ", ".join(back_objs)
                scene_desc = f"{f_str} ahead and {b_str} behind"
                
            elif front_objs:
                scene_desc = f"{', '.join(front_objs)} ahead"
                
            elif back_objs:
                scene_desc = f"{', '.join(back_objs)} behind"

            # 3. Logic: Check if scene changed
            if scene_desc:
                if scene_desc != self.last_spoken_hash:
                    state.is_busy = True
                    
                    thought = self.generate_thought(scene_desc)
                    if not thought: thought = f"I see {scene_desc}."
                    
                    self.speak(thought)
                    self.last_spoken_hash = scene_desc
                    state.is_busy = False
                    
                    time.sleep(2.0)
            
            time.sleep(self.interval)
