#!/bin/bash
# Diagnostic script to test AgentOS components separately

echo "========================================"
echo "AgentOS Diagnostic Test"
echo "========================================"

cd "$(dirname "$0")/.." || exit
PROJECT_DIR="$(pwd)"

# 1. Build kernel
echo ""
echo "Step 1: Building kernel..."
cargo build --package kernel 2>&1 | tail -5
if [ $? -ne 0 ]; then
    echo "❌ Kernel build FAILED"
    exit 1
fi
echo "✅ Kernel build OK"

# 2. Start QEMU in background with log
echo ""
echo "Step 2: Starting QEMU..."
cargo run --package kernel > /tmp/qemu_output.log 2>&1 &
QEMU_PID=$!
echo "QEMU PID: $QEMU_PID"

# 3. Wait for PTY
echo "Waiting for PTY..."
sleep 3

# Check if QEMU is still running
if ! ps -p $QEMU_PID > /dev/null 2>&1; then
    echo "❌ QEMU exited prematurely!"
    echo "Last output:"
    cat /tmp/qemu_output.log
    exit 1
fi

# 4. Find PTY
PTY=$(lsof -p $QEMU_PID -a -d 0-999 -F n 2>/dev/null | grep "n/dev/ttys" | head -n 1 | cut -c 2-)
if [ -z "$PTY" ]; then
    echo "❌ No PTY device found"
    ps aux | grep qemu
    exit 1
fi
echo "✅ PTY found: $PTY"

# 5. Test serial communication
echo ""
echo "Step 3: Testing serial communication..."
echo "Sending test message to kernel..."

# Try to read from PTY
timeout 5 cat "$PTY" &
CAT_PID=$!

sleep 2

# Check if still running
if ps -p $QEMU_PID > /dev/null 2>&1; then
    echo "✅ QEMU is still running after 5 seconds"
else
    echo "❌ QEMU has exited"
    wait $QEMU_PID
    echo "Exit code: $?"
fi

# Cleanup
kill $CAT_PID 2>/dev/null
kill $QEMU_PID 2>/dev/null

echo ""
echo "========================================"
echo "Diagnostic Complete"
echo "========================================"
