import cv2
import json
import serial
import threading
from flask import Flask, render_template, Response
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CAMERA SETUP ---
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Lower res = Lower latency
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def gen_frames():
    """Video streaming generator function."""
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Here is where you'd add OpenCV Obstacle Avoidance logic
            # Example: cv2.putText(frame, 'Obstacle!', (50,50)...)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- TELEMETRY SETUP (ESP32) ---
import re

# Regex to find numbers that look like Lat/Lon (e.g., 40.4247 or -86.9115)
COORD_PATTERN = re.compile(r"[-+]?\d*\.\d+|\d+")

def read_esp32_serial():
    try:
        # Use '/dev/serial0' for the GPIO pins 14/15
        ser = serial.Serial('/dev/serial0', 115200, timeout=1)
        print("Listening on GPIO 14/15...")
    except Exception as e:
        print(f"Serial Error: {e}")
        return

    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Permissive Parsing: Find all numbers in the string
                matches = COORD_PATTERN.findall(line)
                
                if len(matches) >= 2:
                    # Assume the first two numbers are Lat and Lon
                    data = {
                        "lat": float(matches[0]),
                        "lon": float(matches[1])
                    }
                    socketio.emit('location_update', data)
                    print(f"Parsed: {data}")
            except Exception:
                continue
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    threading.Thread(target=read_esp32_serial, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
