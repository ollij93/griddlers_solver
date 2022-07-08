"""
Module containing the griddler solving algorithms.
"""

__all__ = ("Segment",)

import dataclasses
import logging
from dataclasses import dataclass
from typing import Iterator

from .. import grid

_logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """Segment of a line that an algorithm operates on."""

    content: grid.Line
    # Block combinationss that can go in this segment.
    possible: list[list[grid.Block]] = dataclasses.field(default_factory=list)

    def block_fits(self, block: grid.Block, start: int = 0) -> bool:
        """Determine if the block will fit in this segment."""
        return len(self.content) >= start + block.count

    @classmethod
    def from_line(cls, line: grid.Line) -> Iterator[tuple[int, "Segment"]]:
        """Split a grid line into segments."""
        curr: grid.Line = []
        for i, val in enumerate(line):
            if val == grid.VAL_SPACE:
                if curr:
                    yield i - len(curr), cls(curr)
                    curr = []
            else:
                curr.append(val)

        if curr:
            yield len(line) - len(curr), cls(curr)
