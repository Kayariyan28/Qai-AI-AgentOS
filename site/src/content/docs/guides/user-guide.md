---
title: User Guide
description: Detailed usage instructions for Qai AgentOS
---

> **How to talk to your Operating System.**
> This guide details the commands, prompts, and tools available in the AgentOS Natural Language Shell.

## Interaction Philosophy
In AgentOS, you don't type strict syntax. You **state your intent**. The system routes your request to the appropriate specialized agent or tool.

**Format**:
```text
AgentOS> [Your Natural Language Request]
```

---

## 🛠️ Core Tools & Capabilities

### 1. Agent Psychology Test 🧠
Run the benchmark suite to evaluate different AI architectures (ReAct vs Chain-of-Thought) on dynamic logic puzzles.

**Capabilities**:
-   **Dynamic Games**: Solves Pattern Recognition, Deduction, and Strategy games.
-   **SWOT Report**: Generates a detailed Strengths, Weaknesses, Opportunities, Threats analysis.

**Prompts**:
-   `"Run the agent psychology test"`
-   `"Test the agents"`
-   `"Evaluate agent performance"`

**Example Output**:
```text
🏆 GAME 1: PATTERN RECOGNITION
>>> Agent B (Chain-of-Thought) thinking...
Step 1: Analyzing sequence 2, 4, 8...
...
Winner: Agent B

📊 SWOT ANALYSIS
...
```

### 2. Music Control 🎵
Control your host machine's audio (Spotify/Music.app) directly from the OS shell.

**Capabilities**:
-   Play specific songs, albums, or playlists.
-   Pause, resume, skip tracks.

**Prompts**:
-   `"Play some jazz music"`
-   `"Play Bohemian Rhapsody"`
-   `"Pause the music"`
-   `"Next song"`

### 3. Data Auditor 📊
Analyze CSV datasets and generate summary statistics and health checks.

**Capabilities**:
-   Detect missing values.
-   Generate statistical distribution via ASCII charts.
-   Identify outliers.

**Prompts**:
-   `"Audit the sales_data.csv file"`
-   `"Check data/users.csv for errors"`
-   `"Give me a summary of report.csv"`

### 4. ML Model Builder 🤖
Train simple machine learning models on valid CSV datasets.

**Capabilities**:
-   AutoML-style model selection (Regression/Classification).
-   Trains on host, saves model artifact.
-   Reports accuracy/R2 score.

**Prompts**:
-   `"Train a model on housing_prices.csv to predict price"`
-   `"Build a classifier for iris.csv"`

### 5. Chess Battle ♟️
Watch two agents play chess against each other or challenge an agent.

**Capabilities**:
-   Agent vs Agent matches.
-   Visual ASCII board updates.

**Prompts**:
-   `"Start a chess battle"`
-   `"Run the chess simulation"`

### 6. Calculator & Utilities 🧮
Perform complex math or quick lookups.

**Prompts**:
-   `"Calculate the square root of 1444"`
-   `"What is 25% of 850?"`
-   `"Search for the latest Rust release notes"` (Web Search)

---

## 🔧 System Commands

These are "Meta" commands for managing the OS interaction itself.

| Command | Description |
| :--- | :--- |
| `help` | Shows valid command syntax (if in legacy mode). |
| `clear` | Clears the VGA screen. |
| `shutdown` | Safely halts the kernel (and QEMU). |

## 🚨 Troubleshooting

**"The Agent isn't responding!"**
1.  Check the Python Bridge logs in your terminal. Ensure `run_bridge.sh` is still running.
2.  If the bridge died, restart it. The Kernel handles serial reconnection gracefully.

**"It says 'Command not found'?"**
-   The Orchestrator might have failed to classify your intent. Try rephrasing more simply.
    -   *Bad*: "Do the thing with the numbers."
    -   *Good*: "Audit the numbers.csv file."
