"""The answer key's rules for Vanderbilt University Medical Center Finance Policy FIN 4.7, Travel (effective June
2021), as exact integer code. Byte-identical in src/plugin/rules.py and verifier/rules.py; it imports only modules
a verifier may use.

Every rule cites the frozen handbook text (src/plugin/data/policy.txt) by line. The frozen text repeats a five-line
page header 18 times; line numbers count those header lines as they stand. Where the text leaves an answer open,
the rule returns FLAG_FOR_APPROVAL with the unclear words, and a scenario may depend on each unclear phrase at
most once (tests/test_scenarios.py). Combinations no scenario needs raise ValueError, so a new scenario cannot
fall silently into untested logic.

The duration hook. Lines 102-108: business or first class "may be used only if the traveler's applicable officer
approves it in writing in advance. One of the following conditions should be met: Any flight segment has a
scheduled in-air flying time more than four hours; or The total scheduled in-air flight time for all flight
segments is more than seven hours; or A medical justification has been documented and approved by ... (EAD)."
Two duration rules, both strict ("more than"):

- "segment": any single flight of the ticket scheduled at more than 240 minutes (each flight on its own; a
  round-trip ticket's flights back are flight segments of the ticket too).
- "total": the flights' scheduled minutes added together, ground time left out ("in-air"), more than 420. For a
  one-way ticket that is the flights out. For a round-trip ticket "all flight segments" may mean every flight of
  the ticket or the flights of one journey; when only the first reading passes 420 the rule is unclear (None).

The world's scheduled minutes are the scheduled in-air time (the contract's Segment.scheduled_minutes).
"""

from contract import (
    Approver,
    Cabin,
    Clause,
    Decision,
    Funding,
    OutsideOption,
    Passenger,
    Purpose,
    ReasonCode,
    SignOffSubject,
)

HANDBOOK = "Vanderbilt University Medical Center Finance Policy FIN 4.7, Travel (June 2021)"

# Each closed-list section and the heading it names in the frozen text (tests check every heading is there).
CLAUSE_HEADINGS = {
    Clause.PURPOSE: "Purpose:",
    Clause.SCOPE: "Scope:",
    Clause.DEFINITIONS: "Definitions:",
    Clause.POLICY: "Policy:",
    Clause.AIR_TRAVEL: "1. AIR TRAVEL",
    Clause.AIR_RESERVATIONS: "1.1. Air Reservations",
    Clause.FARES_AND_CLASS: "1.2. Fares/Ticket Types/Class of Service",
    Clause.CHANGES_AND_UNUSED_TICKETS: "1.3. Changes, Cancelations, and Unused Tickets",
    Clause.PRE_TRAVEL_REIMBURSEMENT: "1.4. Pre-Travel Reimbursement",
    Clause.BAGGAGE_FEES: "1.5. Baggage Fees",
    Clause.PRIVATE_AIRCRAFT: "1.6. Private Aircraft",
    Clause.FEDERALLY_FUNDED_AIRLINES: "1.7. Airline Requirements for Federally Funded Sponsored Research Projects",
    Clause.HOTELS: "2. HOTELS",
    Clause.AUTOMOBILE_RENTAL: "3. AUTOMOBILE R E N T A L",
    Clause.LOCAL_TRANSPORTATION: "4. LOCAL TRANSPORTATION",
    Clause.BUS_OR_RAIL: "5. BUS OR RAIL",
    Clause.PERSONAL_AUTOMOBILE: "6. TRAVEL VIA PERSONAL AUTOMOBILE",
    Clause.MEALS_AND_ENTERTAINMENT: "7. MEAL A N D ENTERTAINMENT EXPENSES",
    Clause.INSURANCE_AND_RISK: "9. INSURANCE AND RISK MANAGEMENT",
    Clause.INTERNATIONAL_ASSISTANCE: "9.4. International Travel Emergency Assistance",
    Clause.COMPANION_EXPENSES: "10. SPOUSE AND DOMESTIC PARTNER (\"COMPANION\") EXPENSES",
    Clause.COMPANION_TRAVEL: "10.1. Companion Travel",
    Clause.OTHER_CONSIDERATIONS: "11. OTHER TRAVEL CONSIDERATIONS",
    Clause.APPROVAL_TO_TRAVEL: "11.1. Approval to Travel",
    Clause.RECEIPTS: "11.2. Receipt Requirements",
    Clause.PASSPORTS_AND_VISAS: "11.5. International Travel / Passports and Visas",
    Clause.COMBINED_PERSONAL_AND_BUSINESS: "11.7. Combined Personal and Business Travel",
    Clause.LAUNDRY: "11.8. Laundry Expenses for Extended Trips",
    Clause.REWARD_POINTS: "11.10. Frequent Flyer/Guest/Reward Points",
    Clause.UNALLOWABLE_EXPENSES: "12. UNALLOWABLE EXPENSES",
    Clause.DUTY_OF_CARE: "13. DUTY OF CARE",
    Clause.HOME_OFFICE: "14. GUIDANCE FOR REIMBURSEMENT OF HOME OFFICE EXPENSES",
}

