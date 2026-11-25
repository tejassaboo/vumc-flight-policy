"""Writes the VUMC scenario JSON files (an authoring aid, not a test; the JSON files are the truth).

    uv run python tests/build_scenarios.py

Flight numbers that a trip record refers to (a colleague's flight) are read from the shared world, so they
match what search_flights lists. Expected answers are hand-written here; tests/test_scenarios.py checks them
against rules.solve.

The frozen handbook repeats a five-line page header ("Approved By: ... Page N of 18") 18 times. Line numbers
below are the frozen file's, header lines included, and every quote is the frozen text as it stands.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from plugin.world import pinned_offers

POLICY = (ROOT / "src/plugin/data/policy.txt").read_text(encoding="utf-8").split("\n")
OUT = ROOT / "src/plugin/data/scenarios"


def norm(text):
    return " ".join(text.split())


def keep(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    quote = text if quote is None else quote
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "sha256": hashlib.sha256(text.encode()).hexdigest(), "quote": quote, "why": why}


def aside(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "quote": quote, "why": why}


# ----- clauses -----
EXCEPTIONS = keep(67, 68, None, "exceptions to the policy need the COO's and the CFO's approval")
RESERVATIONS = keep(72, 77, "All international air reservations must be made through the online booking tool or "
                    "directly with the designated travel agency, except in documented extreme cases necessitated by "
                    "business needs and/or to preserve personal safety*.",
                    "international air only through the booking tool or the travel agency")
COST_NOTE = keep(84, 85, "*Cost is not defined as a business need.", "a saving is not a business need")
LOWEST = keep(88, 89, "Travelers should purchase the lowest available economy class airfare that meets the business "
              "needs of the travel, except as outlined below.", "the lowest economy fare that meets the business needs")
SELF_UPGRADE = keep(89, 91, "Travelers may upgrade the level of service at personal expense or by using their personal "
                    "airline rewards points/miles/credits.", "upgrades at the traveller's own expense or points")
UPGRADE_FEES = keep(92, 93, None, "fees for economy class upgrades such as Economy Plus are reimbursable")
PREMIUM = keep(102, 108, None, "business or first only with the officer's written approval in advance, and a condition")
OFFICER_ONLY = keep(102, 103, "Business class or first-class seating may be used only if the traveler's applicable "
                    "officer approves it in writing in advance.", "no business seat without the officer's approval")
PRIVATE = keep(133, 138, None, "no non-commercial aircraft without Risk and Insurance Management and the CFO")
FLY_AMERICA = keep(149, 150, "The Fly America Act (FAA) requires the use of a U.S. air carrier for federally funded "
                   "foreign travel.", "federally funded foreign travel on a U.S. carrier")
OPEN_SKIES = keep(158, 169, None, "the Open Skies exception is barred for Department of State or Defense reimbursement")
COMPANION = keep(356, 358, None, "no travel expenses for anyone accompanying a traveller")
SUPERVISOR = keep(383, 384, None, "the supervisor's approval of the trip before committing funds")
SPONSOR = keep(396, 399, "These restrictions, to the extent that they are more restrictive than VUMC's travel policy, "
               "supersede any restrictions outlined in this policy.", "a sponsor's stricter travel terms supersede")
PERSONAL = keep(458, 461, None, "only the business portion is reimbursable; no personal travel on the travel tool")
VACATION = keep(523, 525, None, "vacation and personal expenses on business trips are not reimbursable")
REWARDS = keep(476, 478, "In no case shall VUMC business travelers incur additional expense on behalf of the VUMC with "
               "the sole purpose of obtaining more rewards", "no extra expense to earn rewards")
INTERPRETATION = keep(654, 655, None, "questions on the policy's interpretation go to the finance policy office")

QUESTIONNAIRE = aside(78, 83, "Submission of approval of the Questionnaire is required with the filing of the "
                      "traveler's expense report in Concur.", "the questionnaire is on file and matters at expense time")
CHANGES = aside(113, 114, "Penalties for changes to an airline ticket for business reasons or circumstances beyond the "
                "traveler's control are reimbursable from VUMC funds.", "change penalties, not the fare choice")
RAIL = aside(225, 226, "Travel by bus or rail is allowed when it is less expensive", "rail is allowed, never required")
LAUNDRY = aside(467, 468, "laundry and/or dry-cleaning charges will be reimbursed when travel exceeds four or more "
                "consecutive nights", "a count of nights for laundry, not of hours for a seat")
REWARDS_OK = aside(475, 476, "Travelers may utilize travel-provider rewards related to travel (e.g., Delta Sky Miles, "
                   "Marriot Rewards, etc.).", "earning miles is allowed, but does not choose the fare")
CONDITIONS = aside(104, 106, "Any flight segment has a scheduled in-air flying time more than four hours",
                   "a condition is met, but the officer's approval is still needed")
RECEIPTS = aside(415, 416, "Itemized receipts for all expenditures greater than or equal to $75 are required.",
                 "a dollar threshold for receipts, not for fares")

# ----- builders -----


def trip(**fields):
    base = {
        "traveller_name": "", "traveller_title": "", "passenger": "EMPLOYEE", "accompanies": "", "origin": "",
        "destination": "", "travel_date": "", "return_date": "", "booking_date": "", "must_arrive_by": "",
        "purpose": "", "purpose_kind": "CONFERENCE", "funding": "DEPARTMENT_FUNDS", "sponsor": "", "sponsor_terms": [],
        "requested_cabin": "ECONOMY", "preferred_airline": "", "self_paid_upgrade": "NONE", "outside_option": "NONE",
        "outside_option_detail": "", "sign_offs": [], "travelling_with": [], "notes": [],
    }
    unknown = set(fields) - set(base)
    assert not unknown, unknown
    base.update(fields)
    return base


def sign(role, name, title, subject, terms, conditional=False):
    return {"role": role, "name": name, "title": title, "subject": subject, "subject_to_policy": conditional,
            "terms": terms}


def supervisor(name, title, what):
    return sign("SUPERVISOR", name, title, "TRIP", f"Approved the trip: {what}.")


def questionnaire():
    return sign("EXPORT_COMPLIANCE", "VUMC Export Compliance", "Export Compliance Office", "INTERNATIONAL_QUESTIONNAIRE",
                "Approved the traveller's International Travel Questionnaire for this trip.")


def officer(name, title, conditional):
    terms = (("Approved business class for this trip, provided the trip meets one of the conditions the travel policy "
              "sets for business class.")
             if conditional else "Approved business class for this trip.")
    return sign("OFFICER", name, title, "PREMIUM_CABIN", terms, conditional)


def offer(slot, flight, cabin, cents, seats=True):
    data = {"slot": slot, "flight": flight, "cabin": cabin, "fare_cents": cents}
    if not seats:
        data["seats"] = False
    return data


def expected(decision, slots, cabins, reasons, approvers, clauses, phrase=""):
    return {"decision": decision, "offer_slots": slots, "cabins": cabins, "reason_codes": reasons,
            "approvers": approvers, "clauses": clauses, "unclear_phrase": phrase}


def search(origin, destination, date, flights, offers, background=0, return_date=""):
    # handbook.json background_offers is 0, so a search the scenario does not pin lists nothing; each pinned
    # search sets its own number.
    return {"name": "main", "origin": origin, "destination": destination, "date": date, "return_date": return_date,
            "background": background, "flights": flights, "offers": offers}


def first_flight(scenario_id, search_spec, slot):
    for name, made in pinned_offers(scenario_id, search_spec):
        if name == slot:
            return made.segments[0].flight_number
    raise KeyError(slot)


S = []


def scenario(id, category, overlays, request, trip_, search_spec, exp, must_keep, notes, twin_of="", twin_fact="",
             flag_twins=(), ambiguity="none", distractors=()):
    S.append({
        "id": id, "category": category, "overlays": list(overlays), "twin_of": twin_of, "twin_fact": twin_fact,
        "flag_twins": list(flag_twins), "ambiguity_note": ambiguity, "request": request, "trip": trip_,
        "world": {"searches": [search_spec]}, "expected": exp, "must_keep": list(must_keep),
        "distractors": list(distractors), "design_notes": notes,
    })


AIR = ["AIR_TRAVEL", "FARES_AND_CLASS"]
NOT_MET = ["LONG_FLIGHT_CONDITION_NOT_MET", "UPGRADE_NOT_ELIGIBLE"]
US_REQUIRED = ["FLY_AMERICA_US_CARRIER_REQUIRED", "NATIONAL_CARRIER_REQUIRED"]
UNCLEAR_ROLES = ["NOT_NAMED", "SUPERVISOR", "OFFICER", "CHIEF_OPERATING_OFFICER", "CHIEF_FINANCIAL_OFFICER",
                 "FINANCE_POLICY_OFFICE"]
UNCLEAR_REASONS = ["APPROVAL_REQUIRED", "UNCLEAR_POLICY_TEXT"]


def on_file(*roles):
    """SYNC_NOTES 4': a booking whose sign-offs are on file accepts those roles and NONE."""
    return ["NONE", *roles]


