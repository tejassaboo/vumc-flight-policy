# Build notes: vumc-flight-policy (wave 3)

Built 2026-11-24 from `pilot_work/tier_plan/build/WAVE3_BUILD_BRIEF.md`, unattended. Every open choice below took
the recommended option and is recorded here.

## Handbook

`pilot_work/originals/vumc/frozen/vumc_policy.txt`: Vanderbilt University Medical Center Finance Policy FIN 4.7,
Travel (effective June 2021). 5,837 words, 809 lines, 39,312 characters, sha256 `5dcea9bd...6f449` (raw PDF sha256
`2f2ab043...38ee8`). Under 10,000 words, so 24 scenarios (EDGE_CASES 5.1). Instantiated with `--slug vumc --task-id
book-vumc-flight --background 0 --scenarios 24 --currency USD`. Source URL: not recorded locally (MANIFEST marks it
UNVERIFIED); the raw PDF is the pinned copy.

The PDF's running header ("Approved By: Finance and Revenue Cycle Policy Committee / Policy Number FIN 4.7 /
Effective Date June 2021 / Approval Date June 2021 / Vanderbilt University Medical Center Page N of 18") survives 18
times and breaks the text at page ends: section 1.2 is split by the header at lines 95-100, between the economy
sentences (88-93) and the business-class rule (102-108); section 11.1 is split at lines 385-392. Line numbers and
quotes use the frozen text as it stands; no `must_keep` range was chosen to dodge a header, but none needs to span
one (each rule's sentences sit on one side of it).

## Checkable flight rules found (frozen lines)

| Rule | Lines | Operator | Used by |
|---|---|---|---|
| Exceptions to the policy need the COO's and the CFO's approval | 67-68 | | `poplar-vane`; unclear holds' roles |
| Air through the online booking tool or agency; international must, cost is not a business need (footnote) | 72-77, 84-85 | | `rook-tallow` |
| International reimbursement needs the approved International Travel Questionnaire (at expense-report time) | 78-83 | | on file in every international case; distractor |
| Lowest available economy fare that meets the business needs | 88-89 | | most bookings; `dune-harrow`, `thistle-cove` (deadline) |
| Upgrades at personal expense or with personal points | 89-91 | | `cedar-quill` |
| Fees for economy class upgrades (Economy Plus, exit row, aisle) reimbursable | 92-93 | | `willow-brine` (flag) |
| Business/first only with the applicable officer's written approval in advance, and one condition: a segment over four hours, total in-air over seven hours, or an EAD-approved medical justification | 102-108 | "more than", strict | twins, `birch-ember`, `oriole-shingle`, `sable-wren`, `nettle-quay`, `yarrow-flint` |
| No non-commercial aircraft without Risk and Insurance Management and CFO approval | 133-138 | | `thistle-cove` |
| Fly America for federally funded foreign travel; Open Skies exception barred for DoS/DoD reimbursement | 147-169 | | `lumen-sorrel`, `maple-tor` |
| No travel expenses for persons accompanying travellers | 355-358 | | `umber-cask` |
| Supervisor's approval of the trip before committing funds | 382-384 | | every case; `zinnia-cobble` (hold) |
| A funding sponsor's more restrictive terms supersede the policy | 396-403 | | `nettle-quay` |
| Combined personal and business travel: only the business part; no personal travel on the travel tool | 457-464, 523-525 | | `vetch-orchard` |
| No extra expense to earn rewards | 474-479 | | `quill-saddle` |
| Interpretation questions go to the finance policy office | 654-655 | | unclear holds' roles |

Rules present but not tested: change penalties (113-116, a distractor aside only), unused tickets for personal travel
(118: no case buys with an unused ticket), pre-travel reimbursement (120-126), baggage fees (128-132), the Code Share
paragraph (153-156: the world sells one carrier per offer, no codeshares), the FTR exceptions to Fly America (150-152:
their criteria are outside the text). The handbook has no advance-purchase, connection, stopover or overnight rule,
so `OVERLAY_MINIMUMS` asks for no overnight case, and the two date-arithmetic cases are red-eyes that land the next
day against a stated deadline (one across January 31 / February 1).

## Decisions taken without asking

1. **"Should be met" (line 103).** "Business class or first-class seating may be used only if the traveler's
   applicable officer approves it in writing in advance. One of the following conditions should be met:". The
   officer's approval is an "only if" requirement. The conditions are worded "should", which a reader could take as
   advisory (EDGE_CASES 2.4). Every scenario keeps clear of that reading: a business seat is keyed only where a
   condition is met, and where none is met the officer's sign-off says "provided the trip meets the travel policy's
   requirements for it" (`subject_to_policy: true`), so the answer is economy on either reading. An unconditional
   approval with no condition met raises ValueError (not modelled). This phrase is not used as a flag because the
   lead's own summary (WAVE3B.md) and most readers take the conditions as required; see "Unsure".
2. **Duration.** "segment": any one flight of the ticket over 240 scheduled minutes (strict). "total": the flights'
   scheduled minutes added, ground time left out ("in-air"), over 420 (strict). The world's `scheduled_minutes` is
   taken as the scheduled in-air time. A round-trip ticket whose journeys are each 420 or less but together over 420
   is unclear (`yarrow-flint`, the only such case). The one-way twins add a record note that the traveller does not
   fly home on this trip (drives on, stays for a rotation), so no reader adds an unseen return flight.
3. **The flight a condition is measured on** is the itinerary sold in business: a cheaper business fare on a
   connection whose flights do not qualify (`fern-gable` UA via Denver) is not accepted.
4. **No officer approval and a long flight** (`sable-wren`): the officer declined in writing (record note), so it is a
   booking in economy, not a hold awaiting the officer. Approver accepts NONE, SUPERVISOR and OFFICER (the role whose
   missing approval decides it).
5. **Approvers under SYNC_NOTES 4'.** Every BOOK and REFUSE accepts NONE plus every role on file (the supervisor's
   trip approval, the officer, EAD, Export Compliance, COO and CFO as they appear). The approval hold
   `zinnia-cobble` accepts only SUPERVISOR. The two unclear holds accept NOT_NAMED, FINANCE_POLICY_OFFICE (line 654),
   CHIEF_OPERATING_OFFICER and CHIEF_FINANCIAL_OFFICER (exceptions, lines 67-68), OFFICER (line 102) and SUPERVISOR
   (the trip approval on file), never NONE; reasons UNCLEAR_POLICY_TEXT or APPROVAL_REQUIRED (lesson 2); each holds the
   offer of either reading.
