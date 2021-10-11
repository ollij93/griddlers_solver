"""
Module containing the griddler solving algorithms.
"""

from dataclasses import dataclass
import logging
import typing

from .grid import (
    VAL_SPACE,
    VAL_UNKNOWN,
    Algorithm,
    Block,
    Line,
    Value,
    count_blocks,
)

_logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """Segment of a line that an algorithm operates on."""

    content: Line
    start: int
    # Blocks that must go in this segment and can go nowhere else.
    certain: list[Block]
    # Blocks that can go in this segment, but also other segments.
    possible: list[Block]


def _block_fits(segment: Segment, block: Block, start: int = 0) -> bool:
    """
    Determine if the block will fit in the given segment.
    Can limit the earliest start index.
    """
    if len(segment.content) < start + block.count:
        return False
    return True


def _minspaces(blocks: list[Block]) -> int:
    """
    Calculate the minimum number of spaces that must exist between the
    given blocks.
    """
    ret = 0
    for bi in range(1, len(blocks)):
        if blocks[bi].value == blocks[bi - 1].value:
            ret += 1
    return ret


def _split_segments(line: Line) -> list[Segment]:
    """
    Split a line into segments without filling in the blocks
    for each segment.
    """
    ret: list[Segment] = []
    curr: Line = []
    for i, val in enumerate(line):
        if val == VAL_SPACE:
            if curr:
                ret.append(Segment(curr, i - len(curr), [], []))
                curr = []
        else:
            curr.append(val)
    if curr:
        ret.append(Segment(curr, len(line) - len(curr), [], []))
    return ret


def _poss_start(blocks: list[Block], segments: list[Segment]) -> list[int]:
    """Get the index of the first possible segments each block can live in."""
    ret = []
    si = 0
    filled = 0
    for bi, block in enumerate(blocks):
        while not _block_fits(segments[si], block, filled):
            si += 1
            filled = 0
        ret.append(si)
        filled += block.count + (
            1
            if (bi + 1 < len(blocks) and block.value == blocks[bi].value)
            else 0
        )

    return ret


def _poss_end(blocks: list[Block], segments: list[Segment]) -> list[int]:
    """Get the index of the last possible segments each block can live in."""
    # Just reverse everything to get the mirror image solution.
    revblocks = blocks.copy()
    revsegments = segments.copy()
    revblocks.reverse()
    revsegments.reverse()
    ret = _poss_start(revblocks, revsegments)
    ret.reverse()
    # Need to invert the indexes too as they'll be relative to the end not
    # the begining.
    return [len(segments) - 1 - r for r in ret]


def split_line(blocks: list[Block], line: Line) -> list[Segment]:
    """Split a line into each of the segments an algorithm can operate on individually."""
    segments = _split_segments(line)
    starts = _poss_start(blocks, segments)
    ends = _poss_end(blocks, segments)
    for bi, block in enumerate(blocks):
        poss = [
            i
            for i in range(starts[bi], ends[bi] + 1)
            if block.count <= len(segments[i].content)
        ]
        for si in poss:
            segments[si].possible.append(block)
        if len(poss) == 1:
            segments[poss[0]].certain.append(block)

    # For segments with some content, if there's only one possible block then
    # that block is a certainty
    for segment in segments:
        if (
            len(set(segment.content) - {VAL_SPACE, VAL_UNKNOWN}) >= 1
            and len(segment.possible) == 1
        ):
            segment.certain = segment.possible

    return segments


ALGORITHMS: list[tuple[str, Algorithm]] = []


def segmentalgorithm(
    name: str,
) -> typing.Callable[[typing.Callable[[Segment], Line]], Algorithm]:
    def decorator(method: typing.Callable[[Segment], Line]) -> Algorithm:
        """Decorator wrapping a segment algorithm into a full line algorithm."""

        def newalgo(blocks: list[Block], line: Line) -> Line:
            ret = line.copy()
            segments = split_line(blocks, line)
            for segment in segments:
                segline = method(segment)
                for i, val in enumerate(segline):
                    ret[i + segment.start] = val
            return ret

        ALGORITHMS.append((name, newalgo))
        return newalgo

    return decorator


@segmentalgorithm("Complete segments")
def completeseg(segment: Segment) -> Line:
    """Fill in the spaces in completed segments."""
    if [x[1] for x in count_blocks(segment.content)] == segment.possible:
        return [VAL_SPACE if v == VAL_UNKNOWN else v for v in segment.content]
    else:
        return segment.content.copy()


