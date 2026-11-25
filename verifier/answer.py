"""The answer key of one scenario, shared byte for byte by the tools (src/plugin/answer.py) and the
verifier (verifier/answer.py): the trip record, the offers on its route and date, and the handbook rules'
answer, checked for a consistent shape."""

from contract import Cabin, Decision, ReasonCode

from . import rules
from .scenarios import trip_record
from .world import trip_offers

FIELDS = ("decision", "offer_ids", "cabins", "reason_codes", "approvers", "clauses", "unclear_phrase", "explanation")


def answer_key(scenario):
    """(trip, offers, slots by offer id, answer) for a scenario dict."""
    trip = trip_record(scenario)
    offers, slots = trip_offers(scenario)
    # answer_key_inputs: facts only the answer key sees (never shown by a tool), e.g. a region the agent must
    # work out from the handbook itself. Optional; {} when the scenario has none.
    key = rules.solve(trip, offers, scenario.get("answer_key_inputs", {}))
    problem = shape_problem(key, slots)
    if problem:
        raise ValueError(f"{scenario['id']}: the rules gave an inconsistent answer: {problem}")
    return trip, offers, slots, key


def shape_problem(key, slots):
    if sorted(key) != sorted(FIELDS):
        return f"fields {sorted(key)}"
    if key["decision"] == Decision.REFUSE:
        if key["offer_ids"] or key["cabins"] != [Cabin.NONE]:
            return "a refusal names no offer and cabin NONE"
    elif not key["offer_ids"] or any(offer not in slots for offer in key["offer_ids"]):
        return "a booking or hold names offers from the search"
    for name in ("cabins", "reason_codes", "approvers", "clauses"):
        if not key[name]:
            return f"{name} is empty"
    # A hold is over unclear words (the phrase, UNCLEAR_POLICY_TEXT, and possibly APPROVAL_REQUIRED beside it) or
    # over a missing sign-off (APPROVAL_REQUIRED, possibly beside the reason that calls for the sign-off); a
    # booking or refusal carries neither code and no phrase.
    reasons = key["reason_codes"]
    unclear, approval = ReasonCode.UNCLEAR_POLICY_TEXT in reasons, ReasonCode.APPROVAL_REQUIRED in reasons
    if key["decision"] != Decision.FLAG_FOR_APPROVAL:
        if unclear or approval or key["unclear_phrase"]:
            return "a booking or refusal names no hold reason and no unclear phrase"
    elif key["unclear_phrase"] and not unclear:
        return "a hold over unclear words carries UNCLEAR_POLICY_TEXT"
    elif not key["unclear_phrase"] and (unclear or not approval):
        return "a hold over a missing sign-off carries APPROVAL_REQUIRED and no unclear phrase"
    return ""
