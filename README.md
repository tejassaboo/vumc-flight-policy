# VUMC Flight Policy

**No affiliation with Vanderbilt University Medical Center.** The policy is VUMC's published *Finance Policy FIN
4.7, Travel* (effective June 2021), bundled verbatim for research. Its public URL was not recorded when it was
downloaded (`pilot_work/originals/MANIFEST.md` marks it UNVERIFIED; the raw PDF and its sha256 are the pinned copy):
confirm the source, and that the course staff allow redistribution, before publishing this plugin.

A `nanoagent.plugin/v0001` plugin. An agent handles one traveller's flight request under the medical center's
real travel policy: it reads the trip record, searches a simulated flight world and submits **BOOK**,
**REFUSE** or **FLAG_FOR_APPROVAL** with the offer, cabin, reason, approver and policy section. A
deterministic Python verifier, with no LLM, rebuilds the offers and the policy's answer itself and checks
every field.

## The handbook and the harness flag

The frozen text (`src/plugin/data/policy.txt`, 5,837 words, 809 lines, sha256 `5dcea9bd...6f449`) is never
paraphrased, and the task text restates no rule. The PDF's five-line page header ("Approved By: ... Page N of
18") survives 18 times and splits sections, including 1.2 between the economy and business-class sentences;
every quote and line number uses the frozen text as it stands. Under stock NanoAgent the agent does not see the
policy: the plugin then runs as the `off` baseline. The `harness.policy` switch of the NanoAgent fork
(github.com/tejassaboo/nanoagent, branch `policy-switch`) adds it to the system prompt: `harness.policy: full`
adds all of it, and the selection methods add parts of it. These plugins are meant to run with
`query: instructions+input`, so a selector sees the traveller's request.

## Task

- **Input:** `TaskInput`: `scenario` (one of 24 case ids) and `request`, the traveller's own words.
- **Steps:** `get_trip`, then `search_flights` on the trip's route and date (with the return date in the one
  round-trip case), then `submit` (3 of the 6 hosted steps).
