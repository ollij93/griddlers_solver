"""Tests for the solver module."""

import pytest

from griddlers_solver import Value
import griddlers_solver.solver as solver


@pytest.mark.parametrize("blocks,current,expected", [
    ([], "-", " "),
    ([1], "#-", "# "),
    ([1], "-#", " #"),
    ([1], "-#-", " # "),
    ([1], "--#--", "  #  "),
])
def test_complete_runs(blocks, current, expected):
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    assert solver.complete_runs(blocks, cl) == el

@pytest.mark.parametrize("blocks,current,expected", [
    ([], "-", " "),
    ([1], "-", "-"),
    ([2], "- --", "  --"),
])
def test_empty_sections(blocks, current, expected):
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    assert solver.empty_sections(blocks, cl) == el

@pytest.mark.parametrize("blocks,current,expected", [
    ([], "-", "-"),
    ([1], "-", "#"),
    ([2], "---", "-#-"),
    ([1,2], "-----", "---#-")
])
def test_fill_blocks(blocks, current, expected):
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    assert solver.fill_blocks(blocks, cl) == el

@pytest.mark.parametrize("blocks,current,expected", [
    ([], "-", "-"),
    ([1], "#-", "# "),
    ([1], "-#", " #"),
    ([1], "-#-", " # "),
    ([1], "--#--", "- # -"),
])
def test_complete_blocks(blocks, current: str, expected: str):
    cl = [Value.from_str(x) for x in current]
    el = [Value.from_str(x) for x in expected]
    assert solver.complete_blocks(blocks, cl) == el
