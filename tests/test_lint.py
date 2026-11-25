"""Task-text lint: the agent-visible fixed text (task descriptions and instructions, tool descriptions, the
contract's names and descriptions, the world's conventions) states no rule. No number and no 4-word phrase
it contains may appear in any must_keep clause. The traveller's request (task input) is per scenario and is
not linted here."""

import ast
import re

import yaml

from helpers import range_text, scenarios
from plugin.guide import CONVENTIONS
from plugin.rules import CONVENTIONS as HANDBOOK_CONVENTIONS
from plugin.world import NO_OFFERS, NO_ROUND_TRIP, NOTE
from plugin_spec import ROOT

# "one" and "two" are left out: the shared template text needs them ("one-way", "for one passenger",
# "between two dates") in every plugin, so they cannot leak a handbook's rule. Digits are always checked.
NUMBER_WORDS = {
    "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "fifteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "hundred", "thousand", "half", "quarter", "once", "twice",
}


def manifest_text():
    data = yaml.safe_load((ROOT / "nanoagent.yaml").read_text(encoding="utf-8"))
    sections = [value for key, value in data.items() if key.startswith(("tools", "tasks"))]
    texts = []
    for section in sections:
        for entry in section.values():
            texts.append(entry["description"])
            texts.append(entry.get("instructions") or "")
    return texts


def contract_text():
    tree = ast.parse((ROOT / "contract.py").read_text(encoding="utf-8"))
    texts = []
    module_doc = ast.get_docstring(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value != module_doc:
            texts.append(node.value.replace("_", " "))
        elif isinstance(node, ast.ClassDef):
            texts.append(re.sub(r"(?<!^)(?=[A-Z])", " ", node.name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            texts.append(node.target.id.replace("_", " "))
    return texts


def visible_texts():
    return manifest_text() + contract_text() + list(CONVENTIONS) + list(HANDBOOK_CONVENTIONS) + [NOTE, NO_ROUND_TRIP, NO_OFFERS]


def words(text):
    return re.findall(r"[a-z]+", text.lower())


def numbers(text):
    found = set(re.findall(r"\d+", text))
    return found | (set(words(text)) & NUMBER_WORDS)


def grams(text, size=4):
    tokens = words(text)
    return {" ".join(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def must_keep_text():
    return [range_text(entry["lines"]) for data in scenarios() for entry in data["must_keep"]]


def test_no_number_of_a_must_keep_clause_is_in_the_task_text():
    clause_numbers = set().union(*(numbers(text) for text in must_keep_text()))
    shared = sorted({number for text in visible_texts() for number in numbers(text)} & clause_numbers)
    assert not shared, f"numbers shared with must_keep clauses: {shared}"


def test_no_four_word_phrase_of_a_must_keep_clause_is_in_the_task_text():
    clause_grams = set().union(*(grams(text) for text in must_keep_text()))
    shared = sorted({gram for text in visible_texts() for gram in grams(text)} & clause_grams)
    assert not shared, f"4-word phrases shared with must_keep clauses: {shared}"


def test_the_lint_sees_the_task_instructions():
    assert any("submit" in text for text in manifest_text())


def test_the_lint_catches_planted_rule_wording():
    clause_grams = set().union(*(grams(text) for text in must_keep_text()))
    planted = "Remember to " + must_keep_text()[0]
    assert grams(planted) & clause_grams
