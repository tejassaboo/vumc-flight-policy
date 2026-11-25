# Independent audit: vumc-flight-policy (2026-11-25)

I audited the builder's commit e252877 against `pilot_work/tier_plan/build/WAVE3_AUDIT_BRIEF.md`. I also checked it
against the 12 lessons of WAVE3_BUILD_BRIEF, MASTER_PLAN section 4, EDGE_CASES 1-3 and 5, and SYNC_NOTES 4'. No
money was spent and nothing was pushed. Line numbers are lines of the frozen handbook (`src/plugin/data/policy.txt`).
The PDF page header repeats 18 times in that text. This is expected, and no quote spans it.

## Method

I printed each scenario's `get_trip` record and every pinned `search_flights` result through the plugin's own
tools. I answered each case from lines 67-68, 72-93, 102-108, 133-169, 355-358, 382-403, 457-479, 523-525 and 654
only, then compared my answers with every accept set: decision, offers, cabins, reasons, approvers and clauses.

## Verdict

**Pass after fixes.** My reading agrees with the key's decision and offer in all 21 non-flag cases. The defects
were these:

- one class of wording in the trip records that let a reader change the key: the "should be met" issue below;
- three requests with no stated start time;
- one record that left an exception open;
- two accept sets that were too narrow.

The twins differ in one fact each: fern/gorse (241/240), hazel/iris (421/420 in the air) and juniper/kestrel
(241/240 on the second flight). No request uses rule wording or a threshold. The decline-reason sentence is in the
task instructions.

## The builder's open items

1. **"One of the following conditions should be met" (line 103).** The builder's claim did not hold. The claim was
   that the conditional sign-off ("provided the trip meets the travel policy's requirements for it") keeps every key
   the same under the advisory reading. But if the conditions are only advice, the policy's one requirement is the
   officer's written approval, and that is on file. The keys would then flip:
   - `gorse-inlet`: cheapest business, UA $905;
   - `iris-nook`: AA $1,560;
   - `kestrel-moor`: AA $1,320;
   - `fern-gable`: the cheaper UA business via Denver, $905.

   **Fix.** The officer's conditional sign-off now reads "Approved business class for this trip, provided the trip
   meets one of the conditions the travel policy sets for business class." The officer now makes a condition part
   of her own approval, so the key is the same whether "should" is read as binding or as advice. This covers the 8
   conditional sign-offs: the 6 twins, `oriole-shingle` (medical condition met) and `yarrow-flint` (still open).

   No other key depends on the word:
   - `sable-wren`: the officer declined;
   - `birch-ember`: a condition is met;
   - `nettle-quay`: the sponsor's terms decide;
   - `poplar-vane`: a COO and CFO exception;
   - `cedar-quill`: no officer approval.

   The binding reading is also the stronger one on the text. This handbook uses "should" for its main rules, such as
   line 72 (booking channel) and line 88 (the lowest economy fare). Reading line 103 as advice would make line 88
   advice too. The phrase is therefore not a flag.
2. **`willow-brine` (premium economy against "economy class upgrades (e.g., Economy Plus, exit row, aisle seat,
   etc.)").** It stays a flag, because neither reading clearly wins on the quote test.
   - For economy: line 88 asks for the lowest "economy class airfare", line 89 puts a higher "level of service" at
     the traveller's expense, and the world sells PREMIUM_ECONOMY as its own cabin.
   - For premium economy: lines 92-93 make "economy class upgrades" reimbursable without saying what counts as one.
     Telling Economy Plus (an extra-legroom seat in economy) from a premium economy cabin takes outside knowledge of
     airline products, which the quote test forbids. The traveller also asks for "the extra legroom", which is what
     the listed example sells.

   The key holds either fare. I added the start time "which opens the next morning" to the request, because the
   cheapest premium fare (B6) lands later than the cheapest economy fare (AA). Flags stay at 3: two unclear-text
   flags (`willow-brine`, `yarrow-flint`) and one approval hold (`zinnia-cobble`).
3. **`fern-gable` (the condition is measured on the flights sold in business).** Kept as a clear case. Line 104 asks
   whether "any flight segment" has more than four hours in the air. In this case those are the flights of the
   ticket bought. United's business fare via Denver flies 125 and 150 minutes, so no condition is met on that
   ticket. Under the new sign-off wording the officer's approval does not cover it on either reading of "should".
   Only the AA nonstop business fare ($1,190, 241 minutes) is right.
