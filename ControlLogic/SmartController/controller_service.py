import time
import json
import paho.mqtt.client as mqtt
import requests


class SmartController:
    def __init__(self, room_id):
        self.room_id = room_id
        # کلاینت MQTT جدید
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"Controller_{room_id}")

        # 1. دریافت تنظیمات از کاتالوگ
        try:
            print("⏳ Fetching Config from Catalog...")
            response = requests.get("http://127.0.0.1:8080/all")
            self.config = response.json()
            self.broker_address = self.config["broker"]["address"]
            self.broker_port = self.config["broker"]["port"]

            # آدرس اسکجولر را از کاتالوگ می‌گیریم
            self.scheduler_ip = self.config["services"]["scheduler"]["ip"]
            self.scheduler_port = self.config["services"]["scheduler"]["port"]

            # تنظیمات اتاق
            for room in self.config["rooms"]:
                if room["room_id"] == self.room_id:
                    self.sensor_topic = room["devices"]["sensor_topic"]
                    self.actuator_topic = room["devices"]["actuator_topic"]
                    self.target_temp = room["strategies"]["target_temp"]
                    self.light_threshold = room["strategies"]["light_threshold"]
                    break

            print(f"✅ Controller Started for {self.room_id}")

        except Exception as e:
            print(f"❌ Error connecting to Catalog: {e}")
            exit()

    def check_schedule(self):
        # درخواست REST به سرویس Scheduler
        try:
            url = f"http://{self.scheduler_ip}:{self.scheduler_port}/check"
            resp = requests.get(url, params={"room_id": self.room_id})
            data = resp.json()
            return data["booked"]
        except:
            print("⚠️ Scheduler not reachable, assuming True")
            return True

    def on_sensor_data(self, client, userdata, message):
        try:
            payload = str(message.payload.decode("utf-8"))
            data = json.loads(payload)

            current_temp = data["temperature"]
            occupancy = data["occupancy"]
            light = data["light_lux"]

            print(f"\n📊 Sensor Data: Temp={current_temp}, Occ={occupancy}, Light={light}")

            # --- قدم 1: چک کردن برنامه زمانی (REST) ---
            is_class_booked = self.check_schedule()

            command = {"room_id": self.room_id, "timestamp": time.time()}

            if not is_class_booked:
                # اگر کلاس نیست، همه چیز خاموش!
                command["switch"] = "OFF"
                print("⛔ Decision: Force OFF (No Class Scheduled)")

            else:
                # --- قدم 2: منطق هوشمند (Smart Logic) ---
                if occupancy == 1:
                    if light < self.light_threshold:
                        command["switch"] = "ON"
                        print("💡 Decision: Turn ON Lights (Dark & Occupied)")
                    elif current_temp > self.target_temp:
                        command["switch"] = "ON"  # فن/کولر
                        print("❄️ Decision: Turn ON AC (Too Hot)")
                    else:
                        command["switch"] = "OFF"
                        print("✅ Decision: Optimal Conditions (No Action)")
                else:
                    command["switch"] = "OFF"
                    print("Decision: Turn OFF (Room Empty)")

            # ارسال فرمان
            self.client.publish(self.actuator_topic, json.dumps(command))

        except Exception as e:
            print(f"Error logic: {e}")

    def start(self):
        self.client.on_message = self.on_sensor_data
        self.client.connect(self.broker_address, self.broker_port)
        self.client.subscribe(self.sensor_topic)
        print(f"🎧 Listening to {self.sensor_topic}...")
        self.client.loop_forever()


if __name__ == "__main__":
    controller = SmartController("Classroom_101")
    controller.start()