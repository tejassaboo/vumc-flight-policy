"""verify_input and verify_output for every tool: each output must equal what the bundled data gives."""

from contract import Tool

from .answer import answer_key
from .checks import compared, result
from .guide import requirements
from .scenarios import currency, scenario, trip_record
from .world import LONGEST_BOOKING_DAYS, days_between, is_airport, search, search_note


def verify_input(tool, value):
    if tool == Tool.SEARCH_FLIGHTS:
        for name in ("origin", "destination"):
            code = getattr_free(value, name)
            if not is_airport(code):
                return result(False, f"{name} {code!r} is not an airport this world knows (see booking_requirements)")
        if value.origin == value.destination:
            return result(False, "origin and destination are the same airport")
        trip = scenario(value.scenario)["trip"]
        try:
            ahead = days_between(trip["booking_date"], value.date)
        except ValueError as error:
            return result(False, f"date: {error}")
        if not 0 <= ahead <= LONGEST_BOOKING_DAYS:
            return result(False, f"date must be on or after the booking date {trip['booking_date']} and within the year")
        if value.return_date:
            try:
                back = days_between(value.date, value.return_date)
            except ValueError as error:
                return result(False, f"return_date: {error}")
            if not 0 <= back <= LONGEST_BOOKING_DAYS:
                return result(False, "return_date must be on or after date")
    if tool == Tool.SOLVE_BOOKING and value.request != scenario(value.scenario)["request"]:
        return result(False, "the request is not this scenario's request")
    return result(True, "input is valid")


def getattr_free(value, name):
    """A field of a SearchInput by name, without the getattr builtin a verifier may not use."""
    return {"origin": value.origin, "destination": value.destination}[name]


def verify_output(tool, input_value, output_value):
    if tool == Tool.BOOKING_REQUIREMENTS:
        return compared(tool.value, output_value, requirements(input_value.topic))
    data = scenario(input_value.scenario)
    if tool == Tool.GET_TRIP:
        if output_value.scenario != input_value.scenario or output_value.request != data["request"]:
            return result(False, "get_trip output names another scenario or request")
        return compared(tool.value, output_value.trip, trip_record(data))
    if tool == Tool.SEARCH_FLIGHTS:
        wanted = search(data, input_value.origin, input_value.destination, input_value.date, input_value.return_date)
        if output_value.note != search_note(input_value.return_date, wanted) or output_value.currency != currency():
            return result(False, "search_flights output has another note or currency")
        return result(True, "offers match the bundled world") if output_value.offers == wanted else result(
            False, "search_flights offers differ from the bundled world")
    trip, offers, _, key = answer_key(data)
    if output_value.trip != trip or output_value.offers != offers:
        return result(False, "solve_booking trip or offers differ from the bundled data")
    for name, value in key.items():
        if field_of(output_value, name) != value:
            return result(False, f"solve_booking {name} differs from the rules' answer")
    return result(True, "solve_booking matches the rules' answer")


def field_of(output, name):
    return {
        "decision": output.decision, "offer_ids": output.offer_ids, "cabins": output.cabins,
        "reason_codes": output.reason_codes, "approvers": output.approvers, "clauses": output.clauses,
        "unclear_phrase": output.unclear_phrase, "explanation": output.explanation,
    }[name]