# ===== easy (5) =====

scenario(
    "amber-loom", "easy", [],
    "Chicago to Boston on January 19th for the nursing informatics conference. Economy, the cheapest seat please.",
    trip(traveller_name="Rachel Moreno", traveller_title="Nurse Informaticist (works remotely from the Chicago area)",
         origin="ORD", destination="BOS", travel_date="2027-01-19", booking_date="2026-12-14",
         purpose="Present a poster at a nursing informatics conference",
         sign_offs=[supervisor("Gwen Albright", "Director, Nursing Informatics", "nursing informatics conference, Boston")]),
    search("ORD", "BOS", "2027-01-19", {
        "dawn": {"carrier": "UA", "depart": "06:00"},
        "morning": {"carrier": "AA", "depart": "08:15"},
        "midday": {"carrier": "DL", "depart": "11:40"},
        "afternoon": {"carrier": "B6", "depart": "15:30"},
    }, [
        offer("dawn-economy", "dawn", "ECONOMY", 16_400, seats=False),
        offer("morning-economy", "morning", "ECONOMY", 18_900),
        offer("midday-economy", "midday", "ECONOMY", 20_300),
        offer("afternoon-economy", "afternoon", "ECONOMY", 21_400),
    ], background=2),
    expected("BOOK", ["morning-economy"], ["ECONOMY"], ["LOWEST_FARE"], on_file("SUPERVISOR"), AIR),
    [LOWEST, SUPERVISOR],
    "Line 88: the lowest available economy fare. The 06:00 United fare is sold out, so American at 08:15 ($189). The "
    "supervisor's approval of the trip (lines 383-384) is on file.")

scenario(
    "birch-ember", "easy", ["dearer_option"],
    "I'm presenting in the afternoon session of the European transplant congress in Paris on February 9th, flying "
    "overnight from Atlanta on the 8th. Dr. Hale approved business class for this trip in writing. Business, please.",
    trip(traveller_name="Daniel Osei", traveller_title="Associate Professor of Surgery", origin="ATL",
         destination="CDG", travel_date="2027-02-08", booking_date="2027-01-11",
         purpose="Invited talk at a European transplant congress",
         requested_cabin="BUSINESS",
         sign_offs=[supervisor("Miriam Hale", "Chair, Department of Surgery", "transplant congress, Paris"),
                    officer("Dr. Miriam Hale", "Executive Vice President for Surgical Services", False),
                    questionnaire()]),
    search("ATL", "CDG", "2027-02-08", {
        "delta": {"carrier": "DL", "depart": "17:30", "minutes": [515]},
        "airfrance": {"carrier": "AF", "depart": "19:10", "minutes": [520]},
    }, [
        offer("delta-economy", "delta", "ECONOMY", 104_500),
        offer("delta-business", "delta", "BUSINESS", 462_000),
        offer("airfrance-economy", "airfrance", "ECONOMY", 98_000),
        offer("airfrance-business", "airfrance", "BUSINESS", 438_500),
    ]),
    expected("BOOK", ["airfrance-business"], ["BUSINESS"], ["INTERNATIONAL_LONG_FLIGHT", "LONG_FLIGHT_APPROVED"],
             on_file("SUPERVISOR", "OFFICER", "EXPORT_COMPLIANCE"), AIR),
    [PREMIUM, SUPERVISOR],
    "Lines 102-104: the officer approved business in writing in advance, and the nonstop is scheduled at 515-520 "
    "minutes, over four hours. Business is permitted and asked for: the cheapest business fare, Air France $4,385. "
    "Department funds, so Fly America (line 149) does not arise.",
    distractors=[QUESTIONNAIRE])

CEDAR_SEARCH = search("ATL", "SEA", "2027-03-02", {
    "delta": {"carrier": "DL", "depart": "08:05", "minutes": [330]},
    "alaska": {"carrier": "AS", "depart": "10:20", "minutes": [335]},
    "united": {"carrier": "UA", "depart": "07:15", "via": ["DEN"], "minutes": [195, 150], "layovers": [75]},
}, [
    offer("delta-economy", "delta", "ECONOMY", 31_200),
    offer("delta-business", "delta", "BUSINESS", 148_000),
    offer("alaska-economy", "alaska", "ECONOMY", 33_800),
    offer("united-economy", "united", "ECONOMY", 34_900),
])

