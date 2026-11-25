"""Scenario metadata: size and mix, overlays, flag quota and twins, one scenario per unclear phrase, the
hand-written expected answers equal what the rules compute, and every must_keep range resolves in the
FROZEN text with the hash of its words."""

import json
import math
from collections import Counter

import pytest
from slimconfig import plain_output

from contract import Clause, Decision, ReasonCode, Scenario
from helpers import DATA, POLICY_LINES, range_hash, range_text, scenarios
from plugin import rules
from plugin.answer import answer_key
from plugin_spec import MIX, OVERLAY_MINIMUMS

KEYS = {"id", "category", "overlays", "twin_of", "twin_fact", "flag_twins", "ambiguity_note", "request", "trip",
        "world", "expected", "must_keep", "distractors", "design_notes"}
EXPECTED_KEYS = {"decision", "offer_slots", "cabins", "reason_codes", "approvers", "clauses", "unclear_phrase"}
ALL = scenarios()
BY_ID = {data["id"]: data for data in ALL}
FACTS = json.loads((DATA / "handbook.json").read_text(encoding="utf-8"))


def test_files_ids_and_count_agree():
    files = sorted(path.stem for path in (DATA / "scenarios").glob("*.json"))
    assert files == sorted(member.value for member in Scenario)
    assert len(ALL) == FACTS["scenario_count"] == sum(MIX.values())
    for data in ALL:
        assert KEYS <= set(data) <= KEYS | {"answer_key_inputs"}, data["id"]
        assert set(data["expected"]) == EXPECTED_KEYS, data["id"]


def test_hidden_answer_key_inputs_never_reach_the_agent():
    from contract import TripInput
    from plugin import get_trip

    for data in ALL:
        hidden = data.get("answer_key_inputs", {})
        shown = json.dumps(plain_output(get_trip(TripInput(scenario=Scenario(data["id"])))))
        for value in hidden.values():
            assert json.dumps(value) not in shown or not isinstance(value, str), (data["id"], value)


def test_mix_by_primary_category():
    assert Counter(data["category"] for data in ALL) == Counter(MIX)


def test_overlay_minimums():
    counts = Counter(tag for data in ALL for tag in data["overlays"])
    for tag, least in OVERLAY_MINIMUMS.items():
        assert counts[tag] >= least, f"overlay {tag}: {counts[tag]} < {least}"


def test_flag_quota():
    flags = [data for data in ALL if data["expected"]["decision"] == Decision.FLAG_FOR_APPROVAL.value]
    assert len(flags) >= 2
    assert len(flags) <= math.floor(0.15 * len(ALL)), f"{len(flags)} flags is over 15% of {len(ALL)}"
    assert all(data["category"] == "flag" for data in flags)
    assert len(flags) == MIX["flag"]


def test_every_flag_has_clear_twins_on_both_sides():
    for data in ALL:
        if data["category"] != "flag":
            assert data["flag_twins"] == []
            continue
        twins = data["flag_twins"]
        assert len(twins) == 2 and len(set(twins)) == 2, data["id"]
        for twin in twins:
            other = BY_ID[twin]
            assert other["expected"]["decision"] != Decision.FLAG_FOR_APPROVAL.value, (data["id"], twin)
            assert other["expected"]["unclear_phrase"] == "", (data["id"], twin)
        assert BY_ID[twins[0]]["expected"] != BY_ID[twins[1]]["expected"], f"{data['id']}: twins on one side"


def test_one_scenario_per_unclear_phrase_and_holds_are_either_unclear_or_approval():
    phrases = Counter(data["expected"]["unclear_phrase"] for data in ALL if data["expected"]["unclear_phrase"])
    assert all(count == 1 for count in phrases.values()), phrases
    for data in ALL:
        expected, note = data["expected"], data["ambiguity_note"]
        if expected["unclear_phrase"]:
            assert expected["decision"] == Decision.FLAG_FOR_APPROVAL.value
            assert isinstance(note, dict) and note["phrase"] == expected["unclear_phrase"], data["id"]
            assert len(note["readings"]) == 2, data["id"]
            # A hold over unclear words: UNCLEAR_POLICY_TEXT, possibly with APPROVAL_REQUIRED beside it.
            assert ReasonCode.UNCLEAR_POLICY_TEXT.value in expected["reason_codes"], data["id"]
            assert set(expected["reason_codes"]) <= {ReasonCode.UNCLEAR_POLICY_TEXT.value,
                                                     ReasonCode.APPROVAL_REQUIRED.value}, data["id"]
        elif expected["decision"] == Decision.FLAG_FOR_APPROVAL.value:
            # A hold over a missing sign-off: APPROVAL_REQUIRED, possibly beside the reason that calls for it.
            assert ReasonCode.APPROVAL_REQUIRED.value in expected["reason_codes"], data["id"]
            assert ReasonCode.UNCLEAR_POLICY_TEXT.value not in expected["reason_codes"], data["id"]
            assert isinstance(note, str) and note.startswith("none"), data["id"]
        else:
            assert note == "none", data["id"]


