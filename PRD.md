# Product Requirements Document (PRD)

## Project: Cryptarithmetic Solver — Powered by Google ADK & FastAPI

### 1. Vision & Purpose
A full-stack constraint satisfaction puzzle solver utilizing the Google Agent Development Kit (ADK), Gemini 2.5 Flash, and a pure-Python Backtracking + Forward Checking + MRV (Minimum Remaining Values) + LCV (Least Constraining Value) algorithm engine.

### 2. Functional Requirements
- **FR-1: Constraint Satisfaction Solver Engine**
  - Parse arbitrary alphametic formulas (e.g. `SEND + MORE = MONEY`, `CROSS + ROADS = DANGER`).
  - Leading letters cannot be zero ($D \neq 0$ if first character).
  - All distinct letters must map to unique digits ($0 \dots 9$).
  - Solve with forward checking and MRV/LCV heuristic pruning.
- **FR-2: Validation API**
  - Check puzzle syntax, character set size ($\le 10$ unique letters), and solvability.
- **FR-3: Hint Generation Flow**
  - Progressive 3-tier hints (Letter deduction, range restriction, solution stepping) without instant spoilers.
- **FR-4: Google ADK Conversational Agent**
  - Conversational interface with tool calling (`solve_puzzle`, `give_hint`, `generate_puzzle`).
- **FR-5: Web UI & Vercel Deployment**
  - Interactive HTML/JS frontend in `public/index.html` communicating with `/api/*` endpoints.

### 3. Non-Functional Requirements
- **NFR-1: Performance:** Constraint solver executes typical 8–10 letter puzzles under 100ms.
- **NFR-2: Cloud Compatibility:** Serverless execution on Vercel via Python ASGI adapter.
- **NFR-3: API Security:** Zero exposure of `GOOGLE_API_KEY` on client.
