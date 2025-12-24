import time
import json
import paho.mqtt.client as mqtt
import requests
import csv
import sys


class VirtualSensor:
    def __init__(self, data_file, room_id):
        self.room_id = room_id
        self.data_file = data_file
        # ساخت کلاینت MQTT (سازگار با نسخه جدید)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"Sensor_{room_id}")

        # 1. وصل شدن به کاتالوگ
        print("⏳ Connecting to Catalog...")
        try:
            response = requests.get("http://127.0.0.1:8080/all")
            self.config = response.json()
            self.broker_address = self.config["broker"]["address"]
            self.broker_port = self.config["broker"]["port"]

            # پیدا کردن تاپیک سنسور
            for room in self.config["rooms"]:
                if room["room_id"] == self.room_id:
                    self.topic = room["devices"]["sensor_topic"]
                    break

            print(f"✅ Sensor Ready! Target: {self.topic}")
        except Exception as e:
            print(f"❌ Catalog Error: {e}")
            sys.exit(1)

    def start(self):
        # 2. اتصال به MQTT
        try:
            self.client.connect(self.broker_address, self.broker_port)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ MQTT Connection Error: {e}")
            sys.exit(1)

        # 3. خواندن فایل دیتا
        print("🚀 Simulation Started (Reading UCI Dataset)...")
        try:
            with open(self.data_file, 'r') as csvfile:
                reader = csv.reader(csvfile)

                # رد کردن هدر (ممکن است فایل شما هدر نداشته باشد یا متفاوت باشد)
                header = next(reader, None)
                print(f"ℹ️ First line (Header/Data): {header}")

                for i, row in enumerate(reader):
                    # بررسی خالی نبودن خط
                    if len(row) < 5:
                        continue

                    try:
                        # --- تلاش برای پیدا کردن ستون‌های درست ---
                        # فرض ۱: فایل استاندارد با ستون ID در ابتدا
                        # [0]=ID, [1]=Date, [2]=Temp, [3]=Hum, [4]=Light, ..., [7]=Occ

                        # بیایید با روش امن‌تری ایندکس‌ها را حدس بزنیم
                        # اگر ستون ۱ تاریخ باشد (رشته طولانی)، پس دما ستون ۲ است
                        col_temp = 2
                        col_hum = 3
                        col_light = 4
                        col_occ = 7  # معمولا آخر است

                        # اگر ستون ۱ عدد بود، شاید فایل ID ندارد:
                        # [0]=Date, [1]=Temp...
                        try:
                            float(row[1])
                        except ValueError:
                            # اگر ستون ۱ عدد نشد، یعنی تاریخ است. پس دما ستون ۲ است (همان پیش‌فرض)
                            pass
                        else:
                            # اگر ستون ۱ عدد شد، یعنی دماست (فایل ID ندارد)
                            col_temp = 1
                            col_hum = 2
                            col_light = 3
                            col_occ = 6

                        # خواندن مقادیر
                        temp_val = float(row[col_temp])
                        hum_val = float(row[col_hum])
                        light_val = float(row[col_light])

                        # پیدا کردن Occupancy (ممکن است ستون آخر باشد)
                        # ما فرض می‌کنیم اگر ستون ۷ نبود، آخرین ستون فایل است
                        if len(row) > col_occ:
                            occ_val = int(row[col_occ])
                        else:
                            occ_val = int(row[-1])  # آخرین ستون

                        payload = {
                            "room_id": self.room_id,
                            "timestamp": time.time(),
                            "temperature": temp_val,
                            "humidity": hum_val,
                            "light_lux": light_val,
                            "occupancy": occ_val
                        }

                        # انتشار (Publish)
                        self.client.publish(self.topic, json.dumps(payload))
                        print(f"📡 Row {i + 1}: Temp={temp_val} | Light={light_val} | Occ={occ_val}")

                        # مکث 5 ثانیه‌ای
                        time.sleep(5)

                    except ValueError as e:
                        print(f"⚠️ Skipping row {i + 1} due to data error: {e} | Content: {row}")
                        continue
                    except IndexError as e:
                        print(f"⚠️ Skipping row {i + 1} due to missing columns: {e}")
                        continue

        except FileNotFoundError:
            print(f"❌ Error: '{self.data_file}' not found. Make sure it is in the RPi_Sensor folder!")


if __name__ == "__main__":
    sensor = VirtualSensor("datatraining.txt", "Classroom_101")
    sensor.start()