# The handbook's duration thresholds (the per-handbook duration hook; tests/test_duration.py tests both sides).
DURATION_RULES = (
    {"name": "segment", "minutes": 240, "operator": ">", "lines": [104, 104],
     "quote": "Any flight segment has a scheduled in-air flying time more than four hours; or"},
    {"name": "total", "minutes": 420, "operator": ">", "lines": [105, 106],
     "quote": "The total scheduled in-air flight time for all flight segments is more than seven hours; or"},
)
LIMITS = {rule["name"]: rule["minutes"] for rule in DURATION_RULES}

# Handbook-specific conventions shown by booking_requirements, beyond the template's. Lines 104-106 measure
# "scheduled in-air" time; this says that a flight's scheduled minutes are that time, so no reader takes off taxi time.
CONVENTIONS = (
    ("A flight's scheduled_minutes is its scheduled time in the air, from takeoff to landing; time on the ground "
     "between flights is the layover."),
)

# Line 149: the Fly America Act requires a U.S. air carrier for federally funded foreign travel.
US_CARRIERS = ("American Airlines", "Delta Air Lines", "United Airlines", "Alaska Airlines", "JetBlue",
               "Southwest Airlines")
# Lines 163-166: the Open Skies exception needs travel "not being reimbursed by the Department of State or the
# Department of Defense".
OPEN_SKIES_BARRED = ("Department of State", "Department of Defense")
# Lines 396-399: a funding sponsor's more restrictive travel terms supersede the policy. The one such term the
# scenarios use, word for word as the trip record gives it.
ECONOMY_ONLY_TERM = "Air travel paid from this award is limited to economy class."

PREMIUM_PHRASE = "economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.)"
TOTAL_PHRASE = "The total scheduled in-air flight time for all flight segments"

AIR = [Clause.AIR_TRAVEL, Clause.FARES_AND_CLASS]
# A hold over unclear words: line 654 sends questions on the policy's interpretation to the finance policy
# office; lines 67-68 give exceptions to the COO and CFO; the officer's written approval (line 102) is what a
# business seat rests on; the supervisor's approval of the trip (line 383) is on file.
UNCLEAR_ROLES = [Approver.NOT_NAMED, Approver.FINANCE_POLICY_OFFICE, Approver.CHIEF_OPERATING_OFFICER,
                 Approver.CHIEF_FINANCIAL_OFFICER, Approver.OFFICER, Approver.SUPERVISOR]
UNCLEAR_REASONS = [ReasonCode.UNCLEAR_POLICY_TEXT, ReasonCode.APPROVAL_REQUIRED]


def over(rule, offer):
    """True, False or None (unclear): whether ``offer``'s flights are over the handbook's ``rule``."""
    if rule not in LIMITS:
        raise ValueError(f"unknown duration rule {rule!r}")
    limit = LIMITS[rule]
    out = [segment.scheduled_minutes for segment in offer.segments]
    back = [segment.scheduled_minutes for segment in offer.return_segments]
    if rule == "segment":
        return any(minutes > limit for minutes in out + back)
    if not back:
        return sum(out) > limit
    if sum(out) > limit and sum(back) > limit:
        return True
    if sum(out) + sum(back) <= limit:
        return False
    return None


def by_value(items):
    return sorted(set(items), key=lambda item: item.value)


def answer(decision, offers, reasons, approvers, clauses, why, phrase=""):
    return {
        "decision": decision,
        "offer_ids": sorted(offer.offer_id for offer in offers),
        "cabins": by_value(offer.cabin for offer in offers) or [Cabin.NONE],
        "reason_codes": by_value(reasons),
        "approvers": by_value(approvers),
        "clauses": by_value(clauses),
        "unclear_phrase": phrase,
        "explanation": why,
    }


