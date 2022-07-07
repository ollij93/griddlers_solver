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
        # Working with existing
        (".#....#...", [("#", 4), ("#", 3)], ".###..##.."),
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


@pytest.mark.parametrize(
    "contentstr,blockvals,expectedstr",
    [
        # No blocks to surround
        (".", [], "."),
        # Single block to surround
        ("#.", [("#", 1)], "# "),
        (".#", [("#", 1)], " #"),
        (".#.", [("#", 1)], " # "),
        (".#...", [("#", 1)], " # .."),
        (".#...", [("#", 1), ("#", 1)], " # .."),
        ("...#...", [("#", 1), ("#", 1)], ".. # .."),
        # Multiple blocks to surround
        (".#.#.#.", [("#", 1), ("#", 1), ("#", 1)], " # # # "),
        ("#..#.#.", [("#", 1), ("#", 1), ("#", 1)], "#  # # "),
        ("#..#..#", [("#", 1), ("#", 1), ("#", 1)], "#  #  #"),
        # Surrounding bigger blocks
        ("###.", [("#", 3)], "### "),
        (".###", [("#", 3)], " ###"),
        (".###.", [("#", 3)], " ### "),
        (".###...", [("#", 3)], " ### .."),
        (".###...", [("#", 3), ("#", 1)], " ### .."),
        ("...###...", [("#", 3), ("#", 1)], ".. ### .."),
        (".#.###...", [("#", 1), ("#", 3), ("#", 1)], ".# ### .."),
        # Handling multiple values
        ("#..", [("#", 1), ("%", 1)], "#.."),
        ("##...", [("#", 2), ("#", 1), ("%", 1)], "## .."),
        ("##...", [("#", 2), ("%", 1), ("#", 1)], "##..."),
        ("##..#", [("#", 2), ("%", 1), ("#", 1)], "##..#"),
        ("##.#.", [("#", 2), ("#", 1), ("%", 1)], "## #."),
    ],
)
def test_surround_complete(
    contentstr: str, blockvals: list[tuple[str, int]], expectedstr: str
) -> None:
    """Test the fill surround complete function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            grid.Block(grid.Value.from_str(char), count)
            for char, count in blockvals
        ],
    )

    out = solver.surroundcomplete(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,blockvals,expectedstr",
    [
        # No filling to perform
        ("...", [("#", 2)], "..."),
        ("#..", [("#", 2)], "#.."),
        (".#.", [("#", 2)], ".#."),
        ("..#", [("#", 2)], "..#"),
        ("#.#", [("#", 1), ("#", 1)], "#.#"),
        # Simple filling in complete lines
        ("#.#", [("#", 3)], "###"),
        ("#..#", [("#", 4)], "####"),
        # Filling in with space at the edges
        ("..#..#..", [("#", 4)], "..####.."),
        ("..#..#..", [("#", 5)], "..####.."),
        ("..#..#..", [("#", 8)], "..####.."),
        # Filling in with multiple gaps to be filled
        ("..#.#...#.", [("#", 9)], "..#######."),
    ],
)
def test_fill_between_single(
    contentstr: str, blockvals: list[tuple[str, int]], expectedstr: str
) -> None:
    """Test the fill between single function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            grid.Block(grid.Value.from_str(char), count)
            for char, count in blockvals
        ],
    )

    out = solver.fillbetweensingle(seg)
    assert out == expected


@pytest.mark.parametrize(
    "blockvals,size,expectedstrs",
    [
        # Empty is the only solution
        ([], 1, [" "]),
        ([], 3, ["   "]),
        ([], 10, ["          "]),
        # Full is the only solution
        ([("#", 1)], 1, ["#"]),
        ([("%", 1)], 1, ["%"]),
        ([("#", 3)], 3, ["###"]),
        ([("#", 10)], 10, ["##########"]),
        # Multiple blocks but only one solution
        ([("#", 1), ("%", 1)], 2, ["#%"]),
        ([("#", 1), ("#", 1)], 3, ["# #"]),
        # Multiple solutions for single block
        ([("#", 1)], 2, ["# ", " #"]),
        ([("#", 2)], 4, ["##  ", " ## ", "  ##"]),
        # Multiple solutions for multiple blocks
        ([("#", 1), ("#", 1)], 4, ["# # ", "#  #", " # #"]),
        ([("#", 1), ("%", 1)], 3, ["#% ", "# %", " #%"]),
    ]
)
def test_all_possible_solutions(
    blockvals: list[tuple[str, int]], size: int, expectedstrs: list[str]
) -> None:
    """Test the all_possible_solutions generator."""
    blocks = [
        grid.Block(grid.Value.from_str(char), count)
        for char, count in blockvals
    ]
    expected = [
        [grid.Value.from_str(char) for char in linestr]
        for linestr in expectedstrs
    ]
    generator = solver._all_possible_solutions(blocks, size)
    # Ordering doesn't matter
    assert sorted(generator) == sorted(expected)
