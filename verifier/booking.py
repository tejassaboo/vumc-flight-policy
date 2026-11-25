"""verify_task for the booking task: the verifier rebuilds the scenario's offers and the handbook rules'
answer itself, then checks every submitted field against the accepted values."""

from contract import Decision

from .answer import answer_key
from .checks import plain, result
from .scenarios import scenario
from .tools import field_of

GRADED = ("decision", "offer_id", "cabin", "reason_code", "approver", "clause")


def accepted(key, offers=(), chosen=""):
    """Each graded field and the values the answer key accepts for it. The cabin is the chosen offer's own
    cabin whenever that offer is an accepted one, so a hold that accepts offers in several cabins cannot be
    passed by pairing one offer with another offer's cabin."""
    cabins = key["cabins"]
    if chosen in key["offer_ids"]:
        cabins = [offer.cabin for offer in offers if offer.offer_id == chosen][:1]
    return {
        "decision": [key["decision"]],
        "offer_id": key["offer_ids"] if key["decision"] != Decision.REFUSE else [""],
        "cabin": cabins,
        "reason_code": key["reason_codes"],
        "approver": key["approvers"],
        "clause": key["clauses"],
    }


def submitted(output):
    return {
        "decision": output.decision, "offer_id": output.offer_id, "cabin": output.cabin,
        "reason_code": output.reason_code, "approver": output.approver, "clause": output.clause,
    }


def verify_task(arguments, output, reference, workspace):
    data = scenario(arguments.scenario)
    if arguments.request != data["request"]:
        return result(False, "the task input's request is not this scenario's request", score=0.0)
    trip, offers, slots, key = answer_key(data)
    if reference is not None:
        if reference.trip != trip or reference.offers != offers:
            return result(False, "the pinned reference's trip or offers differ from the verifier's", score=0.0)
        for name, value in key.items():
            if field_of(reference, name) != value:
                return result(False, f"the pinned reference's {name} differs from the verifier's answer", score=0.0)
    wanted, given = accepted(key, offers, output.offer_id), submitted(output)
    wrong = [name for name in GRADED if given[name] not in wanted[name]]
    known = output.offer_id == "" or output.offer_id in slots
    details = {
        "expected": {name: plain(values) for name, values in wanted.items()},
        "submitted": {name: plain(value) for name, value in given.items()},
        "wrong": wrong,
        "offer_known": known,
        "unclear_phrase": key["unclear_phrase"],
        "explanation": key["explanation"],
    }
    score = (len(GRADED) - len(wrong)) / len(GRADED)
    if not wrong:
        return result(True, f"correct: {key['decision'].value} ({key['explanation']})", score=1.0, **details)
    note = "" if known else "; offer_id is not an offer search_flights lists for this trip"
    return result(False, f"wrong {', '.join(wrong)}{note}", score=score, **details)
