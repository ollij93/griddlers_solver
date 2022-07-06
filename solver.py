"""
Module containing the griddler solving algorithms.
"""

import logging
import typing

from .grid import VAL_SPACE, VAL_UNKNOWN, Block, Value, count_blocks

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
        if blocks[index].count <= (len(available[available_index]) - available_curr):
            available_curr += blocks[index].count + 1
            index += 1
        else:
            available_index += 1
            available_curr = 0

    # Available index is now the first block where our block could start
    # Check it fits, or find next available block where it does
    while blocks[block_index].count > (
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
    ret = [VAL_UNKNOWN] * size
    for idx, block in enumerate(blocks):
        possible_start = sum(b.count + 1 for b in blocks[:idx])
        possible_end = size - 1 - sum(b.count + 1 for b in blocks[idx + 1 :])
        definite_start = possible_end - block.count + 1
        definite_end = possible_start + block.count - 1
        for defidx in range(definite_start, definite_end + 1):
            ret[defidx] = block.value
    return ret


def fill_blocks(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the fill blocks algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    available: list[list[Value]] = _list_split(current, VAL_SPACE)
    start_blocks = [
        _get_first_available_block_index(blocks, available, i)
        for i in range(len(blocks))
    ]
    end_blocks = [
        _get_last_available_block_index(blocks, available, i)
        for i in range(len(blocks))
    ]
    ret = current.copy()
    for idx, avals in enumerate(available):
        alen = len(avals)
        start = idx + sum(len(a) for a in available[:idx])
        blks = [
            blocks[bi]
            for bi in range(len(blocks))
            if start_blocks[bi] >= idx
            if end_blocks[bi] <= idx
        ]
        content = _fill_blocks_section(blks, alen)
        for cidx, val in enumerate(content):
            ridx = cidx + start
            assert ret[ridx] != VAL_SPACE
            if val != VAL_UNKNOWN:
                ret[ridx] = val

    return ret


def complete_blocks(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the complete blocks algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    available = _list_split(current, VAL_SPACE)
    starts = [
        _get_first_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ends = [
        _get_last_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ret = current.copy()
    for aidx, section in enumerate(available):
        if not section or set(section) == {VAL_UNKNOWN}:
            # This section is empty so can't contain complete blocks
            continue
        astart = aidx + sum(len(a) for a in available[:aidx])
        possibles = [
            bi for bi in range(len(blocks)) if starts[bi] <= aidx if ends[bi] >= aidx
        ]
        max_poss = max(blocks[bi].count for bi in possibles)
        max_curr = max(b.count for _, b in count_blocks(section))
        if max_poss == max_curr:
            # The current highest block in this section is complete, find its
            # start and end
            for sidx, val in enumerate(section):
                if set(section[sidx : sidx + max_poss]) == {val} and val not in {
                    VAL_SPACE,
                    VAL_UNKNOWN,
                }:
                    if sidx > 0:
                        assert ret[astart + sidx - 1] == VAL_UNKNOWN
                        ret[astart + sidx - 1] = VAL_SPACE
                    if sidx + max_poss < len(section):
                        assert ret[astart + sidx + max_poss] == VAL_UNKNOWN
                        ret[astart + sidx + max_poss] = VAL_SPACE
                    break

    return ret


def complete_runs(blocks: list[Block], current: list[Value]) -> list[Value]:
    """
    Run the complete runs algorithm on a row or column.

    :param blocks: The blocks for this row or column.
    :param current: The current content of the row or column.
    :return: The updated content of the row or column.
    """
    existing = [b for _, b in count_blocks(current)]
    _logger.debug("Blocks: %s, Existing: %s", blocks, existing)
    if blocks == existing:
        return [VAL_SPACE if c == VAL_UNKNOWN else c for c in current]
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
    available = _list_split(current, VAL_SPACE)
    starts = [
        _get_first_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ends = [
        _get_last_available_block_index(blocks, available, bi)
        for bi in range(len(blocks))
    ]
    ret = current.copy()
    for aidx, section in enumerate(available):
        if set(section) != {VAL_UNKNOWN}:
            # This section already contains something, so can't be empty
            continue

        _logger.debug(
            "Checking for empty on section %d of %s onto %s",
            aidx,
            blocks,
            available,
        )
        possibles = [
            bi
            for bi in range(len(blocks))
            if starts[bi] <= aidx
            if ends[bi] >= aidx
            if blocks[bi].count <= len(section)
        ]
        if not possibles:
            # There a no blocks that can fit in this section, so fill it in
            start = aidx + sum(len(a) for a in available[:aidx])
            for ridx in range(start, start + len(section)):
                ret[ridx] = VAL_SPACE
        else:
            _logger.debug("%s %s %s %s", possibles, blocks, starts, ends)

    return ret