scenario(
    "cedar-quill", "easy", ["multi_traveller", "upgrade_not_taken", "synonym"],
    "I'm going to the sepsis trial investigators' meeting in Seattle with Dr. Okafor on March 2nd. She's in business "
    "on her Delta flight. Please book me economy on that same flight; I'll use my own SkyMiles to upgrade so we can "
    "work on the slides together.",
    trip(traveller_name="Lucas Brennan", traveller_title="Clinical Research Coordinator", origin="ATL",
         destination="SEA", travel_date="2027-03-02", booking_date="2027-02-01",
         purpose="Sepsis trial investigators' meeting", purpose_kind="RESEARCH_MEETING",
         self_paid_upgrade="BUSINESS",
         sign_offs=[supervisor("Paula Greer", "Research Program Manager", "sepsis trial investigators' meeting, Seattle")],
         travelling_with=[{"name": "Dr. Ngozi Okafor", "title": "Professor of Emergency Medicine",
                           "flight_number": first_flight("cedar-quill", CEDAR_SEARCH, "delta-economy"),
                           "date": "2027-03-02", "cabin": "BUSINESS"}]),
    CEDAR_SEARCH,
    expected("BOOK", ["delta-economy"], ["ECONOMY"], ["LOWEST_FARE", "TRAVELER_PAYS_UPGRADE"], on_file("SUPERVISOR"),
             AIR),
    [LOWEST, SELF_UPGRADE, SUPERVISOR],
    "Lines 88-91: VUMC buys the lowest economy fare, and the traveller may upgrade at personal expense or with personal "
    "airline points. Delta's economy on Dr. Okafor's flight ($312) is also the lowest economy fare. The traveller has no "
    "officer approval of his own, so VUMC does not buy business for him.")

scenario(
    "dune-harrow", "easy", ["date_arithmetic", "multi_leg", "dearer_option"],
    "Seattle to Boston on the night of Monday, March 8th: I'm teaching the 10 a.m. simulation workshop at the Boston "
    "partner hospital on Tuesday the 9th. The cheapest economy flight that gets me there for it, please.",
    trip(traveller_name="Hannah Lindqvist", traveller_title="Simulation Education Specialist", origin="SEA",
         destination="BOS", travel_date="2027-03-08", booking_date="2027-02-08",
         must_arrive_by="2027-03-09 10:00", purpose="Teach a simulation workshop at a partner hospital",
         purpose_kind="TRAINING",
         sign_offs=[supervisor("Omar Haddad", "Manager, Center for Experiential Learning", "simulation workshop, Boston")]),
    search("SEA", "BOS", "2027-03-08", {
        "day": {"carrier": "DL", "depart": "08:00", "minutes": [320]},
        "chicago": {"carrier": "UA", "depart": "21:50", "via": ["ORD"], "minutes": [245, 135], "layovers": [200]},
        "redeye": {"carrier": "AS", "depart": "22:40", "minutes": [325]},
    }, [
        offer("day-economy", "day", "ECONOMY", 36_500),
        offer("chicago-economy", "chicago", "ECONOMY", 28_900),
        offer("redeye-economy", "redeye", "ECONOMY", 33_800),
    ]),
    expected("BOOK", ["redeye-economy"], ["ECONOMY"], ["LOWEST_FARE"], on_file("SUPERVISOR"), AIR),
    [LOWEST, SUPERVISOR],
    "Line 88: the lowest economy fare that meets the business needs. The United connection ($289) leaves Monday night and "
    "lands Tuesday 10:30 in Boston, after the 10:00 the record gives; the Alaska red-eye ($338) lands Tuesday 07:05. The "
    "day flight costs more.")

scenario(
    "oriole-shingle", "easy", ["dearer_option"],
    "Washington National to Atlanta on April 5th for the stroke registry steering meeting. EAD has approved my medical "
    "justification for a front-cabin seat, and my VP signed off on business class. Business please.",
    trip(traveller_name="Gloria Pennington", traveller_title="Senior Biostatistician", origin="DCA",
         destination="ATL", travel_date="2027-04-05", booking_date="2027-03-08",
         purpose="Stroke registry steering committee meeting", purpose_kind="RESEARCH_MEETING",
         requested_cabin="BUSINESS",
         sign_offs=[supervisor("Victor Lam", "Director, Biostatistics Core", "stroke registry meeting, Atlanta"),
                    officer("Dr. Renata Silva", "Senior Vice President for Research", True),
                    sign("DISABILITY_SERVICES", "Equal Opportunity, Affirmative Action, and Disability Services",
                         "EAD", "MEDICAL_JUSTIFICATION",
                         "Approved the traveller's documented medical justification for a business-class seat.")]),
    search("DCA", "ATL", "2027-04-05", {
        "delta": {"carrier": "DL", "depart": "07:30", "minutes": [125]},
        "charlotte": {"carrier": "AA", "depart": "06:45", "via": ["CLT"], "minutes": [80, 70], "layovers": [60]},
    }, [
        offer("delta-economy", "delta", "ECONOMY", 21_900),
        offer("delta-business", "delta", "BUSINESS", 68_900),
        offer("charlotte-economy", "charlotte", "ECONOMY", 20_500),
    ]),
    expected("BOOK", ["delta-business"], ["BUSINESS"], ["MEDICAL_NEED"],
             on_file("SUPERVISOR", "OFFICER", "DISABILITY_SERVICES"), AIR),
    [PREMIUM, SUPERVISOR],
    "Lines 102-108: the officer approved business in writing in advance (provided the trip meets the policy), and the "
    "third condition is met: a documented medical justification approved by EAD. The flight is short, which does not "
    "matter once a condition is met. The only business fare is Delta's ($689).")

# ===== boundary twins (6) =====

FERN_REQUEST = ("Dallas to San Francisco on February 17th for the clinic site visit the next morning. My VP, Dr. Ruiz, "
                "approved business class as long as the trip qualifies under the policy. Business if it qualifies; "
                "otherwise economy is fine.")


def fern_trip():
    return trip(traveller_name="Jorge Castillo", traveller_title="Director of Clinic Operations", origin="DFW",
                destination="SFO", travel_date="2027-02-17", booking_date="2027-01-20",
                purpose="Site visit at a partner clinic", purpose_kind="SITE_VISIT", requested_cabin="BUSINESS",
                sign_offs=[supervisor("Elena Ruiz", "Vice President, Ambulatory Operations", "clinic site visit, San Francisco"),
                           officer("Dr. Elena Ruiz", "Vice President, Ambulatory Operations", True)],
                notes=[("From San Francisco the traveller drives on to the Sacramento clinic and flies home on a "
                       "separate trip next month.")])


def fern_search(minutes):
    return search("DFW", "SFO", "2027-02-17", {
        "nonstop": {"carrier": "AA", "depart": "09:10", "minutes": [minutes]},
        "denver": {"carrier": "UA", "depart": "07:30", "via": ["DEN"], "minutes": [125, 150], "layovers": [70]},
    }, [
        offer("nonstop-economy", "nonstop", "ECONOMY", 26_800),
        offer("nonstop-business", "nonstop", "BUSINESS", 119_000),
        offer("denver-economy", "denver", "ECONOMY", 24_100),
        offer("denver-business", "denver", "BUSINESS", 90_500),
    ])


scenario(
    "fern-gable", "boundary_twin", ["dearer_option"], FERN_REQUEST, fern_trip(), fern_search(241),
    expected("BOOK", ["nonstop-business"], ["BUSINESS"], ["LONG_FLIGHT_APPROVED"], on_file("SUPERVISOR", "OFFICER"), AIR),
    [PREMIUM, SUPERVISOR],
    "Lines 102-104: the officer approved business in writing in advance, provided the trip qualifies. The American "
    "nonstop is scheduled at 241 minutes, more than four hours, so business on it qualifies ($1,190). United's cheaper "
    "business via Denver flies 125 and 150 minutes (275 in all) and does not qualify.",
    twin_of="gorse-inlet", twin_fact="the nonstop's scheduled minutes, 241 or 240")

