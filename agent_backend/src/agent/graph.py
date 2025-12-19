from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from src.tools.fs_tools import ALL_TOOLS
import os

SYSTEM_PROMPT = """You are AgentOS, an AI assistant. You have tools available:
- plot_with_matplotlib: Generate plots (use: "plot y = sin(x) from -3.14 to 3.14")
- calculator: Evaluate math expressions
- web_search: Search the web
- safe_shell_execute: Run shell commands
- list_directory, make_directory, write_file, read_file: File operations
- build_ml_models: Build ML models & visualize dashboard (use: "build 4 ml models...")
- data_auditor: Generate, Audit, Clean, and Save datasets (use: "run data auditor for...")
- compose_email: Open macOS Mail with draft (use: "draft email to... about...")
- play_music: Control Apple Music (use: 'play "Song" by "Artist"' OR just "open music" to launch app)

ALWAYS use tools to perform actions. DO NOT describe code - call the tools directly.
If the user asks for ML or plots, YOU MUST USE THE TOOLS. DO NOT GENERATE PYTHON CODE."""

def get_agent_graph():
    model_name = os.getenv("AGENT_MODEL", "llama3.2")
    
    llm = ChatOllama(model=model_name, temperature=0)
    
    # Create agent without system prompt modifier (not supported in this version)
    # The SystemMessage will be prepended in main.py instead
    graph = create_react_agent(llm, ALL_TOOLS)
    
    return graph
