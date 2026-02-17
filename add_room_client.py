import requests

# Configuration
CATALOG_URL = "http://localhost:8080/add_room"

def add_room():
    # Define the new room structure
    new_room = {
        "room_id": "room_202",
        "name": "Robotics Lab",
        "mqtt_sensor_topic": "campus/room_202/sensors",
        "mqtt_actuator_topic": "campus/room_202/actuators",
        "thingspeak_channel_id": "000000",
        "thingspeak_write_key": "XXXXXX",
        "thresholds": {
            "co2_warning": 1100,
            "co2_critical": 1600
        },
        "schedule": [
            {
                "day": "Monday",
                "start_time": "08:00",
                "end_time": "18:00"
            }
        ]
    }

    try:
        print(f"📡 Sending POST request to {CATALOG_URL}...")
        response = requests.post(CATALOG_URL, json=new_room)
        
        if response.status_code == 200:
            print("✅ Success! Room added.")
            print("Response:", response.json())
        else:
            print(f"❌ Failed. Status Code: {response.status_code}")
            print("Error:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Catalog Service. Is it running?")

if __name__ == "__main__":
    add_room()