scenario(
    "gorse-inlet", "boundary_twin", ["multi_leg"], FERN_REQUEST, fern_trip(), fern_search(240),
    expected("BOOK", ["denver-economy"], ["ECONOMY"], NOT_MET, on_file("SUPERVISOR", "OFFICER"), AIR),
    [PREMIUM, LOWEST, SUPERVISOR],
    "Lines 104-106: the nonstop is scheduled at exactly 240 minutes, which is not more than four hours; no flight of any "
    "offer is over four hours, none totals over seven hours and no medical justification is on file. The officer approved "
    "only if the trip qualifies, so economy: the lowest economy fare is United via Denver ($241).",
    twin_of="fern-gable", twin_fact="the nonstop's scheduled minutes, 240 or 241",
    distractors=[LAUNDRY])

HAZEL_REQUEST = ("LaGuardia to Los Angeles on March 15th; my research rotation at the partner hospital starts the next "
                 "morning. Dr. Chen approved business class in writing if the itinerary qualifies under the policy. "
                 "Business if it qualifies, otherwise economy is fine.")


def hazel_trip():
    return trip(traveller_name="Priya Natarajan", traveller_title="Research Fellow, Health Policy", origin="LGA",
                destination="LAX", travel_date="2027-03-15", booking_date="2027-02-15",
                purpose="Start a three-month research rotation at a partner hospital", purpose_kind="RESEARCH_MEETING",
                requested_cabin="BUSINESS",
                sign_offs=[supervisor("Thomas Reed", "Director, Health Policy Fellowship", "research rotation, Los Angeles"),
                           officer("Dr. Wei Chen", "Executive Vice President for Research", True)],
                notes=["One-way: the traveller stays in Los Angeles for the rotation; the trip home is a separate trip."])


def hazel_search(second):
    return search("LGA", "LAX", "2027-03-15", {
        "early": {"carrier": "AA", "depart": "06:00", "via": ["DFW"], "minutes": [215, second], "layovers": [85]},
        "late": {"carrier": "AA", "depart": "11:30", "via": ["DFW"], "minutes": [215, second], "layovers": [95]},
    }, [
        offer("early-economy", "early", "ECONOMY", 41_200),
        offer("early-business", "early", "BUSINESS", 156_000),
        offer("late-economy", "late", "ECONOMY", 39_800),
        offer("late-business", "late", "BUSINESS", 161_000),
    ])


scenario(
    "hazel-marsh", "boundary_twin", ["multi_leg", "dearer_option"], HAZEL_REQUEST, hazel_trip(), hazel_search(206),
    expected("BOOK", ["early-business"], ["BUSINESS"], ["LONG_FLIGHT_APPROVED"], on_file("SUPERVISOR", "OFFICER"), AIR),
    [PREMIUM, SUPERVISOR],
    "Lines 105-106: no flight is over four hours (215 and 206 minutes), but the scheduled in-air time of all the "
    "flights is 421 minutes, more than seven hours (ground time at Dallas is left out). The officer's approval holds: "
    "the cheapest business fare, the 06:00 ($1,560).",
    twin_of="iris-nook", twin_fact="the second flight's scheduled minutes, 206 or 205 (421 or 420 in the air)")

scenario(
    "iris-nook", "boundary_twin", ["multi_leg"], HAZEL_REQUEST, hazel_trip(), hazel_search(205),
    expected("BOOK", ["late-economy"], ["ECONOMY"], NOT_MET, on_file("SUPERVISOR", "OFFICER"), AIR),
    [PREMIUM, LOWEST, SUPERVISOR],
    "Lines 105-106: the flights total 420 minutes in the air, which is not more than seven hours (the 85-95 minute "
    "connections make the elapsed time longer, but in-air time leaves them out); no flight is over four hours and no "
    "medical justification is on file. Economy: the 11:30 ($398).",
    twin_of="hazel-marsh", twin_fact="the second flight's scheduled minutes, 205 or 206 (420 or 421 in the air)")

JUNIPER_REQUEST = ("Washington Dulles to San Francisco on April 6th for the Napa research retreat. My officer, Dr. "
                   "Abernathy, signed business class for me if the trip qualifies under the policy. Business if it "
                   "qualifies, otherwise economy is fine; the retreat starts the next morning.")


def juniper_trip():
    return trip(traveller_name="Samuel Okonkwo", traveller_title="Assistant Professor of Biomedical Informatics",
                origin="IAD", destination="SFO", travel_date="2027-04-06", booking_date="2027-03-09",
                purpose="Research retreat with a partner institute", purpose_kind="RESEARCH_MEETING",
                requested_cabin="BUSINESS",
                sign_offs=[supervisor("Laura Whitfield", "Chair, Biomedical Informatics", "research retreat, Napa"),
                           officer("Dr. Gail Abernathy", "Executive Vice President for Academic Affairs", True)],
                notes=["The traveller drives on from San Francisco to Napa and flies home on a separate trip."])


def juniper_search(second):
    return search("IAD", "SFO", "2027-04-06", {
        "charlotte": {"carrier": "AA", "depart": "07:10", "via": ["CLT"], "minutes": [95, second], "layovers": [65]},
        "chicago": {"carrier": "UA", "depart": "08:45", "via": ["ORD"], "minutes": [125, 230], "layovers": [75]},
    }, [
        offer("charlotte-economy", "charlotte", "ECONOMY", 35_600),
        offer("charlotte-business", "charlotte", "BUSINESS", 132_000),
        offer("chicago-economy", "chicago", "ECONOMY", 33_100),
    ])


scenario(
    "juniper-crest", "boundary_twin", ["multi_leg", "dearer_option"], JUNIPER_REQUEST, juniper_trip(), juniper_search(241),
    expected("BOOK", ["charlotte-business"], ["BUSINESS"], ["LONG_FLIGHT_APPROVED"], on_file("SUPERVISOR", "OFFICER"),
             AIR),
    [PREMIUM, SUPERVISOR],
    "Line 104: any flight segment over four hours qualifies. American via Charlotte flies 95 then 241 minutes: the "
    "second flight is over four hours, so the officer's approval holds for the whole ticket ($1,320). The total (336) "
    "is under seven hours, which does not matter.",
    twin_of="kestrel-moor", twin_fact="the Charlotte-San Francisco flight's scheduled minutes, 241 or 240")

scenario(
    "kestrel-moor", "boundary_twin", ["multi_leg"], JUNIPER_REQUEST, juniper_trip(), juniper_search(240),
    expected("BOOK", ["chicago-economy"], ["ECONOMY"], NOT_MET, on_file("SUPERVISOR", "OFFICER"), AIR),
    [PREMIUM, LOWEST, SUPERVISOR],
    "Lines 104-106: the longest flight is 240 minutes, not more than four hours; the flights total 335 and 355 "
    "minutes, under seven hours; no medical justification. Economy: United via Chicago ($331).",
    twin_of="juniper-crest", twin_fact="the Charlotte-San Francisco flight's scheduled minutes, 240 or 241")

# ===== multi-rule (4) =====

