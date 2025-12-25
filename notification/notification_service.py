import paho.mqtt.client as mqtt # Used for MQTT communication (pub/sub)
import json # Used for parsing and creating JSON payloads
import requests # Used for making HTTP requests (Catalog, Telegram API)
import time # Used for delays and rate limiting
from datetime import datetime # Used for timestamp handling

# Configuration
BROKER = "localhost"
PORT = 1883
CATALOG_URL = "http://localhost:8000"

TELEGRAM_BOT_TOKEN = "8360412211:AAGNAo6WbjY4GxeMXi2jOK30rTgDYD5gNWE"
CHAT_ID = "7905772261"

class NotificationService:
    def __init__(self):
        self.client = mqtt.Client(client_id="notification_service")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.last_alert_time = {} # room_id -> timestamp
        self.room_states = {} # room_id -> {lights: str, status: str}

    def get_room_config(self, room_id):
        try:
            res = requests.get(f"{CATALOG_URL}/rooms/{room_id}")
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error fetching config for {room_id}: {e}")
        return None

    def send_telegram_alert(self, message):
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
            print(f"[Telegram] (Simulated) {message}")
            return
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        try:
            requests.post(url, json=payload)
            print(f"[Telegram] Sent: {message}")
        except Exception as e:
            print(f"Telegram Error: {e}")

    def on_connect(self, client, userdata, flags, rc):
        print("Notification Service Connected to MQTT Broker")
        client.subscribe("campus/+/sensors")
        client.subscribe("campus/+/actuators")

    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split("/")
            # Topic format: campus/{room_id}/{type}
            if len(topic_parts) < 3:
                return
            
            room_id = topic_parts[1]
            msg_type = topic_parts[2] # sensors or actuators
            payload = json.loads(msg.payload.decode())

            # Fetch Config (for room name)
            config = self.get_room_config(room_id)
            if not config:
                return
            room_name = config.get('name', room_id)

            # --- Handle Actuator Updates (State Changes) ---
            if msg_type == "actuators":
                new_lights = payload.get("lights")
                new_status = payload.get("status") # active (occupied) or energy_save (empty)
                
                if not new_lights or not new_status:
                    return

                # Check for state change
                current_state = self.room_states.get(room_id, {})
                prev_lights = current_state.get("lights")
                prev_status = current_state.get("status")

                if new_lights != prev_lights or new_status != prev_status:
                    # State has changed!
                    occupancy_text = "Checking Occupancy..."
                    if new_status == "active":
                        occupancy_text = "Occupied (Class Active)"
                    else:
                        occupancy_text = "No Occupancy (Empty)"

                    notification = (
                        f"📢 **State Update: {room_name}**\n"
                        f"👥 Status: {occupancy_text}\n"
                        f"💡 Lights: {new_lights}"
                    )
                    self.send_telegram_alert(notification)
                    
                    # Update Memory
                    self.room_states[room_id] = {"lights": new_lights, "status": new_status}

            # --- Handle Sensor Updates (CO2 Alerts) ---
            elif msg_type == "sensors":
                co2 = payload.get("co2")
                if co2 is None:
                    return

                thresholds = config.get("thresholds", {})
                warn_limit = thresholds.get("co2_warning", 1000)
                crit_limit = thresholds.get("co2_critical", 1500)
                
                alert_msg = None
                if co2 > crit_limit:
                    alert_msg = f"🚨 CRITICAL: High CO2 ({co2} ppm) in {room_name}!"
                elif co2 > warn_limit:
                    alert_msg = f"⚠️ WARNING: Elevated CO2 ({co2} ppm) in {room_name}."
                    
                if alert_msg:
                    # Debounce: 1 alert per 5 mins per room
                    last = self.last_alert_time.get(room_id, 0)
                    if time.time() - last > 300:
                        self.send_telegram_alert(alert_msg)
                        self.last_alert_time[room_id] = time.time()
        except Exception as e:
            print(f"Error processing message: {e}")

    # --- Telegram Polling (Simplified) ---
    def check_telegram_commands(self):
        print("Telegram Command Listener Started...")
        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=10"
                res = requests.get(url, timeout=15)
                updates = res.json().get("result", [])
                
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    text = message.get("text", "").lower()
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    
                    if chat_id == CHAT_ID and text == "/status":
                        self.send_status_report()
            
            except Exception as e:
                # print(f"Telegram Poll Error: {e}")
                time.sleep(5)

    def send_status_report(self):
        # Query Smart Controller via REST (Guidelines Requirement)
        CONTROLLER_API = "http://localhost:8001/status"
        
        try:
            res = requests.get(CONTROLLER_API)
            if res.status_code != 200:
                self.send_telegram_alert(f"⚠️ Error querying Controller: {res.status_code}")
                return
                
            system_state = res.json()
            
            if not system_state:
                 self.send_telegram_alert("ℹ️ System is running, but controller has no data yet.")
                 return

            report = ["📊 **Campus Status Report** (via REST)"]
            
            for room_id, data in system_state.items():
                name = data.get("name", room_id)
                lights = data.get("lights", "Unknown")
                occupancy = data.get("occupancy", "Unknown")
                
                status_icon = "🟢" if occupancy == "Yes" else "⚪"
                
                report.append(f"\n📍 **{name}**\n   {status_icon} Occupied: {occupancy} | Lights: {lights}")
                
            final_msg = "\n".join(report)
            self.send_telegram_alert(final_msg)
            
        except Exception as e:
            print(f"REST Status Check Error: {e}")
            self.send_telegram_alert("⚠️ Failed to contact Smart Controller. Is it running?")

    def run(self):
        print("Starting Notification Service...")
        
        # Start Telegram Poller in background
        import threading
        t = threading.Thread(target=self.check_telegram_commands, daemon=True)
        t.start()
        
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    service = NotificationService()
    service.run()
