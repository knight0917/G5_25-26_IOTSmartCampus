import time
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime

class SmartActuator:
    def __init__(self):
        self.catalog_url = "http://localhost:8080"
        self.broker = "localhost"
        self.port = 1883
        self.client = mqtt.Client(client_id="smart_actuator_service")
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def get_configuration(self):
        try:
            # Fetch broker
            r = requests.get(f"{self.catalog_url}/broker")
            if r.status_code == 200:
                self.broker = r.json()
            
            # Fetch port
            r = requests.get(f"{self.catalog_url}/port")
            if r.status_code == 200:
                self.port = int(r.json())
                
            print(f"Configuration loaded: Broker={self.broker}, Port={self.port}")
        except Exception as e:
            print(f"Error connecting to Catalog: {e}. Using defaults (localhost:1883).")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT Broker at {self.broker}:{self.port}")
            # Subscribe to all actuator topics using wildcard
            # Pattern: campus/{room_id}/actuators
            topic = "campus/+/actuators"
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
            print("waiting for commands...")
        else:
            print(f"❌ Connection failed with result code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic_parts = msg.topic.split('/')
            # Expected topic structure: campus/room_id/actuators
            if len(topic_parts) >= 2:
                room_id = topic_parts[1]
            else:
                room_id = "Unknown"

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] ⚡ ACTION RECEIVED for {room_id}")
            
            # --- SIMULATED PACKET LOSS (5% Chance) ---
            import random
            if random.random() < 0.05:
                print(f"[{timestamp}] ⚠️ SIMULATED PACKET LOSS (Command Dropped)")
                return

            # Simulate physical hardware actuation
            triggered = False
            status_payload = {
                "room_id": room_id,
                "timestamp": timestamp,
                "status": "CONFIRMED"
            }
            
            if "lights" in payload:
                state = payload["lights"]
                icon = "💡" if state == "ON" else "🌑"
                print(f"   {icon} LIGHTS set to {state}")
                status_payload["lights"] = state
                triggered = True
            
            if "heating" in payload:
                state = payload["heating"]
                icon = "🔥" if state == "ON" else "❄️"
                print(f"   {icon} HEATING set to {state}")
                status_payload["heating"] = state
                triggered = True
                
            if triggered:
                # --- CLOSED-LOOP FEEDBACK ---
                # Publish the confirmation back to the broker
                status_topic = f"campus/{room_id}/actuators/status"
                self.client.publish(status_topic, json.dumps(status_payload))
                print(f"   (Status published to {status_topic})")
            else:
                 print(f"   (No specific hardware command found in payload: {payload})")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"Error processing message: {e}")

    def run(self):
        print("🚀 Starting Actuator Service...")
        self.get_configuration()
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\nStopping Actuator Service...")
            self.client.disconnect()
        except Exception as e:
            print(f"Critical Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    actuator = SmartActuator()
    actuator.run()
