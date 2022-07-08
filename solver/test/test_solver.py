"""Tests for the solver module."""
# pylint: disable=protected-access

from unittest import mock

import pytest

from ... import grid
from .. import segment, solver


# Patching the algorithms object to not leave test stuff globally registered
@mock.patch.object(solver, "ALGORITHMS", {})
def test_algorithm() -> None:
    """Test the algorithm decorator."""

    @solver.algorithm("TEST")
    def test_algo(_: list[grid.Block], line: grid.Line) -> grid.Line:
        return line

    # Check the above method has been correctly registered
    assert solver.ALGORITHMS["TEST"] is test_algo
    assert solver.ALGORITHMS["TEST"](
        [], [grid.Value(i) for i in [0, 1, 2]]
    ) == [grid.Value(i) for i in [0, 1, 2]]
    assert "TEST - reversed" not in solver.ALGORITHMS


# Patching the algorithms object to not leave test stuff globally registered
@mock.patch.object(solver, "ALGORITHMS", {})
def test_algorithm_symmetric() -> None:
    """Test the algorithm decorator with the symmetic argument."""

    @solver.algorithm("TEST", symmetric=True)
    def test_algo(_: list[grid.Block], line: grid.Line) -> grid.Line:
        return [grid.Value(3)] + line[1:]

    # Check the symmetric version and the regular version of the above algorithm
    # have been covered
    assert solver.ALGORITHMS["TEST"](
        [], [grid.Value(i) for i in [0, 1, 2]]
    ) == [grid.Value(i) for i in [3, 1, 2]]
    assert solver.ALGORITHMS["TEST - reversed"](
        [], [grid.Value(i) for i in [0, 1, 2]]
    ) == [grid.Value(i) for i in [0, 1, 3]]


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
    ],
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


@pytest.mark.parametrize(
    "blockvals,linestr,expectedparts",
    [
        # Empty line - no blocks
        ([], ".", [(0, ".", [[]])]),
        ([], "...", [(0, "...", [[]])]),
        # Empty line - with blocks
        ([("#", 1)], "...", [(0, "...", [[("#", 1)]])]),
        # Line with spaces - no blocks
        ([], "   ", []),
        ([], " . ", [(1, ".", [[]])]),
        ([], ". .", [(0, ".", [[]]), (2, ".", [[]])]),
        ([], "... . ..", [(0, "...", [[]]), (4, ".", [[]]), (6, "..", [[]])]),
        # Line with spaces - with blocks
        (
            [("#", 1)],
            ". .",
            [(0, ".", [[("#", 1)], []]), (2, ".", [[], [("#", 1)]])],
        ),
        (
            [("#", 2)],
            ".. ..",
            [(0, "..", [[("#", 2)], []]), (3, "..", [[], [("#", 2)]])],
        ),
        ([("#", 2)], ".. .", [(0, "..", [[("#", 2)]]), (3, ".", [[]])]),
        # Line with spaces and values - @@@ These don't currently work
        ([("#", 2)], "#. ..", [(0, "#.", [[("#", 2)]]), (3, "..", [[]])]),
        ([("#", 2)], ".. #.", [(0, "..", [[]]), (3, "#.", [[("#", 2)]])]),
    ],
)
def test_split_line(
    blockvals: list[tuple[str, int]],
    linestr: str,
    expectedparts: list[tuple[int, str, list[list[tuple[str, int]]]]],
) -> None:
    """Test the split lines function."""
    blocks = [
        grid.Block(grid.Value.from_str(char), count)
        for char, count in blockvals
    ]
    line = [grid.Value.from_str(char) for char in linestr]
    expected = [
        (
            strt,
            segment.Segment(
                [grid.Value.from_str(char) for char in content],
                [
                    [
                        grid.Block(grid.Value.from_str(char), count)
                        for char, count in possible
                    ]
                    for possible in possibles
                ],
            ),
        )
        for strt, content, possibles in expectedparts
    ]
    assert solver._split_line(blocks, line) == expected


# Patching the algorithms object to not leave test stuff globally registered
@mock.patch.object(solver, "ALGORITHMS", {})
def test_segment_algorithm() -> None:
    """Test the segment algorithm decorator."""

    @solver.segmentalgorithm("TEST")
    def test_algo(seg: segment.Segment) -> grid.Line:
        return [grid.Value(3)] + seg.content[1:]

    assert solver.ALGORITHMS["TEST"](
        [], [grid.Value(i) for i in [0, 0, 1, 0, 1, 0, 1, 0, 0]]
    ) == [grid.Value(i) for i in [3, 0, 1, 3, 1, 3, 1, 3, 0]]


