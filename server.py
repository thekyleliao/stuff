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
def read_esp32_serial():
    ser = None
    print("Attempting to connect to ESP32...")
    
    try:
        # The timeout is key: it prevents the thread from hanging forever
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
        print("ESP32 Connected!")
    except Exception as e:
        print(f"!!! SERIAL ERROR: {e}")
        print("Server will continue running WITHOUT live telemetry.")
        return # Exit the thread, but the server keeps living

    while True:
        try:
            if ser and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                data = json.loads(line)
                socketio.emit('location_update', data)
        except Exception:
            # This catches garbled data or sudden disconnects
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
