"""The answer contract: closed lists that include codes for rules this handbook lacks, the shared part
unchanged, and a verifier package that keeps NanoAgent's static rules (stock `plugin inspect` checks them
too)."""

import ast

import contract
from helpers import scenarios
from plugin_spec import ROOT

SHARED_REASON_CODES = {
    "LOWEST_FARE", "UPGRADE_NOT_ELIGIBLE", "CLIENT_REIMBURSABLE", "UPGRADE_WITHIN_FARE_MARGIN", "MEDICAL_NEED",
    "COST_SAVINGS", "NO_ECONOMY_SEATS_URGENT", "TRAVELER_PAYS_UPGRADE", "LONG_FLIGHT_APPROVED",
    "LONG_FLIGHT_CONDITION_NOT_MET", "PREMIUM_ECONOMY_ALLOWED", "UPGRADE_COST_NOT_NOMINAL",
    "ALTERNATE_ROUTE_WITHIN_MARGIN", "ALTERNATE_ROUTE_TOO_EXPENSIVE", "LOYALTY_PROGRAM_PREFERENCE",
    "COMPANION_NOT_COVERED", "PERSONAL_TRAVEL_NOT_COVERED", "OUTSIDE_POLICY_SCOPE", "NO_COMPLIANT_OFFER",
    "APPROVAL_REQUIRED", "UNCLEAR_POLICY_TEXT", "ADVANCE_PURCHASE_TOO_LATE", "DISTANCE_BELOW_MINIMUM",
    "DRIVING_EXPECTED", "RAIL_PREFERRED", "REFUNDABLE_FARE_NOT_ALLOWED", "PREFERRED_CARRIER_REQUIRED",
    "CONNECTION_TOO_LONG", "OVERNIGHT_STOP_REQUIRED", "NATIONAL_CARRIER_REQUIRED", "SENIOR_ROLE_ENTITLEMENT",
    "INTERNATIONAL_LONG_FLIGHT", "TRAVELLER_LIMIT_PER_FLIGHT",
}
VERIFIER_IMPORTS = {
    "collections", "dataclasses", "decimal", "difflib", "enum", "fractions", "functools", "hashlib", "itertools",
    "json", "math", "operator", "pathlib", "re", "statistics", "string", "textwrap", "typing", "unicodedata",
    "__future__", "contract",
}
FORBIDDEN_NAMES = {"open", "eval", "exec", "compile", "getattr", "setattr", "delattr", "vars", "globals", "locals",
                   "input", "__import__", "breakpoint"}


def test_decisions_and_cabins():
    assert [member.value for member in contract.Decision] == ["BOOK", "REFUSE", "FLAG_FOR_APPROVAL"]
    assert contract.Cabin.NONE in contract.Cabin


def test_shared_reason_codes_are_all_there():
    assert SHARED_REASON_CODES <= {member.value for member in contract.ReasonCode}


def test_closed_lists_hold_codes_no_scenario_uses():
    used = {code for data in scenarios() for code in data["expected"]["reason_codes"]}
    assert len({member.value for member in contract.ReasonCode} - used) >= 10
    used_roles = {role for data in scenarios() for role in data["expected"]["approvers"]}
    assert len({member.value for member in contract.Approver} - used_roles) >= 3
    assert {"NONE", "NOT_NAMED"} <= {member.value for member in contract.Approver}


def test_verifier_keeps_the_static_rules():
    for path in sorted((ROOT / "verifier").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] in VERIFIER_IMPORTS, (path.name, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module.split(".")[0] in VERIFIER_IMPORTS, (path.name, node.module)
                assert not any(alias.name.startswith("_") for alias in node.names), path.name
            elif isinstance(node, ast.Name):
                assert node.id not in FORBIDDEN_NAMES, (path.name, node.id)
            elif isinstance(node, ast.Attribute):
                assert not node.attr.startswith("_"), (path.name, node.attr)
    assert sorted(path.name for path in (ROOT / "verifier").iterdir() if path.name != "__pycache__") == sorted(
        path.name for path in (ROOT / "verifier").glob("*.py"))