scenario(
    "lumen-sorrel", "multi_rule", ["dearer_option"],
    "Dulles to Frankfurt on May 10th to present our NIH-funded results at the consortium meeting, which starts the "
    "afternoon after I land. Economy, please.",
    trip(traveller_name="Katherine Liu", traveller_title="Research Assistant Professor of Pharmacology", origin="IAD",
         destination="FRA", travel_date="2027-05-10", booking_date="2027-04-12",
         purpose="Present results at an international research consortium meeting", purpose_kind="RESEARCH_MEETING",
         funding="FEDERAL_AWARD", sponsor="National Institutes of Health (R01 research grant)",
         sign_offs=[supervisor("Andrew Feld", "Chair, Department of Pharmacology", "consortium meeting, Frankfurt"),
                    questionnaire()],
         notes=["The traveller has not checked whether Lufthansa is Open Skies compliant for this route."]),
    search("IAD", "FRA", "2027-05-10", {
        "united": {"carrier": "UA", "depart": "17:40", "minutes": [500]},
        "lufthansa": {"carrier": "LH", "depart": "18:05", "minutes": [505]},
    }, [
        offer("united-economy", "united", "ECONOMY", 96_500),
        offer("lufthansa-economy", "lufthansa", "ECONOMY", 88_000),
    ]),
    expected("BOOK", ["united-economy"], ["ECONOMY"], US_REQUIRED, on_file("SUPERVISOR", "EXPORT_COMPLIANCE"),
             [*AIR, "FEDERALLY_FUNDED_AIRLINES"]),
    [FLY_AMERICA, LOWEST, SUPERVISOR],
    "Lines 147-149: the NIH grant pays for foreign travel, so the Fly America Act requires a U.S. air carrier. Lufthansa "
    "is cheaper ($880); United's nonstop ($965) leaves 25 minutes earlier and is the U.S. carrier. No exception is "
    "claimed.", distractors=[QUESTIONNAIRE])

scenario(
    "maple-tor", "multi_rule", ["dearer_option"],
    "Please book Lufthansa from Chicago to Munich on June 14th. They're Open Skies compliant, I checked. If that isn't "
    "allowed, book what the policy allows; I have to be at the military medicine symposium on the 16th.",
    trip(traveller_name="Brian Kowalski", traveller_title="Associate Professor of Orthopaedic Surgery", origin="ORD",
         destination="MUC", travel_date="2027-06-14", booking_date="2027-05-17",
         purpose="Present trauma research at a military medicine symposium", purpose_kind="CONFERENCE",
         funding="FEDERAL_AWARD",
         sponsor="U.S. Department of Defense (Congressionally Directed Medical Research Programs award)",
         preferred_airline="Lufthansa",
         sign_offs=[supervisor("Diane Mercer", "Chair, Orthopaedic Surgery", "military medicine symposium, Munich"),
                    questionnaire()],
         notes=["The traveller checked that Lufthansa is Open Skies compliant for this route."]),
    search("ORD", "MUC", "2027-06-14", {
        "united": {"carrier": "UA", "depart": "16:50", "minutes": [530]},
        "lufthansa": {"carrier": "LH", "depart": "17:35", "minutes": [525]},
    }, [
        offer("united-economy", "united", "ECONOMY", 101_000),
        offer("lufthansa-economy", "lufthansa", "ECONOMY", 90_500),
    ]),
    expected("BOOK", ["united-economy"], ["ECONOMY"], [*US_REQUIRED, "OPEN_SKIES_AGREEMENT"],
             on_file("SUPERVISOR", "EXPORT_COMPLIANCE"), [*AIR, "FEDERALLY_FUNDED_AIRLINES"]),
    [FLY_AMERICA, OPEN_SKIES, SUPERVISOR],
    "Line 149: federally funded foreign travel needs a U.S. carrier. Lines 163-166: the Open Skies exception needs two "
    "criteria, and the first fails: this travel is reimbursed by a Department of Defense award. So United ($1,010), not "
    "Lufthansa ($905), whatever its Open Skies standing.")

scenario(
    "nettle-quay", "multi_rule", ["upgrade_not_taken", "outside_air_section"],
    "Book me business to Tokyo on April 18th; Dr. Brandt approved business class in writing. If business isn't allowed, "
    "economy; I have to be at the Tokyo imaging workshop on the 20th.",
    trip(traveller_name="Elise Varga", traveller_title="Professor of Radiology", origin="DFW", destination="HND",
         travel_date="2027-04-18", booking_date="2027-03-15",
         purpose="Teach at an international imaging workshop", purpose_kind="TRAINING", requested_cabin="BUSINESS",
         funding="NONFEDERAL_AWARD", sponsor="The Hartley Family Foundation (private research award)",
         sponsor_terms=["Air travel paid from this award is limited to economy class."],
         sign_offs=[supervisor("Raymond Ochoa", "Chair, Department of Radiology", "imaging workshop, Tokyo"),
                    officer("Dr. Karl Brandt", "Executive Vice President for Clinical Enterprise", False),
                    questionnaire()]),
    search("DFW", "HND", "2027-04-18", {
        "american": {"carrier": "AA", "depart": "11:00", "minutes": [790]},
        "japan": {"carrier": "JL", "depart": "10:15", "minutes": [785]},
    }, [
        offer("american-economy", "american", "ECONOMY", 138_000),
        offer("american-business", "american", "BUSINESS", 690_000),
        offer("japan-economy", "japan", "ECONOMY", 129_500),
        offer("japan-business", "japan", "BUSINESS", 645_000),
    ]),
    expected("BOOK", ["japan-economy"], ["ECONOMY"], ["SPONSOR_RESTRICTION", "UPGRADE_NOT_ELIGIBLE"],
             on_file("SUPERVISOR", "OFFICER", "EXPORT_COMPLIANCE"),
             [*AIR, "APPROVAL_TO_TRAVEL", "OTHER_CONSIDERATIONS"]),
    [SPONSOR, PREMIUM, SUPERVISOR],
    "The officer's approval and a 785-minute nonstop would allow business under lines 102-104, but the foundation award "
    "that pays limits air travel to economy, and lines 396-399 make a sponsor's more restrictive terms supersede the "
    "policy. Economy: Japan Airlines ($1,295). The award is not federal, so Fly America does not arise.")

THISTLE_SEARCH = search("LAX", "JFK", "2027-01-31", {
    "morning": {"carrier": "DL", "depart": "07:00", "minutes": [325]},
    "afternoon": {"carrier": "AA", "depart": "13:15", "minutes": [320]},
    "redeye": {"carrier": "B6", "depart": "21:30", "minutes": [315]},
    "chicago": {"carrier": "UA", "depart": "22:10", "via": ["ORD"], "minutes": [240, 125], "layovers": [150]},
}, [
    offer("morning-economy", "morning", "ECONOMY", 34_200),
    offer("afternoon-economy", "afternoon", "ECONOMY", 31_800),
    offer("redeye-economy", "redeye", "ECONOMY", 27_600),
    offer("chicago-economy", "chicago", "ECONOMY", 23_100),
])