def test_a_return_date_on_file_means_a_pinned_round_trip():
    """One ticket per case: a trip record gives a return date (a field named return_date, if the handbook's
    record has one) only when the case's ticket is a round trip, which a pinned search then prices."""
    for data in ALL:
        if data["trip"].get("return_date"):
            assert any(search.get("return_date") for search in data["world"]["searches"]), data["id"]


def test_approval_required_is_never_no_compliant_offer():
    for data in ALL:
        decision, reasons = data["expected"]["decision"], set(data["expected"]["reason_codes"])
        if decision == Decision.FLAG_FOR_APPROVAL.value:
            assert ReasonCode.NO_COMPLIANT_OFFER.value not in reasons, data["id"]
        if decision == Decision.REFUSE.value:
            assert not reasons & {ReasonCode.APPROVAL_REQUIRED.value, ReasonCode.UNCLEAR_POLICY_TEXT.value}, data["id"]
        if decision == Decision.BOOK.value:
            assert not reasons & {ReasonCode.APPROVAL_REQUIRED.value, ReasonCode.UNCLEAR_POLICY_TEXT.value}, data["id"]


def test_twins_point_at_real_scenarios_and_boundary_twins_are_mutual():
    for data in ALL:
        twin = data["twin_of"]
        if data["category"] == "boundary_twin":
            assert twin and BY_ID[twin]["twin_of"] == data["id"], data["id"]
            assert BY_ID[twin]["category"] == "boundary_twin"
        if twin:
            assert twin in BY_ID and twin != data["id"] and data["twin_fact"], data["id"]
            assert BY_ID[twin]["expected"] != data["expected"], f"{data['id']}: a twin with the same answer"


def plain_key(data):
    _, _, slots, key = answer_key(data)
    return {
        "decision": key["decision"].value,
        "offer_slots": sorted(slots[offer] for offer in key["offer_ids"]),
        "cabins": sorted(cabin.value for cabin in key["cabins"]),
        "reason_codes": sorted(code.value for code in key["reason_codes"]),
        "approvers": sorted(role.value for role in key["approvers"]),
        "clauses": sorted(clause.value for clause in key["clauses"]),
        "unclear_phrase": key["unclear_phrase"],
    }


@pytest.mark.parametrize("name", sorted(BY_ID))
def test_expected_answer_equals_the_rules(name):
    data = BY_ID[name]
    expected = {key: sorted(value) if isinstance(value, list) else value for key, value in data["expected"].items()}
    assert plain_key(data) == expected


@pytest.mark.parametrize("name", sorted(BY_ID))
def test_must_keep_ranges_resolve_in_the_frozen_text(name):
    data = BY_ID[name]
    assert data["must_keep"], f"{name}: the expected answer cites no clause"
    for entry in data["must_keep"]:
        start, end = entry["lines"]
        assert 1 <= start <= end <= len(POLICY_LINES), (name, entry["lines"])
        assert entry["sha256"] == range_hash(entry["lines"]), (name, entry["lines"])
        assert entry["quote"] and " ".join(entry["quote"].split()) in range_text(entry["lines"]), (name, entry["lines"])
    for entry in data["distractors"]:
        assert " ".join(entry["quote"].split()) in range_text(entry["lines"]), (name, entry["lines"])


def test_every_section_code_names_a_heading_of_the_frozen_text():
    assert set(rules.CLAUSE_HEADINGS) == set(Clause)
    stripped = [line.strip() for line in POLICY_LINES]
    for clause, heading in rules.CLAUSE_HEADINGS.items():
        assert heading in stripped, (clause, heading)


def test_cited_sections_are_closed_list_members():
    for data in ALL:
        for value in data["expected"]["clauses"]:
            Clause(value)
