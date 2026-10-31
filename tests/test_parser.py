"""
Unit tests for the cryptarithmetic puzzle parser.
Covers 2-addend, multi-addend, whitespace, casing, invalid syntax, and variable count limits.
"""
import pytest

from cryptarithmetic_agent.solver import (
    parse_puzzle,
    parse_puzzle_details,
    PuzzleSyntaxError,
    TooManyVariablesError,
)


def test_parse_valid_two_addend() -> None:
    """Test standard 2-addend expression parsing."""
    operands, result, all_letters, leading = parse_puzzle("SEND + MORE = MONEY")
    assert operands == ["SEND", "MORE"]
    assert result == "MONEY"
    assert set(all_letters) == {"S", "E", "N", "D", "M", "O", "R", "Y"}
    assert leading == {"S", "M"}


def test_parse_valid_multi_addend() -> None:
    """Test parsing multi-addend puzzle expressions (3+ addends)."""
    operands, result, all_letters, leading = parse_puzzle("FORTY + TEN + TEN = SIXTY")
    assert operands == ["FORTY", "TEN", "TEN"]
    assert result == "SIXTY"
    assert "F" in leading
    assert "T" in leading
    assert "S" in leading
    assert len(all_letters) <= 10


def test_parse_four_addends() -> None:
    """Test parsing puzzle with 4 addends."""
    operands, result, all_letters, leading = parse_puzzle("SO + MANY + MORE + MEN = SEEM")
    assert len(operands) == 4
    assert result == "SEEM"
    assert operands == ["SO", "MANY", "MORE", "MEN"]


def test_parse_case_insensitivity() -> None:
    """Ensure parser converts lowercase to uppercase correctly."""
    operands, result, all_letters, leading = parse_puzzle("send + more = money")
    assert operands == ["SEND", "MORE"]
    assert result == "MONEY"


def test_parse_whitespace_robustness() -> None:
    """Ensure parser handles leading, trailing, and inter-token whitespace."""
    operands, result, all_letters, leading = parse_puzzle("   SEND   +    MORE    =   MONEY   ")
    assert operands == ["SEND", "MORE"]
    assert result == "MONEY"


def test_parse_missing_equals_raises_error() -> None:
    """Missing '=' sign should raise PuzzleSyntaxError."""
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND + MORE MONEY")


def test_parse_missing_addends_raises_error() -> None:
    """Missing operand (e.g. SEND = MONEY) should raise PuzzleSyntaxError."""
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND = MONEY")


def test_parse_empty_operand_raises_error() -> None:
    """Empty operand between '+' or trailing '+' should raise PuzzleSyntaxError."""
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND + + MORE = MONEY")
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND + MORE + = MONEY")
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("+ SEND + MORE = MONEY")


def test_parse_non_alpha_characters_raises_error() -> None:
    """Numbers and punctuation in words should raise PuzzleSyntaxError."""
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND1 + MORE = MONEY")
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("SEND + MORE! = MONEY")


def test_parse_too_many_unique_letters_raises_error() -> None:
    """More than 10 unique letters cannot map to digits 0-9 and should raise TooManyVariablesError."""
    # 11 unique letters: A, B, C, D, E, F, G, H, I, J, K
    with pytest.raises(TooManyVariablesError):
        parse_puzzle("ABCDEFGHI + JK = RESULT")


def test_parse_empty_string_raises_error() -> None:
    """Empty or non-string input should raise PuzzleSyntaxError."""
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("")
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle("   ")
    with pytest.raises(PuzzleSyntaxError):
        parse_puzzle_details(None)  # type: ignore
