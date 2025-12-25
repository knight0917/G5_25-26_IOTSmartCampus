import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_data(filename="dummy_sensor_data.csv", num_rows=1000):
    start_time = datetime.now()
    data = []
    
    # Initial state
    occupancy = 0
    light = 0
    temp = 20.0
    co2 = 400.0
    
    for i in range(num_rows):
        timestamp = start_time + timedelta(minutes=i)
        
        # Simulate Occupancy (random changes)
        if random.random() < 0.05: # 5% chance to change state
            occupancy = 1 - occupancy
            
        # Simulate Physics
        if occupancy == 1:
            light = random.uniform(300, 600) # Lights ON
            temp += random.uniform(0.01, 0.05) # Temp rises
            co2 += random.uniform(2, 10) # CO2 rises
        else:
            light = random.uniform(0, 50) # Lights OFF (ambient)
            temp -= random.uniform(0.01, 0.05) # Temp drops
            co2 -= random.uniform(1, 5) # CO2 drops
            
        # Bounds
        temp = max(15, min(30, temp))
        co2 = max(400, min(2000, co2))
        
        data.append({
            "date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperature": round(temp, 2),
            "Humidity": round(random.uniform(40, 60), 2),
            "Light": round(light, 2),
            "CO2": round(co2, 2),
            "HumidityRatio": 0.005, # Constant for now
            "Occupancy": occupancy
        })
        
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Generated {filename} with {num_rows} rows.")

if __name__ == "__main__":
    generate_data()
