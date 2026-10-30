<div align="center">

# 🔢 Cryptarithmetic × Google ADK

**AI-Powered Puzzle Solver with Gemini Intelligence**

[![CI](https://github.com/harinish45/cryptarithmetic-adk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/harinish45/cryptarithmetic-adk-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![ADK](https://img.shields.io/badge/Google%20ADK-Agent-orange)](https://google.github.io/adk-docs)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?logo=vercel)](vercel.json)

> *Solves cryptarithmetic puzzles using Google ADK + Gemini 2.5 Flash with step-by-step reasoning and conversational explanations*

[📋 TODO](TODO.md) · [🧪 Test Chat](test_chat.py) · [🚀 Live Demo](#)

</div>

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph User["👤 User"]
        Chat["💬 Chat Interface\n(Web / CLI)"]
    end

    subgraph ADK["🤖 Google ADK Agent"]
        Orchestrator["🧠 Gemini 2.5 Flash\nOrchestrator"]
        SolverTool["🔧 solver_tool\n(ADK Tool)"]
        ExplainerTool["📋 explain_tool\n(ADK Tool)"]
        ValidatorTool["✅ validate_tool\n(ADK Tool)"]
    end

    subgraph Core["⚙️ Python CSP Engine"]
        Parser["🔤 Puzzle Parser"]
        Backtrack["🔙 Backtracking\n+ MRV + LCV"]
        Tracer["📍 Step Tracer"]
    end

    subgraph API["🌐 FastAPI"]
        SolveEP["POST /solve"]
        ChatEP["POST /chat"]
        HistoryEP["GET /history"]
    end

    Chat --> API
    API --> Orchestrator
    Orchestrator --> SolverTool
    Orchestrator --> ExplainerTool
    Orchestrator --> ValidatorTool
    SolverTool --> Core
    Core --> Parser
    Parser --> Backtrack
    Backtrack --> Tracer
```

---

## 💬 Example Conversation

```
You: Solve SEND + MORE = MONEY

Gemini: Let me work through this step by step...
        Setting up constraints: S≠0, M≠0, all digits unique
        Running MRV heuristic — assigning M=1 first (most constrained)
        ...
        ✅ Solution found!
        S=9, E=5, N=6, D=7, M=1, O=0, R=8, Y=2
        9567 + 1085 = 10652 ✓

You: Why did you assign M=1 first?

Gemini: M appears in the result's leftmost position...
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/harinish45/cryptarithmetic-adk-python.git
cd cryptarithmetic-adk-python

pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your-key-here"

# Test the agent
python test_chat.py

# Start web server
uvicorn api.main:app --reload
```

---

## 📁 Structure

```
cryptarithmetic-adk-python/
├── 🤖  cryptarithmetic_agent/  # Google ADK agent + tools
├── 🌐  api/                   # FastAPI backend
├── 🖥️  public/                # Frontend assets
├── 🧪  test_chat.py           # Chat test harness
└── ⚙️  vercel.json            # Deployment config
```

---

<div align="center">
<a href="https://google.github.io/adk-docs">Google ADK Docs</a> · <a href="LICENSE">MIT License</a> · Built by harinish45
</div>