#!/usr/bin/env python3
"""Standalone test for LangGraph agent - no kernel required."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.graph import get_agent_graph, SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage

def test_agent():
    print("=" * 50)
    print("Testing LangGraph Agent (Standalone)")
    print("=" * 50)
    
    print("\n1. Initializing agent graph...")
    try:
        graph = get_agent_graph()
        print("   ✓ Agent graph created successfully!")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n2. Testing simple prompt...")
    try:
        config = {"configurable": {"thread_id": "test-session"}}
        inputs = {"messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content="Hello, what can you do?")
        ]}
        
        print("   Calling agent.invoke()... (this may take a few seconds)")
        result = graph.invoke(inputs, config=config)
        
        messages = result.get("messages", [])
        print(f"   ✓ Got {len(messages)} messages back")
        
        # Print last message
        if messages:
            last = messages[-1]
            print(f"\n   Last message type: {type(last).__name__}")
            print(f"   Content: {str(last.content)[:200]}...")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n3. Testing music tool...")
    try:
        inputs = {"messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content="open music")
        ]}
        
        print("   Calling agent for 'open music'...")
        result = graph.invoke(inputs, config=config)
        
        messages = result.get("messages", [])
        print(f"   ✓ Got {len(messages)} messages back")
        
        for m in messages:
            print(f"   [{type(m).__name__}]: {str(m.content)[:100]}...")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_agent()