6. **Declined requests (lesson 12).** Specific codes only, no LOWEST_FARE, where the ground is another rule: twins'
   economy side (LONG_FLIGHT_CONDITION_NOT_MET, UPGRADE_NOT_ELIGIBLE), `sable-wren` (UPGRADE_NOT_ELIGIBLE),
   `nettle-quay` (SPONSOR_RESTRICTION), `rook-tallow` (BOOKING_TOOL_REQUIRED), `thistle-cove`
   (PRIVATE_AIRCRAFT_NOT_APPROVED), `maple-tor` (FLY_AMERICA_US_CARRIER_REQUIRED, NATIONAL_CARRIER_REQUIRED,
   OPEN_SKIES_AGREEMENT), `lumen-sorrel` (the two Fly America codes: the dearer U.S. fare is not the lowest-fare rule).
   `quill-saddle` keeps LOWEST_FARE beside LOYALTY_PROGRAM_PREFERENCE: lines 476-478 decline the airline because it
   adds expense, which is the lowest-fare ground itself (same call as Goodman sedge-harbor, Standex kiln-meadow).
7. **Fly America** applies when `funding` is FEDERAL_AWARD and the trip leaves the United States. U.S. carriers are
   the six U.S. airlines of the shared world, by name (as UC G-28 does). The DoD/DoS bar on Open Skies is read from the
   record's `sponsor` text.
8. **Sponsor terms** are modelled as one exact sentence ("Air travel paid from this award is limited to economy
   class."); other terms raise.
9. **The booking tool** (lines 72-76): `search_flights` lists what VUMC's booking tool and agency can book (said in
   `rook-tallow`'s record note, not in the shared conventions, to keep the task text free of the clause's words).
10. **Approval to travel** (lines 383-384) is checked in every case: a missing supervisor approval is the
    approval-required hold `zinnia-cobble`; the hold keeps the offer the request would otherwise get.
11. **The International Travel Questionnaire** (lines 78-83) is a condition of reimbursement filed with the expense
    report, not of booking. Every international case has it approved on file, so no case turns on it.
12. **One ticket per case:** the one-way fare out, except `yarrow-flint`, whose record gives a return date and pins a
    round-trip search. Background offers are 0 everywhere except `amber-loom` (2, floored far above the pinned fares).
13. **Origin airports.** BNA (Nashville) is not in the shared world. Trips start at listed airports, and no record says
    the traveller starts from Nashville (one is a remote worker in Chicago, others fly between partner sites).
