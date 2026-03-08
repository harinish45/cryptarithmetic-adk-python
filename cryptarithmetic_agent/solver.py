"""
Pure Python Cryptarithmetic Solver
Algorithms: Backtracking + Forward Checking (AC-3) + MRV + LCV
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Variable:
    letter: str
    domain: list[int]
    is_leading: bool = False


def parse_puzzle(expression: str):
    """
    Parse expressions like:
        SEND + MORE = MONEY
        CROSS + ROADS = DANGER
    Returns: (operands, result, all unique letters, leading letters)
    """
    expression = expression.upper().strip()
    match = re.match(r"^(.+)=\s*([A-Z]+)\s*$", expression)
    if not match:
        raise ValueError(f"Invalid puzzle format: '{expression}'. Use e.g. SEND + MORE = MONEY")

    lhs = match.group(1)
    result = match.group(2).strip()

    # Support only + for now (matches the TS version)
    operands = [w.strip() for w in lhs.split("+")]
    if not all(re.match(r"^[A-Z]+$", op) for op in operands):
        raise ValueError("Operands must contain only letters A-Z")

    all_letters = sorted(set("".join(operands) + result))
    leading = set(op[0] for op in operands) | {result[0]}

    if len(all_letters) > 10:
        raise ValueError(
            f"Too many unique letters ({len(all_letters)}). Max is 10 (only digits 0-9 are available)."
        )

    return operands, result, all_letters, leading


def build_variables(all_letters: list[str], leading: set[str]) -> list[Variable]:
    variables = []
    for letter in all_letters:
        domain = list(range(1, 10)) if letter in leading else list(range(0, 10))
        variables.append(Variable(letter=letter, domain=domain, is_leading=(letter in leading)))
    return variables


def check_solution(operands: list[str], result: str, assignment: dict[str, int]) -> bool:
    try:
        nums = [int("".join(str(assignment[c]) for c in op)) for op in operands]
        res = int("".join(str(assignment[c]) for c in result))
        return sum(nums) == res
    except Exception:
        return False


def forward_check(variables: list[Variable], assigned_idx: int, value: int) -> Optional[list[Variable]]:
    """
    Remove `value` from the domains of all other unassigned variables.
    Returns None if any domain becomes empty (dead end).
    """
    new_vars = []
    for i, v in enumerate(variables):
        if i == assigned_idx:
            new_vars.append(Variable(v.letter, [value], v.is_leading))
        else:
            new_domain = [d for d in v.domain if d != value]
            if len(new_domain) == 0:
                return None  # Domain wipe-out → backtrack
            new_vars.append(Variable(v.letter, new_domain, v.is_leading))
    return new_vars


def select_mrv(variables: list[Variable], assigned: set[int]) -> int:
    """MRV: pick the unassigned variable with the smallest domain."""
    best_idx = -1
    best_size = float("inf")
    for i, v in enumerate(variables):
        if i in assigned:
            continue
        if v.domain[0] == v.domain[0] and len(v.domain) < best_size or (
            len(v.domain) == best_size and variables[i].is_leading
        ):
            best_size = len(v.domain)
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


def solve(expression: str, max_solutions: int = 5) -> dict:
    """
    Main entry-point. Returns a dict with solutions, stats, and metadata.
    """
    try:
        operands, result, all_letters, leading = parse_puzzle(expression)
    except ValueError as e:
        return {"success": False, "error": str(e), "solutions": []}

    variables = build_variables(all_letters, leading)
    solutions = []
    stats = {"nodes_explored": 0, "backtracks": 0}
    assignment: dict[str, int] = {}
    assigned_indices: set[int] = set()

    def backtrack(current_vars: list[Variable]) -> bool:
        stats["nodes_explored"] += 1

        if len(assigned_indices) == len(current_vars):
            if check_solution(operands, result, assignment):
                solutions.append(dict(assignment))
                return len(solutions) >= max_solutions
            return False

        var_idx = select_mrv(current_vars, assigned_indices)
        if var_idx == -1:
            return False

        variable = current_vars[var_idx]
        ordered_values = order_lcv(variable, var_idx, current_vars, assigned_indices)

        for value in ordered_values:
            assignment[variable.letter] = value
            assigned_indices.add(var_idx)

            reduced = forward_check(current_vars, var_idx, value)
            if reduced is not None:
                if backtrack(reduced):
                    return True

            del assignment[variable.letter]
            assigned_indices.discard(var_idx)
            stats["backtracks"] += 1

        return False

    backtrack(variables)

    formatted_solutions = []
    for s in solutions:
        # Build substituted strings like "9567 + 1085 = 10652"
        subst_parts = [
            "".join(str(s[c]) for c in op) for op in operands
        ]
        subst_result = "".join(str(s[c]) for c in result)
        subst_str = " + ".join(subst_parts) + " = " + subst_result
        formatted_solutions.append({
            "mapping": s,
            "substituted": subst_str
        })

    return {
        "success": len(solutions) > 0,
        "solutions": formatted_solutions,
        "stats": stats,
        "metadata": {
            "operands": operands,
            "result": result,
            "unique_letters": all_letters,
            "leading_letters": list(leading),
            "algorithm": "Backtracking + Forward Checking + MRV + LCV"
        }
    }
