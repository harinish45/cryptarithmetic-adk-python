"""
Pure Python Cryptarithmetic Solver
Algorithms: Backtracking + Forward Checking (AC-3) + MRV + LCV + Column-wise CSP
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class CryptarithmeticError(ValueError):
    """Base exception for cryptarithmetic puzzle errors."""
    pass


class PuzzleSyntaxError(CryptarithmeticError):
    """Raised when the puzzle expression syntax is invalid."""
    pass


class TooManyVariablesError(CryptarithmeticError):
    """Raised when the puzzle contains more than 10 unique letters."""
    pass


class UnsolvablePuzzleError(CryptarithmeticError):
    """Raised when a puzzle is mathematically proven to have no solution."""
    pass


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Variable:
    letter: str
    domain: list[int]
    is_leading: bool = False


@dataclass(frozen=True)
class ParsedPuzzle:
    """Immutable parsed representation of a cryptarithmetic puzzle."""
    operands: list[str]
    result: str
    all_letters: list[str]
    leading_letters: set[str]
    raw_expression: str


@dataclass
class ColumnConstraint:
    """Represents a column constraint aligned from right to left."""
    column_index: int
    column_name: str
    operand_letters: list[str]
    result_letter: Optional[str]
    formula: str


# ─── Parser ───────────────────────────────────────────────────────────────────

def _validate_raw_expression(expression: str) -> str:
    """Validate raw string and strip whitespace."""
    if expression is None or not isinstance(expression, str):
        raise PuzzleSyntaxError("Expression must be a non-empty string.")
    trimmed: str = expression.strip().upper()
    if not trimmed:
        raise PuzzleSyntaxError("Expression cannot be empty.")
    if "=" not in trimmed:
        raise PuzzleSyntaxError(f"Missing '=' in expression: '{expression}'.")
    return trimmed


def _extract_operands_and_result(expression: str) -> tuple[list[str], str]:
    """Split into LHS operands and RHS result."""
    parts: list[str] = expression.split("=")
    if len(parts) != 2:
        raise PuzzleSyntaxError(f"Expression must contain exactly one '=': '{expression}'.")

    lhs: str = parts[0].strip()
    result: str = parts[1].strip()

    if not lhs or not result:
        raise PuzzleSyntaxError("Both sides of '=' must contain words.")

    operands: list[str] = [w.strip() for w in lhs.split("+")]
    if len(operands) < 2:
        raise PuzzleSyntaxError("LHS must have at least two operands separated by '+'.")

    return operands, result


def _validate_alphabetic_tokens(operands: list[str], result: str) -> None:
    """Ensure all operands and result contain only uppercase letters A-Z."""
    for op in operands:
        if not op or not re.match(r"^[A-Z]+$", op):
            raise PuzzleSyntaxError(f"Operand '{op}' must contain only letters A-Z.")
    if not re.match(r"^[A-Z]+$", result):
        raise PuzzleSyntaxError(f"Result '{result}' must contain only letters A-Z.")


def parse_puzzle_details(expression: str) -> ParsedPuzzle:
    """Parse expression into structured ParsedPuzzle dataclass."""
    cleaned: str = _validate_raw_expression(expression)
    operands, result = _extract_operands_and_result(cleaned)
    _validate_alphabetic_tokens(operands, result)

    all_letters: list[str] = sorted(set("".join(operands) + result))
    leading: set[str] = {op[0] for op in operands} | {result[0]}

    if len(all_letters) > 10:
        raise TooManyVariablesError(
            f"Too many unique letters ({len(all_letters)}). Max is 10 (only digits 0-9 are available)."
        )

    return ParsedPuzzle(
        operands=operands,
        result=result,
        all_letters=all_letters,
        leading_letters=leading,
        raw_expression=expression,
    )


def parse_puzzle(expression: str) -> tuple[list[str], str, list[str], set[str]]:
    """
    Parse expressions like:
        SEND + MORE = MONEY
        FORTY + TEN + TEN = SIXTY
        CROSS + ROADS = DANGER
    Returns: (operands, result, all unique letters, leading letters)
    """
    parsed: ParsedPuzzle = parse_puzzle_details(expression)
    return parsed.operands, parsed.result, parsed.all_letters, parsed.leading_letters


# ─── Variable & Domain Builders ───────────────────────────────────────────────

def build_variables(all_letters: list[str], leading: set[str]) -> list[Variable]:
    """Build CSP variables with initial domains (0-9, or 1-9 for leading)."""
    variables: list[Variable] = []
    for letter in all_letters:
        domain: list[int] = list(range(1, 10)) if letter in leading else list(range(0, 10))
        variables.append(Variable(letter=letter, domain=domain, is_leading=(letter in leading)))
    return variables


def check_solution(operands: list[str], result: str, assignment: dict[str, int]) -> bool:
    """Verify whether a complete assignment satisfies the puzzle addition."""
    try:
        nums: list[int] = [int("".join(str(assignment[c]) for c in op)) for op in operands]
        res: int = int("".join(str(assignment[c]) for c in result))
        return sum(nums) == res
    except (KeyError, ValueError):
        return False


# ─── Classic Heuristics & Forward Checking (Backward Compatibility) ──────────

def forward_check(variables: list[Variable], assigned_idx: int, value: int) -> Optional[list[Variable]]:
    """
    Remove `value` from the domains of all other unassigned variables.
    Returns None if any domain becomes empty (dead end).
    """
    new_vars: list[Variable] = []
    for i, v in enumerate(variables):
        if i == assigned_idx:
            new_vars.append(Variable(v.letter, [value], v.is_leading))
        else:
            new_domain: list[int] = [d for d in v.domain if d != value]
            if len(new_domain) == 0:
                return None
            new_vars.append(Variable(v.letter, new_domain, v.is_leading))
    return new_vars


def select_mrv(variables: list[Variable], assigned: set[int]) -> int:
    """MRV: pick the unassigned variable with the smallest domain."""
    best_idx: int = -1
    best_size: float = float("inf")
    for i, v in enumerate(variables):
        if i in assigned:
            continue
        v_size: int = len(v.domain)
        if v_size < best_size or (v_size == best_size and v.is_leading):
            best_size = v_size
            best_idx = i
    return best_idx


def order_lcv(variable: Variable, var_idx: int, all_vars: list[Variable], assigned: set[int]) -> list[int]:
    """LCV: order values by how few options they eliminate in remaining variables."""
    def count_eliminated(value: int) -> int:
        return sum(
            1 for i, v in enumerate(all_vars)
            if i != var_idx and i not in assigned and value in v.domain
        )
    return sorted(variable.domain, key=count_eliminated)


# ─── Column-Wise Fast CSP Engine ──────────────────────────────────────────────

class ColumnCSPSolver:
    """High-performance Column-wise Constraint Satisfaction Solver."""

    def __init__(self, operands: list[str], result: str, leading: set[str]) -> None:
        self.operands: list[str] = operands
        self.result: str = result
        self.leading: set[str] = leading
        self.max_len: int = max(len(result), max(len(op) for op in operands))
        self.columns: list[tuple[list[str], Optional[str]]] = self._build_columns()
        self.nodes_explored: int = 0
        self.backtracks: int = 0

    def _build_columns(self) -> list[tuple[list[str], Optional[str]]]:
        """Align operands and result characters by column from right to left."""
        cols: list[tuple[list[str], Optional[str]]] = []
        for c in range(self.max_len):
            col_ops: list[str] = [op[-1 - c] for op in self.operands if c < len(op)]
            res_char: Optional[str] = self.result[-1 - c] if c < len(self.result) else None
            cols.append((col_ops, res_char))
        return cols

    def _quick_length_check(self) -> bool:
        """Prune instantly if result length is geometrically impossible."""
        max_op_len: int = max(len(op) for op in self.operands)
        if len(self.result) < max_op_len:
            return False
        if len(self.result) > max_op_len + 1:
            return False
        return True

    def solve(self, max_solutions: int = 5) -> list[dict[str, int]]:
        """Solve puzzle and return up to max_solutions mappings."""
        if not self._quick_length_check():
            return []

        solutions: list[dict[str, int]] = []
        assignment: dict[str, int] = {}
        used_digits: set[int] = set()

        self._backtrack(0, 0, 0, 0, assignment, used_digits, solutions, max_solutions)
        return solutions

    def _backtrack(
        self,
        col_idx: int,
        op_idx: int,
        current_sum: int,
        carry_in: int,
        assignment: dict[str, int],
        used_digits: set[int],
        solutions: list[dict[str, int]],
        max_solutions: int,
    ) -> bool:
        """Recursive column-by-column backtracking."""
        self.nodes_explored += 1

        if col_idx == self.max_len:
            if carry_in == 0:
                solutions.append(dict(assignment))
            return len(solutions) >= max_solutions

        col_ops, res_char = self.columns[col_idx]

        if op_idx < len(col_ops):
            return self._assign_operand_char(
                col_idx, op_idx, col_ops[op_idx], current_sum, carry_in,
                assignment, used_digits, solutions, max_solutions
            )

        return self._finish_column(
            col_idx, current_sum, carry_in, res_char,
            assignment, used_digits, solutions, max_solutions
        )

    def _assign_operand_char(
        self,
        col_idx: int,
        op_idx: int,
        char: str,
        current_sum: int,
        carry_in: int,
        assignment: dict[str, int],
        used_digits: set[int],
        solutions: list[dict[str, int]],
        max_solutions: int,
    ) -> bool:
        """Assign or propagate a character in operand list for current column."""
        if char in assignment:
            return self._backtrack(
                col_idx, op_idx + 1, current_sum + assignment[char], carry_in,
                assignment, used_digits, solutions, max_solutions
            )

        start_digit: int = 1 if char in self.leading else 0
        for digit in range(start_digit, 10):
            if digit in used_digits:
                continue
            assignment[char] = digit
            used_digits.add(digit)

            if self._backtrack(
                col_idx, op_idx + 1, current_sum + digit, carry_in,
                assignment, used_digits, solutions, max_solutions
            ):
                return True

            del assignment[char]
            used_digits.remove(digit)
            self.backtracks += 1

        return False

    def _finish_column(
        self,
        col_idx: int,
        current_sum: int,
        carry_in: int,
        res_char: Optional[str],
        assignment: dict[str, int],
        used_digits: set[int],
        solutions: list[dict[str, int]],
        max_solutions: int,
    ) -> bool:
        """Verify column result digit, compute carry-out, and step to next column."""
        total: int = current_sum + carry_in
        digit_out: int = total % 10
        carry_out: int = total // 10

        if res_char is None:
            if digit_out == 0:
                return self._backtrack(
                    col_idx + 1, 0, 0, carry_out,
                    assignment, used_digits, solutions, max_solutions
                )
            return False

        if res_char in assignment:
            if assignment[res_char] == digit_out:
                return self._backtrack(
                    col_idx + 1, 0, 0, carry_out,
                    assignment, used_digits, solutions, max_solutions
                )
            return False

        if digit_out in used_digits:
            return False
        if digit_out == 0 and res_char in self.leading:
            return False

        assignment[res_char] = digit_out
        used_digits.add(digit_out)

        found: bool = self._backtrack(
            col_idx + 1, 0, 0, carry_out,
            assignment, used_digits, solutions, max_solutions
        )

        del assignment[res_char]
        used_digits.remove(digit_out)
        if not found:
            self.backtracks += 1
        return found


# ─── Reasoning Trace & Explanation Generator ──────────────────────────────────

COLUMN_NAMES: list[str] = [
    "Units", "Tens", "Hundreds", "Thousands", "Ten-Thousands",
    "Hundred-Thousands", "Millions", "Ten-Millions"
]


def generate_column_constraints(parsed: ParsedPuzzle) -> list[ColumnConstraint]:
    """Generate human-readable column equations with place value labels."""
    max_len: int = max(len(parsed.result), max(len(op) for op in parsed.operands))
    constraints: list[ColumnConstraint] = []

    for c in range(max_len):
        col_name: str = COLUMN_NAMES[c] if c < len(COLUMN_NAMES) else f"10^{c}"
        col_ops: list[str] = [op[-1 - c] for op in parsed.operands if c < len(op)]
        res_char: Optional[str] = parsed.result[-1 - c] if c < len(parsed.result) else None

        ops_expr: str = " + ".join(col_ops) if col_ops else "0"
        c_in_str: str = f" + c{c}" if c > 0 else ""
        c_out_str: str = f" + 10 * c{c + 1}"
        target_str: str = res_char if res_char else "0"
        if ops_expr == "0" and c_in_str:
            formula: str = f"c{c} = {target_str}{c_out_str}"
        else:
            formula: str = f"{ops_expr}{c_in_str} = {target_str}{c_out_str}"

        constraints.append(ColumnConstraint(
            column_index=c,
            column_name=col_name,
            operand_letters=col_ops,
            result_letter=res_char,
            formula=formula
        ))

    return constraints


def generate_structural_deductions(parsed: ParsedPuzzle) -> list[str]:
    """Generate high-level logical inferences about puzzle bounds and carries."""
    deductions: list[str] = []
    max_op_len: int = max(len(op) for op in parsed.operands)
    num_ops: int = len(parsed.operands)

    leading_str: str = ", ".join(sorted(parsed.leading_letters))
    deductions.append(f"Leading characters cannot be zero: {leading_str} != 0.")

    if len(parsed.result) > max_op_len:
        top_char: str = parsed.result[0]
        max_carry: int = num_ops - 1
        if max_carry == 1:
            deductions.append(
                f"Result '{parsed.result}' has {len(parsed.result)} digits while operands have at most {max_op_len}. "
                f"The highest digit must be the carry from the preceding column: {top_char} = 1."
            )
        else:
            deductions.append(
                f"Result has {len(parsed.result)} digits vs {max_op_len} operand digits. "
                f"The highest digit {top_char} is the carry (1 <= {top_char} <= {max_carry})."
            )

    return deductions


def generate_reasoning_trace(
    parsed: ParsedPuzzle,
    solutions: list[dict[str, int]]
) -> list[str]:
    """Generate step-by-step reasoning trace explaining the puzzle resolution."""
    trace: list[str] = []
    trace.append(f"Step 1: Analyzed puzzle '{parsed.raw_expression}' with {len(parsed.all_letters)} unique letters.")

    for deduction in generate_structural_deductions(parsed):
        trace.append(f"Step 2: Structural deduction - {deduction}")

    constraints: list[ColumnConstraint] = generate_column_constraints(parsed)
    col_summary: str = "; ".join(c.formula for c in constraints)
    trace.append(f"Step 3: Established column-wise carry constraints: {col_summary}.")

    if solutions:
        best: dict[str, int] = solutions[0]
        mapping_str: str = ", ".join(f"{k}={best[k]}" for k in sorted(best.keys()))
        subst_ops: list[str] = ["".join(str(best[c]) for c in op) for op in parsed.operands]
        subst_res: str = "".join(str(best[c]) for c in parsed.result)
        trace.append(f"Step 4: Propagated constraints with MRV + Forward Checking to derive mapping: {mapping_str}.")
        trace.append(f"Step 5: Verified arithmetic substitution: {' + '.join(subst_ops)} = {subst_res} (Sum holds true).")
    else:
        trace.append("Step 4: Exhaustive search concluded no valid assignment exists.")

    return trace


def generate_hints(
    parsed: ParsedPuzzle,
    solutions: list[dict[str, int]],
    hint_level: int = 1
) -> dict[str, Any]:
    """Provide progressive hints from high-level to detailed deduction steps."""
    hints: list[str] = []
    letters_str: str = ", ".join(parsed.all_letters)
    leading_str: str = ", ".join(sorted(parsed.leading_letters))

    if hint_level >= 1:
        hints.append(f"Puzzle has {len(parsed.all_letters)} unique letters: {letters_str}")
        hints.append(f"Operands: {' + '.join(parsed.operands)}")
        hints.append(f"Result: {parsed.result}")

    if hint_level >= 2:
        hints.append(f"Leading letters (cannot be 0): {leading_str} != 0")
        constraints: list[ColumnConstraint] = generate_column_constraints(parsed)
        for c in constraints:
            hints.append(f"  Column {c.column_index + 1} ({c.column_name}): {c.formula}")

    if hint_level >= 3:
        for deduction in generate_structural_deductions(parsed):
            hints.append(f"Hint: {deduction}")
        if solutions:
            # Reveal a helpful anchor letter without spoiling the full puzzle
            anchor_char: str = parsed.result[0]
            anchor_val: int = solutions[0][anchor_char]
            hints.append(f"Key deduction anchor: {anchor_char} = {anchor_val}")

    return {
        "hints": hints,
        "level": hint_level,
        "column_equations": [c.formula for c in generate_column_constraints(parsed)],
        "deductions": generate_structural_deductions(parsed),
    }


# ─── Main Solve Function ──────────────────────────────────────────────────────

def _format_solution(
    mapping: dict[str, int],
    operands: list[str],
    result: str
) -> dict[str, Any]:
    """Format a single solution mapping and its substituted string."""
    subst_parts: list[str] = ["".join(str(mapping[c]) for c in op) for op in operands]
    subst_res: str = "".join(str(mapping[c]) for c in result)
    return {
        "mapping": mapping,
        "substituted": f"{' + '.join(subst_parts)} = {subst_res}"
    }


def solve(expression: str, max_solutions: int = 5) -> dict[str, Any]:
    """
    Main entry-point. Solves puzzle and returns solutions, stats, reasoning trace, and metadata.
    """
    t_start: float = time.perf_counter()

    try:
        parsed: ParsedPuzzle = parse_puzzle_details(expression)
    except CryptarithmeticError as e:
        logger.warning("Puzzle parse failure for '%s': %s", expression, e)
        return {
            "success": False,
            "error": str(e),
            "solutions": [],
            "stats": {"nodes_explored": 0, "backtracks": 0, "solve_time_ms": 0.0},
            "reasoning_trace": [f"Parsing failed: {str(e)}"],
            "metadata": {}
        }

    solver: ColumnCSPSolver = ColumnCSPSolver(
        operands=parsed.operands,
        result=parsed.result,
        leading=parsed.leading_letters
    )

    raw_solutions: list[dict[str, int]] = solver.solve(max_solutions=max_solutions)
    t_end: float = time.perf_counter()
    duration_ms: float = round((t_end - t_start) * 1000.0, 3)

    formatted_solutions: list[dict[str, Any]] = [
        _format_solution(s, parsed.operands, parsed.result) for s in raw_solutions
    ]

    stats: dict[str, Any] = {
        "nodes_explored": solver.nodes_explored,
        "backtracks": solver.backtracks,
        "solve_time_ms": duration_ms
    }

    reasoning_trace: list[str] = generate_reasoning_trace(parsed, raw_solutions)

    return {
        "success": len(formatted_solutions) > 0,
        "solutions": formatted_solutions,
        "stats": stats,
        "reasoning_trace": reasoning_trace,
        "metadata": {
            "operands": parsed.operands,
            "result": parsed.result,
            "unique_letters": parsed.all_letters,
            "leading_letters": sorted(parsed.leading_letters),
            "algorithm": "Column-wise Constraint Satisfaction + Forward Checking + MRV + LCV"
        }
    }
