#!/bin/bash

SERVICE_NAME="nemo-reflex"

echo "--- Removing Nemo Reflex Service ---"

# 1. Stop the service
echo "[INFO] Stopping service..."
sudo systemctl stop ${SERVICE_NAME}

# 2. Disable boot start
echo "[INFO] Disabling boot start..."
sudo systemctl disable ${SERVICE_NAME}

# 3. Remove the file
echo "[INFO] Removing unit file..."
sudo rm /etc/systemd/system/${SERVICE_NAME}.service

# 4. Reload daemon
sudo systemctl daemon-reload

echo "--- REMOVAL COMPLETE ---"
echo "Service is deleted. You can now run 'python main.py' manually."
