"""Module containing the griddler solving algorithms."""

import logging
from typing import Callable, Iterator

from .. import grid
from .segment import Segment

_logger = logging.getLogger(__name__)


def algorithm(
    name: str, symmetric: bool = False
) -> Callable[[grid.Algorithm], grid.Algorithm]:
    """Decorator wrapping an algorithm to register it."""

    def decorator(method: grid.Algorithm) -> grid.Algorithm:
        ALGORITHMS[name] = method
        if symmetric:

            def counterpart(
                blocks: list[grid.Block], line: grid.Line
            ) -> grid.Line:
                rev_blocks = blocks[::-1]
                rev_line = line[::-1]
                return method(rev_blocks, rev_line)[::-1]

            ALGORITHMS[name + " - reversed"] = counterpart
        return method

    return decorator


def _min_spaces(blocks: list[grid.Block]) -> int:
    """
    Calculate the minimum number of spaces that must exist between the
    given blocks.
    """
    ret = 0
    for block, prev in zip(blocks[1:], blocks[:-1]):
        if block.value == prev.value:
            ret += 1
    return ret


def _all_possible_solutions(
    blocks: list[grid.Block], size: int
) -> Iterator[grid.Line]:
    """
    Generator yielding all possible solutions for the given blocks in a
    segment of the given size.
    """
    if not blocks:
        # Only one possible solution if there are no blocks
        yield [grid.VAL_SPACE] * size
        return

    block = blocks[0]
    if block.count > size:
        # If the block wont fit, there are no possible solutions
        return

    subblocks = blocks[1:]
    needspace = subblocks and subblocks[0].value == block.value
    for spaces in range(0, size - block.count + 1):
        subsize = size - block.count - spaces
        if needspace:
            subsize -= 1
        for subsolution in _all_possible_solutions(subblocks, subsize):
            yield [grid.VAL_SPACE] * spaces + [block.value] * block.count + (
                [grid.VAL_SPACE] if needspace else []
            ) + subsolution


def _all_possible_assignments(
    items: list[grid.Block], buckets: int
) -> Iterator[list[list[grid.Block]]]:
    """
    Assign the blocks to the given number of buckets to get all possible
    states without considering bucket sizes and content.
    """
    if buckets == 0:
        return
    if buckets == 1:
        yield [items]
        return
    if not items:
        yield [[]] * buckets

    firstlot = items[:]
    otherlot: list[grid.Block] = []
    while firstlot:
        for other in _all_possible_assignments(otherlot, buckets - 1):
            yield [firstlot] + other
        otherlot = [firstlot[-1]] + otherlot
        firstlot = firstlot[:-1]

    if otherlot:
        empty: list[list[grid.Block]] = [[]]
        for other in _all_possible_assignments(otherlot, buckets - 1):
            yield empty + other


def _is_valid_assignment(blocks: list[grid.Block], content: grid.Line) -> bool:
    """
    Determine whether the given list of blocks can fit in a segment with the
    given content.
    """

    def _is_valid_solution(current: grid.Line, solution: grid.Line) -> bool:
        return all(
            c1 in (c2, grid.VAL_UNKNOWN) for c1, c2 in zip(current, solution)
        )

    return any(
        _is_valid_solution(content, soln)
        for soln in _all_possible_solutions(blocks, len(content))
    )


def _split_line(
    blocks: list[grid.Block], line: grid.Line
) -> list[tuple[int, Segment]]:
    """Split a line into each of the segments an algorithm can operate on individually."""
    segments = list(Segment.from_line(line))
    valid_assignments = [
        assignment
        for assignment in _all_possible_assignments(blocks, len(segments))
        if all(
            _is_valid_assignment(blk, segment.content)
            for blk, (_, segment) in zip(assignment, segments)
        )
    ]
    for segidx, (_, segment) in enumerate(segments):
        assignments = []
        for assignment in valid_assignments:
            if assignment[segidx] not in assignments:
                assignments.append(assignment[segidx])
        segment.possible = assignments

    return segments


ALGORITHMS: dict[str, grid.Algorithm] = {}


def segmentalgorithm(
    name: str, symmetric: bool = False
) -> Callable[
    [Callable[[Segment], grid.Line]], Callable[[Segment], grid.Line]
]:
    """Decorator wrapping a segment algorithm into a full line algorithm."""

    def decorator(
        method: Callable[[Segment], grid.Line]
    ) -> Callable[[Segment], grid.Line]:
        @algorithm(name, symmetric)
        def newalgo(blocks: list[grid.Block], line: grid.Line) -> grid.Line:
            ret = line.copy()
            segments = _split_line(blocks, line)
            for start, segment in segments:
                segline = method(segment)
                for i, val in enumerate(segline):
                    ret[i + start] = val
            return ret

        # Return the original method so it can still be tested and used
        # directly as written, but the algorithm is correctly registered
        return method

    return decorator