def cheapest(offers):
    if not offers:
        return []
    low = min(offer.fare_cents for offer in offers)
    return [offer for offer in offers if offer.fare_cents == low]


def signed(trip, subject, roles=None):
    return [record for record in trip.sign_offs if record.subject == subject and (roles is None or record.role in roles)]


def on_file(trip):
    return [record.role for record in trip.sign_offs]


def lands(offer):
    """When the flights out land at the destination: YYYY-MM-DD HH:MM, local."""
    return offer.segments[-1].arrive_local


def in_cabin(offers, cabin):
    return [offer for offer in offers if offer.cabin == cabin]


def solve(trip, offers, hidden):
    """The answer key for one trip and the offers on its route and date: the decision, and every accepted offer
    id, cabin, reason, approver and section. ``hidden`` (answer_key_inputs) is unused by this handbook."""
    if hidden:
        raise ValueError("this handbook's scenarios carry no answer_key_inputs")
    if any(offer.return_segments for offer in offers) != bool(trip.return_date):
        raise ValueError("a round-trip fare only for a record that gives the day to fly back, and only then")
    if trip.passenger == Passenger.COMPANION:
        if not trip.accompanies:
            raise ValueError("a companion with nobody accompanied is not modelled")
        # PERSONAL_TRAVEL_NOT_COVERED too: the companion's trip is not VUMC business for them.
        return answer(Decision.REFUSE, [], [ReasonCode.COMPANION_NOT_COVERED, ReasonCode.PERSONAL_TRAVEL_NOT_COVERED],
                      [Approver.NONE, *on_file(trip)], [Clause.COMPANION_EXPENSES, Clause.COMPANION_TRAVEL],
                      "Lines 355-358: no travel expenses, including transportation, for any persons accompanying "
                      "travelers on VUMC travel are reimbursed. VUMC buys no ticket for the companion.")
    if trip.purpose_kind == Purpose.PERSONAL:
        return answer(Decision.REFUSE, [], [ReasonCode.PERSONAL_TRAVEL_NOT_COVERED, ReasonCode.OUTSIDE_POLICY_SCOPE],
                      [Approver.NONE, *on_file(trip)],
                      [Clause.COMBINED_PERSONAL_AND_BUSINESS, Clause.OTHER_CONSIDERATIONS, Clause.UNALLOWABLE_EXPENSES],
                      "Lines 457-461: when personal travel is combined with VUMC business travel only the business "
                      "portion is reimbursable, and VUMC's travel tool should not be used for personal travel; "
                      "lines 523-525 list vacation and personal expenses on business trips as non-reimbursable. The "
                      "leg asked for is the traveller's own holiday: no ticket is bought.")
    international = trip.origin.country != "US" or trip.destination.country != "US"
    seated = [offer for offer in offers if offer.seats_available]
    notes, clauses, reasons = [], list(AIR), []
    usable = seated
    if trip.must_arrive_by:
        usable = [offer for offer in seated if lands(offer) <= trip.must_arrive_by]
        if len(usable) == len(seated):
            raise ValueError("an arrival time that rules out no offer is not modelled")
        notes.append(f"line 88: the lowest economy fare that meets the business needs, which means landing by "
                     f"{trip.must_arrive_by}; cheaper flights that land later do not meet them")
    pool = usable
    fly_america = trip.funding == Funding.FEDERAL_AWARD and international
    if trip.funding == Funding.FEDERAL_AWARD and not international:
        raise ValueError("domestic federally funded travel is not modelled")
    if fly_america:
        pool = [offer for offer in usable if offer.carrier in US_CARRIERS]
        if not pool or len(pool) == len(usable):
            raise ValueError("Fly America with only one kind of carrier on the route is not modelled")
    decision, chosen, more_reasons, relied, more_clauses, phrase = choose(trip, pool, usable, fly_america,
                                                                         international, notes)
    reasons += more_reasons
    clauses += more_clauses
    trips = signed(trip, SignOffSubject.TRIP, [Approver.SUPERVISOR])
    if not trips:
        if decision != Decision.BOOK or len(trip.sign_offs):
            raise ValueError("a missing trip approval beside other sign-offs, or on a hold, is not modelled")
        return answer(Decision.FLAG_FOR_APPROVAL, chosen, [ReasonCode.APPROVAL_REQUIRED], [Approver.SUPERVISOR],
                      [Clause.APPROVAL_TO_TRAVEL, Clause.OTHER_CONSIDERATIONS],
                      "Lines 383-384: travelers must have the necessary approval from their supervisor to take a trip "
                      "prior to committing VUMC funds. The supervisor has not approved this trip yet: hold the ticket "
                      "the request would otherwise get (" + "; ".join(notes) + ").")
    if decision == Decision.FLAG_FOR_APPROVAL:
        return answer(decision, chosen, UNCLEAR_REASONS, UNCLEAR_ROLES, clauses, "; ".join(notes) + ".", phrase)
    # SYNC_NOTES 4': a BOOK whose sign-offs are on file accepts those roles and NONE; 4(b): unused ones too.
    approvers = [Approver.NONE, *on_file(trip), *relied]
    notes.append("lines 383-384: the supervisor's approval of the trip is on file")
    return answer(decision, chosen, reasons, approvers, clauses, "; ".join(notes) + ".", phrase)