scenario(
    "thistle-cove", "multi_rule", ["date_arithmetic", "month_end", "dearer_option", "multi_leg", "synonym"],
    "A donor has offered to fly me to New York on his company's jet for the 9 a.m. board meeting on February 1st. If I "
    "can't take it, book me a commercial economy flight from LAX on January 31st that gets me there in time.",
    trip(traveller_name="Margaret Ellison", traveller_title="Vice President, Development", origin="LAX",
         destination="JFK", travel_date="2027-01-31", booking_date="2027-01-12", must_arrive_by="2027-02-01 09:00",
         purpose="Board meeting of a donor foundation", purpose_kind="BOARD_MEETING",
         outside_option="PRIVATE_AIRCRAFT",
         outside_option_detail="A seat on a donor's corporate jet from Van Nuys to Teterboro on January 31st",
         sign_offs=[supervisor("Charles Abbott", "Chief Development Officer", "donor foundation board meeting, New York")],
         notes=["No approval for flying on a non-airline plane is on file."]),
    THISTLE_SEARCH,
    expected("BOOK", ["redeye-economy"], ["ECONOMY"], ["PRIVATE_AIRCRAFT_NOT_APPROVED"],
             on_file("SUPERVISOR", "RISK_MANAGEMENT", "CHIEF_FINANCIAL_OFFICER"),
             [*AIR, "PRIVATE_AIRCRAFT"]),
    [PRIVATE, LOWEST, SUPERVISOR],
    "Lines 134-138: a corporate jet is non-commercial aircraft, prohibited without written approval from Risk and "
    "Insurance Management and the CFO, and none is on file. Line 88: the lowest economy fare that meets the business "
    "need. The United connection ($231) leaves January 31 and lands February 1 at 09:45, after 09:00; the JetBlue "
    "red-eye ($276) lands February 1 at 05:45.")

# ===== hidden clause (2) =====

scenario(
    "poplar-vane", "hidden_clause", ["dearer_option", "outside_air_section"],
    "Chicago to Atlanta on May 24th to hand-carry the trial's temperature-controlled sample cooler to the central lab. "
    "The COO and the CFO both signed an exception so I can fly business and keep the cooler at my seat. Business, "
    "please.",
    trip(traveller_name="Tomas Herrera", traveller_title="Clinical Trials Lab Manager", origin="ORD",
         destination="ATL", travel_date="2027-05-24", booking_date="2027-05-03",
         purpose="Hand-carry research samples to a trial's central laboratory", purpose_kind="SITE_VISIT",
         requested_cabin="BUSINESS",
         sign_offs=[supervisor("Nadine Foster", "Director, Clinical Trials Center", "central lab sample delivery, Atlanta"),
                    sign("CHIEF_OPERATING_OFFICER", "Dr. Alan Pierce", "Chief Operating Officer", "POLICY_EXCEPTION",
                         "Approved an exception to the travel policy: business class for this trip, to keep the "
                         "sample cooler at the traveller's seat."),
                    sign("CHIEF_FINANCIAL_OFFICER", "Cecily Monroe", "Chief Financial Officer", "POLICY_EXCEPTION",
                         "Approved an exception to the travel policy: business class for this trip, to keep the "
                         "sample cooler at the traveller's seat.")]),
    search("ORD", "ATL", "2027-05-24", {
        "delta": {"carrier": "DL", "depart": "09:20", "minutes": [120]},
        "charlotte": {"carrier": "AA", "depart": "07:05", "via": ["CLT"], "minutes": [105, 70], "layovers": [55]},
    }, [
        offer("delta-economy", "delta", "ECONOMY", 19_800),
        offer("delta-business", "delta", "BUSINESS", 61_200),
        offer("charlotte-economy", "charlotte", "ECONOMY", 17_600),
    ]),
    expected("BOOK", ["delta-business"], ["BUSINESS"], ["POLICY_EXCEPTION_APPROVED"],
             on_file("SUPERVISOR", "CHIEF_OPERATING_OFFICER", "CHIEF_FINANCIAL_OFFICER"), [*AIR, "POLICY"]),
    [EXCEPTIONS, PREMIUM, SUPERVISOR],
    "Lines 102-108 alone would not allow business on a 120-minute flight with no officer approval. Lines 67-68, in the "
    "Policy preamble before section 1: exceptions require approval of the COO and the CFO, and both approved this one in "
    "writing. The only business fare is Delta's ($612).")

scenario(
    "rook-tallow", "hidden_clause", ["synonym"],
    "JFK to Dublin on May 3rd for the genomics meeting, which starts the afternoon after I land. I found Aer Lingus for "
    "$612 on their own website, cheaper than what VUMC's booking tool shows, so I'll buy it there and expense it; saving "
    "money is a business need. If I can't, book what the policy allows.",
    trip(traveller_name="Owen Fitzgerald", traveller_title="Genetic Counselor", origin="JFK", destination="DUB",
         travel_date="2027-05-03", booking_date="2027-04-05",
         purpose="International genomics consortium meeting", purpose_kind="RESEARCH_MEETING",
         outside_option="AIRLINE_WEBSITE",
         outside_option_detail="An Aer Lingus fare of $612 on the airline's own website, outside VUMC's booking tool and "
                               "travel agency",
         sign_offs=[supervisor("Beatrice Long", "Director, Genetic Counseling", "genomics meeting, Dublin"),
                    questionnaire()],
         notes=["The fares search_flights lists are the ones VUMC's online booking tool and travel agency can book."]),
    search("JFK", "DUB", "2027-05-03", {
        "aerlingus": {"carrier": "EI", "depart": "18:30", "minutes": [400]},
        "delta": {"carrier": "DL", "depart": "20:15", "minutes": [410]},
    }, [
        offer("aerlingus-economy", "aerlingus", "ECONOMY", 68_800),
        offer("delta-economy", "delta", "ECONOMY", 70_500),
    ]),
    expected("BOOK", ["aerlingus-economy"], ["ECONOMY"], ["BOOKING_TOOL_REQUIRED"],
             on_file("SUPERVISOR", "EXPORT_COMPLIANCE"), [*AIR, "AIR_RESERVATIONS"]),
    [RESERVATIONS, COST_NOTE, LOWEST, SUPERVISOR],
    "Lines 73-76: all international air reservations must be made through the online booking tool or the travel agency, "
    "except in documented extreme cases necessitated by business needs or safety; the footnote (line 84) says cost is "
    "not a business need. So not the website fare: the lowest economy fare the tool lists, Aer Lingus $688.",
    distractors=[QUESTIONNAIRE])

# ===== distractor (2) =====

