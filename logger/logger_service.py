import paho.mqtt.client as mqtt
import json
import csv
import os
import requests
from datetime import datetime

# Configuration
LOG_FILE = "sensor_log.csv"
CATALOG_URL = "http://localhost:8080"

class LoggerService:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.client = mqtt.Client(client_id="logger_service")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Initialize Log File
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Topic", "Type", "RoomID", "Data"])

    def get_broker_config(self):
        try:
            res_b = requests.get(f"{CATALOG_URL}/broker")
            if res_b.status_code == 200:
                self.broker = res_b.json()
            res_p = requests.get(f"{CATALOG_URL}/port")
            if res_p.status_code == 200:
                self.port = int(res_p.json())
            print(f"Logger Config: Broker={self.broker}:{self.port}")
        except:
            print("Logger: Catalog not found, using defaults.")

    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ Logger Connected to MQTT Broker")
        # Subscribe to EVERYTHING relevant
        client.subscribe("campus/+/sensors")
        client.subscribe("campus/+/actuators/status")
        # client.subscribe("campus/+/actuators") # Optional: Log commands too if you want

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topic = msg.topic
            
            # Determine Type (Sensor vs Actuator Status)
            if "sensors" in topic:
                log_type = "SENSOR"
            elif "status" in topic:
                log_type = "ACTUATOR_CONFIRM"
            else:
                log_type = "UNKNOWN"
            
            # Extract Room ID
            parts = topic.split('/')
            room_id = parts[1] if len(parts) > 1 else "Unknown"

            # Log to CSV
            with open(LOG_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, topic, log_type, room_id, payload])
                
            print(f"📝 Logged: [{log_type}] for {room_id}")
            
        except Exception as e:
            print(f"Logger Error: {e}")

    def run(self):
        print("📜 Starting Logger Service...")
        self.get_broker_config()
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    logger = LoggerService()
    logger.run()
