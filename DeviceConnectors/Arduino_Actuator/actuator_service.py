import time
import json
import paho.mqtt.client as mqtt
import requests


class VirtualActuator:
    def __init__(self, room_id):
        self.room_id = room_id
        # --- FIX: Added CallbackAPIVersion.VERSION2 for paho-mqtt 2.0 ---
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"Actuator_{room_id}")

        # 1. دریافت تنظیمات از کاتالوگ
        try:
            response = requests.get("http://127.0.0.1:8080/all")
            self.config = response.json()
            self.broker_address = self.config["broker"]["address"]
            self.broker_port = self.config["broker"]["port"]

            # پیدا کردن تاپیک مخصوص این اتاق برای دریافت دستور
            for room in self.config["rooms"]:
                if room["room_id"] == self.room_id:
                    self.topic = room["devices"]["actuator_topic"]
                    break

            print(f"Actuator Configured for {self.room_id}")
            print(f"Broker: {self.broker_address}, Topic: {self.topic}")

        except Exception as e:
            print(f"Error connecting to Catalog: {e}")
            exit()

    def on_message(self, client, userdata, message):
        # این تابع وقتی اجرا می‌شود که پیامی دریافت شود
        payload = str(message.payload.decode("utf-8"))
        print(f"⚡ COMMAND RECEIVED: {payload}")

        # شبیه‌سازی روشن/خاموش کردن سخت‌افزار
        try:
            data = json.loads(payload)
            if "switch" in data:
                status = data["switch"]
                print(f"--> Actuation Logic: Turning {status} devices in {self.room_id}")
        except:
            pass

    def start(self):
        # تنظیم تابع دریافت پیام
        self.client.on_message = self.on_message

        # اتصال و سابسکرایب
        print("Connecting to Broker...")
        self.client.connect(self.broker_address, self.broker_port)
        self.client.subscribe(self.topic)
        print(f"Subscribed to {self.topic}")
        print("Waiting for commands...")

        self.client.loop_forever()


if __name__ == "__main__":
    # شبیه‌سازی آردوینو برای کلاس 101
    actuator = VirtualActuator("Classroom_101")
    actuator.start()