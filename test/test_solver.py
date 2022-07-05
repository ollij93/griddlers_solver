"""Tests for the solver module."""

import pytest

from .. import solver
from ..grid import Block, Value


@pytest.mark.parametrize(
    "blocks,current,expected",
    [
        ([], ".", " "),
        ([1], "#.", "# "),
        ([1], ".#", " #"),
        ([1], ".#.", " # "),
        ([1], "..#..", "  #  "),
    ],
)
def test_complete_runs(blocks, current, expected):
    """Test the complete runs algorithm."""
    curv = [Value.from_str(x) for x in current]
    expv = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in blocks]
    assert solver.complete_runs(blocks, curv) == expv


@pytest.mark.parametrize(
    "blocks,current,expected",
    [
        ([], ".", " "),
        ([1], ".", "."),
        ([2], ". ..", "  .."),
    ],
)
def test_empty_sections(blocks, current, expected):
    """Test the empty sections algorithm."""
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in blocks]
    assert solver.empty_sections(blocks, cl) == el


@pytest.mark.parametrize(
    "blocks,current,expected",
    [([], ".", "."), ([1], ".", "#"), ([2], "...", ".#."), ([1, 2], ".....", "...#.")],
)
def test_fill_blocks(blocks, current, expected):
    """Test the fill block algorithm."""
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in blocks]
    assert solver.fill_blocks(blocks, cl) == el


@pytest.mark.parametrize(
    "blocks,current,expected",
    [
        ([], ".", "."),
        ([1], "#.", "# "),
        ([1], ".#", " #"),
        ([1], ".#.", " # "),
        ([1], "..#..", ". # ."),
    ],
)
def test_complete_blocks(blocks, current: str, expected: str):
    """Test the complete blocks algorithm."""
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    blocks = [Block(Value(2), b) for b in blocks]
    assert solver.complete_blocks(blocks, cl) == el
