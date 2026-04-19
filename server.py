import cv2
import json
import serial
import threading
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import re

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CAMERA SETUP ---
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320) # Lower res = Lower latency
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

# Regex to find numbers that look like Lat/Lon (e.g., 40.4247 or -86.9115)
COORD_PATTERN = re.compile(r"[-+]?\d*\.\d+|\d+")

def read_esp32_serial():
    try:
        # Open the resolved serial0 port. Timeout increased to 1.0 to prevent fragmentation.
        ser = serial.Serial('/dev/serial0', 115200, timeout=1.0)
        print("Listening to ESP32 on /dev/serial0...")
    except Exception as e:
        print(f"Serial Connection Error: {e}")
        return

    while True:
        try:
            if ser.in_waiting > 0:
                # 1. Read the raw bytes first
                raw_bytes = ser.readline()
                
                # Print the exact bytes to the console before any decoding
                print(f"RAW BYTES: {raw_bytes}")
                
                # 2. Now decode, ignoring errors, and strip whitespace/newlines
                line = raw_bytes.decode('utf-8', errors='ignore').strip()
                
                if line:
                    # 3. Split by comma (matching your %.7f,%.7f format)
                    parts = line.split(',')
                    
                    if len(parts) == 2:
                        try:
                            # 4. Safely attempt to convert and emit
                            data = {
                                "lat": float(parts[0]),
                                "lon": float(parts[1])
                            }
                            socketio.emit('location_update', data)
                        except ValueError:
                            print(f"Skipping line (could not convert to float): {line}")
                    else:
                        print(f"Skipping malformed line (part count mismatch): {line}")
        except Exception as e:
            # Prevents the thread from dying if there's a single bad read
            print(f"Read Error: {e}")
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
