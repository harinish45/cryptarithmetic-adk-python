# AGENTS & Autonomous Tool Conventions

## Project Rules & Python Architecture Invariants

1. **Architecture & Frameworks:**
   - Google Agent Development Kit (ADK) + Gemini 2.5 Flash (`cryptarithmetic_agent/`).
   - FastAPI serverless API adapter (`api/index.py`).
   - Static HTML/JS frontend (`public/`).

2. **Python Conventions:**
   - Type hints on all functions and method signatures.
   - Pure Python solver in `solver.py` without external C-extensions to preserve Vercel serverless compatibility.
   - Keep `requirements.txt` lean.

3. **Validation & Testing:**
   - Validate solver with `python test_chat.py` or unit tests before committing.
