"""Main entrypoint of this package."""

import argparse
import logging
import sys

from . import griddlersnet
from .solver import ALGORITHMS

_logger = logging.getLogger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-f", "--brute-force", action="store_true")
    parser.add_argument("puzzle", type=int)

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """Main entry point of this script."""
    args = _parse_args(argv)

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
