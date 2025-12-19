#!/usr/bin/env python3
"""Simple PTY echo bridge for testing AgentOS communication (no LLM).
This script tests basic serial communication without the complexity of the LLM agent.
"""
import os
import sys
import json
import time
import glob

def find_qemu_pty():
    """Find the most recently modified PTY device owned by current user."""
    import subprocess
    result = subprocess.run(
        ["ls", "-lt"] + glob.glob("/dev/ttys*"),
        capture_output=True, text=True
    )
    for line in result.stdout.strip().split('\n'):
        parts = line.split()
        if len(parts) >= 9 and parts[2] == os.environ.get('USER'):
            return parts[-1]
    return None

def main():
    print("=" * 60)
    print("PTY Echo Bridge (No LLM)")
    print("This tests basic kernel <-> host communication")
    print("=" * 60)
    
    # Find PTY
    device_path = find_qemu_pty()
    if not device_path:
        print("ERROR: No PTY device found for current user.")
        print("Make sure QEMU is running first: ./scripts/run_qemu.sh")
        return
    
    print(f"Found PTY: {device_path}")
    
    # Open PTY
    try:
        fd = os.open(device_path, os.O_RDWR | os.O_NONBLOCK)
        print(f"Connected to {device_path}")
    except Exception as e:
        print(f"Failed to open PTY: {e}")
        return
    
    read_buffer = ""
    print("")
    print("Listening for kernel messages...")
    print("(Type in QEMU window and press Enter)")
    print("-" * 40)
    
    try:
        while True:
            # Read from PTY
            try:
                data = os.read(fd, 4096)
                if data:
                    text = data.decode('utf-8', errors='ignore')
                    print(f"[RECV {len(data)} bytes]: {repr(text)}")
                    sys.stdout.flush()
                    read_buffer += text
            except BlockingIOError:
                pass
            except OSError as e:
                if e.errno == 35:  # EAGAIN
                    pass
                elif e.errno == 5:  # EIO - PTY closed
                    print("\n[!] PTY disconnected (QEMU closed?)")
                    break
                else:
                    raise
            
            # Process complete lines
            while '\n' in read_buffer:
                line, read_buffer = read_buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                
                print(f"[LINE]: {line}")
                
                # Try to parse as JSON
                try:
                    msg = json.loads(line)
                    print(f"[JSON OK]: id={msg.get('id')}, type={msg.get('msg_type')}, content={msg.get('content', '')[:50]}")
                    
                    # Send echo response
                    if msg.get('msg_type') == 'task':
                        reply = {
                            "id": msg.get('id'),
                            "target": "shell",
                            "msg_type": "response",
                            "content": f"Echo: {msg.get('content', '')}"
                        }
                        resp_str = json.dumps(reply) + "\n"
                        print(f"[SEND]: {resp_str.strip()}")
                        
                        # Send in chunks
                        for i in range(0, len(resp_str), 32):
                            chunk = resp_str[i:i+32].encode('utf-8')
                            try:
                                os.write(fd, chunk)
                            except BlockingIOError:
                                time.sleep(0.01)
                                os.write(fd, chunk)
                            time.sleep(0.02)
                        
                        print("[SEND OK]")
                except json.JSONDecodeError:
                    print(f"[NOT JSON]: {line[:100]}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        os.close(fd)

if __name__ == "__main__":
    main()