- **Output:** `BookingOutput`: `decision`, `offer_id` (empty when refusing), `cabin` (`NONE` when
  refusing), `reason_code`, `approver` and `clause`, each from a closed list. The reason list is shared by
  every handbook plugin and holds codes for rules this policy lacks, plus decoy codes from other handbooks'
  rules. Bookings accept `NONE` and every role whose sign-off is on file (SYNC_NOTES 4'); a hold accepts only the
  awaited role, or for unclear words `NOT_NAMED` and the roles the text points to.
- **Success:** every field is one the answer key accepts. Score = fields right / 6.

| Scenario | Category | Expected decision (offer) | Reason | Approver | Clause cited (frozen lines) |
|---|---|---|---|---|---|
| `amber-loom` | easy | BOOK (morning-economy) | LOWEST_FARE | NONE or SUPERVISOR | AIR_TRAVEL or FARES_AND_CLASS (88-89, 383-384) |
| `birch-ember` | easy | BOOK (airfrance-business) | INTERNATIONAL_LONG_FLIGHT or LONG_FLIGHT_APPROVED | NONE or SUPERVISOR or OFFICER or EXPORT_COMPLIANCE | AIR_TRAVEL or FARES_AND_CLASS (102-108, 383-384) |
| `cedar-quill` | easy | BOOK (delta-economy) | LOWEST_FARE or TRAVELER_PAYS_UPGRADE | NONE or SUPERVISOR | AIR_TRAVEL or FARES_AND_CLASS (88-89, 89-91, 383-384) |
| `dune-harrow` | easy | BOOK (redeye-economy) | LOWEST_FARE | NONE or SUPERVISOR | AIR_TRAVEL or FARES_AND_CLASS (88-89, 383-384) |
| `oriole-shingle` | easy | BOOK (delta-business) | MEDICAL_NEED | NONE or SUPERVISOR or OFFICER or DISABILITY_SERVICES | AIR_TRAVEL or FARES_AND_CLASS (102-108, 383-384) |
| `fern-gable` | boundary_twin | BOOK (nonstop-business) | LONG_FLIGHT_APPROVED | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 383-384) |
| `gorse-inlet` | boundary_twin | BOOK (denver-economy) | LONG_FLIGHT_CONDITION_NOT_MET or UPGRADE_NOT_ELIGIBLE | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 88-89, 383-384) |
| `hazel-marsh` | boundary_twin | BOOK (early-business) | LONG_FLIGHT_APPROVED | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 383-384) |
| `iris-nook` | boundary_twin | BOOK (late-economy) | LONG_FLIGHT_CONDITION_NOT_MET or UPGRADE_NOT_ELIGIBLE | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 88-89, 383-384) |
| `juniper-crest` | boundary_twin | BOOK (charlotte-business) | LONG_FLIGHT_APPROVED | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 383-384) |
| `kestrel-moor` | boundary_twin | BOOK (chicago-economy) | LONG_FLIGHT_CONDITION_NOT_MET or UPGRADE_NOT_ELIGIBLE | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-108, 88-89, 383-384) |
| `lumen-sorrel` | multi_rule | BOOK (united-economy) | FLY_AMERICA_US_CARRIER_REQUIRED or NATIONAL_CARRIER_REQUIRED | NONE or SUPERVISOR or EXPORT_COMPLIANCE | AIR_TRAVEL or FARES_AND_CLASS or FEDERALLY_FUNDED_AIRLINES (149-150, 88-89, 383-384) |
| `maple-tor` | multi_rule | BOOK (united-economy) | FLY_AMERICA_US_CARRIER_REQUIRED or NATIONAL_CARRIER_REQUIRED or OPEN_SKIES_AGREEMENT | NONE or SUPERVISOR or EXPORT_COMPLIANCE | AIR_TRAVEL or FARES_AND_CLASS or FEDERALLY_FUNDED_AIRLINES (149-150, 158-169, 383-384) |
| `nettle-quay` | multi_rule | BOOK (japan-economy) | SPONSOR_RESTRICTION | NONE or SUPERVISOR or OFFICER or EXPORT_COMPLIANCE | AIR_TRAVEL or FARES_AND_CLASS or APPROVAL_TO_TRAVEL or OTHER_CONSIDERATIONS (396-399, 102-108, 383-384) |
| `thistle-cove` | multi_rule | BOOK (redeye-economy) | PRIVATE_AIRCRAFT_NOT_APPROVED | NONE or SUPERVISOR | AIR_TRAVEL or FARES_AND_CLASS or PRIVATE_AIRCRAFT (133-138, 88-89, 383-384) |
| `poplar-vane` | hidden_clause | BOOK (delta-business) | POLICY_EXCEPTION_APPROVED | NONE or SUPERVISOR or CHIEF_OPERATING_OFFICER or CHIEF_FINANCIAL_OFFICER | AIR_TRAVEL or FARES_AND_CLASS or POLICY (67-68, 102-108, 383-384) |
| `rook-tallow` | hidden_clause | BOOK (aerlingus-economy) | BOOKING_TOOL_REQUIRED | NONE or SUPERVISOR or EXPORT_COMPLIANCE | AIR_TRAVEL or FARES_AND_CLASS or AIR_RESERVATIONS (72-77, 84-85, 88-89, 383-384) |
| `quill-saddle` | distractor | BOOK (american-economy) | LOWEST_FARE or LOYALTY_PROGRAM_PREFERENCE | NONE or SUPERVISOR | AIR_TRAVEL or FARES_AND_CLASS or OTHER_CONSIDERATIONS or REWARD_POINTS (476-478, 88-89, 383-384) |
| `sable-wren` | distractor | BOOK (chicago-economy) | UPGRADE_NOT_ELIGIBLE | NONE or SUPERVISOR or OFFICER | AIR_TRAVEL or FARES_AND_CLASS (102-103, 88-89, 383-384) |
| `umber-cask` | refusal | REFUSE (none) | COMPANION_NOT_COVERED or PERSONAL_TRAVEL_NOT_COVERED | NONE or SUPERVISOR | COMPANION_EXPENSES or COMPANION_TRAVEL (356-358) |
| `vetch-orchard` | refusal | REFUSE (none) | OUTSIDE_POLICY_SCOPE or PERSONAL_TRAVEL_NOT_COVERED | NONE or SUPERVISOR | COMBINED_PERSONAL_AND_BUSINESS or OTHER_CONSIDERATIONS or UNALLOWABLE_EXPENSES (458-461, 523-525) |
| `willow-brine` | flag | FLAG_FOR_APPROVAL (american-economy or jetblue-premium) | APPROVAL_REQUIRED or UNCLEAR_POLICY_TEXT | NOT_NAMED or SUPERVISOR or OFFICER or CHIEF_OPERATING_OFFICER or CHIEF_FINANCIAL_OFFICER or FINANCE_POLICY_OFFICE | AIR_TRAVEL or FARES_AND_CLASS (88-89, 92-93, 102-108, 654-655, 67-68, 383-384) |
| `yarrow-flint` | flag | FLAG_FOR_APPROVAL (delta-business or delta-economy) | APPROVAL_REQUIRED or UNCLEAR_POLICY_TEXT | NOT_NAMED or SUPERVISOR or OFFICER or CHIEF_OPERATING_OFFICER or CHIEF_FINANCIAL_OFFICER or FINANCE_POLICY_OFFICE | AIR_TRAVEL or FARES_AND_CLASS (102-108, 654-655, 67-68, 383-384) |
| `zinnia-cobble` | flag | FLAG_FOR_APPROVAL (denver-economy) | APPROVAL_REQUIRED | SUPERVISOR | APPROVAL_TO_TRAVEL or OTHER_CONSIDERATIONS (383-384, 88-89) |

