"""
Unit tests for step-by-step reasoning trace and explanation generator.
Covers hint levels 1, 2, 3, column equation generation, and structural deductions.
"""
from cryptarithmetic_agent.solver import (
    parse_puzzle_details,
    generate_hints,
    generate_reasoning_trace,
    generate_column_constraints,
    generate_structural_deductions,
    solve,
)


def test_column_equation_generation() -> None:
    """Verify column constraint equations accurately reflect place values and carries."""
    parsed = parse_puzzle_details("SEND + MORE = MONEY")
    constraints = generate_column_constraints(parsed)

    # SEND + MORE has 5 columns (Units up to Ten-Thousands)
    assert len(constraints) == 5

    # Column 0 (Units): D + E = Y + 10 * c1
    assert constraints[0].column_name == "Units"
    assert constraints[0].formula == "D + E = Y + 10 * c1"

    # Column 1 (Tens): N + R + c1 = E + 10 * c2
    assert constraints[1].column_name == "Tens"
    assert constraints[1].formula == "N + R + c1 = E + 10 * c2"

    # Column 4 (Ten-Thousands): c4 = M + 10 * c5
    assert constraints[4].column_name == "Ten-Thousands"
    assert "c4 = M" in constraints[4].formula


def test_structural_deductions() -> None:
    """Verify high-level deduction identifies leading non-zero and carry out."""
    parsed = parse_puzzle_details("SEND + MORE = MONEY")
    deductions = generate_structural_deductions(parsed)

    # Should note M and S != 0
    assert any("M" in d and "S" in d and "!= 0" in d for d in deductions)
    # Should deduce M = 1
    assert any("M = 1" in d for d in deductions)


def test_reasoning_trace_steps() -> None:
    """Verify complete 5-step reasoning trace on solvable puzzle."""
    parsed = parse_puzzle_details("SEND + MORE = MONEY")
    solve_res = solve("SEND + MORE = MONEY")
    solutions = [solve_res["solutions"][0]["mapping"]]

    trace = generate_reasoning_trace(parsed, solutions)
    assert len(trace) >= 5

    assert any(step.startswith("Step 1:") for step in trace)
    assert any(step.startswith("Step 2:") for step in trace)
    assert any(step.startswith("Step 3:") for step in trace)
    assert any(step.startswith("Step 4:") for step in trace)
    assert any(step.startswith("Step 5:") for step in trace)
    assert any("9567 + 1085 = 10652" in step for step in trace)


def test_hints_progressive_levels() -> None:
    """Verify hints expand progressively across levels 1, 2, and 3."""
    parsed = parse_puzzle_details("SEND + MORE = MONEY")
    solutions = [{"S": 9, "E": 5, "N": 6, "D": 7, "M": 1, "O": 0, "R": 8, "Y": 2}]

    h1 = generate_hints(parsed, solutions, hint_level=1)
    h2 = generate_hints(parsed, solutions, hint_level=2)
    h3 = generate_hints(parsed, solutions, hint_level=3)

    assert len(h1["hints"]) < len(h2["hints"])
    assert len(h2["hints"]) < len(h3["hints"])

    # Level 1 contains letter count
    assert any("8 unique letters" in h for h in h1["hints"])

    # Level 2 contains column formulas
    assert any("Column 1 (Units):" in h for h in h2["hints"])

    # Level 3 contains key anchor deduction
    assert any("M = 1" in h for h in h3["hints"])
