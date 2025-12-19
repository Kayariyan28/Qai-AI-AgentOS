#!/bin/bash
# scripts/run_all.sh
#
# Usage: ./scripts/run_all.sh
#
# This script:
# 1. Opens a NEW Terminal tab/window to run the Kernel (QEMU).
# 2. Waits for the Kernel to initialize.
# 3. Automatically connects the Agent Bridge in the CURRENT window.

# Ensure we are in project root
cd "$(dirname "$0")/.." || exit
PROJECT_DIR="$(pwd)"

echo "🚀 AgentOS: Unified Launcher"
echo "--------------------------------"

# 1. Launch QEMU in a separate Terminal window/tab
echo "1. Launching Kernel (QEMU) in new terminal..."
osascript <<EOF
tell application "Terminal"
    do script "cd \"$PROJECT_DIR\" && sh scripts/run_qemu.sh"
end tell
EOF

# 2. Loop until PTY file is created (timeout 30s)
echo "2. Waiting for Kernel to initialize..."
MAX_RETRIES=30
COUNT=0
PTY_FILE="pty_device.txt"

# Clean up old PTY file
rm -f "$PTY_FILE"

while [ $COUNT -lt $MAX_RETRIES ]; do
    if [ -f "$PTY_FILE" ]; then
        PTY_CANDIDATE=$(cat "$PTY_FILE" | tr -d '[:space:]')
        if [ -n "$PTY_CANDIDATE" ]; then
            break
        fi
    fi
    
    sleep 1
    echo -n "."
    COUNT=$((COUNT+1))
done

echo ""

if [ -z "$PTY_CANDIDATE" ]; then
    echo "❌ Error: Timeout waiting for PTY device."
    echo "The pty_device.txt file was not created."
    echo ""
    echo "Debug: Looking for QEMU processes..."
    ps aux | grep qemu | grep -v grep
    exit 1
fi

echo "✅ Kernel detected at $PTY_CANDIDATE"

# 3. Launch Bridge
echo "3. Starting Agent Bridge..."
./scripts/run_bridge.sh
