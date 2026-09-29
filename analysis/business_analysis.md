# Business analysis (phase 2)

Builds on the verified phase 1 foundation (11,750 tickets, 44 agents). No dashboard, memo or submission form yet. All figures below are computed by `src/phase2.py`; tables are in `analysis/*.csv`.

## 1. Strongest business finding

**A quality defect in Pulse 2 earbuds (VA-EB-PL2), lots PL2-2510, 2511 and 2512, drove the support crisis of Dec 2025 to Mar 2026.** Those lots have 31.9 replacements per 100 orders against 5.1 for comparison Pulse 2 lots (1,979 orders, 631 replacements). Tickets per 100 orders are 86 vs 46. The step change is at the lot boundary (lot-month 2509 vs 2510 vs 2601), not gradual, which points at manufacturing rather than at support handling or seasonality.

| lot_month | group | orders | tickets | replacements | tickets_per_100_orders | replacements_per_100_orders | csat |
|---|---|---|---|---|---|---|---|
| 2510 | defect lots | 781 | 660 | 262 | 85 | 33.5 | 2.69 |
| 2511 | defect lots | 679 | 599 | 224 | 88 | 33.0 | 2.79 |
| 2512 | defect lots | 519 | 442 | 145 | 85 | 27.9 | 2.88 |
| 2507 | comparison | 276 | 140 | 19 | 51 | 6.9 | 3.43 |
| 2508 | comparison | 438 | 215 | 20 | 49 | 4.6 | 3.64 |
| 2509 | comparison | 573 | 287 | 30 | 50 | 5.2 | 3.39 |
| 2601 | comparison | 340 | 163 | 21 | 48 | 6.2 | 3.62 |
| 2602 | comparison | 171 | 78 | 8 | 46 | 4.7 | 3.34 |
| 2603 | comparison | 184 | 72 | 10 | 39 | 5.4 | 3.48 |
| 2604 | comparison | 128 | 38 | 0 | 30 | 0.0 | 3.70 |
| 2605 | comparison | 70 | 13 | 3 | 19 | 4.3 | 3.86 |
| 2606 | comparison | 7 | 1 | 0 | 14 | 0.0 | 4.00 |

Comparison lot-months are Jul-Sep 2025 and Jan-Jun 2026 (linked tickets only). Replacement counts come from order-linked tickets, so they are a lower bound.

Measured direct cost of the excess: **Rs 1,184,099** (531 excess replacements at Rs 1,820 plus 790 excess contacts at about Rs 277). It also cost 0.089 points of blended CSAT (section 8).

## 2. CSAT trend

CSAT (respondents only, n=5,196) was steady at about 3.4 to 3.6 through Oct 2025 (Jan-Sep 2025 average 3.49), peaked at 3.76 in 2025-06, then fell to a trough of **2.95 in 2026-02**. The trailing 3-month average bottomed at 3.07 in 2026-03 and has recovered to 3.33 by 2026-06; Apr-Jun 2026 averages 3.33, still below the pre-wave level. Oct-Nov 2025 vs Jan-Feb 2026 differs by 0.50 points (95% CI 0.39 to 0.60), so the drop is not sampling noise; single months carry a CI of roughly +/-0.15 to 0.2.

