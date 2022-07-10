"""Tests for the grid module."""

from unittest import mock

import pytest
import termcolor

from .. import grid


def test_value_sorting() -> None:
    """Test the Value classes comparison methods."""
    assert grid.Value(1) < grid.Value(2)
    assert grid.Value(200) > grid.Value(-100)
    assert sorted([grid.Value(1), grid.Value(0)]) == [
        grid.Value(0),
        grid.Value(1),
    ]


@pytest.mark.parametrize(
    "val,expectedstr",
    [
        (0, "."),
        (1, " "),
        (2, "#"),
        (3, termcolor.colored("#", "red")),
        (4, termcolor.colored("#", "yellow")),
        (5, termcolor.colored("#", "green")),
        (6, termcolor.colored("#", "blue")),
        (7, termcolor.colored("#", "magenta")),
        (8, termcolor.colored("#", "cyan")),
        (9, termcolor.colored("#", "grey")),
    ],
)
def test_value_render(val: int, expectedstr: str) -> None:
    """Test the Value classes render method."""
    assert grid.Value(val).render() == expectedstr


def test_value_render_error() -> None:
    """Test the error raised from Value's render method."""
    with pytest.raises(ValueError):
        grid.Value(100).render()


def test_from_str() -> None:
    """Test the from_str method."""
    assert grid.Value.from_str(".") == grid.VAL_UNKNOWN
    assert grid.Value.from_str(" ") == grid.VAL_SPACE
    assert grid.Value.from_str("#") == grid.Value(2)
    assert grid.Value.from_str("%") == grid.Value(3)
    assert grid.Value.from_str("X") == grid.VAL_UNKNOWN


@pytest.mark.parametrize(
    "val,count,expected",
    [
        (2, 9, " 9"),
        (2, 10, "10"),
        (3, 10, termcolor.colored("10", "red")),
    ],
)
def test_block_prefix(val: int, count: int, expected: str) -> None:
    """Test the block prefix formatting method."""
    assert grid.Block(grid.Value(val), count).prefix() == expected


@pytest.mark.parametrize(
    "linestr,blks",
    [
        # Empty lines, no blocks
        (".", []),
        ("...", []),
        (" ", []),
        (".. ..", []),
        # Single blocks
        ("#", [(0, "#", 1)]),
        ("###", [(0, "#", 3)]),
        ("..###..", [(2, "#", 3)]),
        ("  ###  ", [(2, "#", 3)]),
        ("  %%%  ", [(2, "%", 3)]),
        # Multiple blocks
        ("#.#", [(0, "#", 1), (2, "#", 1)]),
        (".##.###", [(1, "#", 2), (4, "#", 3)]),
        (".%%.###", [(1, "%", 2), (4, "#", 3)]),
    ],
)
def test_count_blocks(linestr: str, blks: list[tuple[int, str, int]]) -> None:
    """Test the count blocks function."""
    line = [grid.Value.from_str(char) for char in linestr]
    expected_blks = [
        (i, grid.Block(grid.Value.from_str(val), count))
        for i, val, count in blks
    ]

    assert grid.count_blocks(line) == expected_blks


def test_grid_init() -> None:
    """Test the init for the Grid class."""
    assert grid.Grid([], []).volume == []
    assert grid.Grid([[]], [[]]).volume == [grid.VAL_UNKNOWN]
    assert grid.Grid([[], []], [[]]).volume == [grid.VAL_UNKNOWN] * 2
    assert grid.Grid([[]], [[], []]).volume == [grid.VAL_UNKNOWN] * 2
    assert grid.Grid([[], []], [[], []]).volume == [grid.VAL_UNKNOWN] * 4
    assert (
        grid.Grid([[], [], []], [[], [], []]).volume == [grid.VAL_UNKNOWN] * 9
    )


