#!/bin/bash
# scripts/run_bridge.sh
#
# Usage: ./scripts/run_bridge.sh
# This script automatically detects the running QEMU kernel and connects the Python Agent Bridge to it.

# 1. Ensure we are in the project root
cd "$(dirname "$0")/.." || exit

# 2. Activate Virtual Environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
else
    echo "Warning: .venv not found. Assuming environment is set up."
fi

# 3. Read PTY from file (created by builder)
echo "AgentBridge: Detecting QEMU Serial Port..."

PTY_FILE="pty_device.txt"
MAX_WAIT=30
COUNT=0

# Wait for valid PTY file
while [ $COUNT -lt $MAX_WAIT ]; do
    if [ -f "$PTY_FILE" ]; then
        PTY_CANDIDATE=$(cat "$PTY_FILE" | tr -d '[:space:]')
        if [ -n "$PTY_CANDIDATE" ] && [ -e "$PTY_CANDIDATE" ]; then
            break
        fi
    fi
    sleep 1
    echo -n "."
    COUNT=$((COUNT+1))
done
echo ""

if [ -z "$PTY_CANDIDATE" ] || [ ! -e "$PTY_CANDIDATE" ]; then
    echo "Error: PTY device not found or doesn't exist."
    echo "Checking for QEMU..."
    ps aux | grep qemu | grep -v grep
    exit 1
fi

echo "AgentBridge: Found Active Kernel at $PTY_CANDIDATE"

# 4. Set PYTHONPATH and Run
export PYTHONPATH=$PYTHONPATH:$(pwd)/agent_backend

echo "AgentBridge: Launching Backend..."
echo "---------------------------------------------------"

# Pass the detected PTY to the python script
echo "$PTY_CANDIDATE" | python3 agent_backend/src/main.py
