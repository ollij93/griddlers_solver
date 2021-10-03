import enum
import logging
import typing

_logger = logging.getLogger(__name__)

Block = int


class Value(enum.Enum):
    UNKNOWN = "-"
    SPACE = " "
    SQUARE = "#"

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, label: str) -> "Value":
        if label == "-":
            return cls.UNKNOWN
        elif label == " ":
            return cls.SPACE
        elif label == "#":
            return cls.SQUARE
        else:
            raise KeyError(label)



def count_blocks(current: list[Value]) -> list[Block]:
    """
    Count the existing blocks in a row or column.

    :param current: The current content of the row or column.
    :return: The list of existing blocks in the row or column.
    """
    ret = []
    count = 0
    for val in current:
        if val in (Value.UNKNOWN, Value.SPACE):
            if count > 0:
                ret.append(count)
                count = 0
        elif val == Value.SQUARE:
            count += 1
    if count > 0:
        ret.append(count)
        count = 0

    return ret


class Grid:
    def __init__(
        self, rowBlocks: list[list[Block]], colBlocks: list[list[Block]]
    ) -> None:
        self.rowBlocks = rowBlocks
        self.colBlocks = colBlocks
        self.volume = [Value.UNKNOWN for _ in rowBlocks for __ in colBlocks]

    @property
    def width(self) -> int:
        return len(self.colBlocks)

    @property
    def height(self) -> int:
        return len(self.rowBlocks)

    @property
    def columns(self) -> list[list[Value]]:
        return [self.volume[c :: self.width] for c in range(self.width)]

    @property
    def rows(self) -> list[list[Value]]:
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
            all(r < 100 and r > 0 for r in row) for row in self.rowBlocks
        )
        row_prefixes = [
            ",".join(str(r) for r in row) for row in self.rowBlocks
        ]
        prefix_length = max(len(p) for p in row_prefixes)

        assert all(
            all(c < 100 and c > 0 for c in col) for col in self.colBlocks
        )
        column_prefixes: list[list[str]] = [
            [str(c) for c in col] for col in self.colBlocks
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
            content = " " + "  ".join(x.value for x in row)
            ret.append(f"{prefix}|{content}")

        return ret
    
    def check_solved(self) -> bool:
        """
        Check if this grid is solved with its current content.
        """
        for ri, row in enumerate(self.rows):
            if count_blocks(row) != self.rowBlocks[ri]:
                return False
        
        for ci, column in enumerate(self.columns):
            if count_blocks(column) != self.colBlocks[ci]:
                return False

        return True

    def apply_algorithm(
        self, method: typing.Callable[[list[Block], list[Value]], list[Value]]
    ) -> bool:
        """
        Apply the fill blocks algorithm to a grid.

        :param grid: The grid to apply the fill blocks algorithm to.
        :return: True if an update was made, false otherwise.
        """
        _logger.info(f"Applying {method.__name__}")
        progress = False

        for y, row in enumerate(self.rowBlocks):
            _logger.debug(f"Processing row {y}: {self.rows[y]}")
            content = method(row, self.rows[y])
            if content == self.rows[y]:
                continue
            for x, val in enumerate(content):
                if val != Value.UNKNOWN:
                    assert self.get(x, y) in {val, Value.UNKNOWN}
                    self.set(x, y, val)
                    progress = True

        for x, col in enumerate(self.colBlocks):
            _logger.debug(f"Processing column {x}: {self.columns[x]}")
            content = method(col, self.columns[x])
            if content == self.columns[x]:
                continue
            for y, val in enumerate(content):
                if val != Value.UNKNOWN:
                    assert self.get(x, y) in {val, Value.UNKNOWN}
                    self.set(x, y, val)
                    progress = True

        return progress
