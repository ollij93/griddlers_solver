"""Main entrypoint of this package."""

import argparse
from griddlers_solver import griddlersnet
import logging
import sys

from . import solver

_logger = logging.getLogger(__name__)


def main():
    """Main entry point of this script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("puzzle", type=int)
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    grid = griddlersnet.getGrid(args.puzzle)

    _logger.info("Begining to solve")
    while not grid.check_solved():
        _logger.info("Applying algorithms")
        print("\n".join(grid.render()))
        progress = False
        for algo in (
            solver.complete_runs,
            solver.empty_sections,
            solver.fill_blocks,
            solver.complete_blocks,
        ):
            progress = grid.apply_algorithm(algo)
            if progress:
                break
        else:
            # Failed to make any progress, exist the main loop
            break

    if grid.check_solved():
        _logger.info("SOLVED!")
        print("\n".join(grid.render()))
    else:
        _logger.info("Failed to find complete solution.")
        print("\n".join(grid.render()))


if __name__ == "__main__":
    main()
