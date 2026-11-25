"""Scenario ids are visible to the agent (they are the task input's case id), so an id must leak nothing:
no graded value, no boundary number, no rule or role term, no category word."""

import re

import contract
from plugin_spec import ID_CATEGORY_ENUMS, ID_FORBIDDEN_TERMS

GRADED_ENUMS = [contract.Decision, contract.Cabin, contract.ReasonCode, contract.Approver, contract.Clause]
UNIVERSAL_TERMS = {
    "red", "eye", "redeye", "long", "haul", "longhaul", "short", "overnight", "boundary", "threshold", "limit",
    "cap", "edge", "exact", "exactly", "over", "under", "max", "min", "minutes", "hours", "days", "cents",
    "dollars", "approve", "approved", "deny", "denied", "reject", "rejected", "compliant", "noncompliant",
    "violation", "exception", "upgrade", "downgrade", "valid", "invalid", "pass", "fail", "allowed",
    "disallowed", "cheap", "cheapest", "trap", "twin", "flag", "hold", "refuse", "book", "easy", "hard",
    "distractor", "refusal", "hidden", "synonym", "unclear", "ambiguous", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "twenty", "thirty", "hundred",
}


def enum_tokens(enums):
    return {word for enum in enums for member in enum for word in str(member.value).lower().split("_")}


FORBIDDEN = UNIVERSAL_TERMS | enum_tokens(GRADED_ENUMS) | enum_tokens(ID_CATEGORY_ENUMS) | ID_FORBIDDEN_TERMS
IDS = [member.value for member in contract.Scenario]


def test_ids_are_kebab_case_words_without_digits():
    for name in IDS:
        assert re.fullmatch(r"[a-z]+(-[a-z]+)*", name), name


def test_ids_leak_no_answer_term():
    for name in IDS:
        leaked = sorted(set(name.split("-")) & FORBIDDEN)
        assert not leaked, f"{name} leaks {leaked}"


def test_ids_are_unique_and_members_match_values():
    assert len(IDS) == len(set(IDS))
    for member in contract.Scenario:
        assert member.name == member.value.upper().replace("-", "_")