@segmentalgorithm("Fill blocks")
def fillseg(segment: Segment) -> Line:
    """Fill in squares due to overlapping blocks in the segment."""
    ret = segment.content.copy()
    blocks = segment.certain
    for bi, block in enumerate(blocks):
        possible_start = sum(b.count for b in blocks[:bi]) + _minspaces(
            blocks[: bi + 1]
        )
        possible_end = (
            len(segment.content)
            - 1
            - sum(b.count for b in blocks[bi + 1 :])
            - _minspaces(blocks[bi:])
        )
        definite_start = possible_end - block.count + 1
        definite_end = possible_start + block.count - 1
        for i in range(definite_start, definite_end + 1):
            ret[i] = block.value
        _logger.debug(
            "Block %d (%s) in %s filled between %d and %d: %s",
            bi,
            block,
            segment,
            definite_start,
            definite_end,
            ret,
        )
    return ret


@segmentalgorithm("Surround complete")
def surroundcomplete(segment: Segment) -> Line:
    """Surround complete blocks in the segment with spaces."""
    ret = segment.content.copy()
    segment_blocks = segment.possible
    existing_blocks = count_blocks(segment.content)

    if not segment_blocks:
        return segment.content

    for idx, block in existing_blocks:
        if block.count != max(
            b.count for b in segment_blocks if b.value == block.value
        ):
            continue

        # Block is definitely complete. figure out which segment block this is.
        sbis = [i for i, b in enumerate(segment_blocks) if b == block]
        sbi = sbis[0]
        if len(sbis) > 1:
            # TODO - need to work out which instance this is if there are
            # multiple.
            # For now, we don't need to worry if the values in this segment
            # are all the same
            if len(set(b.value for b in segment_blocks)) > 1:
                continue

        # If this is the first block or the previous block has the same value,
        # add a space before
        if idx > 0 and (
            sbi == 0 or segment_blocks[sbi - 1].value == block.value
        ):
            ret[idx - 1] = VAL_SPACE

        # If this is the last block or the next block has the same value,
        # add a space before
        if idx + block.count < len(segment.content) and (
            sbi == len(segment_blocks) - 1
            or segment_blocks[sbi + 1].value == block.value
        ):
            _logger.debug(
                "Adding space at idx %d in %s for block %s",
                idx,
                segment.content,
                block,
            )
            ret[idx + block.count] = VAL_SPACE

    return ret


@segmentalgorithm("Fill between single")
def fillbetweensingle(segment: Segment) -> Line:
    """
    In a segment with a single possible value, fill in the unknowns between
    filled squares.
    """
    if len(segment.possible) != 1:
        return segment.content
    
    block = segment.possible[0]

    start = 0
    for i, v in enumerate(segment.content):
        if v != VAL_UNKNOWN:
            start = i
            break
    else:
        return segment.content

    end = len(segment.content)
    for i, v in enumerate(segment.content):
        if v != VAL_UNKNOWN:
            end = i
    if end == len(segment.content) or end == start:
        return segment.content

    ret = segment.content.copy()
    for i in range(start, end + 1):
        ret[i] = block.value
    return ret


@segmentalgorithm("Stretch first")
def stretchfirst(segment: Segment) -> Line:
    """
    If its known exactly which block is first in the segment, apply a stretch
    from the start of the segment to fill in any known squares.
    """
    if not segment.possible or segment.possible != segment.certain:
        return segment.content

    block = segment.possible[0]
    ret = segment.content.copy()
    filling = False
    for i in range(block.count):
        if segment.content[i] == block.value:
            filling = True
        if filling:
            ret[i] = block.value
    return ret


@segmentalgorithm("Inverse stretch first")
def inversestretchfirst(segment: Segment) -> Line:
    """
    If its known exactly which block is first in the segment, add spaces
    before the first filled square such that a stretch would just hit it.

    Example: "..#." -> " .#." for block of 2
    """
    if not segment.possible or segment.possible != segment.certain:
        return segment.content

    block = segment.possible[0]
    should_fill = (
        block.value in set(segment.content[0 : block.count + 1])
    )
    if not should_fill:
        return segment.content

    ret = segment.content.copy()
    end = segment.content.index(block.value)
    while end < len(segment.content):
        if segment.content[end] == block.value:
            end += 1
        else:
            break

    start = end - block.count
    for i in range(0, start):
        ret[i] = VAL_SPACE
    return ret