scenario(
    "sable-wren", "distractor", ["multi_leg"],
    "Boston to San Francisco on February 22nd for the cardiology summit. It's a long flight, so business please. My VP "
    "declined to sign for business this time, but surely a flight that long qualifies anyway? If it doesn't, economy is "
    "fine; the summit starts the next morning.",
    trip(traveller_name="Natalie Brooks", traveller_title="Cardiology Nurse Practitioner", origin="BOS",
         destination="SFO", travel_date="2027-02-22", booking_date="2027-01-25",
         purpose="National cardiology summit", purpose_kind="CONFERENCE", requested_cabin="BUSINESS",
         sign_offs=[supervisor("Greg Patel", "Nurse Manager, Cardiology", "cardiology summit, San Francisco")],
         notes=["The traveller's officer, Dr. Joan Whitaker, declined in writing to approve business class for this trip."]),
    search("BOS", "SFO", "2027-02-22", {
        "nonstop": {"carrier": "UA", "depart": "08:00", "minutes": [385]},
        "chicago": {"carrier": "AA", "depart": "07:15", "via": ["ORD"], "minutes": [150, 270], "layovers": [70]},
    }, [
        offer("nonstop-economy", "nonstop", "ECONOMY", 32_900),
        offer("nonstop-business", "nonstop", "BUSINESS", 145_000),
        offer("chicago-economy", "chicago", "ECONOMY", 30_100),
        offer("chicago-business", "chicago", "BUSINESS", 121_000),
    ]),
    expected("BOOK", ["chicago-economy"], ["ECONOMY"], ["UPGRADE_NOT_ELIGIBLE"], on_file("SUPERVISOR", "OFFICER"), AIR),
    [OFFICER_ONLY, LOWEST, SUPERVISOR],
    "Lines 102-103: business may be used only if the applicable officer approves it in writing in advance; the officer "
    "declined. The flight-length condition (line 104) is met, but it is a condition beside the approval, not instead "
    "of it. Economy: American via Chicago ($301).",
    distractors=[CONDITIONS])

scenario(
    "quill-saddle", "distractor", ["outside_air_section"],
    "Minneapolis to Phoenix on March 9th for the grand rounds visit. Please put me on Delta; I'm close to my next "
    "SkyMiles status level. If that isn't allowed, book what the policy allows.",
    trip(traveller_name="Kevin Marsh", traveller_title="Assistant Professor of Medicine", origin="MSP",
         destination="PHX", travel_date="2027-03-09", booking_date="2027-02-09",
         purpose="Visiting lecturer at grand rounds", purpose_kind="CONFERENCE", preferred_airline="Delta Air Lines",
         sign_offs=[supervisor("Sandra Okoye", "Vice Chair, Department of Medicine", "grand rounds visit, Phoenix")]),
    search("MSP", "PHX", "2027-03-09", {
        "american": {"carrier": "AA", "depart": "08:40"},
        "delta": {"carrier": "DL", "depart": "10:05"},
        "southwest": {"carrier": "WN", "depart": "13:15"},
    }, [
        offer("american-economy", "american", "ECONOMY", 24_300),
        offer("delta-economy", "delta", "ECONOMY", 28_400),
        offer("southwest-economy", "southwest", "ECONOMY", 25_900),
    ]),
    expected("BOOK", ["american-economy"], ["ECONOMY"], ["LOWEST_FARE", "LOYALTY_PROGRAM_PREFERENCE"],
             on_file("SUPERVISOR"), [*AIR, "OTHER_CONSIDERATIONS", "REWARD_POINTS"]),
    [REWARDS, LOWEST, SUPERVISOR],
    "Line 475 lets travellers use rewards, but lines 476-478 forbid any additional expense to VUMC to obtain more "
    "rewards, and line 88 asks for the lowest economy fare. Delta is $41 dearer: American ($243).",
    distractors=[REWARDS_OK, RECEIPTS])

# ===== refusal (2) =====

scenario(
    "umber-cask", "refusal", ["multi_traveller", "outside_air_section"],
    "Please book my husband, Marcus, on a flight to Orlando on April 26th; he's coming along to the pediatric "
    "hospital medicine conference with me.",
    trip(traveller_name="Marcus Brooks", traveller_title="Husband of the employee", passenger="COMPANION",
         accompanies="Dr. Imani Brooks, Associate Professor of Pediatrics", origin="ATL", destination="MCO",
         travel_date="2027-04-26", booking_date="2027-03-29",
         purpose="Accompany his wife to a pediatric hospital medicine conference", purpose_kind="CONFERENCE",
         sign_offs=[supervisor("Harold Vance", "Chair, Department of Pediatrics",
                               "Dr. Imani Brooks to the pediatric hospital medicine conference, Orlando")]),
    search("ATL", "MCO", "2027-04-26", {
        "delta": {"carrier": "DL", "depart": "08:25"},
        "southwest": {"carrier": "WN", "depart": "10:50"},
    }, [
        offer("delta-economy", "delta", "ECONOMY", 14_900),
        offer("southwest-economy", "southwest", "ECONOMY", 13_900),
    ]),
    expected("REFUSE", [], ["NONE"], ["COMPANION_NOT_COVERED", "PERSONAL_TRAVEL_NOT_COVERED"], on_file("SUPERVISOR"),
             ["COMPANION_EXPENSES", "COMPANION_TRAVEL"]),
    [COMPANION],
    "Lines 356-358: no travel expenses, transportation included, for any persons accompanying travelers on VUMC travel "
    "are reimbursed. VUMC buys no ticket for the husband. The supervisor's approval is for the employee's trip.")

scenario(
    "vetch-orchard", "refusal", ["personal_travel", "outside_air_section"],
    "After the Denver conference ends on the 19th I'm spending a few days of vacation in Las Vegas. Please book Denver "
    "to Las Vegas on March 20th through the travel tool.",
    trip(traveller_name="Allison Trent", traveller_title="Pharmacy Operations Manager", origin="DEN", destination="LAS",
         travel_date="2027-03-20", booking_date="2027-02-22",
         purpose="Vacation in Las Vegas after a business conference in Denver", purpose_kind="PERSONAL",
         sign_offs=[supervisor("Philip Grant", "Director of Pharmacy", "pharmacy operations conference, Denver, March 16-19")]),
    search("DEN", "LAS", "2027-03-20", {
        "southwest": {"carrier": "WN", "depart": "09:30"},
        "united": {"carrier": "UA", "depart": "12:10"},
    }, [
        offer("southwest-economy", "southwest", "ECONOMY", 11_900),
        offer("united-economy", "united", "ECONOMY", 14_200),
    ]),
    expected("REFUSE", [], ["NONE"], ["OUTSIDE_POLICY_SCOPE", "PERSONAL_TRAVEL_NOT_COVERED"], on_file("SUPERVISOR"),
             ["COMBINED_PERSONAL_AND_BUSINESS", "OTHER_CONSIDERATIONS", "UNALLOWABLE_EXPENSES"]),
    [PERSONAL, VACATION],
    "Lines 458-461: when personal travel is combined with VUMC business travel, only the business portion is "
    "reimbursable, and the travel tool should not be used for personal travel; lines 523-525 list vacation expenses on "
    "business trips as non-reimbursable. VUMC buys no ticket for the vacation leg.")

# ===== flag (3) =====

