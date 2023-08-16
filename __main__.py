"""Main entrypoint of this package."""

import dataclasses
import logging
import sys

import cfgclasses as cfg

from . import griddlersnet
from .solver import ALGORITHMS

_logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Config(cfg.ConfigClass):
    """Configuration for this package."""

    puzzle: int = cfg.positional("The puzzle to solve")
    debug: bool = cfg.store_true(
        "Turn on debug output", optnames=["-d", "--debug"]
    )
    brute_force: bool = cfg.store_true(
        "Enable brute force algorithms",
        optnames=["-f", "--brute-force"],
    )


def main(argv: list[str]) -> int:
    """Main entry point of this script."""
    args = Config.parse_args(argv, prog="griddlerssolver")

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    grid = griddlersnet.get_grid(args.puzzle)

    _logger.info("Begining to solve")
    while not grid.check_solved():
        _logger.info("Applying algorithms")
        print("\n".join(grid.render()))
        progress = False
        for name, method in ALGORITHMS.items():
            if name.startswith("BruteForce:") and not args.brute_force:
                # Skip this brute force algorithm as not selected
                continue

            progress = grid.apply_algorithm(name, method)
            if progress:
                break
        else:
            # Failed to make any progress, exit the main loop
            break

    if not grid.check_solved():
        _logger.info("Failed to find complete solution.")
        print("\n".join(grid.render()))
        return 1

    _logger.info("SOLVED!")
    print("\n".join(grid.render()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
