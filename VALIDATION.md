# How we know the output is right, and how often it is not

## What was checked, and on how much data
This is a **full-population** analysis, not a sample: all 11,750 tickets, all 44 agents, all 5,196 CSAT responses, all 18 months. Nothing was sampled or dropped;
tickets with data problems stay in and are flagged in `dq_*` columns. Because there is no model in the tool, there is no labelled test set and no accuracy percentage to report.
Correctness is established by recomputing every headline figure by a second, independent route and reconciling the outputs to each other.

| Layer | Checks | What it does |
|---|---|---|
| Phase 1 `src/validate.py` | 89 | Row counts vs raw files, timestamp normalisation, first-response and handle time recomputed from raw timestamps, no negatives, CSAT blanks never zero, agent joins on `agent_id` |
| Tests `tests/` | 15 | Unit tests (timestamps, metrics) and an integration test on the real data |
| Phase 2 `src/validate_phase2.py` | 61 | Independent recompute **from the raw CSVs** (not from Phase 1 outputs): defect-lot orders 1,979, tickets 1,701, replacements 631, cohort CSAT responses 718, excess cost, goal arithmetic, agent context |
| Dashboard `src/validate_task4.py` | 29 | HTML reconciles to the CSVs. New: each of the 44 agents' median and mean handle time in the rendered page equals `agent_metrics.csv`; the same in the bottom-ten table; exactly ten flagged; per-agent handle time recomputed from `ticket_metrics.csv` |
| Final `src/validate_final.py` | see `outputs/validation_report_final.txt` | Both memos and the form quote numbers that match the outputs; required files present; README not stale |

**Error rate:** 0 failed checks in every layer at packaging time (89, 15, 61, 29, final). Read this as "the pipeline is internally consistent and reproduces from raw data",
not as "the conclusions are 100% true". These checks cannot detect a wrong *assumption* (see below). The validators can fail: during the audit one agent's handle time in the HTML
was deliberately corrupted by hand and the new check failed (28/29) as intended, then the file was restored. That mutation test was manual and is not automated.

## Where the tool is wrong or can be wrong
1. **Unlinked tickets.** 4,107 tickets have no `order_id`; 34.6% of Pulse 2 tickets cannot be tied to a lot. Lot counts and the Rs 1,184,099 cost are lower bounds (the scaled upper estimate is Rs 1,809,862, not used).
2. **Case difficulty is unobserved.** The four coaching candidates' mix-adjusted CSAT gaps (-0.28 to -0.38, z -2.8 to -4.2) are statistically clear but could partly be harder cases. The adjustment uses category, channel and defect-lot only.
3. **Small samples per agent.** 42 to 243 CSAT responses per Tier 1 agent (118 to 142 for the four); gaps under about 0.15 are noise.
4. **Timestamp assumption.** 3,189 legacy-system `resolved_at` values are treated as UTC and shifted +5h30 (policy s9). If that were wrong, handle time on those tickets would be wrong. Post-shift, there are no negative or impossible handle times.
5. **Handle time is skewed.** Overall mean 1,647 min vs median 29 min. Means are pulled up by a minority of very long cases (and auto-closed tickets include a 72-hour wait). The dashboard leads with the median and compares agents only with their own team's median. It is not adjusted for ticket type.
6. **CSAT is respondents only** (44.2% response); non-response bias is unknown.
7. **Defect lots were found from the lot table itself**, after looking at the data, not from a pre-registered test. The step change at the lot boundary is strong evidence, not proof of a manufacturing fault.
8. **Free text is not read.** Anything that appears only in `customer_message` or `agent_notes` is invisible to this tool.
9. **Roster has no history.** Shift and site are current values.

## Not checked
- The client's `email-thread.txt`, `README.txt` and `submission-form.md` were not in the project files at audit time, so nothing was reconciled against them.
- No external ground truth exists in the pack; no human review of individual tickets was done.
