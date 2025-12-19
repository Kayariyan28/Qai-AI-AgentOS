# Qai AgentOS 🧠🤖

> **The First Artificial Intelligence Operating System.**
> 
> *Hybrid Rust Kernel + LangGraph Neural Backend.*

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Rust](https://img.shields.io/badge/built_with-Rust-orange.svg) ![AI](https://img.shields.io/badge/AI-LangGraph-purple.svg)

## Overview
AgentOS is an experimental operating system that redefines the "User Space." Instead of a dumb shell waiting for commands, the user interacts with a **Neural Kernel Bridge** connected to state-of-the-art LLM Agents.

-   **Speak Naturally**: The shell understands English, not just Bash.
-   **Agent Arena**: Built-in "Psychology Test" tailored to evaluate and rank different AI architectures (ReAct vs Chain-of-Thought) with dynamic problems.
-   **Real-World Control**: Controls your host environment (Music, Tools) from within the QEMU sandbox.

## 📚 Documentation
-   [**Quick Start**](#quick-start)
-   [**User Guide**](docs/USER_GUIDE.md) - **Detailed commands and tool usage.**
-   [**macOS & Siri Integration**](docs/MACOS_INTEGRATION.md) - 🍎 **Turning your Mac into an Agent.**
-   [**System Architecture**](docs/SYSTEM_ARCHITECTURE.md) - Deep dive into the Rust/Python hybrid design.
-   [**Product Vision**](docs/VISION.md) - The philosophy of the "Post-GUI" OS.
-   [**PRD**](docs/PRD.md) - Features, Roadmap, and Requirements.

## Quick Start

### Prerequisites
-   **Rust Nightly**: `rustup override set nightly`
-   **QEMU**: `brew install qemu`
-   **Python 3.10+**: With `langgraph`, `langchain`, `ollama` installed.

### One-Line Launch
```bash
./scripts/run_bridge.sh
```
*This starts the Python AI Bridge and launches the Kernel in QEMU automatically.*

## Key Features 🌟

### 1. The Agent Psychology Test
A built-in benchmarking suite for AI Agents.
-   **Dynamic Games**: Pattern Recognition, Logic Puzzles, Strategy Games generated on-the-fly by a "GameMaster" LLM.
-   **SWOT Analysis**: Automatically generates a professional SWOT report of the agents' performance.
-   **LangGraph Power**: features distinct `ReAct` and `CoT` (Chain of Thought) graph implementations.

### 2. Natural Language Shell
```text
AgentOS> I'm bored, play some music.
[Agent]: Playing your 'Chilled Mix' on Spotify.
```

### 3. Native macOS Control 
Qai is not trapped in the box. It bridges to your Host Mac to:
-   **Control Siri & Music**: "Play some Jazz" triggers native playback.
-   **Manage System**: Control volume, open apps, and automate workflows via AppleScript.

### 4. Self-Reflection
The OS can inspect its own state and generate implementation plans for new features using the `implementation_plan` artifact standard.

## Tech Stack 🛠️

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Kernel** | **Rust** (`no_std`) | Hardware Abstraction, Interrupts, VGA, Serial |
| **Virtualization** | **QEMU** | Hardware Emulation |
| **Bridge** | **Python 3** | PTY/Serial bridging, JSON-RPC routing |
| **Brain** | **LangGraph** | Agent State Machines (ReAct, CoT) |
| **LLM** | **Ollama / Llama 3** | Inference Engine |

## Directory Structure
```text
AgentOS/
├── kernel/             # Rust Source Code
│   ├── src/main.rs     # Kernel Entry
│   └── src/task/       # Async Executor & Shell
├── agent_backend/      # Python AI Brain
│   ├── src/tools/      # Agent Tools (PsychTest, Music)
│   └── pty_echo_bridge.py # Serial Bridge
├── scripts/            # Build & Run scripts
└── docs/               # Architecture & PRDs
```

## Contributing
We welcome "Architects" who want to build the future of computing. Check out [docs/PRD.md](docs/PRD.md) for the roadmap.

---
*Built with ❤️ by the Antigravity Team.*
