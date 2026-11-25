"""The verifier: the reference answer passes every scenario; every graded field is recomputed, so a wrong
value in any one field fails; a mismatched request, a tampered reference, an unknown offer, task or tool
fail without an exception."""

import dataclasses

import pytest

import verifier
from contract import Approver, BookingOutput, Cabin, Clause, Decision, ReasonCode, Task, Tool
from helpers import build_task_input, first_search, reference, right_answer, scenarios
from plugin_spec import MAX_PASS_ALWAYS_FLAG, MAX_PASS_ALWAYS_LOWEST

TASK = Task.BOOK_FLIGHT.value
ALL = {data["id"]: data for data in scenarios()}
ENUMS = {"decision": Decision, "cabin": Cabin, "reason_code": ReasonCode, "approver": Approver, "clause": Clause}


def accepted(key):
    return {
        "decision": [key.decision], "offer_id": key.offer_ids or [""], "cabin": key.cabins,
        "reason_code": key.reason_codes, "approver": key.approvers, "clause": key.clauses,
    }


@pytest.mark.parametrize("name", sorted(ALL))
def test_reference_answer_passes(name, tmp_path):
    data = ALL[name]
    key = reference(data)
    for pinned in (key, None):
        verdict = verifier.verify_task(TASK, build_task_input(data), right_answer(key), pinned, str(tmp_path))
        assert verdict["valid"] is True and verdict["score"] == 1.0, verdict["message"]


@pytest.mark.parametrize("name", sorted(ALL))
def test_every_accepted_value_passes(name, tmp_path):
    data = ALL[name]
    key = reference(data)
    good = right_answer(key)
    cabin_of = {offer.offer_id: offer.cabin for offer in key.offers}
    for field, values in accepted(key).items():
        for value in values:
            change = {field: value}
            if field == "offer_id" and value:
                change["cabin"] = cabin_of[value]  # the cabin is graded as the chosen offer's own
            if field == "cabin" and key.offer_ids:
                change["offer_id"] = next(offer for offer in key.offer_ids if cabin_of[offer] == value)
            output = dataclasses.replace(good, **change)
            assert verifier.verify_task(TASK, build_task_input(data), output, key, str(tmp_path))["valid"], (field, value)


@pytest.mark.parametrize("name", sorted(ALL))
def test_the_cabin_must_be_the_chosen_offers_own(name, tmp_path):
    data = ALL[name]
    key = reference(data)
    cabin_of = {offer.offer_id: offer.cabin for offer in key.offers}
    for offer_id in key.offer_ids:
        for cabin in key.cabins:
            if cabin == cabin_of[offer_id]:
                continue
            output = dataclasses.replace(right_answer(key), offer_id=offer_id, cabin=cabin)
            verdict = verifier.verify_task(TASK, build_task_input(data), output, key, str(tmp_path))
            assert verdict["valid"] is False and verdict["details"]["wrong"] == ["cabin"], (name, offer_id, cabin)


@pytest.mark.parametrize("name", sorted(ALL))
def test_a_wrong_value_in_any_field_fails(name, tmp_path):
    data = ALL[name]
    key = reference(data)
    good = right_answer(key)
    wanted = accepted(key)
    other_offers = [offer.offer_id for offer in key.offers if offer.offer_id not in key.offer_ids]
    candidates = {"offer_id": other_offers + ["", "NOPE-0000"]}
    for field, enum in ENUMS.items():
        candidates[field] = list(enum)
    for field, values in candidates.items():
        wrong = [value for value in values if value not in wanted[field]]
        assert wrong, f"{name}: no wrong value for {field}"
        for value in wrong:
            verdict = verifier.verify_task(TASK, build_task_input(data), dataclasses.replace(good, **{field: value}), key,
                                           str(tmp_path))
            assert verdict["valid"] is False and field in verdict["details"]["wrong"], (name, field, value)
            assert verdict["score"] == 5 / 6


