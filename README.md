# Vireo Audio: Support Analytics (CSAT and handle time per agent, bottom ten, root cause, goal)

Answer to Priya Raman's request: *"a dashboard of CSAT and handle time per agent, flag the bottom ten"*, plus the finding behind it.
Deterministic Python project: loads the Vireo data pack, computes validated metrics, builds a static dashboard and two memos.
**No LLM calls, no API keys, no network, no paid services at run time.**

## Start here (clean machine)
Needs Python 3.10+ (verified on Python 3.12 with pandas 3.0.2/numpy 2.4.4 and, in a fresh virtualenv, pandas 3.0.6/numpy 2.5.3; `requirements.txt` allows pandas >= 2.0, not re-run on 2.x).
```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.run_all          # about 7 s: runs every stage below in order, stops on first failure
```
Then open **`dashboard/index.html`** (any browser; one static file) and read **`MEMO_TO_PRIYA.md`** (the one-page memo). Run from the project root.

| Open this | What it is |
|---|---|
| `dashboard/index.html` | Dashboard: KPIs, CSAT trend, lot chart, **bottom ten with handle time**, **all 44 agents with CSAT and handle time**, training priority, impact and goal |
| `MEMO_TO_PRIYA.md` | One-page non-technical memo to Priya Raman |
| `FINAL_MEMO.md` | Detailed technical memo (appendix to the one-pager) |
| `VALIDATION.md` | How correctness was checked, sample size, error rate, known failure cases |
| `submission-form.md` | Drafted submission form; items marked `[MANUAL]` need the submitter |
| `SCREEN_RECORDING_OUTLINE.md` | Beat sheet for the 3-minute recording (the recording itself is not in this package) |

`python -m src.run_all` is equivalent to: `pipeline`, `validate`, `tests/run_tests.py`, `phase2_report`, `validate_phase2`, `dashboard`, `validate_task4`,
`memo`, `memo_priya`, `validate_final` (each as `python -m src.<name>`). Every generated file is rebuilt from `data/raw/`.

## Headline result
11,750 tickets, CSAT 3.327 (respondents only, n=5,196). The slide traces mainly to Pulse 2 lots PL2-2510/2511/2512 (31.9 vs 5.1 replacements per 100 orders; direct excess cost Rs 1,184,099).
Of the raw bottom ten, **four** (A3004, A3005, A3006, A3007) show a queue-mix-adjusted CSAT gap that is statistically clear; the other six reflect Delivery/Returns queues.
Goal: blended CSAT 3.33 to at least 3.42, held two quarters, by end of Q1 2027. Handle time is queue-driven (about 19 to 27 min median for everyday queues, about 24 h Logistics/Returns, days for Tier 2), so agents are compared with their own team only.

## Layout
| Path | Contents |
|---|---|
| `data/raw/` | Client exports (tickets, agents, customers, orders, products CSVs) and `support-policy.pdf`. Read-only inputs; never modified. |
| `src/config.py` | Policy constants: SLA targets, Rs 340 replacement logistics, IST offset, low-CSAT threshold |
| `src/load.py` | Loading, required-column checks, independent row counts |
| `src/timestamps.py` | `normalize_timestamps()` (legacy UTC to IST) |
| `src/metrics.py` | Ticket, agent, monthly, channel and overall metrics |
| `src/pipeline.py` | End-to-end runner |
| `src/validate.py` | Validation checks and report |
| `src/summary.py` | Generates `analysis/foundation_summary.md` from the outputs |
| `src/phase2.py`, `phase2_report.py` | Business analysis: trend, queue-mix adjustment, training priority, lot economics, goal |
| `src/dashboard.py` | Builds `dashboard/index.html` from verified outputs |
| `src/memo.py`, `src/memo_priya.py` | Generate `FINAL_MEMO.md` and `MEMO_TO_PRIYA.md`; every number is read from outputs |
| `src/run_all.py` | One-command runner |
| `tests/` | Unit tests plus an integration test on the real data |
| `outputs/` | Generated tables and `validation_report.txt` |
| `analysis/foundation_summary.md` | Assumptions, timestamp handling, data-quality issues, limitations |

