# Foundation summary (phase 1)

Data foundation and core metrics only. No dashboard, memo, ML or per-ticket LLM calls.

## What was calculated
- `outputs/ticket_metrics.csv`: 11,750 rows, one per ticket, none dropped; problem rows are flagged in `dq_*` columns.
- `outputs/agent_metrics.csv` (+ `_tier1` / `_tier2`): 44 agents (38 Tier 1, 6 Tier 2), joined on `agent_id`.
- `outputs/monthly_metrics.csv`, `channel_metrics.csv`, `overall_metrics.csv`, `replacement_by_sku.csv`, `refund_by_reason.csv`.

## Headline numbers
| Metric | Value |
|---|---|
| Tickets | 11,750 (11,183 attended, 567 open/pending) |
| CSAT, respondents only | 3.327 (n=5,196, response rate 44.2%) |
| Low CSAT (<=2) among respondents | 21.6% |
| Handle time, first response to resolution | mean 1647 min, median 29 min |
| SLA breaches | 1,064 (9.06%) |
| Replacements | 1,896, policy cost Rs 3,415,990 (avg Rs 1,802) |
| Refunds | 1,869 tickets, Rs 5,350,871 |

| Channel | Target (min) | Tickets | Breaches | Rate |
|---|---|---|---|---|
| chat | 15 | 5102.0 | 401.0 | 7.9% |
| email | 480 | 3644.0 | 445.0 | 12.2% |
| social | 240 | 1171.0 | 101.0 | 8.6% |
| voice | 120 | 1833.0 | 117.0 | 6.4% |

## Assumptions
- Definitions come from support-policy.pdf v3.2: first response = creation to first human reply; handle time = first response to resolution; breach = first response strictly later than target (chat 15, voice 120, social 240, email 480 min).
- Blank CSAT = no response and is excluded from every average; it is never treated as 0.
- Low CSAT means a score of 1 or 2 (analyst choice; the policy does not define it). Change `LOW_CSAT_MAX` in `src/config.py` to alter it.
- Handle time is computed for attended tickets (status resolved or closed). Closed tickets are auto-closed after 72 hours without a customer reply, so their handle time includes that waiting period.
- Replacement cost = product unit cost + Rs 340, keyed on the ticket's `product_sku`, so it does not need an order link. The Rs 2,500 figure from the email is not used.
- Refund amounts are summed as exported. Refund-to-retail-price ratios are the same in legacy and helpdesk tickets, so no currency conversion was applied even though the policy mentions a legacy "native unit".
- Monthly metrics group by ticket creation month (IST).
- Tier 1 and Tier 2 are separate: ranks are within tier only, the raw bottom-ten flag applies to Tier 1 only, and no cross-tier ranking is produced.

## Timestamp handling
- Canonical timezone is IST, stored timezone-naive. Implemented in `src/timestamps.py::normalize_timestamps`.
- Helpdesk timestamps are used as exported (IST).
- Legacy (`legacy_fd`) `resolved_at` is treated as UTC and shifted +5h30 (3,189 rows). Legacy `created_at` and `first_response_at` are not shifted because they agree with each other.
- Evidence: before the shift 63% of legacy tickets resolved before creation; after it, none do.
- Original values are kept in `resolved_at_raw`; shifted rows carry `resolved_tz_shifted = True`.
- After normalization: negative first-response 0, negative handle time 0, impossible handle time (>30 days) 0, response after resolution 0, unparseable timestamps 0.

## Data-quality issues (flagged, not dropped)
- 4,107 tickets have no `order_id`. They stay in CSAT, handle-time and SLA analysis and are excluded only from order-dependent work (lot, order date). No fallback join was applied in this phase because it is ambiguous for many of them.
- 6 tickets carry both a refund and a replacement, which policy s5 forbids (flag `dq_refund_and_replacement`).
- 567 open/pending tickets have no `resolved_at` and are excluded from handle time and attendance.
- Two agents share the name Kavya Pandey (A3006, A3029); all joins use `agent_id`.
- The roster has one row per agent and no end dates, so no shift or site history is available. Agent shift and site are taken as current.
- The pack says about 40 tickets have junk IVR text. Message text is not used in this phase.

## Known limitations
- Agent averages are raw. They are not adjusted for queue mix. Hardware-heavy queues (Tier 2 and the hardware triage rota) may score lower because of the tickets they get, and this phase does not separate that from agent performance.
- `agent_id` is the resolving agent, while `assigned_team` is only the first-routed team, so an agent's tickets include work routed elsewhere first.
- Agent CSAT rests on about 40 to 240 responses per agent, so small gaps between agents are noisy.
- SLA breach is assigned to the resolving agent per the policy's reporting convention, even when a transfer or routing delay caused it.
- Repeat-contact and first-contact-resolution metrics (policy s10) are not built yet.
- Nothing here establishes cause. The replacement figures are descriptive counts and policy-based costs only.
