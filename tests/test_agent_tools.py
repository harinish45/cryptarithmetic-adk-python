"""
Unit tests for ADK agent tools and schema interfaces.
Covers solve_puzzle, validate_puzzle, explain_solution, and generate_puzzle.
"""
from cryptarithmetic_agent.agent import (
    solve_puzzle,
    validate_puzzle,
    explain_solution,
    explain_puzzle,
    generate_puzzle,
    root_agent,
    ALL_TOOLS,
)


def test_tool_solve_puzzle() -> None:
    """Test solve_puzzle tool returns structured output."""
    res = solve_puzzle("SEND + MORE = MONEY")
    assert res["success"] is True
    assert len(res["solutions"]) == 1
    assert "reasoning_trace" in res
    assert "stats" in res


def test_tool_validate_puzzle_valid() -> None:
    """Test validate_puzzle tool on valid solvable puzzle."""
    res = validate_puzzle("SEND + MORE = MONEY")
    assert res["valid"] is True
    assert res["solvable"] is True
    assert res["unique_letters"] == 8
    assert res["operands"] == ["SEND", "MORE"]
    assert res["result"] == "MONEY"
    assert res["error"] is None


def test_tool_validate_puzzle_invalid_syntax() -> None:
    """Test validate_puzzle tool on malformed syntax."""
    res = validate_puzzle("NOT A VALID PUZZLE")
    assert res["valid"] is False
    assert res["solvable"] is False
    assert res["error"] is not None


def test_tool_explain_solution() -> None:
    """Test explain_solution tool at different hint levels."""
    res = explain_solution("SEND + MORE = MONEY", hint_level=2)
    assert res["success"] is True
    assert res["level"] == 2
    assert len(res["hints"]) > 0
    assert len(res["column_equations"]) > 0
    assert res["error"] is None

    # Test alias
    res_alias = explain_puzzle("SEND + MORE = MONEY", hint_level=1)
    assert res_alias["success"] is True


def test_tool_generate_puzzle() -> None:
    """Test procedural puzzle generator at all difficulty levels."""
    for diff in ["easy", "medium", "hard"]:
        puzzle_data = generate_puzzle(difficulty=diff)
        assert puzzle_data["solvable"] is True
        assert len(puzzle_data["words"]) >= 2
        assert puzzle_data["result_word"] is not None
        assert puzzle_data["difficulty"] == diff


def test_root_agent_configuration() -> None:
    """Verify ADK root_agent has correct name, model, and tool bindings."""
    assert root_agent.name == "cryptarithmetic_agent"
    assert root_agent.model == "gemini-2.5-flash"
    assert len(ALL_TOOLS) == 4
    tool_names = [getattr(t, "name", None) or getattr(t.func, "__name__", "") for t in ALL_TOOLS]
    assert "solve_puzzle" in tool_names
    assert "validate_puzzle" in tool_names
    assert "explain_solution" in tool_names
    assert "generate_puzzle" in tool_names