def choose(trip, pool, usable, fly_america, international, notes):
    """(decision, offers, reasons, roles relied on beyond the trip approval, clauses beyond AIR, unclear phrase)."""
    economy = cheapest(in_cabin(pool, Cabin.ECONOMY))
    if not economy:
        raise ValueError("no economy offer can be bought")
    if trip.requested_cabin == Cabin.PREMIUM_ECONOMY:
        premium = cheapest(in_cabin(pool, Cabin.PREMIUM_ECONOMY))
        if not premium or fly_america or trip.outside_option != OutsideOption.NONE:
            raise ValueError("a premium economy request beside other wishes is not modelled")
        notes.append("lines 88-93: the lowest available economy fare, but fees for economy class upgrades such as "
                     "Economy Plus are reimbursable; whether a premium economy fare is such an upgrade or a class of "
                     "service above economy, which lines 102-108 do not name, is left open. Hold either fare")
        return Decision.FLAG_FOR_APPROVAL, premium + economy, [], [], [], PREMIUM_PHRASE
    if trip.requested_cabin in (Cabin.BUSINESS, Cabin.FIRST):
        if fly_america or trip.outside_option != OutsideOption.NONE or trip.preferred_airline:
            raise ValueError("a premium-cabin request beside other wishes is not modelled")
        return premium_cabin(trip, pool, economy, international, notes)
    if trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError(f"a {trip.requested_cabin.value} request is not modelled")
    return economy_request(trip, pool, usable, economy, fly_america, international, notes)


