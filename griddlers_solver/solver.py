"""
Module containing the griddler solving algorithms.
"""

import logging
import typing

from .grid import Block, Value, count_blocks

_logger = logging.getLogger(__name__)

T = typing.TypeVar("T")


def _list_split(lst: list[T], sep: T) -> list[list[T]]:
    """
    Split a list into a list of sub-lists.

    :param lst: The list to be split.
    :param sep: The object to be seperated.
    :return: List of sub-lists that have been split.
    """
    ret: list[list[T]] = []
    cur: list[T] = []
    for val in lst:
        if val == sep:
            ret.append(cur)
            cur = []
        else:
            cur.append(val)
    ret.append(cur)
    cur = []
    return ret


def _get_first_available_block_index(
    blocks: list[Block], available: list[list[Value]], block_index: int
) -> int:
    """
    Get the index of the first available section that the given block can fit
    into.

    :param blocks: The blocks for the given row.
    :param available: The available sections to check against.
    :param block_index: Which block from the list to check for.
    :return: The first index into `available` that the given block can fit in.
    """
    available_index = 0
    available_curr = 0

    # Go through all the preceeding blocks
    index = 0
    while index < block_index:
        if blocks[index] <= (len(available[available_index]) - available_curr):
            available_curr += blocks[index] + 1
            index += 1
        else:
            available_index += 1
            available_curr = 0

    # Available index is now the first block where our block could start
    # Check it fits, or find next available block where it does
    while blocks[block_index] > (
        len(available[available_index]) - available_curr
    ):
        available_index += 1
        available_curr = 0

    return available_index


def _get_last_available_block_index(
    blocks: list[Block], available: list[list[Value]], block_index: int
) -> int:
    """
    See _get_first_available_block_index
    """
    revblocks = blocks.copy()
    revblocks.reverse()
    revavailable = available.copy()
    revavailable.reverse()
    return (
        len(available)
        - 1
        - _get_first_available_block_index(
            revblocks, revavailable, len(blocks) - 1 - block_index
        )
    )


def _fill_blocks_section(blocks: list[Block], size: int) -> list[Value]:
    """
    Run the fill blocks algorithm on a single available section.

    :param blocks: The blocks that *must* fit in this available section.
    :param size: The size of this available section.
    :return: The list of values determined for this section.
    """
    ret = [Value.UNKNOWN] * size
    for i in range(len(blocks)):
        possible_start = sum(b + 1 for b in blocks[:i])
        possible_end = size - 1 - sum(b + 1 for b in blocks[i + 1 :])
        definite_start = possible_end - blocks[i] + 1
        definite_end = possible_start + blocks[i] - 1
        for x in range(definite_start, definite_end + 1):
            ret[x] = Value.SQUARE
    return ret


def fill_blocks(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the fill blocks algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    available: list[list[Value]] = _list_split(current, Value.SPACE)
    start_blocks = [
        _get_first_available_block_index(blocks, available, i)
        for i in range(len(blocks))
    ]
    end_blocks = [
        _get_last_available_block_index(blocks, available, i)
        for i in range(len(blocks))
    ]
    ret = current.copy()
    for ai in range(len(available)):
        alen = len(available[ai])
        start = ai + sum(len(a) for a in available[:ai])
        bs = [
            blocks[bi]
            for bi in range(len(blocks))
            if start_blocks[bi] >= ai and end_blocks[bi] <= ai
        ]
        content = _fill_blocks_section(bs, alen)
        for ci, val in enumerate(content):
            ri = ci + start
            assert ret[ri] != Value.SPACE
            if val != Value.UNKNOWN:
                ret[ri] = val

    return ret


def complete_blocks(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the complete blocks algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    available = _list_split(current, Value.SPACE)
    starts = [
        _get_first_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ends = [
        _get_last_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ret = current.copy()
    for ai, section in enumerate(available):
        if not section or set(section) == {Value.UNKNOWN}:
            # This section is empty so can't contain complete blocks
            continue
        astart = ai + sum(len(a) for a in available[:ai])
        possibles = [
            bi
            for bi in range(len(blocks))
            if starts[bi] <= ai and ends[bi] >= ai
        ]
        max_poss = max(blocks[bi] for bi in possibles)
        max_curr = max(count_blocks(section))
        if max_poss == max_curr:
            # The current highest block in this section is complete, find its
            # start and end
            for si, val in enumerate(section):
                if set(section[si : si + max_poss]) == {Value.SQUARE}:
                    if si > 0:
                        assert ret[astart + si - 1] == Value.UNKNOWN
                        ret[astart + si - 1] = Value.SPACE
                    if si + max_poss < len(section):
                        assert ret[astart + si + max_poss] == Value.UNKNOWN
                        ret[astart + si + max_poss] = Value.SPACE
                    break

    return ret


def complete_runs(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the complete runs algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    existing = count_blocks(current)
    if blocks == existing:
        return [Value.SPACE if c == Value.UNKNOWN else c for c in current]
    else:
        return current


def empty_sections(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the empty sections algorithm on a row or column.

    This algorithm works by checking, for each available section, whether any
    block can be contained within it.

    :param blocks: The block for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    available = _list_split(current, Value.SPACE)
    starts = [
        _get_first_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ends = [
        _get_last_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ret = current.copy()
    for ai, section in enumerate(available):
        if set(section) != {Value.UNKNOWN}:
            # This section already contains something, so can't be empty
            continue

        _logger.debug(
            "Checking for empty on section %d of %s onto %s",
            ai,
            blocks,
            available,
        )
        possibles = [
            bi
            for bi in range(len(blocks))
            if starts[bi] <= ai
            and ends[bi] >= ai
            and blocks[bi] <= len(section)
        ]
        if not possibles:
            # There a no blocks that can fit in this section, so fill it in
            start = ai + sum(len(a) for a in available[:ai])
            for ri in range(start, start + len(section)):
                ret[ri] = Value.SPACE
        else:
            _logger.debug("%s %s %s %s", possibles, blocks, starts, ends)

    return ret