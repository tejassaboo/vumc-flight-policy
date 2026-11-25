"""Flight duration is coded from this handbook's own clause (rules.DURATION_RULES and rules.over), with no
shared default: every threshold is tested on both sides of its boundary, plus the hand-built cases in
plugin_spec.DURATION_CASES (connections included)."""

import pytest

from contract import Cabin
from helpers import range_text
from plugin import rules
from plugin.world import build_segments, make_offer
from plugin_spec import DURATION_CASES

PATH = ["JFK", "ORD", "DEN", "LAX"]


def offer(minutes, layovers):
    path = PATH[: len(minutes) + 1]
    segments, layovers = build_segments("AA", path, "2026-12-10", "08:00", list(minutes), list(layovers), "duration")
    return make_offer("TEST-0000", "AA", Cabin.ECONOMY, 10_000, True, False,
                      (segments, layovers, [False] * len(layovers)), None)


def sides(rule):
    limit = rule["minutes"]
    if rule["operator"] == ">":
        return [(limit, False), (limit + 1, True)]
    if rule["operator"] == ">=":
        return [(limit - 1, False), (limit, True)]
    raise AssertionError(f"unknown operator {rule['operator']}")


@pytest.mark.parametrize("rule", rules.DURATION_RULES, ids=lambda rule: rule["name"])
def test_nonstop_on_both_sides_of_every_boundary(rule):
    for minutes, expected in sides(rule):
        assert rules.over(rule["name"], offer([minutes], [])) is expected, (rule["name"], minutes)


@pytest.mark.parametrize("rule", rules.DURATION_RULES, ids=lambda rule: rule["name"])
def test_every_rule_quotes_its_clause(rule):
    assert " ".join(rule["quote"].split()) in range_text(rule["lines"])


@pytest.mark.parametrize("case", DURATION_CASES, ids=lambda case: f"{case[0]}-{case[1]}-{case[2]}")
def test_hand_built_cases(case):
    name, minutes, layovers, expected = case
    assert rules.over(name, offer(minutes, layovers)) is expected


def test_every_rule_has_hand_built_cases_on_both_sides():
    for rule in rules.DURATION_RULES:
        verdicts = {expected for name, _, _, expected in DURATION_CASES if name == rule["name"]}
        assert {True, False} <= verdicts, rule["name"]
