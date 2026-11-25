"""Shared test helpers of the original-handbook template."""

import hashlib
import json
from pathlib import Path

from contract import BookingOutput, Cabin, TaskInput
from plugin import solve_booking
from plugin.scenarios import scenario, scenario_ids

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "plugin" / "data"
POLICY_LINES = (DATA / "policy.txt").read_text(encoding="utf-8").split("\n")


def normalized(text):
    return " ".join(text.split())


def range_text(lines):
    start, end = lines
    return normalized(" ".join(POLICY_LINES[start - 1:end]))


def range_hash(lines):
    return hashlib.sha256(range_text(lines).encode()).hexdigest()


def scenarios():
    return [scenario(name) for name in scenario_ids()]


def task_input(data):
    return build_task_input(data)


def build_task_input(data):
    from contract import Scenario

    return TaskInput(scenario=Scenario(data["id"]), request=data["request"])


def reference(data):
    return solve_booking(build_task_input(data))


def right_answer(key):
    """The first accepted value of every field (the first accepted offer, in its own cabin): a correct
    submission."""
    return BookingOutput(
        decision=key.decision,
        offer_id=key.offer_ids[0] if key.offer_ids else "",
        cabin=next(offer.cabin for offer in key.offers if offer.offer_id == key.offer_ids[0]) if key.offer_ids
        else Cabin.NONE,
        reason_code=key.reason_codes[0],
        approver=key.approvers[0],
        clause=key.clauses[0],
    )


def first_search(data):
    """A SearchInput for the scenario's first pinned search."""
    from contract import Scenario, SearchInput

    spec = data["world"]["searches"][0]
    return SearchInput(scenario=Scenario(data["id"]), origin=spec["origin"], destination=spec["destination"],
                       date=spec["date"], return_date=spec.get("return_date", ""))


def dumps(value):
    return json.dumps(value, sort_keys=True)
