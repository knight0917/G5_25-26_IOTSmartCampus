import pandas as pd # Used for reading the CSV data file
import paho.mqtt.client as mqtt # Used for MQTT communication (publishing sensor data)
import time # Used for simulation delays
import json # Used for creating JSON payloads
import requests # Used for fetching room config from Catalog
import sys # Used for system exit on error
import threading # Used to simulate multiple rooms concurrently
import random # Used for Jitter

# Configuration
CATALOG_URL = "http://localhost:8080"
DATA_FILE = "dummy_sensor_data.csv"

def get_rooms():
    try:
        response = requests.get(f"{CATALOG_URL}/rooms")
        return response.json()
    except:
        print("Catalog not reachable")
        return []

def get_broker_config():
    try:
        res_b = requests.get(f"{CATALOG_URL}/broker")
        broker = res_b.json() if res_b.status_code == 200 else "localhost"
        res_p = requests.get(f"{CATALOG_URL}/port")
        port = int(res_p.json()) if res_p.status_code == 200 else 1883
        return broker, port
    except:
        return "localhost", 1883

class RoomSimulator(threading.Thread):
    def __init__(self, room_config, data):
        super().__init__()
        self.room_id = room_config['room_id']
        self.topic = room_config['mqtt_sensor_topic']
        self.data = data
        self.client = mqtt.Client(client_id=f"sim_{self.room_id}")
        
    def run(self):
        try:
            broker, port = get_broker_config()
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            
            print(f"[{self.room_id}] Starting simulation...")
            
            for index, row in self.data.iterrows():
                payload = {
                    "room_id": self.room_id,
                    "timestamp": row['date'], # In real usage, you might use time.time()
                    "temperature": row['Temperature'],
                    "humidity": row['Humidity'],
                    "light": row['Light'],
                    "co2": row['CO2'],
                    "occupancy": int(row['Occupancy'])
                }
                
                self.client.publish(self.topic, json.dumps(payload))
                
                # --- SIMULATED JITTER ---
                # Add random variation to the 1-second interval
                delay = 1.0 + random.uniform(-0.2, 0.2)
                time.sleep(delay) 
                
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            msg = f"Error in room {self.room_id}: {e}\n"
            print(msg)
            with open("simulator.log", "a") as f:
                f.write(msg)

if __name__ == "__main__":
    rooms = get_rooms()
    if not rooms:
        # Fallback for testing without catalog
        rooms = [{"room_id": "room_101", "mqtt_sensor_topic": "campus/room_101/sensors"}]
        
    try:
        df = pd.read_csv(DATA_FILE)
    except:
        print("Data file not found. Run create_dummy_data.py first.")
        sys.exit(1)
        
    active_threads = {}

    print("🚀 Simulator Service Running... (Polling for new rooms every 10s)")

    while True:
        try:
            current_rooms = get_rooms()
            
            for room in current_rooms:
                rid = room['room_id']
                
                # Check if this room is already running
                if rid not in active_threads or not active_threads[rid].is_alive():
                    print(f"🆕 Found new/stopped room: {rid}. Starting simulation...")
                    t = RoomSimulator(room, df)
                    t.start()
                    active_threads[rid] = t
                    
            # Update list of active threads (clean up finished ones)
            # Make a copy of keys to avoid runtime error during iteration
            for rid in list(active_threads.keys()):
                if not active_threads[rid].is_alive():
                    # print(f"Room {rid} simulation finished.")
                    del active_threads[rid]
                    
        except Exception as e:
            print(f"Error in main loop: {e}")
            
        time.sleep(10)
