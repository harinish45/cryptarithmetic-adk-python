"""
Google ADK Cryptarithmetic Agent & Tool Interface
Tools: solve_puzzle, validate_puzzle, explain_solution, generate_puzzle
Conforms to Google Agent Development Kit (ADK) specification.
"""
from __future__ import annotations

import logging
import random
from typing import Any, Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from cryptarithmetic_agent.solver import (
    solve,
    parse_puzzle,
    parse_puzzle_details,
    generate_hints,
    generate_reasoning_trace,
    CryptarithmeticError,
    ParsedPuzzle,
)

logger = logging.getLogger(__name__)


# ─── Pydantic Input Schemas ──────────────────────────────────────────────────

class SolvePuzzleInput(BaseModel):
    """Input parameters for solving a cryptarithmetic puzzle."""
    expression: str = Field(
        ...,
        description="Puzzle expression to solve, e.g. 'SEND + MORE = MONEY' or 'FORTY + TEN + TEN = SIXTY'",
        examples=["SEND + MORE = MONEY", "FORTY + TEN + TEN = SIXTY"]
    )
    max_solutions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of solutions to compute and return (default 5)"
    )


class ValidatePuzzleInput(BaseModel):
    """Input parameters for validating puzzle syntax and solvability."""
    expression: str = Field(
        ...,
        description="Puzzle expression to validate, e.g. 'SEND + MORE = MONEY'",
        examples=["SEND + MORE = MONEY"]
    )


class ExplainPuzzleInput(BaseModel):
    """Input parameters for generating progressive reasoning hints."""
    expression: str = Field(
        ...,
        description="Puzzle expression to explain, e.g. 'SEND + MORE = MONEY'",
        examples=["SEND + MORE = MONEY"]
    )
    hint_level: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Detail level: 1=basic overview, 2=column equations, 3=step-by-step reasoning"
    )


class GeneratePuzzleInput(BaseModel):
    """Input parameters for procedural puzzle generation."""
    difficulty: str = Field(
        default="medium",
        description="Difficulty tier: 'easy', 'medium', or 'hard'"
    )


# ─── Tool Class Wrapper ───────────────────────────────────────────────────────

class CryptarithmeticADKTool:
    """
    Standard ADK Tool wrapper providing metadata, input schema, execution, and FunctionTool conversion.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Any,
        input_schema: type[BaseModel]
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.func: Any = func
        self.input_schema: type[BaseModel] = input_schema

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the underlying tool method with input validation."""
        validated: BaseModel = self.input_schema(**kwargs)
        return self.func(**validated.model_dump())

    def to_tool(self) -> FunctionTool:
        """Convert to Google ADK FunctionTool instance."""
        return FunctionTool(self.func)


# ─── Tool 1: Solve Puzzle ─────────────────────────────────────────────────────

def solve_puzzle(expression: str, max_solutions: int = 5) -> dict[str, Any]:
    """
    Solve a cryptarithmetic puzzle using Column-wise Constraint Satisfaction + MRV + LCV.

    Args:
        expression: Puzzle expression like 'SEND + MORE = MONEY' or 'FORTY + TEN + TEN = SIXTY'
        max_solutions: Maximum solutions to return (default 5)

    Returns:
        Dictionary with solutions, stats, step-by-step reasoning trace, and metadata.
    """
    logger.info("Solving cryptarithmetic puzzle: %s", expression)
    return solve(expression=expression, max_solutions=max_solutions)


# ─── Tool 2: Validate Puzzle ──────────────────────────────────────────────────

def validate_puzzle(expression: str) -> dict[str, Any]:
    """
    Validate if a cryptarithmetic puzzle is properly formed and solvable.

    Args:
        expression: Puzzle expression like 'SEND + MORE = MONEY'

    Returns:
        Dictionary with valid flag, solvable status, letters, and error details.
    """
    logger.info("Validating puzzle: %s", expression)
    try:
        parsed: ParsedPuzzle = parse_puzzle_details(expression)
    except CryptarithmeticError as e:
        return {
            "valid": False,
            "solvable": False,
            "solutions_count": 0,
            "unique_letters": 0,
            "letters": [],
            "leading_letters": [],
            "operands": [],
            "result": "",
            "error": str(e)
        }

    solve_res: dict[str, Any] = solve(expression, max_solutions=1)
    is_solvable: bool = bool(solve_res["success"])

    return {
        "valid": True,
        "solvable": is_solvable,
        "solutions_count": len(solve_res["solutions"]),
        "unique_letters": len(parsed.all_letters),
        "letters": parsed.all_letters,
        "leading_letters": sorted(parsed.leading_letters),
        "operands": parsed.operands,
        "result": parsed.result,
        "error": None
    }


# ─── Tool 3: Explain Solution / Progressive Hints ─────────────────────────────

