# Vireo Audio: Customer Support Review, Detailed Technical Memo

**Audience:** Priya Raman, Head of Customer Experience (technical appendix; the one-page memo is `MEMO_TO_PRIYA.md`)  **Scope:** 11,750 tickets, Jan 2025 to Jun 2026, 44 agents (38 Tier 1, 6 Tier 2)  **Source:** verified project outputs (Phase 1: 89/89 checks, 15/15 tests; Phase 2: 61/61 checks; dashboard: 29/29 checks)

## 1. Executive summary

- CSAT is **3.33** (respondents only, n=5,196). It fell from about 3.49 (Jan-Sep 2025) to a low of **2.95 in 2026-02** and has partly recovered (3.33 in Apr-Jun 2026).
- The main driver is a **Pulse 2 (VA-EB-PL2) quality defect in lots PL2-2510, 2511 and 2512**: 31.9 replacements per 100 orders vs 5.1 for comparison lots.
- Measured direct cost of the excess: **Rs 1,184,099**. The defect also cost **0.089** points of blended CSAT.
- Only **4 of 38** Tier 1 agents (A3004, A3006, A3005, A3007) show a queue-mix-adjusted CSAT gap that is statistically clear. The other six raw-bottom-ten agents do not.
- Proposed goal: **blended CSAT 3.33 to at least 3.42**, held for two consecutive quarters, by end of Q1 2027.

## 2. Current CSAT performance

CSAT 3.327 (median 3); response rate 44.2%; low CSAT (1 or 2) is 21.6% of responses. Blank scores are excluded, never counted as zero. Jun 2026 stands at 3.40; the trailing 3-month average is 3.33. Channel barely moves CSAT (all four between 3.30 and 3.34).

## 3. Main CSAT trend

Steady at about 3.4 to 3.6 until Oct 2025 (3.60), then down through 3.47 (Nov), 3.29 (Dec), 3.12 (Jan) to 2.95 (Feb 2026), recovering to 3.13, 3.23, 3.37, 3.40. The dip follows the share of tickets from the defective lots (0.3% in Oct, 39.7% in Feb 2026, 5.5% in Jun). Excluding those tickets, the low is 3.20 (2026-01), so the defect explains most but not all of the fall.

## 4. Defect / lot finding

Lots PL2-2510/2511/2512 had 1,979 orders, 1,701 order-linked tickets and 631 replacements: 31.9 replacements and 86 tickets per 100 orders, against 5.1 and 46 for Pulse 2 lots from Jul-Sep 2025 and Jan-Jun 2026. The step change sits exactly at the lot boundary, which points to manufacturing rather than support handling. Tickets from these lots score CSAT 2.77 (n=718) vs 3.42 for everything else; they are 13.8% of responses. Only 65.4% of Pulse 2 tickets link to an order, so all lot counts are lower bounds.

## 5. Agent performance and queue-mix context

Raw Tier 1 rankings mostly measure queue: Charging & Battery, Warranty & Repair, Returns and Delivery tickets score lower for every handler. Each agent is therefore compared with the CSAT expected for the same category, channel and defect-lot mix (Tier 1 only; Tier 2 is not ranked against Tier 1 per policy s6).

| Raw rank | Agent | Team | Raw CSAT | Mix-expected | Gap | z |
|---|---|---|---|---|---|---|
| 1 | A3004 Siddharth Kapoor | Chat Frontline | 2.98 | 3.36 | -0.38 | -4.2 |
| 2 | A3006 Kavya Pandey | Chat Frontline | 3.01 | 3.33 | -0.33 | -3.4 |
| 3 | A3007 Siddharth Trivedi | Chat Frontline | 3.01 | 3.29 | -0.28 | -2.9 |
| 4 | A3005 Zaid Khanna | Chat Frontline | 3.04 | 3.32 | -0.28 | -2.8 |
| 5 | A3029 Kavya Pandey | Logistics | 3.13 | 3.22 | -0.09 | -1.2 |
| 6 | A3028 Vivaan Pandey | Logistics | 3.14 | 3.23 | -0.09 | -1.1 |
| 7 | A3030 Geeta Iyer | Logistics | 3.18 | 3.22 | -0.04 | -0.6 |
| 8 | A3038 Varun Reddy | Returns Desk | 3.21 | 3.26 | -0.06 | -0.6 |
| 9 | A3037 Mohammed Desai | Returns Desk | 3.28 | 3.23 | +0.05 | 0.7 |
| 10 | A3036 Divya Tiwari | Returns Desk | 3.29 | 3.22 | +0.07 | 0.7 |

The six Logistics and Returns Desk agents have gaps between -0.09 and +0.07, indistinguishable from typical. The four Chat Frontline agents carry 27% defect-lot tickets (chat peers 10%) and remain 0.32 below expectation on average (z -2.8 to -4.2). Of 1701 defect-lot tickets, 317 went to these four agents (CSAT 2.26, 59% replaced), 448 to Tier 2 (CSAT 1.88) and 936 to other Tier 1 (CSAT 3.39).