def test_an_always_flag_or_always_lowest_agent_fails_most_cases(tmp_path):
    passed = {"flag": 0, "lowest": 0}
    for data in ALL.values():
        key = reference(data)
        lowest = min((offer for offer in key.offers if offer.seats_available), key=lambda offer: offer.fare_cents)
        held = right_answer(key) if key.offer_ids else None
        tries = {
            "flag": BookingOutput(Decision.FLAG_FOR_APPROVAL, held.offer_id if held else lowest.offer_id,
                                  held.cabin if held else lowest.cabin, ReasonCode.UNCLEAR_POLICY_TEXT,
                                  Approver.NOT_NAMED, key.clauses[0]),
            "lowest": BookingOutput(Decision.BOOK, lowest.offer_id, lowest.cabin, ReasonCode.LOWEST_FARE, Approver.NONE,
                                    key.clauses[0]),
        }
        for name, output in tries.items():
            passed[name] += verifier.verify_task(TASK, build_task_input(data), output, key, str(tmp_path))["valid"]
    assert passed["flag"] <= MAX_PASS_ALWAYS_FLAG and passed["lowest"] <= MAX_PASS_ALWAYS_LOWEST, passed


def test_a_mismatched_request_fails(tmp_path):
    data = next(iter(ALL.values()))
    key = reference(data)
    given = dataclasses.replace(build_task_input(data), request=data["request"] + " Please hurry.")
    assert verifier.verify_task(TASK, given, right_answer(key), key, str(tmp_path))["valid"] is False


def test_a_tampered_reference_fails(tmp_path):
    data = next(iter(ALL.values()))
    key = reference(data)
    for change in ({"decision": Decision.REFUSE}, {"offer_ids": []}, {"reason_codes": [ReasonCode.COST_SAVINGS]},
                   {"offers": key.offers[:-1]}):
        verdict = verifier.verify_task(TASK, build_task_input(data), right_answer(key), dataclasses.replace(key, **change),
                                       str(tmp_path))
        assert verdict["valid"] is False, change


def test_unknown_task_and_tool_fail_without_raising(tmp_path):
    assert verifier.verify_task("no-such-task", None, None, None, str(tmp_path))["valid"] is False
    assert verifier.verify_input("no_such_tool", None)["valid"] is False
    assert verifier.verify_output("no_such_tool", None, None, str(tmp_path))["valid"] is False


def test_tool_outputs_pass_verify_output(tmp_path):
    from contract import RequirementsInput, Topic, TripInput
    from plugin import booking_requirements, get_trip, search_flights, solve_booking

    for data in ALL.values():
        trip_in = TripInput(scenario=build_task_input(data).scenario)
        assert verifier.verify_output(Tool.GET_TRIP.value, trip_in, get_trip(trip_in), str(tmp_path))["valid"]
        search_in = first_search(data)
        assert verifier.verify_input(Tool.SEARCH_FLIGHTS.value, search_in)["valid"]
        assert verifier.verify_output(Tool.SEARCH_FLIGHTS.value, search_in, search_flights(search_in), str(tmp_path))["valid"]
        task_in = build_task_input(data)
        assert verifier.verify_output(Tool.SOLVE_BOOKING.value, task_in, solve_booking(task_in), str(tmp_path))["valid"]
    for topic in Topic:
        given = RequirementsInput(topic=topic)
        assert verifier.verify_output(Tool.BOOKING_REQUIREMENTS.value, given, booking_requirements(given),
                                      str(tmp_path))["valid"]


def test_a_changed_search_output_fails(tmp_path):
    from plugin import search_flights

    data = next(iter(ALL.values()))
    given = first_search(data)
    made = search_flights(given)
    made.offers[0] = dataclasses.replace(made.offers[0], fare_cents=made.offers[0].fare_cents - 1)
    assert verifier.verify_output(Tool.SEARCH_FLIGHTS.value, given, made, str(tmp_path))["valid"] is False


def test_bad_search_inputs_fail(tmp_path):
    from contract import SearchInput

    data = next(iter(ALL.values()))
    base = first_search(data)
    for change in ({"origin": "XXX"}, {"destination": base.origin}, {"date": "2026-02-30"}, {"date": "2020-01-01"},
                   {"return_date": "2020-01-01"}):
        fields = {"scenario": base.scenario, "origin": base.origin, "destination": base.destination,
                  "date": base.date, "return_date": base.return_date, **change}
        assert verifier.verify_input(Tool.SEARCH_FLIGHTS.value, SearchInput(**fields))["valid"] is False, change
