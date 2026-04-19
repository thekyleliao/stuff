from flask import Flask, render_template
from flask_socketio import SocketIO
import serial
import threading
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURATION ---
# Change '/dev/ttyUSB0' to your ESP32's port (check 'ls /dev/tty*')
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

def read_esp32_serial():
    """Background thread to read serial data and emit to web client"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                try:
                    # Expecting ESP32 to send: {"lat": 40.42, "lon": -86.91}
                    data = json.loads(line)
                    socketio.emit('location_update', data)
                except json.JSONDecodeError:
                    pass # Ignore partial or garbled lines
    except Exception as e:
        print(f"Serial Error: {e}")

@app.route('/')
def index():
    # Looks for index.html inside the 'templates' folder
    return render_template('index.html')

if __name__ == '__main__':
    # Start the serial thread
    thread = threading.Thread(target=read_esp32_serial, daemon=True)
    thread.start()
    
    # Run the server on your Pi's IP (port 5000)
    socketio.run(app, host='0.0.0.0', port=5000)
