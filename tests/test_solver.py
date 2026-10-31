"""
Unit tests for CSP cryptarithmetic solver engine.
Covers classic puzzles, multi-addend expressions, unsolvable cases, and performance.
"""
import pytest
from cryptarithmetic_agent.solver import (
    solve,
    check_solution,
    build_variables,
    forward_check,
    select_mrv,
    order_lcv,
    Variable,
)


def test_solve_send_more_money() -> None:
    """Validate classic SEND + MORE = MONEY solution."""
    result = solve("SEND + MORE = MONEY")
    assert result["success"] is True
    assert len(result["solutions"]) == 1

    sol = result["solutions"][0]
    mapping = sol["mapping"]
    assert mapping["S"] == 9
    assert mapping["E"] == 5
    assert mapping["N"] == 6
    assert mapping["D"] == 7
    assert mapping["M"] == 1
    assert mapping["O"] == 0
    assert mapping["R"] == 8
    assert mapping["Y"] == 2
    assert sol["substituted"] == "9567 + 1085 = 10652"


def test_solve_multi_addend_forty_ten_ten() -> None:
    """Validate multi-addend puzzle FORTY + TEN + TEN = SIXTY solves quickly."""
    result = solve("FORTY + TEN + TEN = SIXTY")
    assert result["success"] is True
    assert len(result["solutions"]) >= 1

    sol = result["solutions"][0]
    mapping = sol["mapping"]
    # Check arithmetic: FORTY + TEN + TEN == SIXTY
    forty = (
        mapping["F"] * 10000 + mapping["O"] * 1000 + mapping["R"] * 100 + mapping["T"] * 10 + mapping["Y"]
    )
    ten = mapping["T"] * 100 + mapping["E"] * 10 + mapping["N"]
    sixty = (
        mapping["S"] * 10000 + mapping["I"] * 1000 + mapping["X"] * 100 + mapping["T"] * 10 + mapping["Y"]
    )
    assert forty + ten + ten == sixty
    # Should solve in under 100ms
    assert result["stats"]["solve_time_ms"] < 100.0


def test_solve_base_ball_games() -> None:
    """Validate BASE + BALL = GAMES."""
    result = solve("BASE + BALL = GAMES")
    assert result["success"] is True
    sol = result["solutions"][0]
    assert sol["substituted"] == "7483 + 7455 = 14938"


def test_solve_cross_roads_danger() -> None:
    """Validate CROSS + ROADS = DANGER."""
    result = solve("CROSS + ROADS = DANGER")
    assert result["success"] is True
    sol = result["solutions"][0]
    assert sol["substituted"] == "96233 + 62513 = 158746"


def test_solve_unsolvable_length_mismatch() -> None:
    """Result with length < max operand length cannot be solved."""
    result = solve("SEND + MORE = NO")
    assert result["success"] is False
    assert len(result["solutions"]) == 0


def test_solve_unsolvable_contradiction() -> None:
    """Puzzle with arithmetic contradiction has no solution."""
    # A + A = A with A != 0 (leading) is 2A = A => A = 0 contradiction
    result = solve("A + A = A")
    assert result["success"] is False
    assert len(result["solutions"]) == 0


def test_solve_invalid_syntax_returns_clean_error() -> None:
    """Invalid puzzle string returns success=False without unhandled exception."""
    result = solve("INVALID PUZZLE STRING")
    assert result["success"] is False
    assert "error" in result
    assert result["solutions"] == []


def test_max_solutions_limit() -> None:
    """Verify solver respects max_solutions parameter."""
    result = solve("I + BB = ILL", max_solutions=2)
    assert len(result["solutions"]) <= 2


def test_solver_stats_and_metadata() -> None:
    """Verify stats and metadata dictionaries are populated."""
    result = solve("SEND + MORE = MONEY")
    assert "nodes_explored" in result["stats"]
    assert "backtracks" in result["stats"]
    assert "solve_time_ms" in result["stats"]
    assert result["stats"]["nodes_explored"] > 0
    assert result["metadata"]["operands"] == ["SEND", "MORE"]
    assert result["metadata"]["result"] == "MONEY"


def test_legacy_helper_functions() -> None:
    """Verify backward compatibility of legacy helper functions."""
    vars_list = build_variables(["S", "M", "E"], {"S", "M"})
    assert len(vars_list) == 3
    s_var = next(v for v in vars_list if v.letter == "S")
    e_var = next(v for v in vars_list if v.letter == "E")
    assert 0 not in s_var.domain
    assert 0 in e_var.domain

    # Forward check
    reduced = forward_check(vars_list, 0, 9)
    assert reduced is not None

    # Check solution
    assignment = {"S": 9, "E": 5, "N": 6, "D": 7, "M": 1, "O": 0, "R": 8, "Y": 2}
    assert check_solution(["SEND", "MORE"], "MONEY", assignment) is True
    assert check_solution(["SEND", "MORE"], "MONEY", {"S": 1}) is False
