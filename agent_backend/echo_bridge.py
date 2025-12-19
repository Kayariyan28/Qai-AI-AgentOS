#!/usr/bin/env python3
"""Simple echo bridge for testing AgentOS communication (no LLM)."""
import socket
import json
import time

HOST = '127.0.0.1'
PORT = 1234

def main():
    print(f"EchoBridge: Waiting for AgentOS on {HOST}:{PORT}...")
    
    s = None
    while s is None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print("EchoBridge: Connected!")
        except ConnectionRefusedError:
            print(".", end="", flush=True)
            time.sleep(1)
            s = None
    
    read_buffer = ""
    
    try:
        while True:
            data = s.recv(4096)
            if not data:
                print("EchoBridge: Connection closed")
                break
                
            read_buffer += data.decode('utf-8', errors='ignore')
            
            while '\n' in read_buffer:
                line, read_buffer = read_buffer.split('\n', 1)
                line = line.strip()
                if not line: 
                    continue
                
                print(f"<<< {line}")
                
                try:
                    msg = json.loads(line)
                    
                    if msg.get('msg_type') == 'task':
                        # Simple echo response
                        reply = {
                            "id": msg.get('id'),
                            "target": "shell",
                            "msg_type": "response",
                            "content": f"Echo: {msg.get('content')}"
                        }
                        
                        resp_str = json.dumps(reply) + "\n"
                        s.sendall(resp_str.encode('utf-8'))
                        print(f">>> Sent: {resp_str.strip()}")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON Error: {e} - Data: {line[:100]}")
                    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if s: 
            s.close()

if __name__ == "__main__":
    main()
