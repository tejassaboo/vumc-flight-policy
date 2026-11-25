# Validation notes: vumc-flight-policy (paid wave 3 validation, 2026-11-25)

Run: `efficient_corporate_travel_agent/pilot/ladder/runs/validation_w3_2026-11-25/vumc-flight-policy@w3/`, arm
`full`, DeepSeek V4 Flash (Nebius fp8), temperature 0, max_steps 6, max_tokens 8192, one run per scenario, at plugin
head 59ff133. Line numbers are lines of `src/plugin/data/policy.txt`.

## Results

19/24 valid (79.2%), mean field score 0.931, **easy 5/5**. By category: boundary 4/6, distractor 2/2, easy 5/5,
flag 1/3, hidden 2/2, multi 3/4, refusal 2/2. $0.00138 billed per run, 3.96 calls per run, 12,381 prompt tokens per
call, no run over the hosted 65,536 cap. Every run submitted.

## Every failure, classified

| scenario | category | submitted vs key | class | evidence |
|---|---|---|---|---|
| hazel-marsh | boundary_twin | BOOK PZ4A-P8UH (the $412 economy offer) with cabin BUSINESS, LONG_FLIGHT_APPROVED; key the $1,560 business offer K7FD-PMFT on the same flights | model slip (offer misread) | The reasoning is right: "Total flying time is 421 minutes = 7 hours 1 minute. That's more than 7 hours! ... the condition is met" (line 105). Then: "There are two business offers: PZ4A-P8UH (fare 156000) and MKE8-Z736 (fare 161000)". The search lists PZ4A-P8UH as ECONOMY 41200 and K7FD-PMFT as BUSINESS 156000. It copied the id of the economy offer above the fare it meant. The record is right. |
| juniper-crest | boundary_twin | BOOK United economy HWVQ-G4SE, UPGRADE_NOT_ELIGIBLE; key AA business VC4M-8PNC, LONG_FLIGHT_APPROVED | model slip (boundary arithmetic) | "No segment > 4 hours (95 min and 241 min = 4h01m, not more than 4 hours)". The search shows `scheduled_minutes: 241` for AA 2898. Line 104 asks for "more than four hours", and 241 minutes is one minute more. That minute is the designed boundary (twin_fact "241 or 240"); the twin kestrel-moor (240) passed. |
| thistle-cove | multi_rule | right offer (JetBlue red-eye NFPV-XHJM), approver and clause; LOWEST_FARE; key PRIVATE_AIRCRAFT_NOT_APPROVED | model slip (reason code) | It found the ground: "Policy 1.6 Private Aircraft prohibits ... No approval on file. So the private jet is not allowed" (lines 134-138). Then it set the specific code aside: "The reason code list includes PRIVATE_AIRCRAFT_NOT_APPROVED. But that would be for refusing the private aircraft. Since we're booking the commercial flight ... LOWEST_FARE." The traveller asked for the jet first, and the task's last line says the reason code gives why the request is declined. The ground is the jet ban, not the lowest-fare rule, so under APPROVER_REVIEW section 7 `LOWEST_FARE` stays off. |
| willow-brine | flag | BOOK AA economy HYVA-YJ6M (a held offer), UPGRADE_NOT_ELIGIBLE; key FLAG (AA economy or JetBlue premium) | model slip (borderline: a weak flag) | It weighed lines 92-93 ("economy class upgrades (e.g., Economy Plus, exit row, aisle seat, etc.) are reimbursable") and then settled it: "Premium economy is arguably a distinct cabin class, not an economy upgrade. Hmm." It never treated the phrase as open, and booked. The audit (item 2) kept this as a flag because neither reading wins on the quote test. The economy reading is arguably the stronger one (lines 88-89 and the world's separate PREMIUM_ECONOMY cabin). If a re-run books economy again, consider converting the case to a BOOK under a new id. |
| yarrow-flint | flag | BOOK Delta business 4DBQ-Q7T9 (a held offer), LONG_FLIGHT_APPROVED, OFFICER; key FLAG (Delta business or economy) | model slip (borderline) | It raised the open question itself: "Wait, does 'all flight segments' refer to the whole trip (round trip) or just one direction?" It then answered it with one reading ("all flight segments would include both directions. Total = 690 min") and booked. It never weighed the per-journey reading (345 or 355 minutes out, under seven hours). Line 105 does not say which. The audit judged the flag genuine: the literal reading favours the ticket, and the purpose favours the journey. The twins hazel-marsh (one-way, 421) and iris-nook are clear. This is the ember-trellis class. |

## Fixes

None. All five failures are slips, and no accept set was widened. The records, keys and README are unchanged.

## Q2

Always-cheapest agent: **3/24 (12.5%)** before and after (amber-loom, cedar-quill, quill-saddle;
`MAX_PASS_ALWAYS_LOWEST = 3`).

## Re-score

Stored answers re-scored at this head: 19/24, easy 5/5 (nothing changed).

## Re-run

Required: none. Optional (variance only): willow-brine and yarrow-flint, the two borderline flags. If either books
again, consider a BOOK under a new id.

## Checks

`uv run pytest -q` (209 passed), `uv run ruff check .`, `uv lock --check`, `check_shared.py`,
`tools/stock_verify.py` (24 scenarios, 0 failures), stock `nanoagent plugin inspect .` (exit 0).
