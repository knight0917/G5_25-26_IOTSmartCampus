1. Purpose and Scope

The purpose of this project is to design and implement an IoT-based Smart Campus Management Platform that monitors environmental conditions and occupancy across multiple rooms and automatically controls lighting and heating systems to improve energy efficiency, user comfort, and operational awareness.

The system follows a microservice-based IoT architecture and simulates physical devices using real-world datasets from Kaggle, while preserving standard IoT communication protocols (MQTT and REST).

2. System Overview

The platform consists of the following main layers:

Physical Layer (Simulated Devices)
Virtual sensor and actuator connectors simulate real IoT devices.

Data & Logic Layer
Control strategy services process sensor data and generate actuation commands.

User Awareness Layer
Dashboards and notification services provide real-time and historical insights.

All components are loosely coupled and communicate using MQTT for real-time data and REST for configuration and history.

3. Data Sources
   3.1 Sensor Data

Sensor data are simulated using the Kaggle dataset:

Occupancy Detection Data Set
File used: alldatatrain.csv

The dataset provides the following fields:

Temperature (°C)

Humidity (%)

Light (lux)

CO₂ (ppm)

Occupancy (0 = no one present, 1 = occupied)

Timestamp

3.2 Timetable / Class Schedule

A class schedule is defined in the Campus Catalog and specifies expected room usage periods (e.g., lecture hours).

4. Functional Requirements
   FR-1: Virtual Sensor Simulation

The system shall simulate environmental sensors using real-world datasets.

Sensor data shall be published periodically via MQTT.

Each room shall have its own virtual sensor connector and MQTT topic.

FR-2: Multi-Room Support

The system shall support multiple rooms simultaneously.

Each room shall be independently monitored and controlled.

Configuration for rooms shall be retrieved from the Campus Catalog.

FR-3: Lighting Control Strategy

The system shall control lighting based on occupancy, light levels, and class schedules.

Lighting Rules:

Occupied Room

If occupancy = 1 and light < 300 lux → lights ON

If light ≥ 300 lux → lights OFF

Unoccupied Room

If occupancy = 0 for more than 5 minutes → lights OFF

Special Rule (IMPORTANT)

If a class is scheduled but no occupancy is detected, all lights must remain OFF.

This rule prevents unnecessary energy usage due to incorrect schedules or empty classrooms.

FR-4: Heating (Temperature) Control Strategy

The system shall maintain thermal comfort while minimizing energy consumption.

Temperature Setpoints (Recommended & Realistic):

Minimum temperature: 20 °C

Maximum temperature: 23 °C

These values are consistent with:

University building standards

Energy efficiency guidelines

Thermal comfort models

Heating Rules:

If occupancy = 1 and temperature < 20 °C → heating ON

If temperature ≥ 23 °C → heating OFF

If occupancy = 0 → heating OFF (regardless of schedule)

📌 Occupancy always has priority over the schedule.

FR-5: Occupancy Priority Rule (Very Important)

Occupancy detection has higher priority than the timetable.

Schedule Occupancy System Behavior
Class scheduled Occupied Normal operation
Class scheduled Not occupied Lights OFF, Heating OFF
No class Occupied Comfort rules applied
No class Not occupied Everything OFF

This ensures robust and realistic system behavior.

FR-6: Actuation Command Generation

Actuation commands shall be generated only by control strategy services.

Commands shall be published via MQTT.

Sensors shall never directly control actuators.

FR-7: Data Storage and History

Sensor data shall be stored in a historical database (e.g., ThingSpeak).

Historical data shall be accessible via REST APIs.

Dashboards shall visualize both real-time and historical data.

FR-8: User Awareness

A dashboard shall display:

Temperature

Occupancy

Light status

Energy-related indicators

Notifications shall be generated when:

CO₂ exceeds a predefined threshold

Abnormal conditions occur

5. Non-Functional Requirements
   NFR-1: Scalability

Adding a new room shall not require changes to existing services.

Configuration shall be handled through the Campus Catalog.

NFR-2: Modularity

Each component shall run as an independent microservice.

Services shall be replaceable without affecting others.

NFR-3: Protocol Compliance

MQTT shall be used exclusively for real-time data and commands.

REST shall be used only for configuration and historical data.

6. Assumptions and Constraints

Physical IoT devices are not available.

Sensor data are simulated using real datasets.

Virtual connectors behave identically to real hardware in terms of interfaces.

The system is designed to be easily extended to real devices in the future.

7. Success Criteria

The project is considered successful if:

Multiple rooms are monitored and controlled independently

Lighting and heating respond correctly to occupancy and schedules

MQTT and REST are used correctly

Control logic is clearly separated from sensors and actuators

Energy-wasting scenarios (scheduled but empty rooms) are avoided

create dummy data for sensors and actuators as per the dataset.
