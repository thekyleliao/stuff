import serial

# Connect to the Pi's serial port. 
# Make sure the ESP32 is actually transmitting at 115200.
ser = serial.Serial('/dev/serial0', 115200)

print("Dumping raw serial buffer... Press Ctrl+C to stop.")

while True:
    if ser.in_waiting > 0:
        # Read whatever is sitting in the buffer, no matter the size
        raw_data = ser.read(ser.in_waiting)
        
        # repr() prints the exact byte representation (e.g., b'\xff' or b'40.42')
        print(repr(raw_data))
