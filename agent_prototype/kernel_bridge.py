import sys
import subprocess
import threading
import os
import signal
from ai_shell import process_command

# Command to run QEMU
QEMU_CMD = ["sh", "scripts/run_qemu.sh"]

def read_stream(process, input_buffer):
    """
    Reads from QEMU stdout.
    Distinguishes between LOGS and USER INPUT (prefixed with \x02).
    """
    print("[Bridge]: Monitoring QEMU Output...")
    
    current_line = []
    
    while True:
        # Read byte by byte
        byte = process.stdout.read(1)
        if not byte:
            break
            
        byte_val = ord(byte)
        
        # Logic: 
        # If we see \x02, the NEXT byte is User Input.
        # Otherwise, it's a Log byte (pass through).
        # Wait, if we use \x02 as a prefix for EACH char.
        # We need state machine.
        
        # But wait, python read(1) might buffer?
        # Make sure unbuffered or use PTY.
        # For now, simplistic approach.
        
        # If byte is 0x02, read next byte as char data.
        if byte_val == 0x02:
            data_byte = process.stdout.read(1)
            if not data_byte: break
            
            char = data_byte.decode('utf-8', errors='ignore')
            
            # Handle user input buffering
            if char == '\n' or char == '\r':
                # End of commands
                cmd = "".join(current_line).strip()
                current_line = []
                
                if cmd:
                    print(f"\n[Kernel Input]: {cmd}")
                    
                    # Call Agent
                    response = process_command(cmd)
                    
                    # Write response to QEMU Stdin
                    response_formatted = response.replace('\n', '\r\n')
                    response_formatted += "\r\n> "
                    
                    if process.stdin:
                        process.stdin.write(response_formatted.encode('utf-8'))
                        process.stdin.flush()
                        print(f"[Agent Output]: {response}")
                else:
                    if process.stdin:
                        process.stdin.write(b"\r\n> ")
                        process.stdin.flush()
            
            elif char == '\x08' or char == '\x7f': # Backspace
                if current_line:
                    current_line.pop()
            else:
                current_line.append(char)
                
        else:
            # It's a log byte. Print it to console directly.
            # But avoid breaking lines unnecessarily.
            sys.stdout.buffer.write(byte)
            sys.stdout.flush()

def main():
    print("🤖 AgentOS Kernel Bridge (Pipe Mode)")
    
    # Run QEMU as subprocess with Pipes
    # bufsize=0 for unbuffered
    process = subprocess.Popen(
        QEMU_CMD,
        # Run QEMU as subprocess with Pipes
        # User usually runs from project root
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Merge stderr to stdout
        bufsize=0
    )
    
    try:
        read_stream(process, [])
    except KeyboardInterrupt:
        print("\nStopping...")
        process.terminate()
    finally:
        process.wait()

if __name__ == "__main__":
    # Check CWD
    if not os.path.exists("./scripts/run_qemu.sh"):
        print("Error: Please run from project root (AgentKernel/)")
        sys.exit(1)
    main()