scenario(
    "willow-brine", "flag", ["unclear_phrase"],
    "Boston to Miami on April 12th for the nursing leadership conference, which opens the next morning. Premium economy please; I'd like the extra "
    "legroom on this one.",
    trip(traveller_name="Denise Carter", traveller_title="Nurse Manager, Medical ICU", origin="BOS", destination="MIA",
         travel_date="2027-04-12", booking_date="2027-03-15", purpose="Nursing leadership conference",
         requested_cabin="PREMIUM_ECONOMY",
         sign_offs=[supervisor("Frank Liu", "Director of Critical Care Nursing", "nursing leadership conference, Miami")]),
    search("BOS", "MIA", "2027-04-12", {
        "american": {"carrier": "AA", "depart": "08:30", "minutes": [190]},
        "jetblue": {"carrier": "B6", "depart": "10:45", "minutes": [195]},
    }, [
        offer("american-economy", "american", "ECONOMY", 25_800),
        offer("american-premium", "american", "PREMIUM_ECONOMY", 34_600),
        offer("jetblue-economy", "jetblue", "ECONOMY", 27_100),
        offer("jetblue-premium", "jetblue", "PREMIUM_ECONOMY", 33_100),
    ]),
    expected("FLAG_FOR_APPROVAL", ["american-economy", "jetblue-premium"], ["ECONOMY", "PREMIUM_ECONOMY"],
             UNCLEAR_REASONS, UNCLEAR_ROLES, AIR,
             phrase="economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.)"),
    [LOWEST, UPGRADE_FEES, PREMIUM, INTERPRETATION, EXCEPTIONS, SUPERVISOR],
    "Line 88 asks for the lowest economy fare, and lines 102-108 regulate only business and first class. Lines 92-93 "
    "make fees for 'economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.)' reimbursable. Whether a "
    "premium economy fare is such an upgrade (book JetBlue premium, $331) or a class of service above economy that the "
    "traveller pays for personally (book American economy, $258) is not settled. Hold either; line 654 sends questions "
    "of interpretation to the finance policy office.",
    flag_twins=["cedar-quill", "birch-ember"],
    ambiguity={"phrase": "economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.)",
               "readings": [("a premium economy seat is an economy class upgrade like Economy Plus, so its cost is "
                            "reimbursable: book the cheapest premium economy fare"),
                            ("premium economy is a class of service above economy; the policy buys the lowest economy "
                            "fare and upgrades are at personal expense: book the cheapest economy fare")]})

YARROW_SEARCH = search("BOS", "SLC", "2027-05-11", {
    "delta": {"carrier": "DL", "depart": "07:00", "via": ["DTW"], "minutes": [120, 225], "layovers": [70],
              "return": {"depart": "08:30", "via": ["DTW"], "minutes": [215, 115], "layovers": [80]}},
    "united": {"carrier": "UA", "depart": "06:15", "via": ["ORD"], "minutes": [140, 215], "layovers": [75],
               "return": {"depart": "09:10", "via": ["ORD"], "minutes": [205, 130], "layovers": [70]}},
}, [
    offer("delta-economy", "delta", "ECONOMY", 46_200),
    offer("delta-business", "delta", "BUSINESS", 188_000),
    offer("united-economy", "united", "ECONOMY", 48_900),
    offer("united-business", "united", "BUSINESS", 196_000),
], return_date="2027-05-14")

scenario(
    "yarrow-flint", "flag", ["multi_leg", "unclear_phrase"],
    "Round trip Boston to Salt Lake City on one ticket, out May 11th and back May 14th, for the transplant registry site "
    "visit. Dr. Kim approved business class in writing if the trip qualifies under the policy. Business if it "
    "qualifies, otherwise economy.",
    trip(traveller_name="Rebecca Sloane", traveller_title="Transplant Quality Coordinator", origin="BOS",
         destination="SLC", travel_date="2027-05-11", return_date="2027-05-14", booking_date="2027-04-12",
         purpose="Site visit for a transplant registry audit", purpose_kind="SITE_VISIT", requested_cabin="BUSINESS",
         sign_offs=[supervisor("Mark Delgado", "Director, Transplant Quality", "transplant registry site visit, Salt Lake City"),
                    officer("Dr. Hyun Kim", "Executive Vice President for Transplant Services", True)]),
    YARROW_SEARCH,
    expected("FLAG_FOR_APPROVAL", ["delta-business", "delta-economy"], ["BUSINESS", "ECONOMY"], UNCLEAR_REASONS,
             UNCLEAR_ROLES, AIR, phrase="The total scheduled in-air flight time for all flight segments"),
    [PREMIUM, INTERPRETATION, EXCEPTIONS, SUPERVISOR],
    "No flight is over four hours (line 104). Each journey's flights total under seven hours in the air (Delta 345 out, "
    "330 back; United 355 and 335), but the round-trip ticket's four flights together total 675 or 690. 'The total "
    "scheduled in-air flight time for all flight segments' (line 105) may mean every flight of the ticket (business "
    "qualifies: Delta $1,880) or the flights of one journey (economy: Delta $462). Hold either.",
    flag_twins=["hazel-marsh", "iris-nook"],
    ambiguity={"phrase": "The total scheduled in-air flight time for all flight segments",
               "readings": [("all the flight segments of the ticket, out and back: 675 minutes, over seven hours, so "
                            "the officer's approval holds and the cheapest business fare is booked"),
                            ("the flight segments of one journey: 345 minutes out, under seven hours, so the cheapest "
                            "economy fare")]})

scenario(
    "zinnia-cobble", "flag", ["approval_required", "outside_air_section"],
    "Charlotte to Austin on February 17th for the coding compliance training, which starts the next morning. My supervisor hasn't approved the trip "
    "yet (she's back Thursday), but can you take care of the flight?",
    trip(traveller_name="Jasmine Wright", traveller_title="Coding Compliance Analyst", origin="CLT", destination="AUS",
         travel_date="2027-02-17", booking_date="2027-01-19", purpose="Coding compliance training",
         purpose_kind="TRAINING",
         notes=[("The traveller's supervisor, Angela Ruiz, Manager of Coding Compliance, has the trip request and has "
                "not approved it yet.")]),
    search("CLT", "AUS", "2027-02-17", {
        "american": {"carrier": "AA", "depart": "09:10"},
        "southwest": {"carrier": "WN", "depart": "12:40"},
        "denver": {"carrier": "UA", "depart": "07:20", "via": ["DEN"]},
    }, [
        offer("american-economy", "american", "ECONOMY", 23_100),
        offer("southwest-economy", "southwest", "ECONOMY", 24_700),
        offer("denver-economy", "denver", "ECONOMY", 21_900),
    ]),
    expected("FLAG_FOR_APPROVAL", ["denver-economy"], ["ECONOMY"], ["APPROVAL_REQUIRED"], ["SUPERVISOR"],
             ["APPROVAL_TO_TRAVEL", "OTHER_CONSIDERATIONS"]),
    [SUPERVISOR, LOWEST],
    "Lines 383-384: travelers must have their supervisor's approval to take a trip prior to committing VUMC funds or "
    "incurring expenses; buying the ticket commits funds, and the approval is not yet given. Hold the lowest economy "
    "fare (United via Denver, $219) for the supervisor: approval required, not 'no compliant offer'.",
    flag_twins=["amber-loom", "umber-cask"],
    ambiguity="none: an approval is required and missing; the text is clear")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for data in S:
        (OUT / f"{data['id']}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(S)} scenarios to {OUT}")


if __name__ == "__main__":
    main()