def economy_request(trip, pool, usable, economy, fly_america, international, notes):
    reasons, clauses, relied = [ReasonCode.LOWEST_FARE], [], []
    notes.append("lines 88-89: the lowest available economy class airfare that meets the business needs")
    if fly_america:
        cheaper = [offer for offer in usable if offer.cabin == Cabin.ECONOMY and offer.fare_cents < economy[0].fare_cents]
        if not cheaper:
            raise ValueError("Fly America where a U.S. carrier is already the lowest fare is not modelled")
        # The dearer U.S. carrier is booked because of Fly America, not the lowest-fare rule.
        reasons = [ReasonCode.FLY_AMERICA_US_CARRIER_REQUIRED, ReasonCode.NATIONAL_CARRIER_REQUIRED]
        clauses += [Clause.FEDERALLY_FUNDED_AIRLINES]
        notes.append("lines 148-149: federally funded foreign travel must use a U.S. air carrier: the lowest U.S.-carrier "
                     "economy fare")
        if trip.preferred_airline:
            if trip.preferred_airline in US_CARRIERS or not any(name in trip.sponsor for name in OPEN_SKIES_BARRED):
                raise ValueError("an airline wish under Fly America other than a barred Open Skies one is not modelled")
            reasons.append(ReasonCode.OPEN_SKIES_AGREEMENT)
            notes.append("lines 163-166: the Open Skies exception needs travel not reimbursed by the Department of State "
                         "or the Department of Defense, and this award is from one of them")
    elif trip.preferred_airline:
        if any(offer.carrier == trip.preferred_airline for offer in economy):
            raise ValueError("an airline wish that the lowest fare already meets is not modelled")
        # Lines 476-478 decline the airline because it adds expense "with the sole purpose of obtaining more
        # rewards": the ground is the lowest-fare rule itself, so LOWEST_FARE stays beside the loyalty code.
        reasons.append(ReasonCode.LOYALTY_PROGRAM_PREFERENCE)
        clauses += [Clause.REWARD_POINTS, Clause.OTHER_CONSIDERATIONS]
        notes.append("lines 475-478: travellers may use their rewards, but may never add expense to VUMC to earn more "
                     "rewards: the lowest fare, not the preferred airline")
    if trip.self_paid_upgrade != Cabin.NONE:
        if trip.outside_option != OutsideOption.NONE or fly_america:
            raise ValueError("a self-paid upgrade beside other wishes is not modelled")
        reasons.append(ReasonCode.TRAVELER_PAYS_UPGRADE)
        notes.append("lines 89-91: the traveller may upgrade at personal expense or with personal rewards; VUMC buys "
                     "the economy fare")
        for colleague in trip.travelling_with:
            on = [offer for offer in economy
                  if any(segment.flight_number == colleague.flight_number for segment in offer.segments)]
            if not on:
                raise ValueError("a colleague's flight that is not the lowest economy fare is not modelled")
    elif trip.travelling_with:
        raise ValueError("colleagues on file without an upgrade wish are not modelled")
    if trip.outside_option == OutsideOption.AIRLINE_WEBSITE:
        if not international or trip.preferred_airline or fly_america:
            raise ValueError("an outside purchase other than a plain international one is not modelled")
        # The request is declined on line 73's booking-channel rule, not on the lowest-fare rule.
        reasons = [ReasonCode.BOOKING_TOOL_REQUIRED]
        clauses = [Clause.AIR_RESERVATIONS]
        notes.append("lines 73-76 and 84: international air must be booked through the online booking tool or the "
                     "travel agency, and cost is not a business need that excuses it: the lowest economy fare the "
                     "booking tool lists")
    elif trip.outside_option == OutsideOption.PRIVATE_AIRCRAFT:
        if signed(trip, SignOffSubject.PRIVATE_AIRCRAFT):
            raise ValueError("a private aircraft with approvals on file is not modelled")
        reasons = [ReasonCode.PRIVATE_AIRCRAFT_NOT_APPROVED]
        clauses += [Clause.PRIVATE_AIRCRAFT]
        # The roles whose missing approval decides it (as the officer in sable-wren), beside NONE and those on file.
        relied = [Approver.RISK_MANAGEMENT, Approver.CHIEF_FINANCIAL_OFFICER]
        notes.append("lines 134-138: non-commercial aircraft are prohibited without written advance approval from "
                     "Risk and Insurance Management and the CFO, and none is on file: a commercial flight")
    elif trip.outside_option != OutsideOption.NONE:
        raise ValueError("unknown outside option")
    if trip.sponsor_terms or signed(trip, SignOffSubject.PREMIUM_CABIN) or signed(trip, SignOffSubject.POLICY_EXCEPTION):
        raise ValueError("sponsor terms or cabin approvals on an economy request are not modelled")
    return Decision.BOOK, economy, reasons, relied, clauses, ""


def condition(trip, offer):
    """Lines 104-108: True when a condition is met, False when none is, None when only an unclear reading meets one."""
    if signed(trip, SignOffSubject.MEDICAL_JUSTIFICATION, [Approver.DISABILITY_SERVICES]):
        return True
    if over("segment", offer):
        return True
    return over("total", offer)


