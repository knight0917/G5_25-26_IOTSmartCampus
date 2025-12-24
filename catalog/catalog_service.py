from fastapi import FastAPI, HTTPException # Used to create the web API and raise HTTP errors
from pydantic import BaseModel # Used for data validation and schema definitions
from typing import List # Used for type hinting lists in function signatures

app = FastAPI(title="Smart Campus Catalog")

# --- Data Models ---

class Thresholds(BaseModel):
    co2_warning: int = 1000
    co2_critical: int = 1500

class ScheduleItem(BaseModel):
    day: str  # e.g., "Monday"
    start_time: str # "HH:MM", 24h format
    end_time: str   # "HH:MM"

class Room(BaseModel):
    room_id: str
    name: str
    mqtt_sensor_topic: str
    mqtt_actuator_topic: str
    thingspeak_channel_id: str
    thingspeak_write_key: str
    thresholds: Thresholds
    schedule: List[ScheduleItem]

# --- In-Memory Database ---

import json # Used to load configuration from JSON file
import os # Used for file path operations

# --- In-Memory Database (Loaded from file) ---
rooms_db = []

def load_catalog():
    global rooms_db
    try:
        json_path = os.path.join(os.path.dirname(__file__), "catalog.json")
        with open(json_path, "r") as f:
            data = json.load(f)
            # Parse raw JSON into Pydantic models
            rooms_db = [Room(**item) for item in data.get("rooms", [])]
        print(f"Loaded {len(rooms_db)} rooms from catalog.json")
    except Exception as e:
        print(f"Error loading catalog: {e}")
        rooms_db = []

# Load on module start
load_catalog()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Catalog Service Online", "version": "1.0"}

@app.get("/rooms", response_model=List[Room])
def get_rooms():
    return rooms_db

@app.get("/rooms/{room_id}", response_model=Room)
def get_room(room_id: str):
    for room in rooms_db:
        if room.room_id == room_id:
            return room
    raise HTTPException(status_code=404, detail="Room not found")

@app.get("/rooms/{room_id}/schedule", response_model=List[ScheduleItem])
def get_room_schedule(room_id: str):
    for room in rooms_db:
        if room.room_id == room_id:
            return room.schedule
    raise HTTPException(status_code=404, detail="Room not found")

@app.get("/rooms/{room_id}/thresholds", response_model=Thresholds)
def get_room_thresholds(room_id: str):
    for room in rooms_db:
        if room.room_id == room_id:
            return room.thresholds
    raise HTTPException(status_code=404, detail="Room not found")