Handle time (first human response to resolution, per agent on the dashboard) is set by queue: Tier 1 agents outside Logistics/Returns have median handle time 19 to 27 min; Logistics and Returns Desk 1463 to 1473 min (about 24 hours); Tier 2 4522 to 7314 min. The four Chat Frontline agents are 25 to 27 min against a chat median of 23. Means are pulled up by a minority of very long cases, so medians are used for comparison.

## 6. Training priority recommendation

**Train now:** A3004 Siddharth Kapoor, A3006 Kavya Pandey, A3005 Zaid Khanna, A3007 Siddharth Trivedi (95% intervals exclude zero). Nobody else shows a training signal, including the six other raw-bottom-ten agents; sending them to training would target a queue-mix artefact. Closing the four gaps would lift Tier 1 CSAT by about 0.035. Pair the coaching with a routing fix because case severity is not observed.

## 7. SLA and operational findings

- First-response SLA: 1,064 breaches (9.06%). By channel: email 12.2%, social 8.6%, chat 7.9%, voice 6.4%. Email is the outlier.
- Breached tickets score CSAT 2.78 vs 3.38. Email breaches show no clear time-of-day or weekday pattern, so capacity or queue order is the working hypothesis.
- Transfers: 1,215 hand-offs; tickets with a transfer score 2.99 vs 3.36 without.
- 6 tickets carry both a refund and a replacement, which policy s5 forbids (Rs 25,577).

## 8. Business impact

| Item | Amount |
|---|---|
| Excess replacements (531 x Rs 1,820, unit cost + Rs 340 per policy s5) | Rs 965,614 |
| Excess contacts (790 x about Rs 277, policy s4 rates) | Rs 218,485 |
| **Core measured cost of the defect** | **Rs 1,184,099** |
| Robustness: baseline from Jul-Sep 2025 lots only | Rs 1,152,787 |
| Upper estimate if unlinked Pulse 2 tickets behave the same (not used for the goal) | Rs 1,809,862 |
| Context, not attributed to the defect: SLA credits (1,014 x Rs 350) | Rs 354,900 |
| Context, not attributed to the defect: transfers (1,215 x Rs 305) | Rs 370,575 |

No revenue or retention data exists, so CSAT loss is not converted into rupees.

## 9. Recommended actions

1. **Quality/Manufacturing:** root-cause lots PL2-2510/2511/2512 and contain field stock; Support: add a lot-level early-warning trigger (proposal: flag a lot above 10 replacements per 100 orders in its first 60 days; threshold and window are proposals, not derived from data).
2. **Support:** proactive outreach and single-contact replacement for owners of the three lots.
3. **Coaching and routing:** targeted coaching and QA sampling for A3004, A3006, A3005, A3007; spread hardware triage across the chat pool with a defect playbook; re-measure after one quarter.
4. **Do not** send the other six raw-bottom-ten agents to training; fix Delivery and Returns process issues instead.
5. **Email capacity review** and SLA-age queue ordering; fix first-touch routing for Charging and Warranty categories to cut transfers.
6. **Finance/Team Leads:** escalate the six refund-and-replacement tickets.
7. **Goal:** blended CSAT 3.327 to at least 3.42, held two consecutive quarters, by end of Q1 2027. Calculation: defect-lot gap 0.644 x share 0.138 = 0.089; 3.327 + 0.089 = 3.416, rounded to 3.42. Apr-Jun 2026 is 3.33, so the goal needs about +0.09; it depends on defect containment plus the coaching lever (about 0.031).

## 10. Important limitations and caveats

- Association, not proof of cause: the lot step change is strong evidence, but there are no failure-analysis or manufacturing records.
- Lot linkage is partial; counts and costs are lower bounds. No customer-plus-SKU fallback join was applied because it is ambiguous.
- The defect lots were identified from the lot table itself (descriptive, not a pre-registered test).
- Mix adjustment uses category, channel and defect-lot only. There is no case-severity field, so the four agents' gaps may partly reflect harder cases.
- Agent CSAT rests on 42 to 243 survey responses per Tier 1 agent (118 to 142 for the four coaching candidates); gaps below about 0.15 are noise.
- CSAT covers respondents only (44.2% response rate); non-response bias is unknown.
- Roster has no history (shift and site are current values). Repeat-contact and first-contact resolution were not built.
- Free-text fields (customer_message, agent_notes) are not analysed: every finding uses structured fields only. Handle time is descriptive and is not adjusted for queue; compare agents only within their team.
- email-thread.txt, README.txt and submission-form.md from the client pack were not in the project files when this package was audited against the brief.

## 11. What should NOT be concluded from the data

- That the defect is proven to be a manufacturing fault: the data shows where and when, not why.
- That the six other raw-bottom-ten agents are weak performers: their raw ranking is queue mix.
- That A3004 to A3007 are poor performers with certainty: the gap is statistically clear but severity is unobserved.
- That the Rs 2,500 replacement figure from the email applies: policy s5 rates are used.
- That CSAT loss has a rupee value, or that refunds are attributable to the defect (reason codes are agent-selected).
- That Tier 2 agents are comparable with Tier 1 on volume or CSAT (policy s6).
- That the CSAT goal is guaranteed: future lot quality is outside support's control.