Mix (EDGE_CASES.md 5.2): 5 easy, 6 boundary twins, 4 multi-rule, 2 hidden clause, 2 distractor, 2 refusal, 3
flags (12.5%). Decisions: 19 BOOK (6 in business), 2 REFUSE, 3 FLAG. Unclear words are each one flag with clear
twins on both sides: "economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.)" (`willow-brine`,
premium economy; twins `cedar-quill` and `birch-ember`) and "The total scheduled in-air flight time for all flight
segments" (`yarrow-flint`, a round-trip ticket; twins `hazel-marsh` and `iris-nook`). `zinnia-cobble` is an
approval-required hold (no supervisor approval yet), which is never the same as "no compliant offer". The
always-cheapest agent passes 3 of 24 and the always-flag agent 2.

## Tools

| Tool | Does | Code |
|---|---|---|
| `booking_requirements` | The trip record's fields, the world's conventions (local times, dates, fares, sold-out seats) and its airports | `src/plugin/guide.py` |
| `get_trip` | A case's request and trip record: traveller, route, dates, deadline, purpose, funding and sponsor terms, requested cabin and airline, sign-offs, colleagues, notes | `src/plugin/tools.py` |
| `search_flights` | Every offer on a route and local date (one way, or round trip with `return_date`): the pinned scenario offers plus seeded background offers on those searches only; a search the case does not pin lists nothing and says so | `src/plugin/world.py` |
| `solve_booking` | The answer key (`rules.solve`), the agent task's `reference`, never shown to the agent | `src/plugin/rules.py` |

| Task | Does | Runner |
|---|---|---|
| `book-vumc-flight` | Handles one booking request | `agent`, with `get_trip` and `search_flights`; reference `solve_booking` |
| `booking-requirements` | Shows `booking_requirements` | `tool` |
| `search-flights` | Shows `search_flights` | `tool` |

## Layout

- `contract.py`: the template's shared contract plus this policy's scenario ids, approvers, sections, six reason
  codes, decoys and trip record.
- `src/plugin/`: `world.py`, `scenarios.py`, `guide.py`, `answer.py`, `tools.py` (shared), `rules.py` (this
  policy's rules, citing frozen lines), `__main__.py`.
- `src/plugin/data/`: `policy.txt` (frozen), `handbook.json`, `scenarios/*.json`.
- `verifier/`: byte-identical copies of the shared modules and `rules.py`, plus `booking.py` and `tools.py`.
- `tests/`: the template's acceptance suite; `tests/plugin_spec.py` holds this policy's settings.
- `tests/build_scenarios.py`: writes the scenario files (an authoring aid, not a test).
- `tests/BUILD_NOTES.md`: design decisions, the blind read and the acceptance outputs.

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv lock --check
python3 ../_template/check_shared.py .
# from a NanoAgent checkout (read-only use):
nanoagent plugin inspect <this folder>
nanoagent plugin pack <this folder> /tmp/vumc-flight-policy.tar.gz
# from this folder, with that checkout's Python:
/path/to/nanoagent/nanoagent/.venv/bin/python ../_template/tools/stock_verify.py
```

Offline: `hosts: []`, an empty `.env`, `write: []`, no clock (each case fixes its `booking_date`).
