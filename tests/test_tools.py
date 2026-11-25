"""The tools: every output builds into its contract class, the world is deterministic and plausible, offer
ids say nothing about price, round-trip and off-scenario searches work, and the MCP server implements every
tool."""

import itertools

import pytest
from slimconfig import build_output, plain_output

from contract import TOOLS, RequirementsInput, Scenario, SearchInput, Tool, Topic, TripInput, TripType
from helpers import build_task_input, first_search, scenarios
from plugin import booking_requirements, get_trip, search_flights, solve_booking
from plugin.world import NO_OFFERS, NO_ROUND_TRIP, NOTE, background_offers, date_of, day_number

ALL = scenarios()


def roundtrip(value, kind):
    return build_output(plain_output(value), kind)


def test_every_tool_output_builds_into_its_class():
    for data in ALL:
        trip_in = TripInput(scenario=Scenario(data["id"]))
        assert roundtrip(get_trip(trip_in), TOOLS[Tool.GET_TRIP][1]) == get_trip(trip_in)
        search_in = first_search(data)
        assert roundtrip(search_flights(search_in), TOOLS[Tool.SEARCH_FLIGHTS][1]) == search_flights(search_in)
        key = solve_booking(build_task_input(data))
        assert roundtrip(key, TOOLS[Tool.SOLVE_BOOKING][1]) == key
    for topic in Topic:
        made = booking_requirements(RequirementsInput(topic=topic))
        assert roundtrip(made, TOOLS[Tool.BOOKING_REQUIREMENTS][1]) == made


def test_offer_ids_are_unique_and_unrelated_to_price():
    for data in ALL:
        offers = solve_booking(build_task_input(data)).offers
        ids = [offer.offer_id for offer in offers]
        assert len(ids) == len(set(ids))
    sample = [offer for data in ALL for offer in solve_booking(build_task_input(data)).offers]
    by_id = [offer.fare_cents for offer in sorted(sample, key=lambda offer: offer.offer_id)]
    rises = sum(later > earlier for earlier, later in itertools.pairwise(by_id))
    assert 0.3 < rises / (len(by_id) - 1) < 0.7


def test_off_scenario_searches_follow_the_background_setting():
    from plugin.scenarios import handbook

    data = ALL[0]
    booking = data["trip"]["booking_date"]
    made = search_flights(SearchInput(scenario=Scenario(data["id"]), origin="BOS", destination="ORD", date=booking,
                                      return_date=""))
    assert bool(made.offers) == (handbook()["background_offers"] > 0)
    assert made.note == (NOTE if made.offers else f"{NOTE} {NO_OFFERS}")
    assert all(offer.trip_type == TripType.ONE_WAY for offer in made.offers)


def test_round_trip_background_offers():
    made = background_offers("any", ("BOS", "LHR", "2026-12-10", "2026-12-14"), 3, [])
    assert made and all(offer.trip_type == TripType.ROUND_TRIP for _, offer in made)
    assert all(offer.return_segments[0].origin == "LHR" and offer.return_segments[-1].destination == "BOS"
               for _, offer in made)
    assert all(offer.return_segments[0].depart_local.startswith("2026-12-14") for _, offer in made)


def test_a_round_trip_search_in_a_one_way_case_lists_nothing_and_says_so(tmp_path):
    import verifier

    for data in ALL:
        if any(search.get("return_date") for search in data["world"]["searches"]):
            continue
        out = first_search(data)
        back = date_of(day_number(out.date) + 2)
        asked = SearchInput(scenario=out.scenario, origin=out.origin, destination=out.destination, date=out.date,
                            return_date=back)
        made = search_flights(asked)
        assert made.offers == [] and made.note == f"{NOTE} {NO_ROUND_TRIP}", data["id"]
        assert verifier.verify_output(Tool.SEARCH_FLIGHTS.value, asked, made, str(tmp_path))["valid"], data["id"]
        assert search_flights(out).note == NOTE, data["id"]


def test_bad_searches_raise():
    data = ALL[0]
    base = first_search(data)
    for origin, destination, date in (("XXX", "ORD", base.date), ("BOS", "BOS", base.date), ("BOS", "ORD", "2020-01-01")):
        with pytest.raises(ValueError):
            search_flights(SearchInput(scenario=base.scenario, origin=origin, destination=destination, date=date,
                                       return_date=""))


def test_solve_refuses_another_request():
    data = ALL[0]
    with pytest.raises(ValueError):
        solve_booking(build_task_input({**data, "request": "something else"}))


def test_server_implements_every_tool():
    from plugin.__main__ import IMPLEMENTATIONS

    assert set(IMPLEMENTATIONS) == set(Tool)


def test_requirements_topics():
    everything = booking_requirements(RequirementsInput(topic=Topic.ALL))
    assert everything.fields and everything.conventions and everything.airports
    assert not booking_requirements(RequirementsInput(topic=Topic.AIRPORTS)).fields
    assert not booking_requirements(RequirementsInput(topic=Topic.FIELDS)).airports
