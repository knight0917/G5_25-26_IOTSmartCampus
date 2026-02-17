# Project Architecture & Data Flow Map

This document describes the connections, dependencies, and data flow of the IoT Smart Campus system.

## 1. System Overview

The system controls smart classroom environments (Lighting, Heating) based on Sensor Data (Occupancy, CO2, Light) and Rules.

**Core Services:**

1.  `catalog_service.py`: **Registry** (Stores configuration).
2.  `sensor_simulator.py`: **Inputs** (Generates fake sensor data from CSV).
3.  `controller_service.py`: **Brain** (Decides to turn lights ON/OFF).
4.  `notification_service.py`: **Alerts** (Sends Telegram Monitor).
5.  `dashboard.py`: **View** (Visualizes state).

---

## 2. File Connections (Source -> Destination)

| File                        | Connection                            | Usage                                                    |
| :-------------------------- | :------------------------------------ | :------------------------------------------------------- |
| **`catalog.json`**          | Read By -> `catalog_service.py`       | Loads initial room configs and API keys.                 |
| **`dummy_sensor_data.csv`** | Read By -> `sensor_simulator.py`      | Provides row-by-row sensor data for simulation.          |
| **`system_state.json`**     | Written By <- `controller_service.py` | Controller saves the current snapshot of all rooms here. |
| **`system_state.json`**     | Read By -> `dashboard.py`             | Dashboard reads this file every second to update the UI. |
| **`secrets.json`**          | Read By -> `notification_service.py`  | Load Telegram Bot Tokens.                                |

---

## 3. Communication & Data Flow

### Step 1: Configuration (The Setup)

- **Startup**: All services (`sim`, `ctrl`, `notif`) send a **HTTP GET** request to `http://localhost:8080` (Catalog) to get the list of rooms and the MQTT Broker address.

### Step 2: Sensing (The Input & Dynamic Discovery)

- **Simulator Loop (Every 10s)**:
  - Queries `http://localhost:8080/rooms` to see if new rooms have been added.
  - If a new room is found, it spawns a **new thread** for it.
- **Data Generation**:
  - Reads `Temp=22, Occ=1` from CSV.
- **Transmission**:
  - Sends **MQTT Message** to topic: `campus/room_101/sensors`.

### Step 3: Logic (The Controller)

- **Controller** receives the message via MQTT.
- **Logic**:
  - _If Occupancy == 1 AND Light < 300 -> Turn Lights ON._
- **Action 1**: Controller sends **MQTT Message** to `campus/room_101/actuators` (Lights: ON).
- **Action 2**: Controller writes status to `system_state.json`.
- **Action 3**: Controller sends data to **ThingSpeak Cloud** (HTTP).

### Step 4: Alerting (The Notification Service)

- **Notification Service** receives the same MQTT Sensor message.
- **Logic**:
  - _If CO2 > 1500 -> Critical Alert._
- **Action**: Sends **HTTP POST** to **Telegram API**.

### Step 5: Visualization (The Dashboard)

- **Dashboard** continuously reads `system_state.json`.
- Updates the UI: Shows "Occupied" icon and "Lights ON".
- Embeds **ThingSpeak Iframe** for historical charts.

---

## 4. Visual Diagram (Mermaid)

```mermaid
---
config:
  layout: dagre
---
flowchart TB
 subgraph CLOUD["☁️ External Cloud Services"]
    direction LR
        TG("Telegram API")
        TS("ThingSpeak")
  end
 subgraph CORE["🏢 Smart Campus Core"]
    direction TB
        Broker{{"MQTT Broker<br>TCP :1883"}}
        Catalog["Catalog Service"]
        Ctrl["Smart Controller"]
        Notif["Notification Service"]
        State[("system_state.json")]
        Config[("catalog.json")]
  end
 subgraph EDGE["🔌 Simulation"]
        Sim["Sensor Simulator"]
        Actu["Actuator Service"]
        Logger["Logger Service"]
        CSV[("dummy_data.csv")]
        Logs[("sensor_log.csv")]
  end
    Config o--o Catalog
    Catalog -.-> Sim & Ctrl & Notif
    CSV o--o Sim
    Sim -- Pub --> Broker
    Broker <== Sub/Pub ==> Ctrl
    Broker == Sub ==> Notif
    Broker <== Sub/Pub ==> Actu
    Broker == Sub ==> Logger
    Logger -- Append --> Logs
    Ctrl -- Write --> State
    Ctrl -- HTTPS POST --> TS
    Notif -- HTTPS POST --> TG
    TG -. 🔔 Push Alert .-> User(("👤 System Admin<br>Your Phone/PC"))
    TS -. 📉 Historical Charts .-> Dash(["Dashboard UI"])
    State -. Load UI .-> Dash
    Dash == 👀 Visual Monitoring ==o User

     TG:::cloud
     TS:::cloud
     Broker:::infra
     Catalog:::compute
     Ctrl:::compute
     Notif:::compute
     State:::storage
     Config:::storage
     Sim:::compute
     Actu:::compute
     Logger:::compute
     Logs:::storage
     CSV:::storage
     User:::human
     Dash:::ui
    classDef compute fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,rx:5,ry:5,color:#0d47a1,font-weight:bold
    classDef storage fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,rx:5,ry:5,color:#e65100
    classDef infra   fill:#263238,stroke:#000,stroke-width:2px,color:#fff,shape:hexagon
    classDef cloud   fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,stroke-dasharray: 5 5,color:#4a148c
    classDef ui      fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40
    classDef human   fill:#ffcdd2,stroke:#c62828,stroke-width:4px,color:#b71c1c,font-size:16px
```

## 5. Connectivity Reference (ASCII)

```text
+---------------------+       HTTP GET (:8080)      +-------------------+
|   Catalog Service   | <-------------------------- | All Other Services|
+---------------------+                             +-------------------+
          ^
          | Reads
   [catalog.json]

       +-------------------------+
       |      MQTT Broker        |
       |  (localhost:1883)       |
       +-----------+-------------+
                   ^
        Pub/Sub    |
   +---------------+---------------+
   |               |               |               |
   |               |               |               |
[Simulator]   [Controller]   [Notification]   [Actuator] --- [Logger]
   |               |               |               |             |
Reads CSV       Writes JSON      Sends TG       Pub Status    Writes CSV
                   |
            [system_state.json]
                   |
              [Dashboard]
```

## 6. Port & Protocol Matrix

| Source Service   | Target Service  | Protocol | Port   | Purpose                                 |
| :--------------- | :-------------- | :------- | :----- | :-------------------------------------- |
| **Any Service**  | **Catalog**     | HTTP     | `8080` | Fetch configuration/settings.           |
| **Simulator**    | **MQTT Broker** | MQTT     | `1883` | Publish sensor data.                    |
| **Controller**   | **MQTT Broker** | MQTT     | `1883` | Subscribe to sensors, Publish commands. |
| **Notification** | **MQTT Broker** | MQTT     | `1883` | Subscribe to sensors/alerts.            |
| **Controller**   | **ThingSpeak**  | HTTPS    | `443`  | Cloud data logging.                     |
| **Notification** | **Telegram**    | HTTPS    | `443`  | Send user alerts.                       |
| **Dashboard**    | **FileSystem**  | File I/O | N/A    | Read `system_state.json`.               |
| **Browser**      | **Dashboard**   | HTTP     | `8501` | User Interface (Streamlit).             |
