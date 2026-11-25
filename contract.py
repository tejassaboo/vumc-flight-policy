"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only.

The first part is the original-handbook template's shared contract and is the same in every plugin made from
it. The HANDBOOK-SPECIFIC part in the middle is filled per handbook: the scenario ids, the closed lists of
approvers and sections, and the trip record; the shared inputs and outputs after it refer to those names.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output

# ---------------------------------------------------------------------------------------------------------
# SHARED (template): keep identical across plugins, except the agent task's id in Task.BOOK_FLIGHT.
# ---------------------------------------------------------------------------------------------------------


class Tool(Enum):
    BOOKING_REQUIREMENTS = "booking_requirements"
    GET_TRIP = "get_trip"
    SEARCH_FLIGHTS = "search_flights"
    SOLVE_BOOKING = "solve_booking"


class Task(Enum):
    BOOKING_REQUIREMENTS = "booking-requirements"
    SEARCH_FLIGHTS = "search-flights"
    BOOK_FLIGHT = "book-vumc-flight"


class Decision(Enum):
    BOOK = "BOOK"
    REFUSE = "REFUSE"
    FLAG_FOR_APPROVAL = "FLAG_FOR_APPROVAL"


class Cabin(Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    NONE = "NONE"


class ReasonCode(Enum):
    """Why the decision was made. The list is shared by every handbook plugin, so it also holds reasons
    that a given handbook never uses."""

    LOWEST_FARE = "LOWEST_FARE"
    UPGRADE_NOT_ELIGIBLE = "UPGRADE_NOT_ELIGIBLE"
    CLIENT_REIMBURSABLE = "CLIENT_REIMBURSABLE"
    UPGRADE_WITHIN_FARE_MARGIN = "UPGRADE_WITHIN_FARE_MARGIN"
    MEDICAL_NEED = "MEDICAL_NEED"
    COST_SAVINGS = "COST_SAVINGS"
    NO_ECONOMY_SEATS_URGENT = "NO_ECONOMY_SEATS_URGENT"
    TRAVELER_PAYS_UPGRADE = "TRAVELER_PAYS_UPGRADE"
    LONG_FLIGHT_APPROVED = "LONG_FLIGHT_APPROVED"
    LONG_FLIGHT_CONDITION_NOT_MET = "LONG_FLIGHT_CONDITION_NOT_MET"
    PREMIUM_ECONOMY_ALLOWED = "PREMIUM_ECONOMY_ALLOWED"
    UPGRADE_COST_NOT_NOMINAL = "UPGRADE_COST_NOT_NOMINAL"
    ALTERNATE_ROUTE_WITHIN_MARGIN = "ALTERNATE_ROUTE_WITHIN_MARGIN"
    ALTERNATE_ROUTE_TOO_EXPENSIVE = "ALTERNATE_ROUTE_TOO_EXPENSIVE"
    LOYALTY_PROGRAM_PREFERENCE = "LOYALTY_PROGRAM_PREFERENCE"
    COMPANION_NOT_COVERED = "COMPANION_NOT_COVERED"
    PERSONAL_TRAVEL_NOT_COVERED = "PERSONAL_TRAVEL_NOT_COVERED"
    OUTSIDE_POLICY_SCOPE = "OUTSIDE_POLICY_SCOPE"
    NO_COMPLIANT_OFFER = "NO_COMPLIANT_OFFER"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    UNCLEAR_POLICY_TEXT = "UNCLEAR_POLICY_TEXT"
    ADVANCE_PURCHASE_TOO_LATE = "ADVANCE_PURCHASE_TOO_LATE"
    DISTANCE_BELOW_MINIMUM = "DISTANCE_BELOW_MINIMUM"
    DRIVING_EXPECTED = "DRIVING_EXPECTED"
    RAIL_PREFERRED = "RAIL_PREFERRED"
    REFUNDABLE_FARE_NOT_ALLOWED = "REFUNDABLE_FARE_NOT_ALLOWED"
    PREFERRED_CARRIER_REQUIRED = "PREFERRED_CARRIER_REQUIRED"
    CONNECTION_TOO_LONG = "CONNECTION_TOO_LONG"
    OVERNIGHT_STOP_REQUIRED = "OVERNIGHT_STOP_REQUIRED"
    NATIONAL_CARRIER_REQUIRED = "NATIONAL_CARRIER_REQUIRED"
    SENIOR_ROLE_ENTITLEMENT = "SENIOR_ROLE_ENTITLEMENT"
    INTERNATIONAL_LONG_FLIGHT = "INTERNATIONAL_LONG_FLIGHT"
    TRAVELLER_LIMIT_PER_FLIGHT = "TRAVELLER_LIMIT_PER_FLIGHT"
    # HANDBOOK-SPECIFIC reason codes go below this line; keep every shared one above.
    FLY_AMERICA_US_CARRIER_REQUIRED = "FLY_AMERICA_US_CARRIER_REQUIRED"
    OPEN_SKIES_AGREEMENT = "OPEN_SKIES_AGREEMENT"
    PRIVATE_AIRCRAFT_NOT_APPROVED = "PRIVATE_AIRCRAFT_NOT_APPROVED"
    BOOKING_TOOL_REQUIRED = "BOOKING_TOOL_REQUIRED"
    SPONSOR_RESTRICTION = "SPONSOR_RESTRICTION"
    POLICY_EXCEPTION_APPROVED = "POLICY_EXCEPTION_APPROVED"
    # Decoys: codes for rules of other handbooks that this one lacks, so the list hints at none of its own rules.
    WEEKEND_TRAVEL_HOME = "WEEKEND_TRAVEL_HOME"
    NEXT_OF_KIN_TRAVEL = "NEXT_OF_KIN_TRAVEL"
    CREATIVE_TICKETING = "CREATIVE_TICKETING"
    DENIED_BOARDING_NOT_ALLOWED = "DENIED_BOARDING_NOT_ALLOWED"
    CHANCELLOR_WRITTEN_AUTHORIZATION = "CHANCELLOR_WRITTEN_AUTHORIZATION"
    DOUBLE_BOOKING_PROHIBITED = "DOUBLE_BOOKING_PROHIBITED"
    CANDIDATE_TRIP_NOT_COVERED = "CANDIDATE_TRIP_NOT_COVERED"
    SAME_CLASS_AS_CUSTOMER = "SAME_CLASS_AS_CUSTOMER"


class TripType(Enum):
    ONE_WAY = "ONE_WAY"
    ROUND_TRIP = "ROUND_TRIP"


class Topic(Enum):
    ALL = "ALL"
    FIELDS = "FIELDS"
    AIRPORTS = "AIRPORTS"


CODE = "An IATA airport code, e.g. JFK"


@dataclass
class Airport(Output):
    code: Annotated[str, CODE]
    name: Annotated[str, "The airport's name"]
    city: Annotated[str, "The city it serves"]
    country: Annotated[str, "Its country, as an ISO code"]


@dataclass
class Segment(Output):
    flight_number: Annotated[str, "The airline's flight number, e.g. BA 117"]
    origin: Annotated[str, CODE]
    destination: Annotated[str, CODE]
    depart_local: Annotated[str, "When it leaves: YYYY-MM-DD HH:MM, local time at that airport"]
    arrive_local: Annotated[str, "When it lands: YYYY-MM-DD HH:MM, local time at that airport"]
    depart_utc: Annotated[str, "When it leaves: YYYY-MM-DD HH:MM, UTC"]
    arrive_utc: Annotated[str, "When it lands: YYYY-MM-DD HH:MM, UTC"]
    scheduled_minutes: Annotated[int, "Its scheduled time from departure to arrival, in minutes"]


@dataclass
class Offer(Output):
    offer_id: Annotated[str, "The offer's id, to submit when booking or holding it"]
    carrier: Annotated[str, "The airline"]
    trip_type: Annotated[TripType, "ONE_WAY, or ROUND_TRIP when the fare covers the flights out and back"]
    cabin: Annotated[Cabin, "The cabin sold on every flight of the offer"]
    fare_cents: Annotated[int, "The whole fare for one passenger, in cents of the search's currency"]
    seats_available: Annotated[bool, "False when this cabin is sold out on these flights: it is listed but cannot be bought"]
    refundable: Annotated[bool, "Whether the fare can be refunded or changed without a fee"]
    stops: Annotated[int, "Connections on the way out; zero for a nonstop"]
    segments: Annotated[list[Segment], "The flights out, in order"]
    layover_minutes: Annotated[list[int], "Minutes on the ground between consecutive flights out"]
    stopover_nights: Annotated[list[bool], "Per connection out: true when it is a ticketed stopover with a hotel night booked"]
    flying_minutes: Annotated[int, "The flights' scheduled minutes out added together, ground time left out"]
    elapsed_minutes: Annotated[int, "Minutes from the first departure out to the last arrival, ground time included"]
    return_segments: Annotated[list[Segment], "For a round trip, the flights back, in order; empty otherwise"]
    return_layover_minutes: Annotated[list[int], "Minutes on the ground between consecutive flights back"]
    return_stopover_nights: Annotated[list[bool], "Per connection back: true for a ticketed stopover with a hotel night"]
    return_flying_minutes: Annotated[int, "The flights' scheduled minutes back added together; zero one way"]
    return_elapsed_minutes: Annotated[int, "Minutes from the first departure back to the last arrival; zero one way"]


# ---------------------------------------------------------------------------------------------------------
# HANDBOOK-SPECIFIC: Vanderbilt University Medical Center Finance Policy FIN 4.7, Travel (effective June 2021).
# ---------------------------------------------------------------------------------------------------------


class Scenario(Enum):
    AMBER_LOOM = "amber-loom"
    BIRCH_EMBER = "birch-ember"
    CEDAR_QUILL = "cedar-quill"
    DUNE_HARROW = "dune-harrow"
    FERN_GABLE = "fern-gable"
    GORSE_INLET = "gorse-inlet"
    HAZEL_MARSH = "hazel-marsh"
    IRIS_NOOK = "iris-nook"
    JUNIPER_CREST = "juniper-crest"
    KESTREL_MOOR = "kestrel-moor"
    LUMEN_SORREL = "lumen-sorrel"
    MAPLE_TOR = "maple-tor"
    NETTLE_QUAY = "nettle-quay"
    ORIOLE_SHINGLE = "oriole-shingle"
    POPLAR_VANE = "poplar-vane"
    QUILL_SADDLE = "quill-saddle"
    ROOK_TALLOW = "rook-tallow"
    SABLE_WREN = "sable-wren"
    THISTLE_COVE = "thistle-cove"
    UMBER_CASK = "umber-cask"
    VETCH_ORCHARD = "vetch-orchard"
    WILLOW_BRINE = "willow-brine"
    YARROW_FLINT = "yarrow-flint"
    ZINNIA_COBBLE = "zinnia-cobble"


class Approver(Enum):
    """Roles that may sign off. NONE: the decision relies on no one's sign-off, given or awaited (one for
    something else may be on file). NOT_NAMED: one is needed, but the handbook names no role."""

    NONE = "NONE"
    NOT_NAMED = "NOT_NAMED"
    SUPERVISOR = "SUPERVISOR"
    OFFICER = "OFFICER"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    BUSINESS_ADMINISTRATOR = "BUSINESS_ADMINISTRATOR"
    CHIEF_OPERATING_OFFICER = "CHIEF_OPERATING_OFFICER"
    CHIEF_FINANCIAL_OFFICER = "CHIEF_FINANCIAL_OFFICER"
    DISABILITY_SERVICES = "DISABILITY_SERVICES"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    EXPORT_COMPLIANCE = "EXPORT_COMPLIANCE"
    TRAVEL_OFFICE = "TRAVEL_OFFICE"
    GRANT_ACCOUNTING = "GRANT_ACCOUNTING"
    FINANCE_POLICY_OFFICE = "FINANCE_POLICY_OFFICE"
    CHIEF_EXECUTIVE = "CHIEF_EXECUTIVE"
    DEAN = "DEAN"
    PROVOST = "PROVOST"
    HUMAN_RESOURCES = "HUMAN_RESOURCES"


class Clause(Enum):
    """The handbook's sections, by heading."""

    PURPOSE = "PURPOSE"
    SCOPE = "SCOPE"
    DEFINITIONS = "DEFINITIONS"
    POLICY = "POLICY"
    AIR_TRAVEL = "AIR_TRAVEL"
    AIR_RESERVATIONS = "AIR_RESERVATIONS"
    FARES_AND_CLASS = "FARES_AND_CLASS"
    CHANGES_AND_UNUSED_TICKETS = "CHANGES_AND_UNUSED_TICKETS"
    PRE_TRAVEL_REIMBURSEMENT = "PRE_TRAVEL_REIMBURSEMENT"
    BAGGAGE_FEES = "BAGGAGE_FEES"
    PRIVATE_AIRCRAFT = "PRIVATE_AIRCRAFT"
    FEDERALLY_FUNDED_AIRLINES = "FEDERALLY_FUNDED_AIRLINES"
    HOTELS = "HOTELS"
    AUTOMOBILE_RENTAL = "AUTOMOBILE_RENTAL"
    LOCAL_TRANSPORTATION = "LOCAL_TRANSPORTATION"
    BUS_OR_RAIL = "BUS_OR_RAIL"
    PERSONAL_AUTOMOBILE = "PERSONAL_AUTOMOBILE"
    MEALS_AND_ENTERTAINMENT = "MEALS_AND_ENTERTAINMENT"
    INSURANCE_AND_RISK = "INSURANCE_AND_RISK"
    INTERNATIONAL_ASSISTANCE = "INTERNATIONAL_ASSISTANCE"
    COMPANION_EXPENSES = "COMPANION_EXPENSES"
    COMPANION_TRAVEL = "COMPANION_TRAVEL"
    OTHER_CONSIDERATIONS = "OTHER_CONSIDERATIONS"
    APPROVAL_TO_TRAVEL = "APPROVAL_TO_TRAVEL"
    RECEIPTS = "RECEIPTS"
    PASSPORTS_AND_VISAS = "PASSPORTS_AND_VISAS"
    COMBINED_PERSONAL_AND_BUSINESS = "COMBINED_PERSONAL_AND_BUSINESS"
    LAUNDRY = "LAUNDRY"
    REWARD_POINTS = "REWARD_POINTS"
    UNALLOWABLE_EXPENSES = "UNALLOWABLE_EXPENSES"
    DUTY_OF_CARE = "DUTY_OF_CARE"
    HOME_OFFICE = "HOME_OFFICE"


class Passenger(Enum):
    EMPLOYEE = "EMPLOYEE"
    COMPANION = "COMPANION"


class Purpose(Enum):
    CONFERENCE = "CONFERENCE"
    RESEARCH_MEETING = "RESEARCH_MEETING"
    SITE_VISIT = "SITE_VISIT"
    BOARD_MEETING = "BOARD_MEETING"
    TRAINING = "TRAINING"
    RECRUITING = "RECRUITING"
    PERSONAL = "PERSONAL"


class Funding(Enum):
    DEPARTMENT_FUNDS = "DEPARTMENT_FUNDS"
    FEDERAL_AWARD = "FEDERAL_AWARD"
    NONFEDERAL_AWARD = "NONFEDERAL_AWARD"


class OutsideOption(Enum):
    NONE = "NONE"
    AIRLINE_WEBSITE = "AIRLINE_WEBSITE"
    PRIVATE_AIRCRAFT = "PRIVATE_AIRCRAFT"


class SignOffSubject(Enum):
    TRIP = "TRIP"
    PREMIUM_CABIN = "PREMIUM_CABIN"
    MEDICAL_JUSTIFICATION = "MEDICAL_JUSTIFICATION"
    POLICY_EXCEPTION = "POLICY_EXCEPTION"
    INTERNATIONAL_QUESTIONNAIRE = "INTERNATIONAL_QUESTIONNAIRE"
    PRIVATE_AIRCRAFT = "PRIVATE_AIRCRAFT"


@dataclass
class SignOff(Output):
    role: Annotated[Approver, "The signer's role"]
    name: Annotated[str, "Their name"]
    title: Annotated[str, "Their job title"]
    subject: Annotated[
        SignOffSubject,
        "What they signed off: the trip itself, a business or first-class seat, a documented medical "
        "justification, an exception to the travel policy, the international travel questionnaire, or flying "
        "on a plane that is not an airline's",
    ]
    subject_to_policy: Annotated[
        bool, "True when the signer approved only on condition that the trip meets the travel policy's own requirements for it"
    ]
    terms: Annotated[str, "What the sign-off says, in plain words"]


@dataclass
class Colleague(Output):
    name: Annotated[str, "The colleague's name"]
    title: Annotated[str, "Their job title"]
    flight_number: Annotated[str, "The flight they are ticketed on, e.g. DL 1520"]
    date: Annotated[str, "That flight's local departure date, YYYY-MM-DD"]
    cabin: Annotated[Cabin, "The cabin they are ticketed in"]


@dataclass
class Trip(Output):
    traveller_name: Annotated[str, "Who flies"]
    traveller_title: Annotated[str, "Their job title, or their relation to the employee they go with"]
    passenger: Annotated[Passenger, "What the person flying is to the organisation"]
    accompanies: Annotated[str, "The employee this person goes with, when the person flying is not an employee; empty otherwise"]
    origin: Annotated[Airport, "Where the flight leaves from"]
    destination: Annotated[Airport, "Where it goes"]
    travel_date: Annotated[str, "The day to leave, YYYY-MM-DD: the local date at the origin airport"]
    return_date: Annotated[
        str,
        "For a round-trip ticket, the day to fly back, YYYY-MM-DD, local at the destination; empty when the case "
        "buys a one-way fare",
    ]
    booking_date: Annotated[str, "Today in this world, the day the request is made and the ticket bought, YYYY-MM-DD"]
    must_arrive_by: Annotated[
        str,
        "The latest local time at the destination, YYYY-MM-DD HH:MM, by which the traveller has to land for the "
        "trip's work; empty when the record names none",
    ]
    purpose: Annotated[str, "Why the trip is made, in plain words"]
    purpose_kind: Annotated[Purpose, "The kind of trip"]
    funding: Annotated[Funding, "What pays for the trip: the traveller's department, or a research award from a federal agency or from another sponsor"]
    sponsor: Annotated[str, "Who made the paying award, in plain words; empty for department funds"]
    sponsor_terms: Annotated[list[str], "What the paying award's own terms say about travel, in plain words; empty when they say nothing"]
    requested_cabin: Annotated[Cabin, "The cabin the traveller asks the organisation to buy"]
    preferred_airline: Annotated[str, "The airline the traveller asks to fly, as search_flights names airlines; empty when none"]
    self_paid_upgrade: Annotated[
        Cabin, "A better cabin the traveller will get at their own cost or with their own points once the ticket is bought; NONE when none"
    ]
    outside_option: Annotated[OutsideOption, "A way of flying the traveller asks about that search_flights does not list; NONE when none"]
    outside_option_detail: Annotated[str, "That way of flying, in plain words; empty when none"]
    sign_offs: Annotated[list[SignOff], "Sign-offs already on file for this trip, each given in writing before today"]
    travelling_with: Annotated[list[Colleague], "Colleagues ticketed on flights of this route and date for the same trip; empty when none"]
    notes: Annotated[list[str], "Other facts on file about the trip, in plain words; empty when none"]


# ---------------------------------------------------------------------------------------------------------
# SHARED (template), continued: the tools' and tasks' inputs and outputs.
# ---------------------------------------------------------------------------------------------------------


@dataclass
class TaskInput(Output):
    scenario: Annotated[Scenario, "The booking request's case id"]
    request: Annotated[str, "The traveller's request, in their own words"]


@dataclass
class TripInput(Output):
    scenario: Annotated[Scenario, "The booking request's case id, as the task input gives it"]


@dataclass
class TripOutput(Output):
    scenario: Annotated[Scenario, "The case id"]
    request: Annotated[str, "The traveller's request, in their own words"]
    trip: Annotated[Trip, "The trip record behind the request"]


@dataclass
class SearchInput(Output):
    scenario: Annotated[Scenario, "The booking request's case id"]
    origin: Annotated[str, "The airport to leave from: An IATA airport code, e.g. JFK"]
    destination: Annotated[str, "The airport to fly to: An IATA airport code, e.g. JFK"]
    date: Annotated[str, "The day to leave, YYYY-MM-DD: the local date at the origin airport, on or after the booking date"]
    return_date: Annotated[str, "For round-trip fares, the day to fly back, YYYY-MM-DD, local at the destination; empty for one way"]


@dataclass
class SearchOutput(Output):
    note: Annotated[str, "Where the offers come from, and a word when this case lists none for the search"]
    currency: Annotated[str, "The currency of every fare, as an ISO code"]
    offers: Annotated[list[Offer], "Every offer leaving on that local date, in departure order"]


@dataclass
class BookingOutput(Output):
    decision: Annotated[
        Decision,
        "BOOK: buy offer_id now. REFUSE: buy nothing, because the organisation buys no ticket at all for this request. "
        "FLAG_FOR_APPROVAL: hold offer_id and buy nothing yet, because someone must approve it first or "
        "the handbook's words leave the answer open",
    ]
    offer_id: Annotated[str, "The offer bought or held, exactly as search_flights listed it; empty when refusing"]
    cabin: Annotated[Cabin, "That offer's cabin; NONE when refusing"]
    reason_code: Annotated[ReasonCode, "Why, from the closed list"]
    approver: Annotated[
        Approver,
        "The role whose sign-off this decision relies on, whether already on file or still awaited; NONE when "
        "this decision relies on no one's sign-off, even if a sign-off for something else is on file; NOT_NAMED "
        "when a sign-off is needed but the handbook names no role",
    ]
    clause: Annotated[Clause, "The handbook section the decision rests on"]


@dataclass
class SolveOutput(Output):
    trip: Annotated[Trip, "The trip record"]
    offers: Annotated[list[Offer], "Every offer on the trip's route and date"]
    decision: Annotated[Decision, "The correct decision"]
    offer_ids: Annotated[list[str], "Every offer id that is a correct choice; empty when refusing"]
    cabins: Annotated[list[Cabin], "Every correct cabin"]
    reason_codes: Annotated[list[ReasonCode], "Every accepted reason"]
    approvers: Annotated[list[Approver], "Every accepted approver"]
    clauses: Annotated[list[Clause], "Every accepted section"]
    unclear_phrase: Annotated[str, "For a hold over unclear words, those words; empty otherwise"]
    explanation: Annotated[str, "How the answer key reached the answer"]


@dataclass
class FieldHelp(Output):
    name: Annotated[str, "The trip record field's name"]
    kind: Annotated[str, "Its type"]
    description: Annotated[str, "What it means"]


@dataclass
class RequirementsInput(Output):
    topic: Annotated[Topic, "ALL for everything, FIELDS for the trip record's fields, AIRPORTS for the airport list"]


@dataclass
class RequirementsOutput(Output):
    fields: Annotated[list[FieldHelp], "The trip record's fields; empty for AIRPORTS"]
    conventions: Annotated[list[str], "How times, dates, fares and seats work in this world; empty for AIRPORTS"]
    airports: Annotated[list[Airport], "The airports the simulated world knows; empty for FIELDS"]


TOOLS = {
    Tool.BOOKING_REQUIREMENTS: (RequirementsInput, RequirementsOutput),
    Tool.GET_TRIP: (TripInput, TripOutput),
    Tool.SEARCH_FLIGHTS: (SearchInput, SearchOutput),
    Tool.SOLVE_BOOKING: (TaskInput, SolveOutput),
}
TASKS = {
    Task.BOOKING_REQUIREMENTS: (RequirementsInput, RequirementsOutput),
    Task.SEARCH_FLIGHTS: (SearchInput, SearchOutput),
    Task.BOOK_FLIGHT: (TaskInput, BookingOutput),
}
