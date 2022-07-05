import enum
import logging
import typing

from dataclasses import dataclass

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Value:
    idx: int

    def __repr__(self) -> str:
        return f'"{self.render()}"'

    def render(self) -> str:
        """Get the string for rendering a single square of this value."""
        if self == VAL_UNKNOWN:
            return "."
        if self == VAL_SPACE:
            return " "
        return "#"


VAL_UNKNOWN = Value(0)
VAL_SPACE = Value(1)


@dataclass(frozen=True)
class Block:
    """
    Block of multiple consecutive squares of the same value.
    """

    value: Value
    count: int

    def __post_init___(self) -> None:
        """Check the values are sane."""
        assert self.count > 0
        assert self.value not in (VAL_UNKNOWN, VAL_SPACE)

    def prefix(self) -> str:
        """Get the string for rendering this block prefix."""
        return str(self.count)


Line = list[Value]


def count_blocks(current: Line) -> list[tuple[int, Block]]:
    """
    Count the existing blocks in a row or column.

    :param current: The current content of the row or column.
    :return: The list of existing blocks in the row or column.
    """
    ret: list[tuple[int, Block]] = []

    currval = current[0]
    count = 0
    for idx, val in enumerate(current):
        if val != currval:
            if currval not in (VAL_UNKNOWN, VAL_SPACE):
                ret.append((idx - count, Block(currval, count)))
            currval = val
            count = 0
        count += 1

    if currval not in (VAL_UNKNOWN, VAL_SPACE):
        ret.append((len(current) - count, Block(currval, count)))

    return ret


Algorithm = typing.Callable[[list[Block], Line], Line]


class Grid:
    def __init__(
        self, rowBlocks: list[list[Block]], colBlocks: list[list[Block]]
    ) -> None:
        self.rowBlocks = rowBlocks
        self.colBlocks = colBlocks
        self.volume = [VAL_UNKNOWN for _ in rowBlocks for __ in colBlocks]

    @property
    def width(self) -> int:
        return len(self.colBlocks)

    @property
    def height(self) -> int:
        return len(self.rowBlocks)

    @property
    def columns(self) -> list[Line]:
        return [self.volume[c :: self.width] for c in range(self.width)]

    @property
    def rows(self) -> list[Line]:
        return [
            self.volume[self.width * r : self.width * (r + 1)]
            for r in range(self.height)
        ]

    def get(self, x: int, y: int) -> Value:
        return self.volume[self.width * y + x]

    def set(self, x: int, y: int, val: Value) -> None:
        self.volume[self.width * y + x] = val

    def render(self) -> list[str]:
        ret = []

        assert all(
            all(b.count < 100 and b.count > 0 for b in blocks)
            for blocks in self.rowBlocks
        )
        row_prefixes = [
            ",".join([b.prefix() for b in blocks]) for blocks in self.rowBlocks
        ]
        prefix_length = max(len(p) for p in row_prefixes)

        assert all(
            all(b.count < 100 and b.count > 0 for b in blocks)
            for blocks in self.colBlocks
        )
        column_prefixes: list[list[str]] = [
            [b.prefix() for b in blocks] for blocks in self.colBlocks
        ]
        prefix_height = max(len(p) for p in column_prefixes)

        for h in range(prefix_height):
            index = prefix_height - h
            line = " ".join(
                f"{p[-index]:>2}" if len(p) >= index else "  "
                for p in column_prefixes
            )
            ret.append(f"{' '*prefix_length}|{line}")

        ret.append("-" * (prefix_length + 1 + 3 * self.width))

        for ri, row in enumerate(self.rows):
            prefix = row_prefixes[ri].rjust(prefix_length)
            content = " " + "  ".join(x.render() for x in row)
            ret.append(f"{prefix}|{content}")

        return ret

    def check_solved(self) -> bool:
        """
        Check if this grid is solved with its current content.
        """
        for ri, row in enumerate(self.rows):
            if [x[1] for x in count_blocks(row)] != self.rowBlocks[ri]:
                return False

        for ci, column in enumerate(self.columns):
            if [x[1] for x in count_blocks(column)] != self.colBlocks[ci]:
                return False

        return True

    def apply_algorithm(self, name: str, method: Algorithm) -> bool:
        """
        Apply an algorithm to all lines in the grid.

        :param name: Name of the algorithm being applied.
        :param method: Method to invoke on each line to run the algorithm.
        :return: True if an update was made, false otherwise.
        """
        _logger.info(f"Applying {name}")
        progress = False

        for y, row in enumerate(self.rowBlocks):
            _logger.debug(f"Processing row {y}: {self.rows[y]}")
            content = method(row, self.rows[y])
            _logger.debug(f"New content: {content}")
            if content == self.rows[y]:
                continue
            for x, val in enumerate(content):
                if val != VAL_UNKNOWN:
                    assert self.get(x, y) in {val, VAL_UNKNOWN}, f"{x}, {y}, {self.get(x,y)}, {val}"
                    self.set(x, y, val)
                    progress = True

        for x, col in enumerate(self.colBlocks):
            _logger.debug(f"Processing column {x}: {self.columns[x]}")
            content = method(col, self.columns[x])
            _logger.debug(f"New content: {content}")
            if content == self.columns[x]:
                continue
            for y, val in enumerate(content):
                if val != VAL_UNKNOWN:
                    assert self.get(x, y) in {val, VAL_UNKNOWN}, f"{x}, {y}, {self.get(x,y)}, {val}"
                    self.set(x, y, val)
                    progress = True

        return progress
