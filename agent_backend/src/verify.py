from src.agent.graph import get_agent_graph
from langchain_core.messages import HumanMessage
import sys
import os

def verify():
    print("Verifying Agent...")
    try:
        graph = get_agent_graph()
        
        # Simple task: List files
        print("Task: list directory")
        inputs = {"messages": [HumanMessage(content="List the files in the current directory.")]}
        
        # Just run one step or until completion
        final_state = graph.invoke(inputs)
        
        messages = final_state["messages"]
        last_message = messages[-1]
        print(f"Agent response: {last_message.content}")
        
        if "pyproject.toml" in last_message.content or "src" in last_message.content:
             print("SUCCESS: Agent listed files.")
        else:
             print("WARNING: Agent response did not contain expected files.")
             
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