| month | responses | CSAT | rolling 3m | defect-lot ticket share | CSAT defect lots | CSAT excl. defect lots |
|---|---|---|---|---|---|---|
| 2025-01 | 126 | 3.48 | 3.48 | 0.0% |  | 3.48 |
| 2025-02 | 129 | 3.40 | 3.44 | 0.0% |  | 3.40 |
| 2025-03 | 173 | 3.58 | 3.49 | 0.0% |  | 3.58 |
| 2025-04 | 171 | 3.39 | 3.46 | 0.0% |  | 3.39 |
| 2025-05 | 173 | 3.57 | 3.51 | 1.0% | 3.00 | 3.58 |
| 2025-06 | 153 | 3.76 | 3.57 | 0.5% | 3.00 | 3.76 |
| 2025-07 | 195 | 3.47 | 3.59 | 0.0% |  | 3.47 |
| 2025-08 | 269 | 3.41 | 3.52 | 0.2% | 4.00 | 3.41 |
| 2025-09 | 262 | 3.42 | 3.43 | 0.0% |  | 3.42 |
| 2025-10 | 309 | 3.60 | 3.48 | 0.3% |  | 3.60 |
| 2025-11 | 371 | 3.47 | 3.50 | 6.4% | 2.95 | 3.51 |
| 2025-12 | 465 | 3.29 | 3.43 | 18.3% | 2.92 | 3.38 |
| 2026-01 | 517 | 3.12 | 3.28 | 33.4% | 2.96 | 3.20 |
| 2026-02 | 501 | 2.95 | 3.12 | 39.7% | 2.55 | 3.23 |
| 2026-03 | 481 | 3.13 | 3.07 | 30.8% | 2.72 | 3.31 |
| 2026-04 | 344 | 3.23 | 3.09 | 18.9% | 2.67 | 3.34 |
| 2026-05 | 293 | 3.37 | 3.22 | 10.4% | 3.21 | 3.39 |
| 2026-06 | 264 | 3.40 | 3.33 | 5.5% | 2.64 | 3.43 |

The dip follows the defect-lot share of tickets (0.3% in Oct, 40% in Feb). Excluding defect-lot tickets the monthly CSAT still dips (to 3.20), so the defect explains most but not all of it; queue overload on the chat hardware rota and unlinked Pulse 2 tickets (see limitations) account for part of the rest.

## 3. Queue, channel and category mix

Category is the strongest predictor of CSAT. Hardware and post-purchase categories score 0.6 to 1.3 points below Product Enquiry or Account & Login for reasons unrelated to the agent, so raw agent averages mostly measure which queue an agent sits in.

| category | tickets | share_of_tickets | responses | avg_csat | replacement_rate | transfer_rate |
|---|---|---|---|---|---|---|
| Charging & Battery | 1,355 | 11.5% | 618 | 2.73 | 44.4% | 0.13 |
| Warranty & Repair | 785 | 6.7% | 344 | 2.86 | 39.2% | 0.10 |
| Returns & Refunds | 1,116 | 9.5% | 484 | 3.14 | 14.5% | 0.09 |
| Audio Quality | 772 | 6.6% | 329 | 3.17 | 30.8% | 0.15 |
| Delivery & Shipping | 1,884 | 16.0% | 867 | 3.20 | 17.8% | 0.07 |
| Billing & Payments | 1,471 | 12.5% | 666 | 3.49 | 0.0% | 0.10 |
| Other | 1,732 | 14.7% | 718 | 3.55 | 6.5% | 0.10 |
| App & Firmware | 734 | 6.2% | 319 | 3.57 | 7.1% | 0.08 |
| Connectivity | 1,013 | 8.6% | 459 | 3.73 | 8.6% | 0.14 |
| Account & Login | 333 | 2.8% | 150 | 3.84 | 0.0% | 0.09 |
| Product Enquiry | 555 | 4.7% | 242 | 4.01 | 0.0% | 0.08 |

Tier 1 teams (agent-level averages, mix expectation from a category + channel + defect-lot model fitted on Tier 1 responses):

| agent_team | agents | tickets | raw_csat | mix_expected | mix_adjusted_gap | hardware_share | defect_share |
|---|---|---|---|---|---|---|---|
| Billing | 4 | 1,494 | 3.49 | 3.49 | +0.00 | 3% | 8% |
| Chat Frontline | 15 | 3,474 | 3.48 | 3.50 | -0.02 | 56% | 15% |
| Email Frontline | 7 | 1,670 | 3.60 | 3.54 | +0.06 | 53% | 12% |
| Logistics | 5 | 1,907 | 3.21 | 3.22 | -0.01 | 3% | 9% |
| Returns Desk | 3 | 1,104 | 3.26 | 3.24 | +0.02 | 5% | 11% |
| Voice Frontline | 4 | 797 | 3.60 | 3.55 | +0.05 | 56% | 9% |

Channel makes little difference to CSAT (Tier 1):

