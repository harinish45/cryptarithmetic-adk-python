"""
FastAPI backend for the Cryptarithmetic ADK Solver.
Vercel entry point: api/index.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptarithmetic_agent.solver import solve, parse_puzzle
import random

app = FastAPI(title="Cryptarithmetic Solver API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request Models ───────────────────────────────────────────────────────────

class SolveRequest(BaseModel):
    expression: str
    max_solutions: int = 5

class ValidateRequest(BaseModel):
    expression: str

class HintRequest(BaseModel):
    expression: str
    hint_level: int = 1

class GenerateRequest(BaseModel):
    difficulty: str = "medium"

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Cryptarithmetic Solver API"}

@app.post("/api/solve")
def solve_endpoint(req: SolveRequest):
    result = solve(req.expression, max_solutions=req.max_solutions)
    return result

@app.post("/api/validate")
def validate_endpoint(req: ValidateRequest):
    try:
        operands, result_word, letters, leading = parse_puzzle(req.expression)
    except ValueError as e:
        return {"valid": False, "error": str(e)}
    solved = solve(req.expression, max_solutions=1)
    return {
        "valid": True,
        "solvable": solved["success"],
        "unique_letters": letters,
        "leading_letters": list(leading),
        "operands": operands,
        "result": result_word,
        "solutions_count": len(solved["solutions"]),
    }

@app.post("/api/hint")
def hint_endpoint(req: HintRequest):
    hints = []
    try:
        operands, result_word, letters, leading = parse_puzzle(req.expression)
    except ValueError as e:
        return {"hints": [f"Error: {e}"], "level": req.hint_level}

    if req.hint_level >= 1:
        hints.append(f"📝 {len(letters)} unique letters: {', '.join(letters)}")
        hints.append(f"➕ Operands: {' + '.join(operands)}")
        hints.append(f"📊 Result word: {result_word}")
    if req.hint_level >= 2:
        hints.append(f"⚠️ Leading letters (cannot be 0): {', '.join(leading)}")
        max_len = max(len(result_word), max(len(op) for op in operands))
        for col in range(max_len):
            col_letters = []
            for op in operands:
                idx = len(op) - (max_len - col)
                if idx >= 0:
                    col_letters.append(op[idx])
            res_idx = len(result_word) - (max_len - col)
            if res_idx >= 0:
                col_letters.append(result_word[res_idx])
            if col_letters:
                hints.append(f"  Column {max_len - col}: {' | '.join(col_letters)}")
    if req.hint_level >= 3:
        hints.append("💡 Work right-to-left tracking carries")
        hints.append("💡 Leading letters are heavily constrained — start there")
    return {"hints": hints, "level": req.hint_level}

WORD_LISTS = {
    "easy":   [("CAT","DOG","BEAST"),("RED","BLUE","GREEN"),("ONE","TWO","THREE")],
    "medium": [("SEND","MORE","MONEY"),("TEAR","DEAR","HEART"),("LIAR","LIAR","PANTS")],
    "hard":   [("CROSS","ROADS","DANGER"),("FORTY","TEN","SIXTY"),("APPLE","GRAPE","LEMON")],
}

@app.post("/api/generate")
def generate_endpoint(req: GenerateRequest):
    level = req.difficulty.lower() if req.difficulty.lower() in WORD_LISTS else "medium"
    word1, word2, result_word = random.choice(WORD_LISTS[level])
    expression = f"{word1} + {word2} = {result_word}"
    solved = solve(expression, max_solutions=1)
    return {
        "expression": expression,
        "words": [word1, word2],
        "result_word": result_word,
        "difficulty": level,
        "solvable": solved["success"],
    }
