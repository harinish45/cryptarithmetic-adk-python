# Cryptarithmetic Solver — Powered by Google ADK

A full-stack cryptarithmetic puzzle solver using **Google Agent Development Kit (ADK)** + **Gemini 2.5 Flash**, with a pure-Python **Backtracking + MRV + LCV** algorithm engine.

🔗 **Live Demo**: [View on Vercel](#)

---

## Features

- 🔢 **Solve** any cryptarithmetic puzzle (e.g. `SEND + MORE = MONEY`)
- ✅ **Validate** — check if a puzzle is well-formed and solvable
- 💡 **Hints** — 3 progressive hint levels without spoiling the answer
- ✨ **Generate** — create new puzzles at easy / medium / hard difficulty
- 🤖 **ADK Agent** — run the full AI assistant with `adk web`

## Algorithm

| Component | Description |
|---|---|
| Backtracking | Core recursive search with undo on failure |
| Forward Checking | Prunes domains after each assignment |
| MRV Heuristic | Picks the letter with fewest options — fail fast |
| LCV Heuristic | Tries digits that eliminate the least for others |

## Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key
echo "GOOGLE_API_KEY=your_key" > .env

# 3. Run the ADK web UI (agent chat + trace inspector)
adk web

# 4. Or run the FastAPI backend
uvicorn api.index:app --reload --port 8000
```

Then open `http://localhost:8000` in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/solve` | Solve a puzzle |
| POST | `/api/validate` | Validate a puzzle |
| POST | `/api/hint` | Get progressive hints |
| POST | `/api/generate` | Generate a new puzzle |

## Deploy to Vercel

```bash
npm i -g vercel
vercel --prod
```

Add `GOOGLE_API_KEY` in your Vercel dashboard environment variables.

## Project Structure

```
cryptarithmetic-adk-py/
├── api/
│   └── index.py              # FastAPI backend (Vercel entry point)
├── cryptarithmetic_agent/
│   ├── solver.py             # Pure Python solver engine
│   └── agent.py              # Google ADK LlmAgent definition
├── public/
│   └── index.html            # Frontend UI
├── vercel.json               # Vercel routing config
├── requirements.txt
└── .env                      # GOOGLE_API_KEY (not committed)
```
