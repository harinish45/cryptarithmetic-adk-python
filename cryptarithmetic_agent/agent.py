"""
Google ADK Cryptarithmetic Agent
Tools: solve_puzzle, validate_puzzle, explain_solution, generate_puzzle
"""
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from cryptarithmetic_agent.solver import solve, parse_puzzle
import random

# ─── Tool 1: Solve ───────────────────────────────────────────────────────────

def solve_puzzle(expression: str, max_solutions: int = 5) -> dict:
    """
    Solve a cryptarithmetic puzzle using Backtracking + MRV + LCV + Forward Checking.

    Args:
        expression: Puzzle like 'SEND + MORE = MONEY'
        max_solutions: How many solutions to return (default 5)

    Returns:
        Dictionary with solutions, stats, and metadata.
    """
    return solve(expression, max_solutions=max_solutions)


# ─── Tool 2: Validate ────────────────────────────────────────────────────────

def validate_puzzle(expression: str) -> dict:
    """
    Validate if a cryptarithmetic puzzle is properly formed and solvable.

    Args:
        expression: Puzzle expression like 'SEND + MORE = MONEY'

    Returns:
        Dictionary with valid flag, details, and any errors.
    """
    try:
        operands, result, letters, leading = parse_puzzle(expression)
    except ValueError as e:
        return {"valid": False, "error": str(e)}

    result_data = solve(expression, max_solutions=1)
    return {
        "valid": True,
        "solvable": result_data["success"],
        "solutions_count": len(result_data["solutions"]),
        "unique_letters": len(letters),
        "leading_letters": list(leading),
        "operands": operands,
        "result": result,
    }


# ─── Tool 3: Explain / Hints ─────────────────────────────────────────────────

def explain_solution(expression: str, hint_level: int = 1) -> dict:
    """
    Provide progressive hints for a cryptarithmetic puzzle without revealing the full answer.

    Args:
        expression: Puzzle expression like 'SEND + MORE = MONEY'
        hint_level: 1=basic structure, 2=column constraints, 3=strategic tips

    Returns:
        Dictionary with hints list and partial guidance.
    """
    hints = []
    try:
        operands, result, letters, leading = parse_puzzle(expression)
    except ValueError as e:
        return {"hints": [f"Error: {e}"], "level": hint_level}

    if hint_level >= 1:
        hints.append(f"📝 This puzzle has {len(letters)} unique letters: {', '.join(letters)}")
        hints.append(f"➕ Operands: {' + '.join(operands)}")
        hints.append(f"📊 Result word: {result}")

    if hint_level >= 2:
        hints.append(f"⚠️  Leading letters (cannot be 0): {', '.join(leading)}")
        max_len = max(len(result), max(len(op) for op in operands))
        for col in range(max_len):
            col_letters = []
            for op in operands:
                idx = len(op) - (max_len - col)
                if idx >= 0:
                    col_letters.append(op[idx])
            res_idx = len(result) - (max_len - col)
            if res_idx >= 0:
                col_letters.append(result[res_idx])
            if col_letters:
                hints.append(f"  Column {max_len - col} (right→left): {' | '.join(col_letters)}")

    if hint_level >= 3:
        hints.append("💡 Work from the rightmost column left, tracking carries (0 or 1).")
        hints.append("💡 If more than 2 operands in a column, the carry can be larger.")
        hints.append("💡 Leading letters constrain choices heavily — try those first.")

    return {"hints": hints, "level": hint_level}


# ─── Tool 4: Generate ────────────────────────────────────────────────────────

WORD_LISTS = {
    "easy": [
        ("CAT", "DOG", "BEAST"),
        ("RED", "BLUE", "GREEN"),
        ("ONE", "TWO", "THREE"),
    ],
    "medium": [
        ("SEND", "MORE", "MONEY"),
        ("LIAR", "LIAR", "PANTS"),
        ("TEAR", "DEAR", "HEART"),
    ],
    "hard": [
        ("CROSS", "ROADS", "DANGER"),
        ("FORTY", "TEN", "SIXTY"),
        ("APPLE", "GRAPE", "LEMON"),
    ],
}


def generate_puzzle(difficulty: str = "medium") -> dict:
    """
    Generate a new random cryptarithmetic puzzle at the specified difficulty.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Dictionary with expression, words, and whether it's solvable.
    """
    level = difficulty.lower() if difficulty.lower() in WORD_LISTS else "medium"
    options = WORD_LISTS[level]
    word1, word2, result = random.choice(options)
    expression = f"{word1} + {word2} = {result}"
    solved = solve(expression, max_solutions=1)
    return {
        "expression": expression,
        "words": [word1, word2],
        "result_word": result,
        "difficulty": level,
        "solvable": solved["success"],
        "example_solution": solved["solutions"][0] if solved["success"] else None,
    }


# ─── Build Agent ─────────────────────────────────────────────────────────────

root_agent = LlmAgent(
    name="cryptarithmetic_agent",
    model="gemini-2.5-flash",
    description="An expert AI assistant for cryptarithmetic puzzles — it solves, validates, hints, and generates them.",
    instruction="""You are an expert Cryptarithmetic Puzzle Assistant.

In cryptarithmetic, each letter represents a unique digit (0-9).
For example: SEND + MORE = MONEY means each letter maps to a unique digit
so that the addition holds true numerically.

YOUR TOOLS:
1. solve_puzzle       - Solve any puzzle with the Backtracking+MRV+LCV algorithm
2. validate_puzzle    - Check if a puzzle is well-formed and has solutions
3. explain_solution   - Give hints at level 1 (basic), 2 (columns), or 3 (strategy)
4. generate_puzzle    - Create a new puzzle at easy / medium / hard difficulty

BEHAVIOR:
- Always use tools — never guess digit values yourself
- When asked to solve, call solve_puzzle and explain the result
- When asked for hints, call explain_solution with the appropriate level
- Be friendly, educational, and always encourage the user to try first
- If asked about algorithm, explain: Backtracking + Forward Checking + MRV + LCV

Always show the substituted string (e.g. 9567 + 1085 = 10652) from the solution.""",
    tools=[
        FunctionTool(solve_puzzle),
        FunctionTool(validate_puzzle),
        FunctionTool(explain_solution),
        FunctionTool(generate_puzzle),
    ],
)