4. **241/240 minutes and taxi time.** The contract's `scheduled_minutes` ("scheduled time from departure to
   arrival") could be read as gate-to-gate time, from which a reader might subtract taxi time. I added a world
   convention in two places:
   - in the agent's task instructions (`nanoagent.yaml`, after the calendar-days convention), which the agent
     always sees;
   - in `rules.CONVENTIONS`, which `booking_requirements` shows.

   It reads: "A flight's scheduled_minutes is its scheduled time in the air, from takeoff to landing; time on the
   ground between flights is the layover." It contains no number and no 4-word phrase from a `must_keep` clause, and
   `test_lint` passes.
5. **`rook-tallow`.** Kept. "If I can't, book what the policy allows" makes BOOK the only answer.

## Defects found and fixed

| Scenario | Problem | Fix |
|---|---|---|
| fern-gable, gorse-inlet, hazel-marsh, iris-nook, juniper-crest, kestrel-moor (also oriole-shingle, yarrow-flint) | The key flips under the advisory reading of "should be met" (see item 1). | The officer's sign-off terms now require one of the policy's conditions. The keys are unchanged. |
| birch-ember | Lesson 4. The talk is "on February 9th" with no time. The key's AF flight lands at 09:50 and the dearer DL flight at 08:05, so a reader could pick DL for a morning talk. | Request: "presenting in the afternoon session". |
| zinnia-cobble | Lesson 4. The held UA connection lands at 12:50 and the AA nonstop at 10:40, and the training has no start time. | Request: "which starts the next morning". |
| willow-brine | Lesson 4, for the premium reading (see item 2). | Request: "which opens the next morning". |
| lumen-sorrel | NIH is not the Department of State or the Department of Defense, and Germany is an Open Skies partner. A reader could therefore argue for the Open Skies exception (lines 157-169) and book the cheaper Lufthansa fare. Its second test, that the traveller has checked the airline, was not settled in the record. | Record note: "The traveller has not checked whether Lufthansa is Open Skies compliant for this route." This is the counterpart of `maple-tor`'s note, so United is the only answer. |
| thistle-cove | The approver set was {NONE, SUPERVISOR}. The decision rests on the jet approval that is missing, from RISK_MANAGEMENT and the CFO (lines 135-138). `sable-wren` already accepts OFFICER for the same reason. | RISK_MANAGEMENT and CHIEF_FINANCIAL_OFFICER added, in `rules.py` and in the key. |
| nettle-quay | Only SPONSOR_RESTRICTION was accepted, but the request declined is a business seat. | UPGRADE_NOT_ELIGIBLE added. It is a class-of-service code, not a generic one, so lesson 12 still holds. |

`src/plugin/rules.py` and `verifier/rules.py` are byte-identical, and the scenario JSON was regenerated with
`tests/build_scenarios.py`. No scenario id or decision category changed.

**MAX_PASS_ALWAYS_LOWEST: 3 -> 3** (`amber-loom`, `cedar-quill`, `quill-saddle`; 12.5%). MAX_PASS_ALWAYS_FLAG stays
at 2.

## Seen and kept

- `cedar-quill`: Delta's 330-minute flight would meet line 104. The traveller asks for economy and has no officer
  approval, so VUMC buys economy and he upgrades with his own miles (89-91).
- `sable-wren`: a condition is met, but the officer declined. Line 102's "only if" decides it, so the key is economy
  under any reading of "should".
- `yarrow-flint`: "all flight segments" on a round-trip ticket (675 minutes in all, 345 and 330 per journey). This is
  a genuine flag. The literal reading favours the ticket and the purpose favours the journey.
- `quill-saddle` keeps LOWEST_FARE beside LOYALTY_PROGRAM_PREFERENCE: lines 476-478 decline the airline because it
  adds expense, which is the lowest-fare ground itself.

## Acceptance outputs

```
uv run pytest -q                        209 passed
uv run ruff check .                     All checks passed!
uv lock --check                         Resolved 42 packages
python3 ../_template/check_shared.py .  : ok
stock_verify.py .                       24 scenarios, 0 failures
nanoagent plugin inspect .              exit 0
```
