"""Tests for the solver module."""
# pylint: disable=protected-access

import pytest

from ... import grid
from .. import segment, solver


@pytest.mark.parametrize(
    "inblocks,expected",
    [
        # Empty row
        ([], 0),
        # Single blocks
        ([("#", 1)], 0),
        ([("%", 1)], 0),
        # Single value rows
        ([("#", 1), ("#", 1)], 1),
        ([("#", 5), ("#", 7)], 1),
        ([("#", 1), ("#", 5), ("#", 7)], 2),
        # Multi value rows
        ([("%", 1), ("#", 1)], 0),
        ([("#", 1), ("%", 1), ("#", 1)], 0),
        ([("%", 1), ("%", 1), ("#", 1)], 1),
        ([("#", 1), ("%", 1), ("%", 1)], 1),
    ],
)
def test_min_spaces(inblocks: list[tuple[str, int]], expected: int) -> None:
    """Test the min_spaces function."""
    blocks = [
        grid.Block(grid.Value.from_str(char), count)
        for char, count in inblocks
    ]
    assert solver._min_spaces(blocks) == expected


@pytest.mark.parametrize(
    "contentstr,blockvals,expectedstr",
    [
        # Filling empty segments
        (".", [], " "),
        ("..", [], "  "),
        ("......", [], "      "),
        # Not filling incomplete empty segments
        ("..", [("#", 1)], ".."),
        ("..", [("#", 2)], ".."),
        # Filling non-empty segments
        (".#.", [("#", 1)], " # "),
        (
            "..%#%.%%%%..#",
            [("%", 1), ("#", 1), ("%", 1), ("%", 4), ("#", 1)],
            "  %#% %%%%  #",
        ),
    ],
)
def test_complete_seg(
    contentstr: str, blockvals: list[tuple[str, int]], expectedstr: str
) -> None:
    """Test the complete segs function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            grid.Block(grid.Value.from_str(char), count)
            for char, count in blockvals
        ],
    )

    out = solver.completeseg(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,blockvals,expectedstr",
    [
        # Filling complete segments
        (".", [("#", 1)], "#"),
        ("..", [("#", 2)], "##"),
        (".....", [("#", 5)], "#####"),
        # Not filling at all
        (".", [], "."),
        ("..", [("#", 1)], ".."),
        (".....", [("#", 1)], "....."),
        (".....", [("#", 2)], "....."),
        # Partially filling single
        ("...", [("#", 2)], ".#."),
        ("....", [("#", 3)], ".##."),
        (".....", [("#", 3)], "..#.."),
        (".....", [("#", 4)], ".###."),
        # Filling multiple
        ("...", [("#", 1), ("#", 1)], "#.#"),
        ("..", [("#", 1), ("%", 1)], "#%"),
        (".....", [("#", 3), ("#", 1)], "###.#"),
        ("....", [("#", 3), ("%", 1)], "###%"),
        # Partially filling multiple
        ("..........", [("#", 6), ("#", 2)], ".#####..#."),
        ("..........", [("#", 6), ("%", 3)], ".#####.%%."),
    ],
)
def test_fill_seg(
    contentstr: str, blockvals: list[tuple[str, int]], expectedstr: str
) -> None:
    """Test the fill segs function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        certain=[
            grid.Block(grid.Value.from_str(char), count)
            for char, count in blockvals
        ],
    )

    out = solver.fillseg(seg)
    assert out == expected