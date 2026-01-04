# IoT Smart Campus Management Platform

## Overview

An IoT-based Smart Campus Management Platform designed to monitor environmental conditions and occupancy across multiple rooms. The system automatically controls lighting and heating systems to improve energy efficiency and user comfort.

## Architecture

The system follows a microservice-based IoT architecture:

- **Physical Layer (Simulated)**: Virtual sensors and actuators using Kaggle datasets.
- **Data & Logic Layer**: Control strategy services (Smart Controller) processing sensor data and generating actuation commands.
- **User Awareness Layer**: Dashboard and notification services for real-time and historical insights.
- **Communication**: MQTT for real-time data, REST for configuration and history.

## Components

- **Catalog Service**: Central configuration management.
- **Smart Controller**: Logic for managing lighting and heating based on occupancy and schedules.
- **Sensor Simulator**: Simulates real-world sensor data.
- **Notification Service**: Alerts users via Telegram for critical events (e.g., high CO2).
- **Dashboard**: Web interface built with Streamlit for monitoring.

## Installation & Usage

1. **Requirements**:

   - Python 3.8+
   - MQTT Broker (e.g., Mosquitto) running on default port.

2. **Setup**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Running the System**:
   You can start the entire system using the provided batch file:
   ```cmd
   start_system.bat
   ```

## License

MIT
