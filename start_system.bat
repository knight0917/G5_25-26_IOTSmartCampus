@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo      IoT Smart Campus - Auto Setup
echo ============================================

if exist "venv" goto :found_venv

:create_venv
echo [Setup] Creating Python Virtual Environment (venv)...
python -m venv venv

:found_venv
echo [Setup] Activating venv...
call venv\Scripts\activate

:install_deps
echo [Setup] Installing dependencies (this tracks new requirements)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b
)

:launch_services
echo.
echo [1/5] Starting Catalog Service...
start "Catalog Service" cmd /k "call venv\Scripts\activate & uvicorn catalog.catalog_service:app --reload --port 8000"
timeout /t 2 /nobreak >nul

echo [2/5] Starting Smart Controller...
start "Smart Controller" cmd /k "call venv\Scripts\activate & uvicorn controller.controller_service:app --reload --port 8001"

echo [3/5] Starting Dashboard...
start "Dashboard" cmd /k "call venv\Scripts\activate & python -m streamlit run dashboard/dashboard.py"

echo [4/5] Starting Notification Service (Component 5)...
start "Notification Service" cmd /k "call venv\Scripts\activate & python notification/notification_service.py"

echo [5/5] Starting Sensor Simulator...
start "Sensor Simulator" cmd /k "call venv\Scripts\activate & python simulator/sensor_simulator.py"

echo ============================================
echo      All Services Launched!
echo ============================================
pause