@pytest.mark.parametrize(
    "contentstr,possibles,expectedstr",
    [
        # Filling empty segments
        (".", [[]], " "),
        ("..", [[]], "  "),
        ("......", [[]], "      "),
        # Not filling incomplete empty segments
        ("..", [[("#", 1)]], ".."),
        ("..", [[("#", 2)]], ".."),
        # Not filling uncertain segments
        ("..", [[("#", 2)], []], ".."),
        # Filling non-empty segments
        (".#.", [[("#", 1)]], " # "),
        (
            "..%#%.%%%%..#",
            [[("%", 1), ("#", 1), ("%", 1), ("%", 4), ("#", 1)]],
            "  %#% %%%%  #",
        ),
    ],
)
def test_complete_seg(
    contentstr: str, possibles: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the complete segs function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possibles
        ],
    )

    out = solver.completeseg(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,possibles,expectedstr",
    [
        # Filling complete segments
        (".", [[("#", 1)]], "#"),
        ("..", [[("#", 2)]], "##"),
        (".....", [[("#", 5)]], "#####"),
        # Not filling at all
        (".", [[]], "."),
        ("..", [[("#", 1)]], ".."),
        (".....", [[("#", 1)]], "....."),
        (".....", [[("#", 2)]], "....."),
        # Not filling when uncertain
        ("...", [[("#", 3)], []], "..."),
        # Partially filling single
        ("...", [[("#", 2)]], ".#."),
        ("....", [[("#", 3)]], ".##."),
        (".....", [[("#", 3)]], "..#.."),
        (".....", [[("#", 4)]], ".###."),
        # Filling multiple
        ("...", [[("#", 1), ("#", 1)]], "#.#"),
        ("..", [[("#", 1), ("%", 1)]], "#%"),
        (".....", [[("#", 3), ("#", 1)]], "###.#"),
        ("....", [[("#", 3), ("%", 1)]], "###%"),
        # Partially filling multiple
        ("..........", [[("#", 6), ("#", 2)]], ".#####..#."),
        ("..........", [[("#", 6), ("%", 3)]], ".#####.%%."),
        # Working with existing
        (".#....#...", [[("#", 4), ("#", 3)]], ".###..##.."),
    ],
)
def test_fill_seg(
    contentstr: str, possibles: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the fill segs function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possibles
        ],
    )

    out = solver.fillseg(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,possible,expectedstr",
    [
        # No blocks to surround
        (".", [[]], "."),
        # Single block to surround
        ("#.", [[("#", 1)]], "# "),
        (".#", [[("#", 1)]], " #"),
        (".#.", [[("#", 1)]], " # "),
        (".#...", [[("#", 1)]], " # .."),
        (".#...", [[("#", 1), ("#", 1)]], " # .."),
        ("...#...", [[("#", 1), ("#", 1)]], ".. # .."),
        # Multiple blocks to surround
        (".#.#.#.", [[("#", 1), ("#", 1), ("#", 1)]], " # # # "),
        ("#..#.#.", [[("#", 1), ("#", 1), ("#", 1)]], "#  # # "),
        ("#..#..#", [[("#", 1), ("#", 1), ("#", 1)]], "#  #  #"),
        # Surrounding bigger blocks
        ("###.", [[("#", 3)]], "### "),
        (".###", [[("#", 3)]], " ###"),
        (".###.", [[("#", 3)]], " ### "),
        (".###...", [[("#", 3)]], " ### .."),
        (".###...", [[("#", 3), ("#", 1)]], " ### .."),
        ("...###...", [[("#", 3), ("#", 1)]], ".. ### .."),
        (".#.###...", [[("#", 1), ("#", 3), ("#", 1)]], ".# ### .."),
        # Handling multiple values
        ("#..", [[("#", 1), ("%", 1)]], "#.."),
        ("##...", [[("#", 2), ("#", 1), ("%", 1)]], "## .."),
        ("##...", [[("#", 2), ("%", 1), ("#", 1)]], "##..."),
        ("##..#", [[("#", 2), ("%", 1), ("#", 1)]], "##..#"),
        ("##.#.", [[("#", 2), ("#", 1), ("%", 1)]], "## #."),
        # Not filing when uncertain
        (".#.", [[], [("#", 1)]], ".#."),
    ],
)
def test_surround_complete(
    contentstr: str, possible: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the fill surround complete function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possible
        ],
    )

    out = solver.surroundcomplete(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,possible,expectedstr",
    [
        # No filling to perform
        ("...", [[("#", 2)]], "..."),
        ("#..", [[("#", 2)]], "#.."),
        (".#.", [[("#", 2)]], ".#."),
        ("..#", [[("#", 2)]], "..#"),
        ("#.#", [[("#", 1), ("#", 1)]], "#.#"),
        (".#.", [[], [("#", 1)]], ".#."),
        # Simple filling in complete lines
        ("#.#", [[("#", 3)]], "###"),
        ("#..#", [[("#", 4)]], "####"),
        # Filling in with space at the edges
        ("..#..#..", [[("#", 4)]], "..####.."),
        ("..#..#..", [[("#", 5)]], "..####.."),
        ("..#..#..", [[("#", 8)]], "..####.."),
        # Filling in with multiple gaps to be filled
        ("..#.#...#.", [[("#", 9)]], "..#######."),
    ],
)
def test_fill_between_single(
    contentstr: str, possible: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the fill between single function."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possible
        ],
    )

    out = solver.fillbetweensingle(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,possible,expectedstr",
    [
        # No blocks to stretch
        ("...", [[]], "..."),
        # Not certain which block is first
        ("#...", [[("#", 2)], []], "#..."),
        ("#...", [[("#", 2)], [("#", 3)]], "#..."),
        ("#...", [[("#", 2), ("#", 3)], [("#", 3)]], "#..."),
        ("#...", [[("#", 2)], [("%", 2)]], "#..."),
        # Not stretchable
        (".#..", [[("#", 2)]], ".#.."),
        ("..#..", [[("#", 2)]], "..#.."),
        ("..#.", [[("#", 3)]], "..#."),
        # Single possibility to be stretched
        ("#...", [[("#", 2)]], "##.."),
        ("#...", [[("#", 3)]], "###."),
        (".#..", [[("#", 3)]], ".##."),
        # Multiple possibilities but known value to stretch
        (
            "#...",
            [[("#", 2)], [("#", 2), ("#", 1)], [("#", 2), ("%", 2)]],
            "##..",
        ),
    ],
)
def test_stretch_first(
    contentstr: str, possible: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the stretch first algorithm."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possible
        ],
    )

    out = solver.stretchfirst(seg)
    assert out == expected


