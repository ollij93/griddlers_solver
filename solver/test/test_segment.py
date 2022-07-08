"""Tests for the segment module."""

import pytest

from ... import grid
from .. import segment


@pytest.mark.parametrize(
    "seglen,blocklen,fits",
    [
        (1, 1, True),
        (2, 1, True),
        (5, 1, True),
        (1, 2, False),
        (1, 5, False),
    ],
)
def test_block_fits(seglen: int, blocklen: int, fits: bool) -> None:
    """Test the block_fits method of the Segment class."""
    block = grid.Block(grid.Value(2), blocklen)
    # Start position of the segment doesn't matter
    assert (
        segment.Segment([grid.VAL_UNKNOWN] * seglen).block_fits(block) == fits
    )


@pytest.mark.parametrize(
    "seglen,blocklen,start,fits",
    [
        # Single block fitting in several start places
        (1, 1, 0, True),
        (2, 1, 0, True),
        (2, 1, 1, True),
        # Big block not fitting even with offset start
        (2, 5, 1, False),
        # Block that does fit only for some starts
        (3, 2, 0, True),
        (3, 2, 1, True),
        (3, 2, 2, False),
        (3, 2, 3, False),
    ],
)
def test_block_fits_start(
    seglen: int, blocklen: int, start: int, fits: bool
) -> None:
    """Test block_fits with the 'start' optional argument."""
    block = grid.Block(grid.Value(2), blocklen)
    # Start position of the segment doesn't matter
    assert (
        segment.Segment([grid.VAL_UNKNOWN] * seglen).block_fits(block, start)
        == fits
    )


@pytest.mark.parametrize(
    "linetext,expectedstrs",
    [
        # Single blocks
        ("#", [("#", 0)]),
        (".", [(".", 0)]),
        ("##", [("##", 0)]),
        ("..", [("..", 0)]),
        (".. ", [("..", 0)]),
        (" ..", [("..", 1)]),
        # Multiple blocks
        (". .", [(".", 0), (".", 2)]),
        ("# .", [("#", 0), (".", 2)]),
        ("# #", [("#", 0), ("#", 2)]),
        (". #", [(".", 0), ("#", 2)]),
        (".. ..", [("..", 0), ("..", 3)]),
        # Mixed value blocks
        ("#.", [("#.", 0)]),
        (".#", [(".#", 0)]),
        (" .# ", [(".#", 1)]),
        ("#. .#", [("#.", 0), (".#", 3)]),
    ],
)
def test_from_line(linetext: str, expectedstrs: list[tuple[str, int]]) -> None:
    """Test the from_line class method of Segment."""
    line = [grid.Value.from_str(char) for char in linetext]
    expected = [
        (strt, segment.Segment([grid.Value.from_str(char) for char in seg]))
        for seg, strt in expectedstrs
    ]
    assert list(segment.Segment.from_line(line)) == expected