@segmentalgorithm("Complete segments")
def completeseg(segment: Segment) -> grid.Line:
    """Fill in the spaces in completed segments."""
    current_blocks = [x[1] for x in grid.count_blocks(segment.content)]
    if len(segment.possible) != 1:
        return segment.content

    return [
        v
        if v != grid.VAL_UNKNOWN or current_blocks != segment.possible[0]
        else grid.VAL_SPACE
        for v in segment.content
    ]


@segmentalgorithm("Fill blocks")
def fillseg(segment: Segment) -> grid.Line:
    """Fill in squares due to overlapping blocks in the segment."""
    ret = segment.content.copy()
    if len(segment.possible) != 1:
        return ret
    blocks = segment.possible[0]

    for bidx, block in enumerate(blocks):
        possible_start = sum(b.count for b in blocks[:bidx]) + _min_spaces(
            blocks[: bidx + 1]
        )
        possible_end = (
            len(segment.content)
            - 1
            - sum(b.count for b in blocks[bidx + 1 :])
            - _min_spaces(blocks[bidx:])
        )
        definite_start = possible_end - block.count + 1
        definite_end = possible_start + block.count - 1
        for i in range(definite_start, definite_end + 1):
            ret[i] = block.value
        _logger.debug(
            "Block %d (%s) in %s filled between %d and %d: %s",
            bidx,
            block,
            segment,
            definite_start,
            definite_end,
            ret,
        )
    return ret


@segmentalgorithm("Surround complete")
def surroundcomplete(segment: Segment) -> grid.Line:
    """Surround complete blocks in the segment with spaces."""
    if len(segment.possible) != 1:
        return segment.content

    ret = segment.content.copy()
    segment_blocks = segment.possible[0]
    existing_blocks = grid.count_blocks(segment.content)

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
            # @@@ Need to work out which instance this is if there are multiple.
            # For now, we don't need to worry if the values in this segment
            # are all the same
            assert len(set(b.value for b in segment_blocks)) <= 1

        # If this is the first block or the previous block has the same value,
        # add a space before
        if idx > 0 and (
            sbi == 0 or segment_blocks[sbi - 1].value == block.value
        ):
            ret[idx - 1] = grid.VAL_SPACE

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
            ret[idx + block.count] = grid.VAL_SPACE

    return ret


@segmentalgorithm("Fill between single")
def fillbetweensingle(segment: Segment) -> grid.Line:
    """
    In a segment with a single possible value, fill in the unknowns between
    filled squares.
    """
    if len(segment.possible) != 1 or len(segment.possible[0]) != 1:
        return segment.content

    block = segment.possible[0][0]

    start = 0
    for i, val in enumerate(segment.content):
        if val != grid.VAL_UNKNOWN:
            start = i
            break
    else:
        return segment.content

    end = len(segment.content)
    for i, val in enumerate(segment.content):
        if val != grid.VAL_UNKNOWN:
            end = i
    if end == len(segment.content) or end == start:
        return segment.content

    ret = segment.content.copy()
    for i in range(start, end + 1):
        ret[i] = block.value
    return ret


@segmentalgorithm("Stretch first", symmetric=True)
def stretchfirst(segment: Segment) -> grid.Line:
    """
    If its known exactly which block is first in the segment, apply a stretch
    from the start of the segment to fill in any known squares.
    """
    if (
        not all(segment.possible)
        or len({blks[0] for blks in segment.possible}) != 1
    ):
        return segment.content

    block = segment.possible[0][0]
    ret = segment.content.copy()
    filling = False
    for i in range(block.count):
        if segment.content[i] == block.value:
            filling = True
        if filling:
            ret[i] = block.value
    return ret


@segmentalgorithm("Inverse stretch first", symmetric=True)
def inversestretchfirst(segment: Segment) -> grid.Line:
    """
    If its known exactly which block is in the segment, add spaces
    before the first filled square such that a stretch would just hit it.

    Example: "..#." -> " .#." for block of 2
    """
    if (
        not all(segment.possible)
        or len({blks[0] for blks in segment.possible}) != 1
    ):
        return segment.content

    block = segment.possible[0][0]
    should_fill = block.value in set(segment.content[0 : block.count + 1])
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
        ret[i] = grid.VAL_SPACE
    return ret


@algorithm("BruteForce: Single possible value")
def singlepossiblevalue(
    blocks: list[grid.Block], line: grid.Line
) -> grid.Line:
    """
    Brute force approach to figure out the value of a square by figuring out
    if there's more than one possible value for a square given the lines
    current state.
    """
    size = len(line)
    values: list[set[grid.Value]] = [set() for _ in range(size)]
    for solution in _all_possible_solutions(blocks, size):
        valid = all(
            line[i] in {grid.VAL_UNKNOWN, solution[i]} for i in range(size)
        )
        if not valid:
            continue
        for i in range(size):
            values[i].add(solution[i])

    ret = line.copy()
    for i in range(size):
        if len(values[i]) == 1:
            ret[i] = list(values[i])[0]
    return ret