## Outputs
`ticket_metrics.csv` (one row per ticket, none dropped, problems flagged in `dq_*` columns),
`agent_metrics.csv` (plus `_tier1` and `_tier2`), `monthly_metrics.csv`, `channel_metrics.csv`,
`overall_metrics.csv`, `replacement_by_sku.csv`, `refund_by_reason.csv`, `validation_report.txt`.
Timestamps in outputs are IST, timezone-naive.

## Key decisions (see `analysis/foundation_summary.md` for detail)
- Handle time = first human response to resolution. First response measured from ticket creation.
- Legacy (`legacy_fd`) `resolved_at` is UTC and is shifted +5h30 to IST; original kept in `resolved_at_raw`.
- Blank CSAT means no response and is never treated as zero. Low CSAT means a score of 1 or 2 (`LOW_CSAT_MAX` in config).
- Joins use `agent_id`, never the agent name (two agents are named Kavya Pandey).
- Tier 1 and Tier 2 are analyzed separately; ranks are within tier only, and the raw bottom-ten flag is Tier 1 only.
- Replacement cost = product unit cost + Rs 340 (policy s5). The Rs 2,500 figure from the email is not used.
- Tickets without an order link stay in CSAT, handle-time and SLA analysis; order-dependent work excludes them.
- No per-ticket LLM or API calls anywhere.

## Expected result
89 Phase 1 checks pass, 0 fail; 15 tests pass. Headline: 11,750 tickets, CSAT 3.327 among respondents,
1,064 SLA breaches (9.06%), 1,896 replacements costing Rs 34,15,990 at policy rates, refunds Rs 53,50,871.

## Phase 2 (business analysis)
```
python -m src.phase2_report      # builds analysis/*.csv and analysis/business_analysis.md
python -m src.validate_phase2    # 61 checks incl. independent recompute from raw CSVs -> outputs/validation_report_phase2.txt
```
Adds `analysis/csat_trend.csv`, `agent_context.csv`, `training_priority.csv`, `root_causes.csv`, `business_impact.csv`,
`business_analysis.md`. Phase 1 code and outputs are unchanged. Code: `src/phase2.py`, `src/phase2_report.py`, `src/validate_phase2.py`.

## Phase 3 (Task 4 core: static dashboard)
```
python -m src.dashboard          # writes dashboard/index.html + dashboard/dashboard_data.json
python -m src.validate_task4     # 29 checks -> outputs/validation_report_task4.txt
```
Open `dashboard/index.html` in any browser. It is one static file (no JavaScript, no network, no LLM calls) built only from
verified Phase 1/2 outputs. The dashboard shows CSAT **and handle time per agent** (bottom-ten table and a table of all 44 agents). Full pipeline from a clean checkout: `python -m src.pipeline && python -m src.validate && python tests/run_tests.py &&
python -m src.phase2_report && python -m src.validate_phase2 && python -m src.dashboard && python -m src.validate_task4`

## Validation status
Phase 1: 89/89 checks, 15/15 tests. Phase 2: 61/61. Dashboard: 29/29 (20 original + 9 covering handle time). Final: see `outputs/validation_report_final.txt`.
Method, sample size, error rate and failure cases: `VALIDATION.md`.

## Limitations and deliberate exclusions
- This is a deterministic analytics tool. It contains no model; the two free-text fields (`customer_message`, `agent_notes`) are **not analysed**. All findings use structured fields only.
- Findings are associations, not proven cause. Only 65% of Pulse 2 tickets link to a lot, so lot counts and costs are lower bounds.
- No case-severity field: the four coaching candidates' gaps may partly reflect harder cases. CSAT is respondents only (44%).
- Money is the measured direct cost of the defect (one-off, not a per-quarter run rate). No revenue data, so CSAT loss is not monetised.
- Handle time is descriptive: not adjusted for queue, so compare agents within a team only; means are skewed by long cases, medians are shown first.
- Not built: repeat-contact / first-contact-resolution, shift or site analysis (roster has no history), Tier 1 vs Tier 2 ranking (policy s6), interactive filters.
- Known wording error left in Phase 2 (deliberately unchanged): `analysis/business_analysis.md` says agent CSAT rests on "97 to 243" responses; the true Tier 1 range is 42 to 243. No calculation uses that sentence; `FINAL_MEMO.md` and `MEMO_TO_PRIYA.md` state the correct range.
- Not in this package: the client's `email-thread.txt`, `README.txt`, `submission-form.md`, the screen recording, and the GitHub / Drive links (see `submission-form.md`).
