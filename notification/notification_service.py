import paho.mqtt.client as mqtt # Used for MQTT communication (pub/sub)
import json # Used for parsing and creating JSON payloads
import requests # Used for making HTTP requests (Catalog, Telegram API)
import time # Used for delays and rate limiting
from datetime import datetime # Used for timestamp handling

import os

# Configuration
CATALOG_URL = "http://localhost:8080"
# Broker will be fetched from Catalog

# Load Secrets --already loaded in secret.json
TELEGRAM_BOT_TOKEN = ""
CHAT_ID = ""

try:
    # Try looking in the current directory first
    if os.path.exists("secrets.json"):
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
    # Try looking in the script's directory
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        secrets_path = os.path.join(script_dir, "secrets.json")
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            
    TELEGRAM_BOT_TOKEN = secrets.get("TELEGRAM_BOT_TOKEN", "")
    CHAT_ID = secrets.get("CHAT_ID", "")
except Exception as e:
    print(f"Error loading secrets.json: {e}")
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"

class NotificationService:
    def __init__(self):
        # Fix for Paho MQTT v2 warning
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="notification_service")
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

    def get_broker_config(self):
        try:
            # Fetch Broker
            res_b = requests.get(f"{CATALOG_URL}/broker")
            broker = res_b.json() if res_b.status_code == 200 else "localhost"
            
            # Fetch Port
            res_p = requests.get(f"{CATALOG_URL}/port")
            port = int(res_p.json()) if res_p.status_code == 200 else 1883
            
            return broker, port
        except Exception as e:
            print(f"⚠️ Could not fetch broker config from Catalog from {CATALOG_URL}: {e}")
            return "localhost", 1883

    def send_telegram_alert(self, message, target_chat_id=None):
        chat_to_use = target_chat_id if target_chat_id else CHAT_ID

        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
            # Safe print for simulation
            try:
                print(f"[Telegram] (Simulated -> {chat_to_use}) {message}")
            except UnicodeEncodeError:
                print(f"[Telegram] (Simulated -> {chat_to_use}) [Message with Emojis sent]")
            return
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_to_use, "text": message}
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                try:
                    print(f"[Telegram] Sent to {chat_to_use}: {message}")
                except UnicodeEncodeError:
                     print(f"[Telegram] Sent to {chat_to_use}: [Message with Emojis sent]")
            else:
                print(f"[Telegram] [WARN] Send Failed: {r.status_code} - {r.text}")
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
                        occupancy_text = "Occupied"
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
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
                res = requests.get(url, timeout=15)
                data = res.json()
                
                if not data.get("ok"):
                    time.sleep(5)
                    continue

                updates = data.get("result", [])
                
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    if not message:
                         continue
                         
                    text = message.get("text", "").lower()
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    
                    if chat_id:
                        # Only adding to active broadcast if they explicitly ask for status
                        # or if they previously joined.
                        pass

                    if text.startswith("/status"):
                        if chat_id not in self.active_users:
                            print(f"[INFO] New User Subscribed: {chat_id}")
                            self.active_users.add(chat_id)
                        self.send_status_report(chat_id)
                    
                    elif text.startswith("/stop"):
                        if chat_id in self.active_users:
                            print(f"[INFO] User Unsubscribed: {chat_id}")
                            self.active_users.discard(chat_id)
                            self.send_telegram_alert("🔕 Notifications stopped.", chat_id)
            
            except Exception as e:
                time.sleep(5)

    def _fetch_system_state(self):
        # Query Smart Controller via REST
        CONTROLLER_API = "http://localhost:8001/status"
        try:
            res = requests.get(CONTROLLER_API, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error fetching system state: {e}")
        return None

    def _format_summary_report(self, system_state):
        if not system_state:
            return "ℹ️ System online. Waiting for data..."
            
        total_rooms = len(system_state)
        occupied_rooms = []
        max_co2 = 0
        max_co2_room = ""
        
        for rid, data in system_state.items():
            # Check occupancy
            if data.get("occupancy") == "Yes":
                occupied_rooms.append(data.get("name", rid))
                
            # Check CO2
            co2 = data.get("co2", 0)
            if isinstance(co2, (int, float)) and co2 > max_co2:
                max_co2 = co2
                max_co2_room = data.get("name", rid)
        
        msg = [f"ℹ️ **System Update**"]
        msg.append(f"✅ System Operational")
        msg.append(f"🏢 Rooms Occupied: {len(occupied_rooms)}/{total_rooms}")
        
        if occupied_rooms:
            msg.append(f"📍 Active: {', '.join(occupied_rooms)}")
            
        if max_co2 > 0:
            icon = "🟢"
            if max_co2 > 1000: icon = "⚠️" 
            if max_co2 > 1500: icon = "🚨"
            msg.append(f"{icon} Max CO2: {max_co2} ppm ({max_co2_room})")
            
        return "\n".join(msg)

    def _format_detailed_report(self, system_state):
        if not system_state:
            return "ℹ️ System online. Waiting for sensor data..."

        report = ["📊 **Detailed Campus Status**"]
        for room_id, data in system_state.items():
            name = data.get("name", room_id)
            lights = data.get("lights", "Unknown")
            occupancy = data.get("occupancy", "Unknown")
            status_icon = "🟢" if occupancy == "Yes" else "⚪"
            report.append(f"\n📍 **{name}**\n   {status_icon} Occupied: {occupancy} | Lights: {lights}")
        
        return "\n".join(report)

    def send_status_report(self, chat_id=None):
        state = self._fetch_system_state()
        if state is None:
            self.send_telegram_alert("⚠️ Failed to contact Smart Controller.", chat_id)
            return
            
        # Use Detailed Report for explicit commands
        msg = self._format_detailed_report(state)
        self.send_telegram_alert(msg, chat_id)

    def periodic_broadcast_loop(self):
        print(f"[INFO] Periodic Broadcast Loop Started (Every 30s)")
        while True:
            time.sleep(30)
            try:
                if not self.active_users:
                    continue

                state = self._fetch_system_state()
                if not state:
                    continue
                    
                # Use Summary Report for periodic updates
                msg = self._format_summary_report(state)
                
                # Broadcast to all active users
                for user_id in list(self.active_users):
                    self.send_telegram_alert(msg, user_id)
                    
            except Exception as e:
                print(f"Broadcast Error: {e}")

    def run(self):
        print("Starting Notification Service...")
        
        # Initialize active users with default from secrets
        self.active_users = set()
        if CHAT_ID and CHAT_ID != "YOUR_CHAT_ID":
            self.active_users.add(str(CHAT_ID))
            print(f"Loaded default chat ID: {CHAT_ID}")

        # Start Telegram Poller in background
        import threading
        t_poll = threading.Thread(target=self.check_telegram_commands, daemon=True)
        t_poll.start()

        # Start Periodic Broadcast in background
        t_broadcast = threading.Thread(target=self.periodic_broadcast_loop, daemon=True)
        t_broadcast.start()

        # Fetch dynamic broker config
        # Retry loop for MQTT connection
        while True:
            try:
                broker, port = self.get_broker_config()
                print(f"[INFO] Attempting to connect to Broker: {broker}:{port}")
                self.client.connect(broker, port, 60)
                print("[INFO] MQTT Connection Successful!")
                self.client.loop_forever()
            except Exception as e:
                print(f"[ERROR] MQTT/Catalog Connection Failed: {e}")
                print("[INFO] Retrying in 10 seconds...")
                time.sleep(10)

if __name__ == "__main__":
    service = NotificationService()
    service.run()
