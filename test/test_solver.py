"""Tests for the solver module."""

import pytest

from .. import solver
from ..grid import Block, Value


@pytest.mark.parametrize(
    "block_values,current,expected",
    [
        ([], ".", " "),
        ([1], "#.", "# "),
        ([1], ".#", " #"),
        ([1], ".#.", " # "),
        ([1], "..#..", "  #  "),
    ],
)
def test_complete_runs(block_values: list[int], current: str, expected: str) -> None:
    """Test the complete runs algorithm."""
    curv = [Value.from_str(x) for x in current]
    expv = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in block_values]
    assert solver.complete_runs(blocks, curv) == expv


@pytest.mark.parametrize(
    "block_values,current,expected",
    [
        ([], ".", " "),
        ([1], ".", "."),
        ([2], ". ..", "  .."),
    ],
)
def test_empty_sections(block_values: list[int], current: str, expected: str) -> None:
    """Test the empty sections algorithm."""
    curv = [Value.from_str(x) for x in current]
    expv = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in block_values]
    assert solver.empty_sections(blocks, curv) == expv


@pytest.mark.parametrize(
    "block_values,current,expected",
    [([], ".", "."), ([1], ".", "#"), ([2], "...", ".#."), ([1, 2], ".....", "...#.")],
)
def test_fill_blocks(block_values: list[int], current: str, expected: str) -> None:
    """Test the fill block algorithm."""
    curv = [Value.from_str(x) for x in current]
    expv = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in block_values]
    assert solver.fill_blocks(blocks, curv) == expv


@pytest.mark.parametrize(
    "block_values,current,expected",
    [
        ([], ".", "."),
        ([1], "#.", "# "),
        ([1], ".#", " #"),
        ([1], ".#.", " # "),
        ([1], "..#..", ". # ."),
    ],
)
def test_complete_blocks(block_values: list[int], current: str, expected: str) -> None:
    """Test the complete blocks algorithm."""
    curv = [Value.from_str(x) for x in current]
    expv = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in block_values]
    assert solver.complete_blocks(blocks, curv) == expv
