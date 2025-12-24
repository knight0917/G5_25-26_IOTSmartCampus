import streamlit as st # Used for creating the web dashboard interface
import json # Used for loading the system state from JSON file
import time # Used for the dashboard refresh loop
import pandas as pd # Used for data manipulation if needed (e.g. historical data)

st.set_page_config(page_title="IoT Smart Campus", page_icon="🏫", layout="wide")

st.title("🏫 Smart Campus Management Dashboard")

# --- Quick Links ---
with st.sidebar:
    st.header("🔗 Quick Links")
    st.markdown("[📡 Controller API Status (JSON)](http://localhost:8001/status)")
    st.markdown("[🤖 Open Telegram Bot](https://t.me/+ZbDgRMvfSv8yNjg0)")
    st.info("Click above to view raw system state or interact with the bot.")

# Function to load data
def load_state():
    try:
        with open("system_state.json", "r") as f:
            return json.load(f)
    except:
        return {}

# Auto-refresh logic
placeholder = st.empty()

while True:
    state = load_state()
    
    with placeholder.container():
        st.write(f"Last Refreshed: {time.strftime('%H:%M:%S')}")
        
        if not state:
            st.warning("Waiting for data... Ensure Controller and Simulator are running.")
        else:
            # Create columns for each room
            cols = st.columns(len(state))
            
            sorted_rooms = sorted(state.items())
            
            for index, (room_id, data) in enumerate(sorted_rooms):
                with cols[index % len(cols)]: # Handle wrap if many rooms
                    st.header(f"{data.get('name', room_id)}")
                    
                    # --- Schedule Status (NEW) ---
                    sched_status = data.get('scheduled', 'Unknown')
                    if sched_status == 'Class Active':
                        st.success(f"📅 **{sched_status}**")
                    else:
                        st.info(f"📅 **{sched_status}**")
                    
                    st.divider()

                    # Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Temperature", f"{data['temp']} °C")
                    c2.metric("Humidity", f"{data['humidity']} %")
                    
                    c3, c4 = st.columns(2)
                    c3.metric("Light", f"{data['lux']} Lux")
                    
                    # --- CO2 Visual Alert (NEW) ---
                    co2_val = float(data.get('co2', 400))
                    if co2_val > 1500:
                        c4.error(f"🚨 **CO2 CRITICAL**: {co2_val} ppm")
                    elif co2_val > 1000:
                        c4.warning(f"⚠️ **CO2 Warning**: {co2_val} ppm")
                    else:
                        c4.metric("CO2", f"{co2_val} ppm") # Default look
                    
                    # Status Indicators
                    st.subheader("Status")
                    occ_color = "🟢" if data['occupancy'] == "Yes" else "⚪"
                    st.markdown(f"**Occupancy:** {occ_color} {data['occupancy']}")
                    
                    light_icon = "💡" if data['lights'] == "ON" else "🌑"
                    st.markdown(f"**Lights:** {light_icon} {data['lights']}")
                    
                    heat_icon = "🔥" if data['heating'] == "ON" else "❄️"
                    st.markdown(f"**Heating:** {heat_icon} {data['heating']}")
                    
                    st.text(f"Updated: {data['last_update']}")
                    st.divider()

    time.sleep(1) # Refresh every second
