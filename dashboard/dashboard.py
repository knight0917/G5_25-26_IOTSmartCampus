import streamlit as st # Used for creating the web dashboard interface
import json # Used for loading the system state from JSON file
import time # Used for the dashboard refresh loop
import pandas as pd # Used for data manipulation if needed (e.g. historical data)

st.set_page_config(page_title="IoT Smart Campus", page_icon="🏫", layout="wide")

st.title("🏫 Smart Campus Management Dashboard")

# --- CSS to Hide Anchor Links ---
st.markdown("""
    <style>
    /* Hide the link button */
    .stApp a.anchor-link { display: none; }
    /* Hide the link icon that appears on hover in newer Streamlit versions */
    [data-testid="stHeaderActionElements"] { display: none; }
    /* Target the specific class for header anchors if the above don't work */
    .css-15zrgzn {display: none}
    .css-1629p8f h1 a, .css-1629p8f h2 a, .css-1629p8f h3 a {display: none}
    /* Most generic way to hide the chain icon next to headers */
    h1 > a, h2 > a, h3 > a { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

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

def load_catalog_metadata():
    """Load static metadata like ThingSpeak IDs from catalog."""
    try:
        with open("catalog/catalog.json", "r") as f:
            data = json.load(f)
            # Create a map: room_id -> thingspeak_channel_id
            return {room["room_id"]: room.get("thingspeak_channel_id") for room in data.get("rooms", [])}
    except Exception as e:
        # st.error(f"Error loading catalog: {e}")
        return {}

# Auto-refresh logic
placeholder = st.empty()

while True:
    state = load_state()
    
    # Load catalog metadata once (or periodically if needed)
    if 'ts_map' not in st.session_state:
        st.session_state.ts_map = load_catalog_metadata()
    
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
                    
                    # --- ThingSpeak Link ---
                    ts_id = getattr(st.session_state, 'ts_map', {}).get(room_id)
                    if ts_id:
                        st.markdown(f"📈 [View on ThingSpeak](https://thingspeak.com/channels/{ts_id})")
                        
                        with st.expander("📉 View Live Charts"):
                            # Embed ThingSpeak Charts
                            # Field 1: Temperature, Field 2: Humidity
                            st.write("**Temperature**")
                            st.components.v1.iframe(f"https://thingspeak.com/channels/{ts_id}/charts/1?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=60&type=line&update=15", height=260)
                            
                            st.write("**Humidity**")
                            st.components.v1.iframe(f"https://thingspeak.com/channels/{ts_id}/charts/2?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=60&type=line&update=15", height=260)
                    
                    st.divider()

    time.sleep(1) # Refresh every second