def premium_cabin(trip, pool, economy, international, notes):
    """Lines 102-108 (officer's written approval in advance, and a condition), lines 67-68 (exceptions approved by
    the COO and the CFO), lines 396-399 (a sponsor's more restrictive terms supersede)."""
    premium = in_cabin(pool, trip.requested_cabin)
    officer = signed(trip, SignOffSubject.PREMIUM_CABIN, [Approver.OFFICER])
    medical = signed(trip, SignOffSubject.MEDICAL_JUSTIFICATION, [Approver.DISABILITY_SERVICES])
    if ECONOMY_ONLY_TERM in trip.sponsor_terms:
        if not officer or not any(condition(trip, offer) for offer in premium):
            raise ValueError("a sponsor's economy term on a seat the policy would not allow anyway is not modelled")
        notes.append("lines 396-399: the award's own terms limit air travel to economy class, and a sponsor's more "
                     "restrictive terms supersede the policy, so the officer's approval does not buy business: the "
                     "lowest economy fare")
        # UPGRADE_NOT_ELIGIBLE too: the business seat asked for is not allowed on this award.
        return (Decision.BOOK, economy, [ReasonCode.SPONSOR_RESTRICTION, ReasonCode.UPGRADE_NOT_ELIGIBLE], [],
                [Clause.APPROVAL_TO_TRAVEL, Clause.OTHER_CONSIDERATIONS], "")
    if trip.sponsor_terms:
        raise ValueError("other sponsor terms are not modelled")
    exception = {record.role for record in signed(trip, SignOffSubject.POLICY_EXCEPTION)}
    if exception:
        if exception != {Approver.CHIEF_OPERATING_OFFICER, Approver.CHIEF_FINANCIAL_OFFICER} or officer or not premium:
            raise ValueError("an exception without both the COO and the CFO, or beside an officer's approval, is not modelled")
        if any(condition(trip, offer) for offer in premium):
            raise ValueError("an exception for a seat the policy already allows is not modelled")
        notes.append("lines 67-68: exceptions to the policy need the approval of the COO and the CFO, and both approved "
                     "this one in writing: the cheapest seat in the cabin asked for")
        return (Decision.BOOK, cheapest(premium), [ReasonCode.POLICY_EXCEPTION_APPROVED],
                [Approver.CHIEF_OPERATING_OFFICER, Approver.CHIEF_FINANCIAL_OFFICER], [Clause.POLICY], "")
    verdicts = {offer.offer_id: condition(trip, offer) for offer in premium}
    met = [offer for offer in premium if verdicts[offer.offer_id] is True]
    open_ = [offer for offer in premium if verdicts[offer.offer_id] is None]
    if not officer:
        if medical:
            raise ValueError("a medical justification without the officer's approval is not modelled")
        if not met or open_:
            raise ValueError("a premium request without the officer's approval on a short flight is not modelled")
        notes.append("lines 102-103: business or first class may be used only if the traveler's applicable officer "
                     "approves it in writing in advance; a flight over four hours does not do without that approval, "
                     "and none is on file: the lowest economy fare")
        return Decision.BOOK, economy, [ReasonCode.UPGRADE_NOT_ELIGIBLE], [Approver.OFFICER], [], ""
    if met and open_:
        raise ValueError("premium offers on both sides of a clear and an unclear condition are not modelled")
    if met:
        best = cheapest(met)
        if medical:
            reasons, relied = [ReasonCode.MEDICAL_NEED], [Approver.OFFICER, Approver.DISABILITY_SERVICES]
            notes.append("lines 102-108: the officer approved in writing in advance and EAD approved a documented "
                         "medical justification: the cheapest seat in the cabin asked for")
        else:
            reasons, relied = [ReasonCode.LONG_FLIGHT_APPROVED], [Approver.OFFICER]
            if international:
                reasons.append(ReasonCode.INTERNATIONAL_LONG_FLIGHT)
            minutes = max(segment.scheduled_minutes for segment in best[0].segments)
            notes.append(f"lines 102-106: the officer approved in writing in advance, and the flights are over the "
                         f"handbook's limit (longest flight {minutes} minutes, {best[0].flying_minutes} in the air in "
                         "all): the cheapest seat in the cabin asked for")
        return Decision.BOOK, best, reasons, relied, [], ""
    if open_:
        notes.append("lines 104-106: no flight is over four hours, and each journey's flights are seven hours or less, "
                     "but the round-trip ticket's flights out and back together are over seven hours; 'all flight "
                     "segments' may mean the ticket's or one journey's. Hold either fare")
        return Decision.FLAG_FOR_APPROVAL, cheapest(open_) + economy, [], [], [], TOTAL_PHRASE
    if not all(record.subject_to_policy for record in officer):
        raise ValueError("an officer's unconditional approval with no condition met ('should be met') is not modelled")
    notes.append("lines 104-108: the officer approved only if the trip meets the policy's conditions, and no flight "
                 "is over four hours, the flights total seven hours or less in the air and no medical justification "
                 "is on file: the lowest economy fare")
    return (Decision.BOOK, economy, [ReasonCode.LONG_FLIGHT_CONDITION_NOT_MET, ReasonCode.UPGRADE_NOT_ELIGIBLE], [],
            [], "")
