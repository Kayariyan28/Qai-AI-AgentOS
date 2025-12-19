---
title: Product Requirements
description: Detailed PRD and Roadmap
---

| Metadata | Details |
| :--- | :--- |
| **Product Name** | AgentOS |
| **Version** | 0.1.0 (Alpha) |
| **Status** | In Development |
| **Target** | AI Researchers, Systems Engineers |

## 1. Problem Statement
Traditional Operating Systems are passive tools. They wait for explicit, granular commands. As AI capabilities explode, we need an OS where the "User Space" is not just a collection of binaries, but an intelligent agent capable of understanding intent, executing complex multi-step workflows, and creating/modifying its own tools.

## 2. Strategic Vision
**"The Last OS You'll Ever Need."**
AgentOS aims to shift the paradigm from "Human operating the computer" to "Human collaborating with the computer." The OS kernel becomes a thin layer of reality (hardware), while the user experience is entirely mediated by a super-intelligent, context-aware agent.

## 3. Key Features

### Core Experience
-   **Natural Language Shell (NLS)**: No more `ls -la | grep x`. Just say "Show me the large files I worked on yesterday."
-   **Hybrid Microkernel**: Rust-based safety for hardware, Python/LangGraph flexibility for intelligence.

### Native Applications (Agent-Native)
-   **Psychology Test Bench**: A rigorous arena to test and rank different AI agent architectures (ReAct vs CoT) on logic, pattern recognition, and strategy. Includes dynamic problem generation and SWOT analysis.
-   **Universal Control**: Native ability to control the Host environment (when running in virtualization) via bridged tools (Music, Files, Calendar).

## 4. User Personas
-   **The Architect**: Wants to design new agent flows and test them in a sandboxed, low-level environment unique to AgentOS.
-   **The Power User**: Wants an OS that anticipates their needs and automates the boring "glue" work of computing.

## 5. Roadmap

### Phase 1: Bootstrap (Current)
-   [x] Rust Kernel booting on QEMU.
-   [x] Basic Serial/VGA I/O.
-   [x] Host-Bridge for AI injection.

### Phase 2: Intelligence Layer (Current)
-   [x] LangGraph Integration.
-   [x] "Psych Test" Agent Evaluation Framework.
-   [x] Dynamic Content Generation.

### Phase 3: Self-Evolution (Future)
-   [ ] **Agent-Compiler Loop**: Agents writing and compiling their own Rust kernel modules live.
-   [ ] **Neural Filesystem**: Storing data not by path, but by semantic meaning vector embeddings.
-   [ ] **Voice Interface**: Pure voice interaction eliminating the keyboard.

## 6. Technical Constraints
-   **Latency**: Serial bridge introduces ms-level latency; acceptable for text, challenging for real-time UI.
-   **Host Dependency**: Currently relies on Host Python environment; goal is to move inference closer to metal (edge models).
