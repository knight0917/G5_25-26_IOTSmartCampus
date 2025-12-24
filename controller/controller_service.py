import paho.mqtt.client as mqtt # Used for MQTT communication (pub/sub)
import json # Used for parsing and creating JSON payloads
import requests # Used for making HTTP requests to other services (Catalog, ThingSpeak)
import time # Used for timing and delays
from datetime import datetime # Used for handling timestamp and current time

from fastapi import FastAPI # Used to create the REST API for status checks
import threading # Used to run the MQTT loop in a background thread
import uvicorn # Used as the ASGI server to run the FastAPI app

# Configuration
BROKER = "localhost"
PORT = 1883
CATALOG_URL = "http://localhost:8000"

app = FastAPI(title="Smart Campus Controller")

class SmartController:
    def __init__(self):
        self.client = mqtt.Client(client_id="smart_controller")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.rooms_config = {}
        # self.last_alert_time = {} # Removed: notification logic moved
        self.last_thingspeak_time = {} # Rate limiting: room_id -> timestamp
        self.system_state = {} # room_id -> {metrics}

    def save_state(self):
        try:
            with open("system_state.json", "w") as f:
                json.dump(self.system_state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def get_room_config(self, room_id):
        # In a real app, cache this with a TTL
        try:
            res = requests.get(f"{CATALOG_URL}/rooms/{room_id}")
            return res.json()
        except Exception as e:
            print(f"Error fetching config for {room_id}: {e}")
            return None

    def send_to_thingspeak(self, room_id, write_key, data):
        # Rate Limit: ThingSpeak free tier allows update every 15 seconds
        last = self.last_thingspeak_time.get(room_id, 0)
        if time.time() - last < 16:
            return

        url = f"https://api.thingspeak.com/update?api_key={write_key}"
        # Field Mapping:
        # F1=Temp, F2=Hum, F3=Lux, F4=CO2, F5=Occ, F6=LightState, F7=HeatState
        fields = f"&field1={data['temp']}&field2={data['hum']}&field3={data['lux']}&field4={data['co2']}&field5={data['occ']}&field6={data['light_s']}&field7={data['heat_s']}"
        
        try:
            requests.get(url + fields)
            self.last_thingspeak_time[room_id] = time.time()
            # print(f"[{room_id}] Sent to ThingSpeak")
        except Exception as e:
            print(f"ThingSpeak Error: {e}")

    def on_connect(self, client, userdata, flags, rc):
        print("Controller Connected to MQTT Broker")
        client.subscribe("campus/+/sensors")

    def check_schedule(self, room_config):
        # Simple check: Is there a class RIGHT NOW?
        schedule = room_config.get('schedule', [])
        now = datetime.now()
        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M")
        
        for item in schedule:
            if item['day'] == current_day:
                if item['start_time'] <= current_time <= item['end_time']:
                    return True
        return False

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            room_id = payload.get("room_id")
            
            if not room_id:
                return

            config = self.get_room_config(room_id)
            if not config:
                return

            # --- Extract Sensor Data ---
            occ = payload.get("occupancy", 0)
            lux = payload.get("light", 0)
            temp = payload.get("temperature", 20)
            co2 = payload.get("co2", 400)
            
            # --- Logic: Occupancy Priority ---
            lights = "OFF"
            heating = "OFF"
            
            is_scheduled = self.check_schedule(config)
            
            if occ == 1:
                # Occupied: Comfort Mode
                if lux < 300:
                    lights = "ON"
                if temp < 20:
                    heating = "ON"
            else:
                # Unoccupied: Energy Save Mode
                # Even if scheduled, if nobody is there, turn OFF (per PRD FR-3: Special Rule)
                lights = "OFF"
                heating = "OFF"
            
            # --- Actuation ---
            cmd_topic = config['mqtt_actuator_topic']
            cmd_payload = {
                "timestamp": time.time(),
                "lights": lights,
                "heating": heating,
                "status": "active" if occ else "energy_save"
            }
            client.publish(cmd_topic, json.dumps(cmd_payload))

            # --- Update State for Dashboard ---
            self.system_state[room_id] = {
                "name": config['name'],
                "temp": temp,
                "humidity": payload.get("humidity", 0),
                "lux": lux,
                "co2": co2,
                "occupancy": "Yes" if occ else "No",
                "scheduled": "Class Active" if is_scheduled else "No Class",
                "lights": lights,
                "heating": heating,
                "last_update": datetime.now().strftime("%H:%M:%S")
            }
            self.save_state()
            
            # --- ThingSpeak Integration ---
            ts_key = config.get('thingspeak_write_key')
            if ts_key:
                ts_data = {
                    "temp": temp, "hum": payload.get("humidity", 0),
                    "lux": lux, "co2": co2,
                    "occ": occ,
                    "light_s": 1 if lights == "ON" else 0,
                    "heat_s": 1 if heating == "ON" else 0
                }
                # Run in thread to not block MQTT loop
                import threading
                threading.Thread(target=self.send_to_thingspeak, args=(room_id, ts_key, ts_data)).start()

        except Exception as e:
            print(f"Error processing message: {e}")

    def run(self):
        print("Smart Controller Running...")
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_forever()

# --- Global Controller Instance ---
controller = SmartController()

@app.on_event("startup")
def start_mqtt_loop():
    # Start MQTT loop in background thread
    t = threading.Thread(target=controller.run, daemon=True)
    t.start()

@app.get("/status")
def get_status():
    """Returns the current state of all rooms"""
    return controller.system_state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
