import threading

def read_serial():
    print("--- STARTING RAW DEBUG STREAM ---")
    while True:
        if ser.in_waiting > 0:
            try:
                # 1. Capture the raw bytes exactly as they hit the Pi
                raw_bytes = ser.readline()
                
                # 2. Show the RAW bytes (Look for \x00 or weird hex codes here)
                print(f"RAW: {raw_bytes}")

                # 3. Try to decode the data
                line = raw_bytes.decode('utf-8', errors='ignore').strip()
                
                if line:
                    print(f"DECODED: '{line}'")
                    parts = line.split(',')
                    
                    # 4. Check if we have the 2 parts we expect
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0])
                            lon = float(parts[1])
                            print(f"PARSED SUCCESS: Lat={lat}, Lon={lon}")
                            
                            # Push to your Leaflet Map
                            socketio.emit('location_update', {'lat': lat, 'lon': lon})
                        except ValueError:
                            print(f"PARSED FAIL: '{parts}' are not valid numbers.")
                    else:
                        print(f"FORMAT MISMATCH: Expected 2 parts, found {len(parts)}")
                
                print("-" * 30) # Visual break for each packet
                
            except Exception as e:
                print(f"CRITICAL SERIAL ERROR: {e}")

# In your main block, ensure the thread points to this function
if __name__ == '__main__':
    # Ensure the thread is set to run this specific function
    t = threading.Thread(target=read_serial, daemon=True)
    t.start()
    
    socketio.run(app, host='0.0.0.0', port=5000)