def explain_solution(expression: str, hint_level: int = 1) -> dict[str, Any]:
    """
    Provide progressive hints and step-by-step reasoning for a cryptarithmetic puzzle.

    Args:
        expression: Puzzle expression like 'SEND + MORE = MONEY'
        hint_level: 1=basic overview, 2=column equations, 3=deduction steps

    Returns:
        Dictionary with hints list, reasoning steps, and column formulas.
    """
    logger.info("Generating explanation for: %s (level %d)", expression, hint_level)
    try:
        parsed: ParsedPuzzle = parse_puzzle_details(expression)
    except CryptarithmeticError as e:
        return {
            "success": False,
            "expression": expression,
            "level": hint_level,
            "hints": [f"Error: {e}"],
            "reasoning_steps": [],
            "column_equations": [],
            "error": str(e)
        }

    solve_res: dict[str, Any] = solve(expression, max_solutions=1)
    raw_solutions: list[dict[str, int]] = (
        [solve_res["solutions"][0]["mapping"]] if solve_res["success"] else []
    )

    hint_data: dict[str, Any] = generate_hints(parsed, raw_solutions, hint_level=hint_level)
    reasoning_steps: list[str] = generate_reasoning_trace(parsed, raw_solutions)

    return {
        "success": True,
        "expression": expression,
        "level": hint_level,
        "hints": hint_data["hints"],
        "reasoning_steps": reasoning_steps,
        "column_equations": hint_data["column_equations"],
        "deductions": hint_data["deductions"],
        "error": None
    }


def explain_puzzle(expression: str, hint_level: int = 1) -> dict[str, Any]:
    """Alias for explain_solution conforming to PRD tool naming."""
    return explain_solution(expression=expression, hint_level=hint_level)


# ─── Tool 4: Procedural Puzzle Generation ─────────────────────────────────────

# Curated catalog of verified mathematically solvable cryptarithmetic puzzles
VERIFIED_PUZZLES: dict[str, list[tuple[list[str], str]]] = {
    "easy": [
        (["TO", "GO"], "OUT"),
        (["HE", "ME"], "WE"),
        (["NO", "NO", "TOO"], "LATE"),
    ],
    "medium": [
        (["SEND", "MORE"], "MONEY"),
        (["BASE", "BALL"], "GAMES"),
        (["EAT", "THAT"], "APPLE"),
    ],
    "hard": [
        (["CROSS", "ROADS"], "DANGER"),
        (["FORTY", "TEN", "TEN"], "SIXTY"),
        (["DONALD", "GERALD"], "ROBERT"),
    ],
}


def generate_puzzle(difficulty: str = "medium") -> dict[str, Any]:
    """
    Generate a new verified cryptarithmetic puzzle at specified difficulty tier.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Dictionary with expression, addends, result word, difficulty, and example solution.
    """
    level: str = difficulty.lower() if difficulty.lower() in VERIFIED_PUZZLES else "medium"
    candidates: list[tuple[list[str], str]] = VERIFIED_PUZZLES[level]
    operands, result = random.choice(candidates)
    expression: str = f"{' + '.join(operands)} = {result}"

    solved: dict[str, Any] = solve(expression, max_solutions=1)

    return {
        "expression": expression,
        "words": operands,
        "result_word": result,
        "difficulty": level,
        "solvable": solved["success"],
        "example_solution": solved["solutions"][0] if solved["success"] else None,
    }


# ─── ADK Tool Declarations ────────────────────────────────────────────────────

solve_tool = FunctionTool(solve_puzzle)
validate_tool = FunctionTool(validate_puzzle)
explain_tool = FunctionTool(explain_solution)
generate_tool = FunctionTool(generate_puzzle)

ALL_TOOLS: list[FunctionTool] = [
    solve_tool,
    validate_tool,
    explain_tool,
    generate_tool,
]


# ─── Root Agent Definition ────────────────────────────────────────────────────

root_agent = LlmAgent(
    name="cryptarithmetic_agent",
    model="gemini-2.5-flash",
    description="An expert AI assistant for cryptarithmetic puzzles - it solves, validates, hints, and generates them.",
    instruction="""You are an expert Cryptarithmetic Puzzle Assistant.

In cryptarithmetic, each letter represents a unique digit (0-9).
For example: SEND + MORE = MONEY means each letter maps to a unique digit
so that the addition holds true numerically.

YOUR TOOLS:
1. solve_puzzle       - Solve any puzzle with the Constraint Satisfaction + MRV + LCV engine
2. validate_puzzle    - Check if a puzzle is well-formed and has solutions
3. explain_solution   - Give hints and step-by-step reasoning at level 1, 2, or 3
4. generate_puzzle    - Create a new verified puzzle at easy / medium / hard difficulty

BEHAVIOR:
- Always use tools - never guess digit values yourself
- When asked to solve, call solve_puzzle and present the step-by-step reasoning trace
- When asked for hints, call explain_solution with the appropriate level
- Be friendly, educational, and always encourage the user to try first
- If asked about algorithm, explain: Column-wise Constraint Satisfaction + Forward Checking + MRV + LCV

Always show the substituted string (e.g. 9567 + 1085 = 10652) from the solution.""",
    tools=ALL_TOOLS,
)