| channel | tickets | replacement_rate | sla_breach_rate | avg_csat | responses |
|---|---|---|---|---|---|
| chat | 4,537 | 11.7% | 8.0% | 3.44 | 1,996 |
| email | 3,245 | 13.0% | 12.3% | 3.41 | 1,436 |
| social | 1,042 | 11.8% | 8.8% | 3.43 | 467 |
| voice | 1,622 | 12.5% | 6.2% | 3.39 | 713 |

Email has the worst first-response breach rate (12.2% overall); channel does not move CSAT by more than 0.05.

## 4. Raw Tier-1 bottom ten, with context

Raw = plain average CSAT among respondents, ranked within Tier 1 only (38 agents). `mix_expected_csat` is what a typical Tier 1 agent would score on the same category/channel/defect-lot mix; `mix_adjusted_gap` is actual minus expected; z is the gap over its standard error.

| raw_bottom_ten_rank | agent_id | agent_name | agent_team | site | shift | ticket_count | csat_response_count | avg_csat | mix_expected_csat | mix_adjusted_gap | resid_z | defect_cohort_share | hardware_category_share | workload_vs_tier1_median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A3004 | Siddharth Kapoor | Chat Frontline | Bengaluru | Day | 305 | 129 | 2.98 | 3.36 | -0.38 | -4.2 | 30% | 62% | 1.21x |
| 2 | A3006 | Kavya Pandey | Chat Frontline | Indore | Morning | 281 | 142 | 3.01 | 3.33 | -0.33 | -3.4 | 25% | 65% | 1.11x |
| 3 | A3007 | Siddharth Trivedi | Chat Frontline | Indore | Morning | 278 | 120 | 3.01 | 3.29 | -0.28 | -2.9 | 27% | 63% | 1.10x |
| 4 | A3005 | Zaid Khanna | Chat Frontline | Bengaluru | Day | 299 | 118 | 3.04 | 3.32 | -0.28 | -2.8 | 27% | 61% | 1.18x |
| 5 | A3029 | Kavya Pandey | Logistics | Bengaluru | Morning | 340 | 159 | 3.13 | 3.22 | -0.09 | -1.2 | 9% | 3% | 1.35x |
| 6 | A3028 | Vivaan Pandey | Logistics | Bengaluru | Morning | 348 | 154 | 3.14 | 3.23 | -0.09 | -1.1 | 8% | 3% | 1.38x |
| 7 | A3030 | Geeta Iyer | Logistics | Bengaluru | Morning | 337 | 150 | 3.18 | 3.22 | -0.04 | -0.6 | 9% | 3% | 1.33x |
| 8 | A3038 | Varun Reddy | Returns Desk | Bengaluru | Day | 284 | 121 | 3.21 | 3.26 | -0.06 | -0.6 | 10% | 5% | 1.12x |
| 9 | A3037 | Mohammed Desai | Returns Desk | Indore | Morning | 563 | 243 | 3.28 | 3.23 | +0.05 | 0.7 | 11% | 3% | 2.23x |
| 10 | A3036 | Divya Tiwari | Returns Desk | Indore | Day | 257 | 106 | 3.29 | 3.22 | +0.07 | 0.7 | 13% | 8% | 1.02x |

Reading it: six of the ten (Logistics x3, Returns Desk x3) sit in Delivery/Returns queues that score about 3.2 for everyone; their mix-adjusted gaps are between -0.09 and +0.07, indistinguishable from typical. The other four (A3004 to A3007, Chat Frontline) carry 63% hardware tickets and 27% defect-lot tickets (Chat peers 10%) and are still 0.32 below expectation, -2.8 to -4.2 standard errors out. Mix explains only 23% of their raw gap. A `share_of_raw_gap_explained_by_mix` above 100% means the agent beats expectation once mix is considered.

## 5. Training priority (Tier 1 only)

Ranked by shrunken mix-adjusted gap times ticket volume (empirical-Bayes shrinkage k=60 responses; agents need at least 80 responses). Tier 2 is not ranked against Tier 1 (policy s6).

