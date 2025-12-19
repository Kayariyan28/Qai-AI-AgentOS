# AgentOS Architecture

## Overview
AgentOS is a minimal, monolithic, x86_64 kernel tailored for AI-agentic workflows. It treats "agents" as first-class citizens via a character device `/dev/agent` that bridges kernel and user space to an external LLM.

## Boot Flow (Phase 0)
1. BIOS starts.
2. `bootloader` (Rust crate) loads the kernel ELF.
3. Maps kernel to virtual address space.
4. Jumps to `_start` in `kernel/src/main.rs`.

## Kernel (Phase 1+)
- **Arch**: x86_64
- **Language**: Rust (`no_std`)
- **Memory**: Paging enabled by bootloader.
- **Interrupts**: IDT will be set up for Timer and Keyboard.
- **Syscalls**: `syscall`/`sysret` instruction based.

## Userspace (Phase 2+)
- **Init**: First process starting the shell.
- **Shell (`sh`)**: Basic command interpreter.
- **Agentsh**: AI-aware shell.

## Agent Bridge (Phase 3-4)
- **Kernel Device**: `/dev/agent` (Character device).
- **Daemon (`agentd`)**: Reads from `/dev/agent`, talks to Host TCP bridge.
- **Host Bridge**: Python script forwarding JSON to local LLM.
