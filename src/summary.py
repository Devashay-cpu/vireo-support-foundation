"""Generates analysis/foundation_summary.md so the numbers always match the outputs."""
import pandas as pd


def _ov(ov, k):
    return ov.set_index("metric").loc[k, "value"]


def write_summary(path, d, tm, am, mo, ch, ov, rs):
    o = lambda k: _ov(ov, k)
    dq = {c: int(tm[c].sum()) for c in tm.columns if c.startswith("dq_")}
    chan = ch[["channel", "sla_target_minutes", "ticket_volume", "sla_breach_count", "sla_breach_rate"]].copy()
    chan["sla_breach_rate"] = (chan["sla_breach_rate"] * 100).round(1).astype(str) + "%"
    chan_md = "\n".join(f"| {r.channel} | {r.sla_target_minutes} | {r.ticket_volume} | {r.sla_breach_count} | {r.sla_breach_rate} |"
                        for r in chan.itertuples())
    t1 = am[am.tier == 1]; t2 = am[am.tier == 2]
    txt = f"""# Foundation summary (phase 1)

Data foundation and core metrics only. No dashboard, memo, ML or per-ticket LLM calls.

## What was calculated
- `outputs/ticket_metrics.csv`: {len(tm):,} rows, one per ticket, none dropped; problem rows are flagged in `dq_*` columns.
- `outputs/agent_metrics.csv` (+ `_tier1` / `_tier2`): {len(am)} agents ({len(t1)} Tier 1, {len(t2)} Tier 2), joined on `agent_id`.
- `outputs/monthly_metrics.csv`, `channel_metrics.csv`, `overall_metrics.csv`, `replacement_by_sku.csv`, `refund_by_reason.csv`.

## Headline numbers
| Metric | Value |
|---|---|
| Tickets | {int(o('tickets_total')):,} ({int(o('tickets_attended_resolved_or_closed')):,} attended, {int(o('tickets_open_or_pending'))} open/pending) |
| CSAT, respondents only | {o('csat_avg_respondents_only'):.3f} (n={int(o('csat_response_count')):,}, response rate {o('csat_response_rate')*100:.1f}%) |
| Low CSAT (<=2) among respondents | {o('low_csat_rate_respondents')*100:.1f}% |
| Handle time, first response to resolution | mean {o('avg_handle_time_min'):.0f} min, median {o('median_handle_time_min'):.0f} min |
| SLA breaches | {int(o('sla_breach_count')):,} ({o('sla_breach_rate')*100:.2f}%) |
| Replacements | {int(o('replacement_count')):,}, policy cost Rs {o('replacement_cost_policy_inr'):,.0f} (avg Rs {o('replacement_avg_cost_policy_inr'):,.0f}) |
| Refunds | {int(o('refund_ticket_count')):,} tickets, Rs {o('refund_total_inr'):,.0f} |

| Channel | Target (min) | Tickets | Breaches | Rate |
|---|---|---|---|---|
{chan_md}

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
- Legacy (`legacy_fd`) `resolved_at` is treated as UTC and shifted +5h30 ({int(o('legacy_resolved_at_shifted_utc_to_ist')):,} rows). Legacy `created_at` and `first_response_at` are not shifted because they agree with each other.
- Evidence: before the shift 63% of legacy tickets resolved before creation; after it, none do.
- Original values are kept in `resolved_at_raw`; shifted rows carry `resolved_tz_shifted = True`.
- After normalization: negative first-response {dq['dq_negative_first_response']}, negative handle time {dq['dq_negative_handle']}, impossible handle time (>30 days) {dq['dq_impossible_handle']}, response after resolution {dq['dq_response_after_resolution']}, unparseable timestamps {dq['dq_ts_unparseable']}.

## Data-quality issues (flagged, not dropped)
- {int(o('tickets_without_order_link')):,} tickets have no `order_id`. They stay in CSAT, handle-time and SLA analysis and are excluded only from order-dependent work (lot, order date). No fallback join was applied in this phase because it is ambiguous for many of them.
- {int(o('tickets_refund_and_replacement_both'))} tickets carry both a refund and a replacement, which policy s5 forbids (flag `dq_refund_and_replacement`).
- {int(o('tickets_open_or_pending'))} open/pending tickets have no `resolved_at` and are excluded from handle time and attendance.
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
"""
    path.write_text(txt, encoding="utf-8")
