# Qai AgentOS Prototype

This is the Python-based AI Agent prototype for Qai AgentOS. It demonstrates an "Agentic" interface where an LLM (running locally via Ollama) controls the system using tools.

## Prerequisites

1.  **Python 3.10+**
2.  **Ollama**: Used to run the local LLM.
    - Install: `curl -fsSL https://ollama.com/install.sh | sh`
    - Pull Model: `ollama pull llama3.2` (or `mistral`)

## Setup

1.  **Create Virtual Environment**:
    ```bash
    cd agent_prototype
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Agent**:
    ```bash
    python3 ai_shell.py
    ```

2.  **Interact**:
    The agent supports the following capabilities:

    -   **Shell Commands**: "List files in this folder", "Create a directory called test"
        -   *Note: Only safe commands like `ls`, `mkdir`, `echo` are allowed.*
    -   **Web Search**: "Who won the super bowl in 2024?", "Search for Rust tutorials"
    -   **Math**: "Calculate integral of x^2", "Is 99991 prime?"
    -   **Plotting**: "Plot y=sin(x)", "Plot a bar chart with [10, 20, 15]"

## Troubleshooting

-   **Ollama Connection Error**: Ensure Ollama is running (`ollama serve`).
-   **Missing Model**: Run `ollama list` to check if `llama3.2` is installed. If not, run `ollama pull llama3.2`.
