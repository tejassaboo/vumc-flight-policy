"""The tools: each a plain function from its contract input to its contract output. They read only the
bundled data and write nothing. Shared by every plugin made from the original-handbook template."""

from contract import (
    RequirementsInput,
    RequirementsOutput,
    SearchInput,
    SearchOutput,
    SolveOutput,
    TaskInput,
    TripInput,
    TripOutput,
)

from .answer import answer_key
from .guide import requirements
from .scenarios import currency, scenario, trip_record
from .world import search, search_note


def booking_requirements(value: RequirementsInput) -> RequirementsOutput:
    return requirements(value.topic)


def get_trip(value: TripInput) -> TripOutput:
    data = scenario(value.scenario)
    return TripOutput(scenario=value.scenario, request=data["request"], trip=trip_record(data))


def search_flights(value: SearchInput) -> SearchOutput:
    data = scenario(value.scenario)
    offers = search(data, value.origin, value.destination, value.date, value.return_date)
    return SearchOutput(note=search_note(value.return_date, offers), currency=currency(), offers=offers)


def solve_booking(value: TaskInput) -> SolveOutput:
    data = scenario(value.scenario)
    if value.request != data["request"]:
        raise ValueError("the request is not this scenario's request")
    trip, offers, _, key = answer_key(data)
    return SolveOutput(trip=trip, offers=offers, **key)
