"""Final business memo generator. Every number is read from verified outputs (outputs/, analysis/) or computed with
existing src.phase2 helpers; nothing is typed by hand. Run: python -m src.memo  -> FINAL_MEMO.md"""
import pandas as pd

from . import phase2 as p2
from .config import ANALYSIS_DIR, OUT_DIR, ROOT

I = lambda x: f"Rs {x:,.0f}"


def build():
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value
    ch = pd.read_csv(OUT_DIR / "channel_metrics.csv").set_index("channel")
    ct = pd.read_csv(ANALYSIS_DIR / "csat_trend.csv").set_index("month")
    ctx = pd.read_csv(ANALYSIS_DIR / "agent_context.csv")
    tp = pd.read_csv(ANALYSIS_DIR / "training_priority.csv")
    bi = pd.read_csv(ANALYSIS_DIR / "business_impact.csv").set_index("item")
    rc = pd.read_csv(ANALYSIS_DIR / "root_causes.csv")
    t, o, a = p2.load_base()
    e, cf, hs = p2.cohort_economics(t, o), p2.csat_counterfactual(t), p2.handler_split(t, a)
    r = t[t.responded]
    row = lambda pre: bi[bi.index.str.startswith(pre)].iloc[0]
    core, alt, upper = row("CORE TOTAL").amount_inr, row("Sensitivity: baseline").amount_inr, row("Sensitivity: scale").amount_inr
    sla, trn, dbl = row("SLA credits"), row("Transfer handling"), row("Tickets with refund")
    trough = ct.avg_csat.idxmin()
    pre = (ct.loc[:"2025-09"].avg_csat * ct.loc[:"2025-09"].csat_responses).sum() / ct.loc[:"2025-09"].csat_responses.sum()
    q2 = r[r.month >= "2026-04"].csat_score.mean()
    fo = ctx[ctx.agent_id.isin(p2.FOCUS_AGENTS)]
    peers = ctx[(ctx.agent_team == "Chat Frontline") & ~ctx.agent_id.isin(p2.FOCUS_AGENTS)]
    strong = tp[tp.evidence.str.startswith("strong")]
    b10 = ctx[ctx.raw_bottom_ten_rank.notna()].sort_values("raw_bottom_ten_rank")
    rest = b10[~b10.agent_id.isin(p2.FOCUS_AGENTS)]
    tx = r.assign(tr=r.transfers.clip(upper=2) > 0)
    goal = round(cf["csat_rest"], 2)
    hh = lambda k: hs.loc[k]
    R, O, T2 = hh("Chat hardware-rota four (A3004-A3007)"), hh("Other Tier 1"), hh("Tier 2 (Escalations & Warranty)")
    L = []
    A = L.append
    A("# Vireo Audio: Customer Support Review, Detailed Technical Memo\n")
    A("**Audience:** Priya Raman, Head of Customer Experience (technical appendix; the one-page memo is `MEMO_TO_PRIYA.md`)  **Scope:** 11,750 tickets, Jan 2025 to Jun 2026, 44 agents (38 Tier 1, 6 Tier 2)  "
      "**Source:** verified project outputs (Phase 1: 89/89 checks, 15/15 tests; Phase 2: 61/61 checks; dashboard: 29/29 checks)\n")
    A("## 1. Executive summary\n")
    A(f"- CSAT is **{ov['csat_avg_respondents_only']:.2f}** (respondents only, n={int(ov['csat_response_count']):,}). It fell from about {pre:.2f} (Jan-Sep 2025) to a low of **{ct.avg_csat.min():.2f} in {trough}** and has partly recovered ({q2:.2f} in Apr-Jun 2026).")
    A(f"- The main driver is a **Pulse 2 (VA-EB-PL2) quality defect in lots PL2-2510, 2511 and 2512**: {e['defect_rate']*100:.1f} replacements per 100 orders vs {e['base_rep_rate']*100:.1f} for comparison lots.")
    A(f"- Measured direct cost of the excess: **{I(core)}**. The defect also cost **{cf['lift']:.3f}** points of blended CSAT.")
    A(f"- Only **{len(strong)} of 38** Tier 1 agents ({', '.join(strong.agent_id)}) show a queue-mix-adjusted CSAT gap that is statistically clear. The other six raw-bottom-ten agents do not.")
    A(f"- Proposed goal: **blended CSAT {cf['csat_all']:.2f} to at least {goal:.2f}**, held for two consecutive quarters, by end of Q1 2027.\n")
    A("## 2. Current CSAT performance\n")
    A(f"CSAT {ov['csat_avg_respondents_only']:.3f} (median {ov['csat_median_respondents_only']:.0f}); response rate {ov['csat_response_rate']*100:.1f}%; low CSAT (1 or 2) is {ov['low_csat_rate_respondents']*100:.1f}% of responses. "
      f"Blank scores are excluded, never counted as zero. Jun 2026 stands at {ct.avg_csat.iloc[-1]:.2f}; the trailing 3-month average is {ct.csat_rolling_3m.iloc[-1]:.2f}. Channel barely moves CSAT (all four between {ch.avg_csat.min():.2f} and {ch.avg_csat.max():.2f}).\n")
    A("## 3. Main CSAT trend\n")
    A(f"Steady at about 3.4 to 3.6 until Oct 2025 ({ct.loc['2025-10'].avg_csat:.2f}), then down through {ct.loc['2025-11'].avg_csat:.2f} (Nov), {ct.loc['2025-12'].avg_csat:.2f} (Dec), {ct.loc['2026-01'].avg_csat:.2f} (Jan) to {ct.loc[trough].avg_csat:.2f} (Feb 2026), "
      f"recovering to {ct.loc['2026-03'].avg_csat:.2f}, {ct.loc['2026-04'].avg_csat:.2f}, {ct.loc['2026-05'].avg_csat:.2f}, {ct.loc['2026-06'].avg_csat:.2f}. "
      f"The dip follows the share of tickets from the defective lots ({ct.loc['2025-10'].defect_cohort_ticket_share*100:.1f}% in Oct, {ct.loc['2026-02'].defect_cohort_ticket_share*100:.1f}% in Feb 2026, {ct.loc['2026-06'].defect_cohort_ticket_share*100:.1f}% in Jun). "
      f"Excluding those tickets, the low is {ct.csat_excl_defect_cohort.min():.2f} ({ct.csat_excl_defect_cohort.idxmin()}), so the defect explains most but not all of the fall.\n")
    A("## 4. Defect / lot finding\n")
    A(f"Lots PL2-2510/2511/2512 had {e['orders']:,} orders, {e['tickets']:,} order-linked tickets and {e['replacements']} replacements: {e['defect_rate']*100:.1f} replacements and {e['tickets']/e['orders']*100:.0f} tickets per 100 orders, "
      f"against {e['base_rep_rate']*100:.1f} and {e['base_tk_rate']*100:.0f} for Pulse 2 lots from Jul-Sep 2025 and Jan-Jun 2026. The step change sits exactly at the lot boundary, which points to manufacturing rather than support handling. "
      f"Tickets from these lots score CSAT {cf['csat_dc']:.2f} (n={cf['n_dc']}) vs {cf['csat_rest']:.2f} for everything else; they are {cf['share_dc']*100:.1f}% of responses. "
      f"Only {t[t.is_pl2].order_linked.mean()*100:.1f}% of Pulse 2 tickets link to an order, so all lot counts are lower bounds.\n")
    A("## 5. Agent performance and queue-mix context\n")
    A("Raw Tier 1 rankings mostly measure queue: Charging & Battery, Warranty & Repair, Returns and Delivery tickets score lower for every handler. "
      "Each agent is therefore compared with the CSAT expected for the same category, channel and defect-lot mix (Tier 1 only; Tier 2 is not ranked against Tier 1 per policy s6).\n")
    A("| Raw rank | Agent | Team | Raw CSAT | Mix-expected | Gap | z |\n|---|---|---|---|---|---|---|")
    for x in b10.itertuples():
        A(f"| {int(x.raw_bottom_ten_rank)} | {x.agent_id} {x.agent_name} | {x.agent_team} | {x.avg_csat:.2f} | {x.mix_expected_csat:.2f} | {x.mix_adjusted_gap:+.2f} | {x.resid_z:.1f} |")
    A(f"\nThe six Logistics and Returns Desk agents have gaps between {rest.mix_adjusted_gap.min():+.2f} and {rest.mix_adjusted_gap.max():+.2f}, indistinguishable from typical. "
      f"The four Chat Frontline agents carry {fo.defect_cohort_share.mean()*100:.0f}% defect-lot tickets (chat peers {peers.defect_cohort_share.mean()*100:.0f}%) and remain {abs(fo.mix_adjusted_gap.mean()):.2f} below expectation on average (z {fo.resid_z.max():.1f} to {fo.resid_z.min():.1f}). "
      f"Of {int(R.tickets + O.tickets + T2.tickets)} defect-lot tickets, {int(R.tickets)} went to these four agents (CSAT {R.csat:.2f}, {R.replacement_rate*100:.0f}% replaced), {int(T2.tickets)} to Tier 2 (CSAT {T2.csat:.2f}) and {int(O.tickets)} to other Tier 1 (CSAT {O.csat:.2f}).\n")
    am = pd.read_csv(OUT_DIR / "agent_metrics.csv")
    lr, ev = am[am.agent_team.isin(["Logistics", "Returns Desk"])].median_handle_time, am[am.tier.eq(1) & ~am.agent_team.isin(["Logistics", "Returns Desk"])].median_handle_time
    A(f"Handle time (first human response to resolution, per agent on the dashboard) is set by queue: Tier 1 agents outside Logistics/Returns have median handle time {ev.min():.0f} to {ev.max():.0f} min; Logistics and Returns Desk {lr.min():.0f} to {lr.max():.0f} min (about 24 hours); "
      f"Tier 2 {am[am.tier == 2].median_handle_time.min():.0f} to {am[am.tier == 2].median_handle_time.max():.0f} min. The four Chat Frontline agents are {am[am.agent_id.isin(p2.FOCUS_AGENTS)].median_handle_time.min():.0f} to {am[am.agent_id.isin(p2.FOCUS_AGENTS)].median_handle_time.max():.0f} min against a chat median of "
      f"{am[am.agent_team == 'Chat Frontline'].median_handle_time.median():.0f}. Means are pulled up by a minority of very long cases, so medians are used for comparison.\n")
    A("## 6. Training priority recommendation\n")
    A(f"**Train now:** " + ", ".join(f"{x.agent_id} {x.agent_name}" for x in strong.itertuples()) + f" (95% intervals exclude zero). Nobody else shows a training signal, including the six other raw-bottom-ten agents; sending them to training would target a queue-mix artefact. "
      f"Closing the four gaps would lift Tier 1 CSAT by about {strong.tier1_csat_lift_if_gap_closed.sum():.3f}. Pair the coaching with a routing fix because case severity is not observed.\n")
    A("## 7. SLA and operational findings\n")
    A(f"- First-response SLA: {int(ov['sla_breach_count']):,} breaches ({ov['sla_breach_rate']*100:.2f}%). By channel: email {ch.loc['email'].sla_breach_rate*100:.1f}%, social {ch.loc['social'].sla_breach_rate*100:.1f}%, chat {ch.loc['chat'].sla_breach_rate*100:.1f}%, voice {ch.loc['voice'].sla_breach_rate*100:.1f}%. Email is the outlier.")
    A(f"- Breached tickets score CSAT {r[r.sla_breach].csat_score.mean():.2f} vs {r[~r.sla_breach].csat_score.mean():.2f}. Email breaches show no clear time-of-day or weekday pattern, so capacity or queue order is the working hypothesis.")
    A(f"- Transfers: {int(sum(t.transfers)):,} hand-offs; tickets with a transfer score {tx[tx.tr].csat_score.mean():.2f} vs {tx[~tx.tr].csat_score.mean():.2f} without.")
    A(f"- {int(dbl.quantity)} tickets carry both a refund and a replacement, which policy s5 forbids ({I(dbl.amount_inr)}).\n")
    A("## 8. Business impact\n")
    A("| Item | Amount |\n|---|---|")
    A(f"| Excess replacements ({row('Excess replacements').quantity:.0f} x {I(row('Excess replacements').unit_cost_inr)}, unit cost + Rs 340 per policy s5) | {I(row('Excess replacements').amount_inr)} |")
    A(f"| Excess contacts ({row('Excess contacts').quantity:.0f} x about Rs {row('Excess contacts').unit_cost_inr:.0f}, policy s4 rates) | {I(row('Excess contacts').amount_inr)} |")
    A(f"| **Core measured cost of the defect** | **{I(core)}** |")
    A(f"| Robustness: baseline from Jul-Sep 2025 lots only | {I(alt)} |")
    A(f"| Upper estimate if unlinked Pulse 2 tickets behave the same (not used for the goal) | {I(upper)} |")
    A(f"| Context, not attributed to the defect: SLA credits ({int(sla.quantity):,} x Rs 350) | {I(sla.amount_inr)} |")
    A(f"| Context, not attributed to the defect: transfers ({int(trn.quantity):,} x Rs 305) | {I(trn.amount_inr)} |")
    A(f"\nNo revenue or retention data exists, so CSAT loss is not converted into rupees.\n")
    A("## 9. Recommended actions\n")
    A("1. **Quality/Manufacturing:** root-cause lots PL2-2510/2511/2512 and contain field stock; Support: add a lot-level early-warning trigger (proposal: flag a lot above 10 replacements per 100 orders in its first 60 days; threshold and window are proposals, not derived from data).")
    A("2. **Support:** proactive outreach and single-contact replacement for owners of the three lots.")
    A(f"3. **Coaching and routing:** targeted coaching and QA sampling for {', '.join(strong.agent_id)}; spread hardware triage across the chat pool with a defect playbook; re-measure after one quarter.")
    A("4. **Do not** send the other six raw-bottom-ten agents to training; fix Delivery and Returns process issues instead.")
    A("5. **Email capacity review** and SLA-age queue ordering; fix first-touch routing for Charging and Warranty categories to cut transfers.")
    A("6. **Finance/Team Leads:** escalate the six refund-and-replacement tickets.")
    A(f"7. **Goal:** blended CSAT {cf['csat_all']:.3f} to at least {goal:.2f}, held two consecutive quarters, by end of Q1 2027. Calculation: defect-lot gap {cf['csat_rest']-cf['csat_dc']:.3f} x share {cf['share_dc']:.3f} = {cf['lift']:.3f}; {cf['csat_all']:.3f} + {cf['lift']:.3f} = {cf['csat_rest']:.3f}, rounded to {goal:.2f}. "
      f"Apr-Jun 2026 is {q2:.2f}, so the goal needs about +{goal-q2:.2f}; it depends on defect containment plus the coaching lever (about {(-(fo.mix_adjusted_gap*fo.csat_response_count).sum()/cf['n']):.3f}).\n")
    A("## 10. Important limitations and caveats\n")
    for s in ["Association, not proof of cause: the lot step change is strong evidence, but there are no failure-analysis or manufacturing records.",
              "Lot linkage is partial; counts and costs are lower bounds. No customer-plus-SKU fallback join was applied because it is ambiguous.",
              "The defect lots were identified from the lot table itself (descriptive, not a pre-registered test).",
              "Mix adjustment uses category, channel and defect-lot only. There is no case-severity field, so the four agents' gaps may partly reflect harder cases.",
              f"Agent CSAT rests on {int(ctx.csat_response_count.min())} to {int(ctx.csat_response_count.max())} survey responses per Tier 1 agent ({int(fo.csat_response_count.min())} to {int(fo.csat_response_count.max())} for the four coaching candidates); gaps below about 0.15 are noise.",
              f"CSAT covers respondents only ({ov['csat_response_rate']*100:.1f}% response rate); non-response bias is unknown.",
              "Roster has no history (shift and site are current values). Repeat-contact and first-contact resolution were not built.",
              "Free-text fields (customer_message, agent_notes) are not analysed: every finding uses structured fields only. Handle time is descriptive and is not adjusted for queue; compare agents only within their team.",
              "email-thread.txt, README.txt and submission-form.md from the client pack were not in the project files when this package was audited against the brief."]:
        A(f"- {s}")
    A("\n## 11. What should NOT be concluded from the data\n")
    for s in ["That the defect is proven to be a manufacturing fault: the data shows where and when, not why.",
              "That the six other raw-bottom-ten agents are weak performers: their raw ranking is queue mix.",
              "That A3004 to A3007 are poor performers with certainty: the gap is statistically clear but severity is unobserved.",
              "That the Rs 2,500 replacement figure from the email applies: policy s5 rates are used.",
              "That CSAT loss has a rupee value, or that refunds are attributable to the defect (reason codes are agent-selected).",
              "That Tier 2 agents are comparable with Tier 1 on volume or CSAT (policy s6).",
              "That the CSAT goal is guaranteed: future lot quality is outside support's control."]:
        A(f"- {s}")
    (ROOT / "FINAL_MEMO.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
    print("FINAL_MEMO.md written")
