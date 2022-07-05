"""Module for loading puzzles from griddlers.net."""
import requests
import json
from .grid import Block, Grid, Value


def getjs(idx: int) -> str:
    """Get the JS code for the given puzzle ID."""
    url = (
        "https://www.griddlers.net/nonogram/-/g/t1632255045917/i01"
        "?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle"
        f"&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id={idx}"
        "&_gpuzzles_WAR_puzzles_lite=false"
    )
    response = requests.get(url)
    assert response.status_code == 200
    return response.text


def getpuzzle(jscode: str) -> str:
    """Extract the puzzle specific part of the JS code."""
    lines = jscode.splitlines()

    start = -1
    for i, line in enumerate(lines):
        if line.startswith("var puzzle = {"):
            start = i
            break
    else:
        raise Exception("Didn't find the start of the puzzle in the JS")

    end = -1
    for i in range(start, len(lines)):
        if lines[i].startswith("}"):
            end = i
            break
    else:
        raise Exception("Didn't find the end of the puzzle in the JS")

    puzzle = "\n".join(["{"] + lines[start + 1 : end + 1])
    return puzzle


def getlolol(puzzlejs: str, key: str) -> list[list[list[int]]]:
    """
    Get the list-of-list-of-lists-of-values from the puzzle part of the JS.
    """
    content = puzzlejs.split(key + ":")[1]
    content = content.strip()
    assert content[0] == "["
    depth = 1
    retstr = "["
    for char in content[1:]:
        retstr += char
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        else:
            assert char == "," or char.isdigit() or char.isspace()
        if depth == 0:
            break
    else:
        raise Exception(f"Never found the end of entry {key}")

    lolol: list[list[list[int]]] = json.loads(retstr)
    return lolol


def to_grid(
    top_header: list[list[list[int]]], left_header: list[list[list[int]]]
) -> Grid:
    """
    Create a grid from the header values on the top and left sides.
    """
    cols = [[Block(Value(b[0]), b[1]) for b in block] for block in top_header]
    rows = [[Block(Value(b[0]), b[1]) for b in block] for block in left_header]
    return Grid(rows, cols)


def get_grid(puzid: int) -> Grid:
    """Create a solvable grid for the given puzzleid."""
    puzzle = getpuzzle(getjs(puzid))
    top_header = getlolol(puzzle, "topHeader")
    left_header = getlolol(puzzle, "leftHeader")
    return to_grid(top_header, left_header)