| training_priority_rank | agent_id | agent_name | agent_team | avg_csat | mix_adjusted_gap | resid_ci95_low | resid_ci95_high | evidence | tier1_csat_lift_if_gap_closed |
|---|---|---|---|---|---|---|---|---|---|
| 1 | A3004 | Siddharth Kapoor | Chat Frontline | 2.98 | -0.38 | -0.55 | -0.20 | strong: mix-adjusted gap, 95% CI excludes 0 | 0.011 |
| 2 | A3006 | Kavya Pandey | Chat Frontline | 3.01 | -0.33 | -0.52 | -0.14 | strong: mix-adjusted gap, 95% CI excludes 0 | 0.010 |
| 3 | A3005 | Zaid Khanna | Chat Frontline | 3.04 | -0.28 | -0.47 | -0.09 | strong: mix-adjusted gap, 95% CI excludes 0 | 0.007 |
| 4 | A3007 | Siddharth Trivedi | Chat Frontline | 3.01 | -0.28 | -0.47 | -0.09 | strong: mix-adjusted gap, 95% CI excludes 0 | 0.007 |
| 5 | A3029 | Kavya Pandey | Logistics | 3.13 | -0.09 | -0.24 | +0.06 | no evidence of gap after mix |  |
| 6 | A3028 | Vivaan Pandey | Logistics | 3.14 | -0.09 | -0.24 | +0.07 | no evidence of gap after mix |  |
| 7 | A3034 | Meera Pereira | Billing | 3.42 | -0.06 | -0.21 | +0.08 | no evidence of gap after mix |  |
| 8 | A3032 | Kunal Jain | Billing | 3.43 | -0.06 | -0.21 | +0.10 | no evidence of gap after mix |  |
| 9 | A3035 | Nisha Rao | Billing | 3.45 | -0.05 | -0.19 | +0.10 | no evidence of gap after mix |  |
| 10 | A3038 | Varun Reddy | Returns Desk | 3.21 | -0.06 | -0.23 | +0.12 | no evidence of gap after mix |  |
| 11 | A3030 | Geeta Iyer | Logistics | 3.18 | -0.04 | -0.19 | +0.11 | no evidence of gap after mix |  |
| 12 | A3020 | Riya Pillai | Email Frontline | 3.50 | -0.05 | -0.26 | +0.16 | no evidence of gap after mix |  |

**Train now:** A3004, A3006, A3005, A3007, the only agents whose gap's 95% CI excludes zero. Everyone else, including the six other raw-bottom-ten agents, shows no training signal; sending them to training would spend effort on a queue-mix artefact. Closing the four agents' gap would lift Tier 1 CSAT by about 0.035 points. Caveat: the rota may receive harder cases than category shows (no severity field), so pair training with a routing fix.

## 6. Root causes (ranked)

