#!/bin/bash
set -e

cd "$(dirname "$0")/.." || exit

# Clean up old PTY file
rm -f pty_device.txt

echo "Building and starting kernel..."

# Run cargo which builds kernel and starts QEMU
# Redirect stderr to tee so we can capture and display it
cargo run --package kernel 2>&1 | while IFS= read -r line; do
    echo "$line"
    # Look for PTY device path in QEMU output
    if [[ "$line" == *"char device redirected to"* ]]; then
        PTY_PATH=$(echo "$line" | grep -o '/dev/ttys[0-9]*')
        if [ -n "$PTY_PATH" ]; then
            echo "$PTY_PATH" > pty_device.txt
            echo ">>> Saved PTY path: $PTY_PATH"
        fi
    fi
done
