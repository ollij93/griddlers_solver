import requests
from .grid import Grid

def getjs(id: int) -> str:
    url = f"https://www.griddlers.net/nonogram/-/g/t1632255045917/i01?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id={id}&_gpuzzles_WAR_puzzles_lite=false"
    r = requests.get(url)
    assert r.status_code == 200
    return r.text


def getpuzzle(js: str) -> str:
    lines = js.splitlines()

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
    content = puzzlejs.split(key + ":")[1]
    content = content.strip()
    assert content[0] == "["
    depth = 1
    retstr = "["
    for c in content[1:]:
        retstr += c
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        else:
            assert c == "," or c.isdigit() or c.isspace()
        if depth == 0:
            break
    else:
        raise Exception(f"Never found the end of entry {key}")

    return eval(retstr)


def toGrid(
    topHeader: list[list[list[int]]], leftHeader: list[list[list[int]]]
) -> Grid:
    cols = [[b[1] for b in block] for block in topHeader]
    rows = [[b[1] for b in block] for block in leftHeader]
    return Grid(rows, cols)

def getGrid(puzid: int) -> Grid:
    puzzle = getpuzzle(getjs(puzid))
    topHeader = getlolol(puzzle, "topHeader")
    leftHeader = getlolol(puzzle, "leftHeader")
    return toGrid(topHeader, leftHeader)