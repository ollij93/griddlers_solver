"""
Module containing the griddler solving algorithms.
"""

__all__ = ("Segment",)

import logging
from dataclasses import dataclass
from typing import Iterator

from .. import grid

_logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """Segment of a line that an algorithm operates on."""

    content: grid.Line
    start: int
    # Blocks that must go in this segment and can go nowhere else.
    certain: list[grid.Block]
    # Blocks that can go in this segment, but also other segments.
    possible: list[grid.Block]

    def block_fits(self, block: grid.Block, start: int = 0) -> bool:
        """Determine if the block will fit in this segment."""
        return len(self.content) >= start + block.count

    @classmethod
    def from_line(cls, line: grid.Line) -> Iterator["Segment"]:
        """Split a grid line into segments."""
        curr: grid.Line = []
        for i, val in enumerate(line):
            if val == grid.VAL_SPACE:
                if curr:
                    yield cls(curr, i - len(curr), [], [])
                    curr = []
            else:
                curr.append(val)

        if curr:
            yield cls(curr, len(line) - len(curr), [], [])
