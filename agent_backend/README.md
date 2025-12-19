# Agent Backend

This directory contains the brain of the AgentKernel. It is a Python-based system that uses LangChain and LangGraph to execute user instructions agentically.

## Architecture

- **`src/main.py`**: Entry point.
- **`src/agent/`**: Core agent logic (Graph definition).
- **`src/tools/`**: Low-level system tools (FS, Process).
- **`src/llm.py`**: LLM Interface (Ollama).

## Usage

1. Create a virtual environment: `python3 -m venv .venv`
2. Activate: `source .venv/bin/activate`
3. Install: `pip install -e .`
4. Run: `python -m src.main`
