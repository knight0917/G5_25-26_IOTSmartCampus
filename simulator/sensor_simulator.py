import pandas as pd # Used for reading the CSV data file
import paho.mqtt.client as mqtt # Used for MQTT communication (publishing sensor data)
import time # Used for simulation delays
import json # Used for creating JSON payloads
import requests # Used for fetching room config from Catalog
import sys # Used for system exit on error
import threading # Used to simulate multiple rooms concurrently

# Configuration
BROKER = "localhost"
PORT = 1883
CATALOG_URL = "http://localhost:8000"
DATA_FILE = "dummy_sensor_data.csv"

def get_rooms():
    try:
        response = requests.get(f"{CATALOG_URL}/rooms")
        return response.json()
    except:
        print("Catalog not reachable")
        return []

class RoomSimulator(threading.Thread):
    def __init__(self, room_config, data):
        super().__init__()
        self.room_id = room_config['room_id']
        self.topic = room_config['mqtt_sensor_topic']
        self.data = data
        self.client = mqtt.Client(client_id=f"sim_{self.room_id}")
        
    def run(self):
        try:
            self.client.connect(BROKER, PORT, 60)
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
                # print(f"[{self.room_id}] pub -> {self.topic}")
                
                time.sleep(1) # Speed factor: 1 row per second
                
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"Error in room {self.room_id}: {e}")

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
        
    threads = []
    for room in rooms:
        t = RoomSimulator(room, df)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
