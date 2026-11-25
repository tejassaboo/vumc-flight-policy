"""What booking_requirements shows, shared byte for byte by the tools (src/plugin/guide.py) and the
verifier (verifier/guide.py): the trip record's fields (from the contract's own descriptions), the
conventions of the simulated world, and its airports."""

import re
import typing

from contract import Airport, FieldHelp, RequirementsOutput, Topic, Trip

from .rules import CONVENTIONS as HANDBOOK_CONVENTIONS
from .world import AIRPORTS

# Conventions no handbook states. They are the world's, never a policy's, so they hold in every plugin.
CONVENTIONS = (
    ("Every time is shown twice: local time at the airport and UTC. Each airport keeps its standard UTC offset "
     "all year in this world, with no daylight saving."),
    "A flight's date is the local date at the airport it leaves from.",
    "Days between two dates are calendar days: the later date minus the earlier one.",
    ("Fares are whole prices in cents for one passenger, taxes included: a search without a return date lists "
     "one-way fares, and a search with one lists round-trip fares (trip_type ROUND_TRIP) that cover the flights "
     "out and back."),
    ("Each case buys one ticket: the one-way fare out on the trip's day to leave, unless the trip record gives a "
     "return date for a round-trip ticket (as for a weekend trip home or a visit), which is then one round-trip "
     "fare; otherwise the trip's return is booked separately and is not part of this decision."),
    "An offer whose seats_available is false is sold out: its price is shown but it cannot be bought.",
    "Offers on the same flights in different cabins share flight numbers and times.",
    "The trip record's booking_date is today in this world.",
)


def kind_name(kind):
    origin = typing.get_origin(kind)
    if origin is list:
        return f"list of {kind_name(typing.get_args(kind)[0])}"
    found = re.fullmatch(r"<(?:class|enum) '(?:[\w]+\.)*(\w+)'>", str(kind))
    return found.group(1) if found else str(kind)


def trip_fields():
    hints = typing.get_type_hints(Trip, include_extras=True)
    fields = []
    for name, hint in hints.items():
        kind, description = typing.get_args(hint)[0], typing.get_args(hint)[1]
        fields.append(FieldHelp(name=name, kind=kind_name(kind), description=description))
    return fields


def requirements(topic):
    airports = [Airport(code=row[0], name=row[1], city=row[2], country=row[3]) for row in AIRPORTS]
    show_fields = topic in (Topic.ALL, Topic.FIELDS)
    return RequirementsOutput(
        fields=trip_fields() if show_fields else [],
        conventions=[*CONVENTIONS, *HANDBOOK_CONVENTIONS] if show_fields else [],
        airports=airports if topic in (Topic.ALL, Topic.AIRPORTS) else [],
    )
