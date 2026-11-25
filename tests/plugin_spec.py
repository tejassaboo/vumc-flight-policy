"""The handbook-specific settings the template's acceptance tests read. Every other file in tests/ is the
template's and stays identical across plugins (see TEMPLATE_GUIDE.md)."""

from pathlib import Path

import contract

ROOT = Path(__file__).resolve().parents[1]

# Ids that are published or taken: a new plugin never reuses one (MASTER_PLAN section 4, "id check").
PUBLISHED_IDS = {
    "aiib-delegation-entitlement", "ec-mission-cabin-allowance", "ftr-city-pair-fare-selection",
    "gates-vendor-flight-ranking", "njc-cabin-meal-allowance", "sfc-travel-preapproval", "uc-g28-expense-audit",
    "un-staff-air-travel-audit", "vt-airfare-policy-booking", "wa-saam-travel-versioned-audit",
    "energy-corporate-flight-booking", "pharma-distributor-flight-booking", "shipping-company-flight-booking",
    "telecommunications-flight-booking", "preference-aware-flight-booking", "llm-context-compress",
    "weather-alert", "word-check", "arxiv-source",
}

# The frozen original's SHA256SUMS, when this checkout sits beside pilot_work/ (skipped elsewhere).
FROZEN_SHA256SUMS = ROOT.parents[1] / "pilot_work" / "originals" / "vumc" / "frozen" / "SHA256SUMS"

# Scenario mix by primary category (EDGE_CASES.md section 5.2; the 24-scenario row).
MIX = {"easy": 5, "boundary_twin": 6, "multi_rule": 4, "hidden_clause": 2, "distractor": 2, "refusal": 2, "flag": 3}

# Overlay minimums (EDGE_CASES.md section 5.3) for the rules this handbook has. It has no overnight-stop rule,
# so no overnight scenario is required.
OVERLAY_MINIMUMS = {
    "multi_leg": 3, "date_arithmetic": 2, "month_end": 1, "personal_travel": 1, "multi_traveller": 1,
    "dearer_option": 2, "upgrade_not_taken": 2, "outside_air_section": 2,
}

# Words a scenario id may not contain beyond the template's universal list: this handbook's rule and role
# terms.
ID_FORBIDDEN_TERMS = {
    "officer", "business", "first", "class", "economy", "premium", "plus", "upgrade", "medical", "federal", "america",
    "skies", "open", "private", "jet", "charter", "aircraft", "plane", "sponsor", "grant", "award", "foundation",
    "companion", "spouse", "husband", "wife", "partner", "personal", "vacation", "holiday", "supervisor", "exception",
    "coo", "cfo", "booking", "tool", "agency", "website", "miles", "points", "rewards", "loyalty", "deadline",
    "nonstop", "connection", "segment", "total", "hours", "round", "return", "ead", "disability", "risk", "export",
    "questionnaire", "international", "domestic", "fly", "carrier", "refundable", "penalty", "unused", "rail",
}

# The handbook-specific enums whose member words a scenario id may not contain either.
ID_CATEGORY_ENUMS = [contract.Passenger, contract.Purpose, contract.Funding, contract.OutsideOption,
                     contract.SignOffSubject]

# How many scenarios a degenerate agent may pass: one that always holds the right offer for approval, and
# one that always books the cheapest seat (with the right section and approver NONE).
MAX_PASS_ALWAYS_FLAG = 2
MAX_PASS_ALWAYS_LOWEST = 3  # amber-loom, cedar-quill, quill-saddle: the lowest seat is right and LOWEST_FARE accepted

# Hand-built duration cases beyond the automatic both-sides tests: (rule, outbound scheduled minutes per
# flight, layovers, expected True / False / None for unclear).
DURATION_CASES = [
    ("segment", [241], [], True),
    ("segment", [240], [], False),
    ("segment", [95, 241], [65], True),  # any one flight over four hours
    ("segment", [95, 240], [65], False),
    ("segment", [240, 240], [60], False),  # flights are never added for this rule
    ("total", [421], [], True),
    ("total", [215, 206], [85], True),  # in-air time added, ground time left out
    ("total", [215, 205], [85], False),  # 420 in the air, though 505 elapsed
    ("total", [140, 140, 140], [60, 60], False),
]