14. **Decoys:** WEEKEND_TRAVEL_HOME, NEXT_OF_KIN_TRAVEL, CREATIVE_TICKETING, DENIED_BOARDING_NOT_ALLOWED,
    CHANCELLOR_WRITTEN_AUTHORIZATION, DOUBLE_BOOKING_PROHIBITED, CANDIDATE_TRIP_NOT_COVERED, SAME_CLASS_AS_CUSTOMER
    (each subject grepped: absent). Dropped after grepping: WEEKEND_TRIP_NOT_EARNED and EXTENDED_TRAVEL_SAVINGS (line
    462's "Saturday stay" saving), TRAVEL_PACKAGE_NOT_ITEMIZED (itemized receipts, line 415). FLY_AMERICA, OPEN_SKIES
    and PRIVATE_AIRCRAFT codes, decoys elsewhere, are this handbook's own rules here. Handbook codes added:
    BOOKING_TOOL_REQUIRED, SPONSOR_RESTRICTION, POLICY_EXCEPTION_APPROVED.
15. **Approver name.** "Office of Risk and Insurance Management" is `RISK_MANAGEMENT` in the enum: the full name is a
    4-word phrase of a `must_keep` range and the lint rejects it.

## Mix and overlays

5 easy, 6 boundary twins (241/240 minutes on a nonstop; 421/420 in the air on a connection; 241/240 on a
connection's second flight), 4 multi-rule, 2 hidden clause, 2 distractor, 2 refusal, 3 flags (12.5%). Decisions: 19
BOOK (13 economy, 6 business), 2 REFUSE, 3 FLAG. Overlays: multi_leg 9, date_arithmetic 2, month_end 1,
personal_travel 1, multi_traveller 2, dearer_option 10, upgrade_not_taken 2, outside_air_section 6.

Degenerate agents (measured): always-cheapest (cheapest seated offer, LOWEST_FARE, NONE) passes 3 of 24
(`amber-loom`, `cedar-quill`, `quill-saddle`); always-flag passes 2 (`willow-brine`, `yarrow-flint`).
`MAX_PASS_ALWAYS_LOWEST = 3`, `MAX_PASS_ALWAYS_FLAG = 2`.

## Independent blind read (non-flag scenarios)

Re-derived from the handbook text and a dump of every `get_trip` and pinned `search_flights` output (background
offers included), before comparing with the key and without reading `rules.py`. Agreement on decision and offer for
all 21 non-flag scenarios:

| Scenario | My reading | Agrees |
|---|---|---|
| amber-loom | UA 06:00 $164 sold out; AA 08:15 $189 is the lowest economy (88); supervisor on file | yes |
| birch-ember | officer approved in writing, nonstops 515/520 min > 4 h (104): cheapest business AF $4,385; dept funds | yes |
| cedar-quill | economy asked; DL 2749 economy $312 is the lowest and is Dr. Okafor's flight; miles upgrade is his own (89-91) | yes |
| dune-harrow | must land by Tue 10:00; UA connection lands 10:30 (fails); AS red-eye $338 lands 07:05 (88 "meets the business needs") | yes |
| oriole-shingle | officer (conditional) + EAD medical approval: third condition (107-108); only business is DL $689 | yes |
| fern-gable | AA nonstop 241 > 240: business $1,190; UA business via DEN (125+150) does not qualify | yes |
| gorse-inlet | 240 is not more than four hours, totals <= 420, no medical; conditional approval: lowest economy UA via DEN $241 | yes |
| hazel-marsh | 215+206 = 421 in air > 420 (105-106): cheapest business AA 06:00 $1,560 | yes |
| iris-nook | 420 in air, not more than seven hours (elapsed 505/515 is not in-air); economy AA 11:30 $398 | yes |
| juniper-crest | CLT-SFO 241 > 240 (104): AA business $1,320 | yes |
| kestrel-moor | 240 and totals 335/355: economy, UA via ORD $331 | yes |
| lumen-sorrel | NIH grant, foreign travel: U.S. carrier (149): UA $965 over LH $880 | yes |
| maple-tor | DoD award: Open Skies criterion one fails (165-166): UA $1,010 | yes |
| nettle-quay | officer + 785 min would allow business, but the award limits air to economy and supersedes (396-399): JL economy $1,295 | yes |
| poplar-vane | 120 min, no officer; COO and CFO exception (67-68): DL business $612 | yes |
| quill-saddle | Delta $284 adds $41 to earn status (476-478): AA $243 | yes |
| rook-tallow | international: booking tool only, cost is not a business need (73-76, 84): EI $688 in the tool | yes |
| sable-wren | officer declined; a flight over four hours is not enough without approval (102-103): AA via ORD $301 | yes |
| thistle-cove | corporate jet prohibited without RIM and CFO (134-138); land by Feb 1 09:00: UA $231 lands 09:45 (fails), B6 red-eye $276 lands 05:45 | yes |
| umber-cask | the husband is a companion (356-358): refuse | yes |
| vetch-orchard | vacation leg after the conference (458-461, 523-525): refuse | yes |

Flags (not blind-read, by design): `willow-brine` (premium economy against "economy class upgrades (e.g., Economy
Plus, exit row, aisle seat, etc.)"), `yarrow-flint` (round-trip ticket against "The total scheduled in-air flight
time for all flight segments"), `zinnia-cobble` (approval required: no supervisor approval yet).

## Hosted-cap estimate

0.2 tokens a character of policy plus 1,800 (the Thornton/NJC paid calibration): call 1 about 9,700 input tokens
with the full policy. Trip records are 1,100-1,900 characters (about 330-550 tokens), searches 1,450-5,700 (about
420-1,600 tokens; the largest is the round-trip `yarrow-flint`). Call 2 about 10,300, call 3 about 10,700-12,000; a
3-call run about 31,000-32,500 input tokens, well under the 65,536 hosted cap (a repeated search still fits).

## Unsure

- **"should be met" (line 103)** is kept out of every keyed answer (decision 1). If a paid run books business on a
  conditional approval with no condition met, the model read the conditions as advisory and ignored the sign-off's
  own proviso: a model slip. It could become a fourth unclear flag, but that would exceed 15%.
- **`willow-brine`** is the weakest flag: many readers will say premium economy is a class of service and book
  economy. Premium economy is named nowhere in the policy, and Economy Plus is an economy upgrade sold as a fee, so
  both readings stand; the key holds either offer.
- **`fern-gable`**: a reader who checks the condition on "the trip" rather than on the flights flown in business
  could book United's $905 business via Denver. The conditions name flight segments and in-air time, which belong to
  the itinerary flown, so only the AA nonstop is accepted.
- **241 against 240 minutes** relies on `scheduled_minutes` being the "scheduled in-air flying time"; a reader who
  subtracts taxi time would see both under four hours. The quote test rules out that outside knowledge.
- **`rook-tallow`**: a model might REFUSE because the traveller says they will buy the fare themselves. The request
  adds "If I can't, book what the policy allows", so BOOK is the only answer.

## Template change requests

- Add BNA (Nashville) to the shared `world.py` airports (already queued as BACKLOG item 7 for Dollar General); VUMC is
  in Nashville. Worked around: other origins.
- `instantiate.py` leaves Thornton text in `README.md`, `product/product.yaml`, `pyproject.toml` and
  `tests/plugin_spec.py` (BACKLOG item 8); rewritten here.

## Acceptance outputs

```
$ uv run pytest -q
209 passed in 2.40s
$ uv run ruff check .
All checks passed!
$ uv lock --check
Resolved 42 packages in 7ms
$ python3 ../_template/check_shared.py .
: ok
$ nanoagent plugin inspect .   (stock nanoagent/nanoagent/.venv/bin/nanoagent)
exit 0
$ nanoagent plugin pack . <scratch>/vumc-flight-policy.tar.gz
packed . into <scratch>/vumc-flight-policy.tar.gz (173430 bytes)
$ <stock python> ../_template/tools/stock_verify.py .
amber-loom           right=True score=1.00 identical=True wrong-decision-rejected=True
birch-ember          right=True score=1.00 identical=True wrong-decision-rejected=True
cedar-quill          right=True score=1.00 identical=True wrong-decision-rejected=True
dune-harrow          right=True score=1.00 identical=True wrong-decision-rejected=True
fern-gable           right=True score=1.00 identical=True wrong-decision-rejected=True
gorse-inlet          right=True score=1.00 identical=True wrong-decision-rejected=True
hazel-marsh          right=True score=1.00 identical=True wrong-decision-rejected=True
iris-nook            right=True score=1.00 identical=True wrong-decision-rejected=True
juniper-crest        right=True score=1.00 identical=True wrong-decision-rejected=True
kestrel-moor         right=True score=1.00 identical=True wrong-decision-rejected=True
lumen-sorrel         right=True score=1.00 identical=True wrong-decision-rejected=True
maple-tor            right=True score=1.00 identical=True wrong-decision-rejected=True
nettle-quay          right=True score=1.00 identical=True wrong-decision-rejected=True
oriole-shingle       right=True score=1.00 identical=True wrong-decision-rejected=True
poplar-vane          right=True score=1.00 identical=True wrong-decision-rejected=True
quill-saddle         right=True score=1.00 identical=True wrong-decision-rejected=True
rook-tallow          right=True score=1.00 identical=True wrong-decision-rejected=True
sable-wren           right=True score=1.00 identical=True wrong-decision-rejected=True
thistle-cove         right=True score=1.00 identical=True wrong-decision-rejected=True
umber-cask           right=True score=1.00 identical=True wrong-decision-rejected=True
vetch-orchard        right=True score=1.00 identical=True wrong-decision-rejected=True
willow-brine         right=True score=1.00 identical=True wrong-decision-rejected=True
yarrow-flint         right=True score=1.00 identical=True wrong-decision-rejected=True
zinnia-cobble        right=True score=1.00 identical=True wrong-decision-rejected=True
24 scenarios, 0 failures
```
