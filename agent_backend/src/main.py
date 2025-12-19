import sys
import os
import json
import time
import traceback
import glob
from src.agent.graph import get_agent_graph, SYSTEM_PROMPT
from src.tools.fs_tools import ALL_TOOLS
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import re

def find_qemu_pty():
    """Find the PTY device created by QEMU on macOS."""
    candidates = glob.glob("/dev/ttys*")
    if candidates:
        candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return candidates[0]
    return None

def main():
    print("AgentBridge: Looking for QEMU PTY device...")
    print("=" * 50)
    print("IMPORTANT: When QEMU starts, look for a line like:")
    print('  "char device redirected to /dev/ttysXXX"')
    print("Enter that device path below:")
    print("=" * 50)
    
    device_path = input("PTY device path (e.g., /dev/ttys000): ").strip()
    
    if not device_path:
        print("No device specified. Trying to auto-detect...")
        device_path = find_qemu_pty()
        if not device_path:
            print("Could not find PTY device. Please specify manually.")
            return
        print(f"Found: {device_path}")
    
    if not os.path.exists(device_path):
        print(f"Device {device_path} does not exist!")
        return
    
    print(f"AgentBridge: Opening {device_path}...")
    
    try:
        fd = os.open(device_path, os.O_RDWR | os.O_NONBLOCK)
        print("AgentBridge: Connected to PTY!")
    except Exception as e:
        print(f"Failed to open device: {e}")
        return
    
    # Initialize Agent Graph with tools
    print("AgentBridge: Initializing LangGraph Agent with tools...")
    try:
        graph = get_agent_graph()
        config = {"configurable": {"thread_id": "agentos-session"}}
        print("AgentBridge: Agent ready with 8 tools!")
    except Exception as e:
        print(f"AgentBridge: Agent Init FAILED: {e}")
        traceback.print_exc()
        graph = None
    
    read_buffer = ""
    
    print("AgentBridge: Ready! Waiting for messages...")
    tool_names = [t.name for t in ALL_TOOLS]
    print(f"Available tools: {', '.join(tool_names)}")
    
    heartbeat_counter = 0
    try:
        while True:
            try:
                data = os.read(fd, 4096)
                if data:
                    # Debug disabled for cleaner output
                    # print(f"[RAW RECV {len(data)} bytes]: {data[:100]}")
                    read_buffer += data.decode('utf-8', errors='ignore')
            except BlockingIOError:
                pass
            except OSError as e:
                if e.errno == 35:  # EAGAIN
                    pass
                elif e.errno == 5:  # EIO - PTY disconnected (QEMU closed)
                    print("\n[!] QEMU disconnected. Waiting for reconnection...")
                    time.sleep(2)
                    # Check if PTY still exists
                    if not os.path.exists(device_path):
                        print("[!] PTY device gone. Exiting.")
                        break
                else:
                    raise
            
            # Heartbeat every ~10 seconds to show bridge is alive
            heartbeat_counter += 1
            if heartbeat_counter >= 1000:
                print(".", end="", flush=True)
                heartbeat_counter = 0
            
            while '\n' in read_buffer:
                line, read_buffer = read_buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                print(f"\n>>> Received: {json.dumps(msg, indent=2)}")
                
                if msg.get('msg_type') == 'task':
                    user_prompt = msg.get('content', '')
                    msg_id = msg.get('id')
                    
                    print(f">>> Processing task #{msg_id}: {user_prompt}")
                    
                    # Direct tool calling for common patterns (bypasses LLM)
                    prompt_lower = user_prompt.lower()
                    
                    if 'plot' in prompt_lower and ('=' in prompt_lower or 'sin' in prompt_lower or 'cos' in prompt_lower):
                        # Direct call to plot tool
                        print(">>> Detected plot request - calling tool directly...")
                        from src.tools.plotter import plot_with_matplotlib
                        response_content = plot_with_matplotlib.invoke(user_prompt)
                    elif 'calculate' in prompt_lower or ('what is' in prompt_lower and any(op in user_prompt for op in ['+', '-', '*', '/', '^', 'sqrt', 'sin', 'cos'])):
                        # Direct call to calculator
                        print(">>> Detected calculation - calling tool directly...")
                        from src.tools.calculator import calculator
                        expr = user_prompt.replace('what is', '').replace('calculate', '').strip()
                        response_content = calculator.invoke(expr)
                    elif 'chess' in prompt_lower or 'chess battle' in prompt_lower:
                        # Direct call to chess battle with streaming updates
                        print(">>> Detected chess request - starting AI Chess Battle...")
                        from src.tools.chess_battle import play_chess_battle, set_pty_fd
                        set_pty_fd(fd)  # Enable streaming GUI updates
                        response_content = play_chess_battle.invoke({})
                    elif 'agent test' in prompt_lower or 'psych test' in prompt_lower or 'psychology test' in prompt_lower:
                        # Direct call to agent psychology test
                        print(">>> Detected psychology test request - starting Agent Psychology Test...")
                        from src.tools.psych_test.orchestrator import run_agent_psych_test, set_pty_fd as set_psych_pty
                        set_psych_pty(fd)  # Enable streaming GUI updates
                        response_content = run_agent_psych_test.invoke({})
                    elif 'music' in prompt_lower or ('play' in prompt_lower and 'chess' not in prompt_lower):
                        # Direct call to music tool
                        print(">>> Detected music request - calling tool directly...")
                        from src.tools.music_player import play_music
                        # Extract song name if present (simple heuristic)
                        song_match = re.search(r'play\s+["\']?(.+?)["\']?(?:\s+by\s+|$)', prompt_lower)
                        if 'open' in prompt_lower and 'music' in prompt_lower:
                            response_content = play_music.invoke({})
                        elif song_match:
                            song = song_match.group(1).strip()
                            response_content = play_music.invoke({"song": song})
                        else:
                            response_content = play_music.invoke({})
                    elif graph:
                        try:
                            print(">>> Calling Agent (with tools)...")
                            # Include System Prompt to enforce tool use
                            inputs = {"messages": [
                                SystemMessage(content=SYSTEM_PROMPT),
                                HumanMessage(content=user_prompt)
                            ]}
                            result = graph.invoke(inputs, config=config)
                            
                            # Extract response
                            messages = result.get("messages", [])
                            response_content = "No response generated."
                            
                            # DEBUG: Print full conversation trace
                            print("--- DEBUG: Conversation Trace ---")
                            for m in messages:
                                if isinstance(m, HumanMessage):
                                    print(f"[User]: {m.content}")
                                elif isinstance(m, ToolMessage):
                                    print(f"[Tool Output ({m.name})]: {m.content}")
                                elif isinstance(m, AIMessage):
                                    if m.tool_calls:
                                        print(f"[Assistant Call]: {m.tool_calls}")
                                    else:
                                        print(f"[Assistant Msg]: {m.content}")
                            print("---------------------------------")

                            # 1. Prefer GUI payload from Tool Execution directly
                            gui_found = False
                            for m in reversed(messages):
                                if isinstance(m, ToolMessage) and isinstance(m.content, str):
                                    if m.content.startswith("GUI_PLOT:") or m.content.startswith("GUI_ML_DASHBOARD:") or m.content.startswith("GUI_PIPELINE_DIAGRAM:"):
                                        response_content = m.content
                                        gui_found = True
                                        print(f">>> Found GUI payload in ToolMessage (id={m.tool_call_id})")
                                        break
                            
                            # 2. Fallback to Final AI Answer if no GUI found
                            if not gui_found:
                                for m in reversed(messages):
                                    if isinstance(m, AIMessage) and m.content:
                                        response_content = m.content
                                        break
                            
                            # 3. CRITICAL FALLBACK: Check if response contains a JSON Tool Call
                            # Regex to find {"name": "...", "parameters": {...}}
                            tool_call_match = re.search(r'(\{.*"name":\s*".*?",\s*"parameters":\s*\{.*\}\s*\})', response_content, re.DOTALL)
                            
                            if tool_call_match:
                                json_str = tool_call_match.group(1)
                                try:
                                    call_data = json.loads(json_str)
                                    if "name" in call_data and "parameters" in call_data:
                                        t_name = call_data["name"]
                                        t_params = call_data["parameters"]
                                        print(f">>> Detected JSON Tool Call for '{t_name}'. Executing locally...")
                                        
                                        # Find tool
                                        target_tool = next((t for t in ALL_TOOLS if t.name == t_name), None)
                                        if target_tool:
                                            # Execute
                                            tool_result = target_tool.invoke(t_params)
                                            response_content = str(tool_result)
                                            print(f">>> Local Tool Execution Result len={len(response_content)}")
                                            
                                            # Re-check for GUI payload in manual result
                                            if response_content.startswith("GUI_PLOT:"):
                                                msg_type = "gui_plot"
                                                final_content = response_content[9:]
                                                print(">>> Detected GUI PLOT (from local fallback) - Sending...")
                                            elif response_content.startswith("GUI_ML_DASHBOARD:"):
                                                msg_type = "gui_ml_dashboard"
                                                final_content = response_content[17:]
                                                print(">>> Detected ML DASHBOARD (from local fallback) - Sending...")
                                            elif response_content.startswith("GUI_PIPELINE_DIAGRAM:"):
                                                msg_type = "gui_pipeline_diagram"
                                                final_content = response_content[21:]
                                                print(">>> Detected PIPELINE DIAGRAM (from local fallback) - Sending...")
                                        else:
                                            print(f">>> Tool '{t_name}' not found in ALL_TOOLS.")
                                except json.JSONDecodeError:
                                    pass # Not JSON
                                except Exception as e:
                                    print(f">>> Local Tool Execution FAILED: {e}")

                            print(f">>> Agent Response: {response_content[:200]}...")
                        except Exception as e:
                            response_content = f"Agent Error: {str(e)}"
                            print(f">>> Agent Error: {e}")
                            traceback.print_exc()
                    else:
                        response_content = "Agent not initialized"
                    
                    msg_type = "response"
                    final_content = response_content

                    # Robust Regex Detection for GUI Payloads
                    # Check for Pipeline
                    pipe_match = re.search(r'GUI_PIPELINE_DIAGRAM:(\{.*\})', response_content, re.DOTALL)
                    # Check for ML Dashboard
                    ml_match = re.search(r'GUI_ML_DASHBOARD:(\{.*\})', response_content, re.DOTALL)
                    # Check for Plot
                    plot_match = re.search(r'GUI_PLOT:(\{.*\})', response_content, re.DOTALL)
                    # Check for Chess
                    chess_match = re.search(r'GUI_CHESS:(\{.*\})', response_content, re.DOTALL)
                    
                    if pipe_match:
                        msg_type = "gui_pipeline_diagram"
                        final_content = pipe_match.group(1) # Extract just JSON
                        print(">>> Detected PIPELINE DIAGRAM - Sending extracted JSON...")
                    elif ml_match:
                        msg_type = "gui_ml_dashboard"
                        final_content = ml_match.group(1) # Extract just JSON
                        print(">>> Detected ML DASHBOARD - Sending extracted JSON...")
                    elif plot_match:
                        msg_type = "gui_plot"
                        final_content = plot_match.group(1) # Extract just JSON
                        print(">>> Detected GUI PLOT - Sending extracted JSON...")
                    elif chess_match:
                        msg_type = "gui_chess"
                        final_content = chess_match.group(1) # Extract just JSON
                        print(">>> Detected GUI CHESS - Sending extracted JSON...")
                    elif chess_match:
                        msg_type = "gui_chess"
                        final_content = chess_match.group(1) # Extract just JSON
                        print(">>> Detected GUI CHESS - Sending extracted JSON...")
                    
                    # Original/simple checks as fallback (for backward compat if tool output is raw)
                    elif response_content.startswith("GUI_PLOT:"):
                        msg_type = "gui_plot"
                        final_content = response_content[9:]
                        print(">>> Detected GUI PLOT (Direct) - Sending...")
                    elif response_content.startswith("GUI_PIPELINE_DIAGRAM:"):
                        msg_type = "gui_pipeline_diagram"
                        final_content = response_content[21:]
                        print(">>> Detected PIPELINE DIAGRAM (Direct) - Sending...")
                    elif response_content.startswith("GUI_ML_DASHBOARD:"):
                        msg_type = "gui_ml_dashboard"
                        final_content = response_content[17:]
                        print(">>> Detected ML DASHBOARD (Direct) - Sending...")

                    reply = {
                        "id": msg_id,
                        "target": "shell",
                        "msg_type": msg_type,
                        "content": final_content
                    }
                    
                    resp_str = json.dumps(reply) + "\n"
                    
                    # Send in chunks to avoid overrunning kernel serial FIFO (16 bytes)
                    # 115200 baud = ~11KB/s. 16 bytes fill in ~1.4ms.
                    # Safety: 32 byte chunks with 0.02s delay.
                    chunk_size = 32
                    for i in range(0, len(resp_str), chunk_size):
                        chunk = resp_str[i:i+chunk_size]
                        # Debug disabled for cleaner output
                        # print(f">>> Sending chunk {i//chunk_size}: {chunk[:10]}...")
                        
                        # Write chunk with retry logic
                        retries = 3
                        while retries > 0:
                            try:
                                os.write(fd, chunk.encode('utf-8'))
                                break
                            except BlockingIOError:
                                time.sleep(0.01)
                                retries -= 1
                        
                        time.sleep(0.02) # 20ms delay to let kernel drain
                    
                    # Debug disabled
                    # print(">>> SENT COMPLETE!")
            
            time.sleep(0.01)
                    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        os.close(fd)

if __name__ == "__main__":
    main()
