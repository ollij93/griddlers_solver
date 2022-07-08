"""Module defining a solvable grid and it's components."""
import logging
from dataclasses import dataclass
from typing import Callable

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Value:
    """Single value in a grid."""

    idx: int

    def __repr__(self) -> str:
        return f'"{self.render()}"'

    def __lt__(self, other: "Value") -> bool:
        if not isinstance(other, Value):
            return NotImplemented
        return self.idx < other.idx

    def render(self) -> str:
        """Get the string for rendering a single square of this value."""
        if self == VAL_UNKNOWN:
            return "."
        if self == VAL_SPACE:
            return " "
        if self.idx == 2:
            return "#"
        if self.idx == 3:
            return "%"
        raise ValueError(f"Unrenderable idx value: {self.idx}")

    @staticmethod
    def from_str(value: str) -> "Value":
        """Decode an instance of this class from a string."""
        if value == "#":
            return Value(2)
        if value == "%":
            return Value(3)
        if value == " ":
            return VAL_SPACE
        return VAL_UNKNOWN


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


Algorithm = Callable[[list[Block], Line], Line]


class Grid:
    """Solvable grid."""

    def __init__(
        self, row_blocks: list[list[Block]], col_blocks: list[list[Block]]
    ) -> None:
        self.row_blocks = row_blocks
        self.col_blocks = col_blocks
        self.volume = [VAL_UNKNOWN for _ in row_blocks for __ in col_blocks]

    @property
    def width(self) -> int:
        """Width of the grid."""
        return len(self.col_blocks)

    @property
    def height(self) -> int:
        """Height of the grid."""
        return len(self.row_blocks)

    @property
    def columns(self) -> list[Line]:
        """The grid divided into columns."""
        return [self.volume[c :: self.width] for c in range(self.width)]

    @property
    def rows(self) -> list[Line]:
        """The grid divided into rows."""
        return [
            self.volume[self.width * r : self.width * (r + 1)]
            for r in range(self.height)
        ]

    def get(self, xcoord: int, ycoord: int) -> Value:
        """Access a value using the X,Y coordinates."""
        return self.volume[self.width * ycoord + xcoord]

    def set(self, xcoord: int, ycoord: int, val: Value) -> None:
        """Set a value using the X,Y coordinates."""
        self.volume[self.width * ycoord + xcoord] = val

    def render(self) -> list[str]:
        """Render the grid to a series of ASCII lines."""
        ret = []

        assert all(
            all(b.count < 100 and b.count > 0 for b in blocks)
            for blocks in self.row_blocks
        )
        row_prefixes = [
            ",".join([b.prefix() for b in blocks])
            for blocks in self.row_blocks
        ]
        prefix_length = max(len(p) for p in row_prefixes)

        assert all(
            all(b.count < 100 and b.count > 0 for b in blocks)
            for blocks in self.col_blocks
        )
        column_prefixes: list[list[str]] = [
            [b.prefix() for b in blocks] for blocks in self.col_blocks
        ]
        prefix_height = max(len(p) for p in column_prefixes)

        for height in range(prefix_height):
            index = prefix_height - height
            line = " ".join(
                f"{p[-index]:>2}" if len(p) >= index else "  "
                for p in column_prefixes
            )
            ret.append(f"{' '*prefix_length}|{line}")

        ret.append("-" * (prefix_length + 1 + 3 * self.width))

        for ridx, row in enumerate(self.rows):
            prefix = row_prefixes[ridx].rjust(prefix_length)
            content = " " + "  ".join(x.render() for x in row)
            ret.append(f"{prefix}|{content}")

        return ret

    def check_solved(self) -> bool:
        """
        Check if this grid is solved with its current content.
        """
        for ridx, row in enumerate(self.rows):
            if [x[1] for x in count_blocks(row)] != self.row_blocks[ridx]:
                return False

        for cidx, column in enumerate(self.columns):
            if [x[1] for x in count_blocks(column)] != self.col_blocks[cidx]:
                return False

        return True

    def apply_algorithm(self, name: str, method: Algorithm) -> bool:
        """
        Apply an algorithm to all lines in the grid.

        :param name: Name of the algorithm being applied.
        :param method: Method to invoke on each line to run the algorithm.
        :return: True if an update was made, false otherwise.
        """
        _logger.info("Applying %s", name)
        progress = False

        for ycoord, row in enumerate(self.row_blocks):
            _logger.debug("Processing row %d: %s", ycoord, self.rows[ycoord])
            content = method(row, self.rows[ycoord])
            _logger.debug("New content: %s", content)
            if content == self.rows[ycoord]:
                continue
            for xcoord, val in enumerate(content):
                if val != VAL_UNKNOWN:
                    assert self.get(xcoord, ycoord) in {
                        val,
                        VAL_UNKNOWN,
                    }, f"{xcoord}, {ycoord}, {self.get(xcoord,ycoord)}, {val}"
                    self.set(xcoord, ycoord, val)
                    progress = True

        for xcoord, col in enumerate(self.col_blocks):
            _logger.debug(
                "Processing column %d: %s", xcoord, self.columns[xcoord]
            )
            content = method(col, self.columns[xcoord])
            _logger.debug("New content: %s", content)
            if content == self.columns[xcoord]:
                continue
            for ycoord, val in enumerate(content):
                if val != VAL_UNKNOWN:
                    assert self.get(xcoord, ycoord) in {
                        val,
                        VAL_UNKNOWN,
                    }, f"{xcoord}, {ycoord}, {self.get(xcoord,ycoord)}, {val}"
                    self.set(xcoord, ycoord, val)
                    progress = True

        return progress