1. **Pulse 2 (VA-EB-PL2) quality defect in lots PL2-2510/2511/2512.** Replacement rate 31.9 per 100 orders in these three lot-months vs 5.1 in comparison Pulse 2 lot-months; tickets per 100 orders 86 vs 46; concentrated in Charging & Battery, Audio Quality, Warranty & Repair; volume wave Dec 2025 to Mar 2026 tracks the sales of those lots. *Confidence: High (lot-level, clear step change, dose-response by lot; causal mechanism not observable in this data).* Action: Quality/Manufacturing: root-cause the three lots and contain field stock; Support: lot-level early-warning trigger.
2. **Defect-cohort tickets scored much lower on CSAT and drag the blended score.** CSAT 2.77 on defect-cohort tickets (n=718) vs 3.42 on all other tickets; cohort is 13.8% of responses, worth 0.089 CSAT points overall. *Confidence: High for size of effect; medium for attribution (some of the cohort's low CSAT is handler/queue driven, see #3).* Action: Proactive outreach to owners of lots 2510-2512; fast-track replacement without a second contact.
3. **Defect tickets were routed disproportionately to four Chat Frontline agents and to Tier 2.** Of 1701 defect-cohort tickets, 317 went to A3004-A3007 (4 of 44 agents) and 448 to Tier 2; CSAT on those tickets 2.26 (rota four) and 1.88 (Tier 2) vs 3.39 for other Tier 1; rota four replaced 59% of them vs 16% for other Tier 1 agents. *Confidence: Medium: routing concentration is observed; whether the rota got harder cases cannot be tested (no severity field).* Action: Spread hardware triage across the chat pool; give the rota a defect playbook (script, replace-or-repair rule).
4. **Residual coaching gap on the same four agents after adjusting for queue mix.** Mix-adjusted CSAT gap -0.38 to -0.28 (z -2.8 to -4.2); gap is also present on non-defect charging tickets (non-defect Charging & Battery CSAT 2.51 vs 3.37 for other frontline agents); their CSAT gap to other chat agents was 0.27 before Oct 2025, widening to 0.91 in Dec 2025 to Mar 2026. *Confidence: Medium: statistically clear, but unobserved case severity could explain part of it.* Action: Targeted coaching + QA sampling for these four; re-measure after one quarter.
5. **Low raw CSAT for Logistics and Returns Desk agents is queue mix, not performance.** Their mix-adjusted gap is small (Logistics -0.09 to +0.10; Returns Desk -0.06 to +0.07), inside noise; Delivery & Shipping and Returns & Refunds tickets average 3.20 CSAT for all handlers vs 3.42 overall. *Confidence: High.* Action: Do not send these six agents to training; fix delivery/returns process instead.
6. **Email first-response SLA misses (12.2% vs 6.4 to 8.6% elsewhere).** Breach rate by weekday 10 to 13%, by time-of-day block 11 to 15%, by month 6 to 18% (small monthly n): no clear peak-time driver, so capacity/queue order is the working hypothesis; breached tickets score CSAT 2.78 vs 3.38; 1014 attended breaches trigger Rs 350 credits each. *Confidence: Medium (association only).* Action: Capacity review of Email Frontline; consider priority ordering by SLA age.
7. **Hand-offs between teams (transfers).** 1215 transfers cost Rs 305 each; tickets with a transfer score CSAT 2.98 to 3.10 vs 3.36 with none; Tier 2 transfer rate is double Tier 1. *Confidence: Medium (association only).* Action: Fix first-touch routing for Charging/Warranty categories.

Handler split for defect-lot tickets: Chat hardware-rota four (A3004-A3007): 317 tickets, CSAT 2.26, 59% replaced; Other Tier 1: 936 tickets, CSAT 3.39, 16% replaced; Tier 2 (Escalations & Warranty): 448 tickets, CSAT 1.88, 65% replaced.

## 7. Business impact

| item | quantity | unit_cost_inr | amount_inr | treatment |
|---|---|---|---|---|
| Excess replacements, defective Pulse 2 lots | 531 | 1,820 | 965,614 | core, order-linked tickets only (lower bound) |
| Excess contacts, defective Pulse 2 lots | 790 | 277 | 218,485 | core, order-linked tickets only (lower bound) |
| CORE TOTAL: measured direct cost of the defect |  |  | 1,184,099 | headline |
| Sensitivity: baseline from Jul-Sep 2025 lots only (fully matured, excludes recent right-censored lots) |  |  | 1,152,787 | robustness check; 2.6% from core |
| Sensitivity: scale core total for the 34.6% of Pulse 2 tickets with no order link |  |  | 1,809,862 | upper estimate, assumption-dependent, not used in the goal |
| SLA credits paid on attended breaches | 1,014 | 350 | 354,900 | context: not defect-specific, only partly avoidable |
| Transfer handling cost | 1,215 | 305 | 370,575 | context: not defect-specific, only partly avoidable |
| Tickets with refund AND replacement (policy s5 breach) | 6 |  | 25,577 | control failure; small, escalate to Finance |
| CSAT drag from the defect cohort (not monetised) |  |  |  | no revenue/retention data in the pack, so no rupee value is claimed |

Use the core total (Rs 1,184,099) as the defensible figure. It is order-linked only; scaling for the 34.6% of Pulse 2 tickets with no order link gives about Rs 1,809,862, which is an upper estimate and is not used for the goal. SLA credits and transfer costs are real spend but only partly avoidable and are not attributed to the defect. Replacement costs follow policy s5 (unit cost + Rs 340, no refurbishment recovery); the Rs 2,500 figure from the email is not used. No revenue or retention data exists in the pack, so CSAT loss is not converted into rupees.

## 8. Numeric business goal

**Goal: raise blended CSAT from 3.33 to at least 3.42 and hold it for two consecutive quarters, by end of Q1 2027.**

Calculation:

- Blended CSAT over 18 months: 3.327 (n=5,196).
- CSAT on all tickets outside the defect lots: 3.416 (n=4,478). This is what the desk already delivers when the product is not failing.
- Defect-lot tickets: n=718 (13.8% of responses) at 2.772. Gap 0.644 x 0.138 = **0.089 points**.
- 3.327 + 0.089 = 3.416, rounded to **3.42**.
- The target is conservative: unlinked Pulse 2 tickets in Nov 2025 to Jun 2026 (568 responses) score 2.93, so they look like defect cases too; treating them as cohort lifts the clean baseline to 3.49. The pre-wave level (Jan-Sep 2025) was 3.49.
- Feasibility: Jun 2026 is already 3.40; Apr-Jun 2026 is 3.33 (3.39 excluding strict defect-lot tickets, 3.44 excluding all Pulse 2 tickets without an order link). Reaching 3.42 needs about +0.09 on the current quarter. Removing the cohort alone is not quite enough on the strict definition (3.39), so the goal also needs lever (b) and continued fading of the wave.
- Levers: (a) defect containment, proactive outreach and single-contact replacement for owners of the three lots, worth up to 0.089; (b) coaching plus rerouting for A3004 to A3007, worth about 0.031 (0.32 gap x 509 responses / 5,196). Lever (b) alone cannot reach the target; it depends on (a).
- Guardrail (supporting): flag any new lot whose replacement rate exceeds 10 per 100 orders (2x the 5.1 baseline) within its first 60 days. The 10 threshold and 60-day window are proposals, not derived from this data.

## 9. Limitations

1. Association, not proof of cause. The lot-level step change is strong evidence of a lot defect, but this data has no failure-analysis or manufacturing records.
2. Lot linkage covers only order-linked tickets: 65.4% of Pulse 2 tickets. Unlinked Pulse 2 tickets during the wave score 2.93, so the strict cohort understates the defect and the counterfactual CSAT is biased slightly low. No fallback join (customer + SKU) was applied because it is ambiguous.
3. The defect lot months (2510 to 2512) were identified from the lot table itself (every month above 25 replacements per 100 orders; no other lot-month above 7), so this is descriptive, not a pre-registered test. Comparison lots are Jul-Sep 2025 and Jan-Jun 2026 (Apr-Jun 2025 lots are too small). Recent lots are right-censored (they have had less time to generate tickets), which slightly understates the baseline; using Jul-Sep 2025 lots only gives a core cost of Rs 1,152,787 vs Rs 1,184,099.
4. Mix adjustment uses category, channel, defect-lot and Pulse 2 dummies. Unobserved case severity, customer mood and any routing rule (the chat hardware rota) can still bias the four agents' gaps; no ticket-level severity field exists. Message text was not analysed.
5. Agent CSAT rests on 97 to 243 responses per agent; gaps below about 0.15 are not distinguishable from noise. The shrinkage constant (k=60) is a judgement call.
6. CSAT is respondents only (44% response rate); non-response bias is unknown.
7. Business impact excludes lost revenue, churn, brand cost and any refurbishment recovery (policy says do not assume it). Refund figures were not attributed to the defect because refund reason codes are agent-selected from a dropdown.
8. SLA and transfer costs use policy planning rates. Breaches are assigned to the resolving agent per policy, even where routing caused the delay.
9. Roster has no history, so shift and site are current values. Repeat-contact and first-contact-resolution (policy s10) are still not built.
10. The goal target (3.42) is a floor tied to this dataset's own baseline; whether future lots are defect-free is outside support's control.
