from flask import Flask, Response, render_template, send_file, jsonify
import time
import io
from shared_state import state

# Ensure Flask looks in the current folder's 'templates' subdirectory
app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    # This now loads the HTML file we just created
    return render_template('index.html')

def gen_frames(camera_type):
    """
    Generator function that yields video frames.
    """
    while True:
        frame_data = None
        with state.lock:
            frame_data = state.frame_rgb if camera_type == 'rgb' else state.frame_noir
        
        if frame_data:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            # 0.04s = ~25 FPS. Smoother stream than 0.1s
            time.sleep(0.04)
        else:
            # If no frame available, wait a bit to save CPU
            time.sleep(0.1)

@app.route('/feed_rgb')
def feed_rgb(): 
    return Response(gen_frames('rgb'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/feed_noir')
def feed_noir(): 
    return Response(gen_frames('noir'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    with state.lock: 
        return jsonify({"caption": state.caption, "audio_id": state.audio_id})

@app.route('/latest_audio')
def latest_audio():
    with state.lock:
        if state.last_audio_bytes is None: 
            return "No audio", 404
        return send_file(
            io.BytesIO(state.last_audio_bytes), 
            mimetype="audio/wav", 
            download_name="nemo_voice.wav"
        )
