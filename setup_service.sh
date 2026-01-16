#!/bin/bash

# Configuration
SERVICE_NAME="nemo-reflex"
USER="nemo"
WORKING_DIR="/home/nemo/Desktop/my_projects/explorer/nemo_reflex/agents"
PYTHON_EXEC="/home/nemo/miniforge3/envs/nemo_reflex/bin/python"
MAIN_SCRIPT="main.py"

echo "--- Installing Nemo Reflex Service ---"

# 1. Install System Dependencies (Just in case)
echo "[INFO] Checking dependencies..."
sudo apt update
sudo apt install -y v4l-utils libcamera-apps

# 2. Create Systemd Unit File
echo "[INFO] Creating service file..."
sudo bash -c "cat > /etc/systemd/system/${SERVICE_NAME}.service" <<EOL
[Unit]
Description=Nemo Reflex - Dual Vision Agent
After=network.target sound.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WORKING_DIR}
ExecStart=${PYTHON_EXEC} ${MAIN_SCRIPT}
Restart=always
RestartSec=5
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=/usr/bin:/bin:${WORKING_DIR}"

[Install]
WantedBy=multi-user.target
EOL

# 3. Reload and Enable
echo "[INFO] Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "[INFO] Enabling service on boot..."
sudo systemctl enable ${SERVICE_NAME}

echo "[INFO] Starting service now..."
sudo systemctl start ${SERVICE_NAME}

echo "--- INSTALLATION COMPLETE ---"
echo "Check status with: sudo systemctl status ${SERVICE_NAME}"
echo "View logs with:    journalctl -u ${SERVICE_NAME} -f"