def test_grid_properties() -> None:
    """Test the property accessors of the Grid class."""
    grd = grid.Grid([], [])
    assert grd.width == 0
    assert grd.height == 0
    assert grd.columns == []
    assert grd.rows == []

    grd = grid.Grid([[], []], [[], [], []])
    grd.volume = [grid.Value(x) for x in range(1, 7)]
    assert grd.width == 3
    assert grd.height == 2
    assert grd.columns == [
        [grid.Value(x) for x in i] for i in [[1, 4], [2, 5], [3, 6]]
    ]


def test_grid_getset() -> None:
    """Test the get and set methods of the Grid class."""
    grd = grid.Grid([[], []], [[], [], []])
    grd.volume = [grid.Value(x) for x in range(1, 7)]
    assert grd.get(0, 0) == grid.Value(1)
    assert grd.get(1, 0) == grid.Value(2)
    assert grd.get(2, 1) == grid.Value(6)

    grd.set(0, 0, grid.Value(9))
    assert grd.get(0, 0) == grid.Value(9)


def test_grid_render() -> None:
    """Test the grid render method."""
    grd = grid.Grid(
        [
            [grid.Block(grid.Value(2), 1), grid.Block(grid.Value(2), 1)],
            [grid.Block(grid.Value(2), 2)],
            [grid.Block(grid.Value(2), 1)],
        ],
        [
            [grid.Block(grid.Value(2), 2)],
            [grid.Block(grid.Value(2), 1)],
            [grid.Block(grid.Value(2), 1), grid.Block(grid.Value(2), 1)],
        ],
    )
    assert grd.render() == [
        " .  .  .| 1, 1",
        " .  .  .| 2",
        " .  .  .| 1",
        "---------",
        " 2  1  1|",
        "       1|",
    ]

    grd.volume = [
        grid.Value(2),
        grid.VAL_SPACE,
        grid.Value(2),
        grid.Value(2),
        grid.Value(2),
        grid.VAL_SPACE,
        grid.VAL_SPACE,
        grid.VAL_SPACE,
        grid.Value(2),
    ]
    assert grd.render() == [
        " #     #| 1, 1",
        " #  #   | 2",
        "       #| 1",
        "---------",
        " 2  1  1|",
        "       1|",
    ]


def test_grid_check_solved() -> None:
    """Test the check_solved method of the Grid class."""
    assert grid.Grid([], []).check_solved()
    assert not grid.Grid([[]], [[]]).check_solved()

    grd = grid.Grid([[], []], [[], []])
    grd.volume = [grid.VAL_SPACE] * 4
    assert grd.check_solved()

    grd.set(0, 0, grid.Value(2))
    assert grd.check_solved()


def test_apply_algorithm() -> None:
    """Test the apply algorithm method of the Grid class."""
    # Dummy block to check it's passed through where expected
    mock_block = mock.Mock()

    # Construct the grid and fill in a couple of values
    grd = grid.Grid([[mock_block], [], []], [[], []])
    grd.volume = [grid.VAL_UNKNOWN] * 4 + [grid.VAL_SPACE] * 2

    # Weird algorithm that fills in spaces that mean we get all the
    # appropriate skipping tested.
    stub_algo = mock.Mock(
        side_effect=[
            # Fill in the top left when called for the first row
            [grid.VAL_SPACE, grid.VAL_UNKNOWN],
            # Fill in the full second row
            [grid.VAL_SPACE] * 2,
            # Bottom row is already full, so should be skipped
            # First column should be skipped since it's full from the above
            # Fill in the full second colomn
            [grid.VAL_SPACE] * 3,
        ]
    )
    # Apply the algorithm and check the content has been applied as expected
    grd.apply_algorithm("STUB", stub_algo)
    assert grd.volume == [grid.VAL_SPACE] * 6

    # Check the algorithm was invoked as expected
    stub_algo.assert_has_calls(
        [
            # First row
            mock.call([mock_block], [grid.VAL_UNKNOWN] * 2),
            # Second row
            mock.call([], [grid.VAL_UNKNOWN] * 2),
            # Second column
            mock.call([], [grid.VAL_UNKNOWN, grid.VAL_SPACE, grid.VAL_SPACE]),
        ]
    )
    assert stub_algo.call_count == 3