@pytest.mark.parametrize(
    "contentstr,possible,expectedstr",
    [
        # No blocks to pad
        ("...", [[]], "..."),
        # Not certain which block is partially filled or first
        ("..#..", [[("#", 2)], [("#", 3)]], "..#.."),
        ("..#..", [[("#", 2)], [("%", 1), ("#", 2)]], "..#.."),
        ("..#..", [[("#", 1), ("#", 1)]], "..#.."),
        # Nothing to pad
        ("#..", [[("#", 3)]], "#.."),
        (".#.", [[("#", 3)]], ".#."),
        ("..#", [[("#", 3)]], "..#"),
        # Single possibility to be padded
        ("..#..", [[("#", 2)]], " .#.."),
        ("..##.", [[("#", 2)]], "  ##."),
        # Multiple possibilities but known value to padded
        (
            "..#..",
            [[("#", 2)], [("#", 2), ("#", 1)], [("#", 2), ("%", 2)]],
            " .#..",
        ),
    ],
)
def test_inverse_stretch_first(
    contentstr: str, possible: list[list[tuple[str, int]]], expectedstr: str
) -> None:
    """Test the inverse stretch first algorithm."""
    content = [grid.Value.from_str(char) for char in contentstr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    seg = segment.Segment(
        content,
        possible=[
            [
                grid.Block(grid.Value.from_str(char), count)
                for char, count in blockvals
            ]
            for blockvals in possible
        ],
    )

    out = solver.inversestretchfirst(seg)
    assert out == expected


@pytest.mark.parametrize(
    "blockvals,instr,expectedstr",
    [
        # Empty lines
        ([], ".", " "),
        ([], "..", "  "),
        ([], "...", "   "),
        # Full lines
        ([("#", 1)], ".", "#"),
        ([("#", 2)], "..", "##"),
        ([("#", 3)], "...", "###"),
        # Unreachable areas
        ([("#", 2)], ". ....", "  ...."),
        ([("#", 2)], ".. . ....", "..   ...."),
        # Partial fills
        ([("#", 3)], ".....", "..#.."),
        ([("#", 4)], ".....", ".###."),
        ([("#", 4)], ". .....", "  .###."),
        # Multiple value fills
        ([("#", 2), ("%", 2)], "....", "##%%"),
        ([("#", 2), ("%", 2)], ".....", ".#.%."),
    ],
)
def test_single_possible_value(
    blockvals: list[tuple[str, int]], instr: str, expectedstr: str
) -> None:
    """Test the single possible values brute force algorithm."""
    blocks = [
        grid.Block(grid.Value.from_str(char), count)
        for char, count in blockvals
    ]
    inline = [grid.Value.from_str(char) for char in instr]
    expected = [grid.Value.from_str(char) for char in expectedstr]
    outline = solver.singlepossiblevalue(blocks, inline)
    assert outline == expected
