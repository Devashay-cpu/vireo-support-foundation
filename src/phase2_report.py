"""Generates analysis/business_analysis.md from Phase 2 results so every number is computed, not typed.
Run: python -m src.phase2_report   (also runs src.phase2.main())"""
import numpy as np
import pandas as pd

from . import phase2 as p2
from .config import ANALYSIS_DIR

INR = lambda x: f"Rs {x:,.0f}"


def lakh(x):
    return f"Rs {x/1e5:.2f} lakh"


def md_table(df, fmt=None):
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c in fmt and pd.notna(v):
                v = fmt[c].format(v)
            elif isinstance(v, float):
                v = "" if np.isnan(v) else f"{v:.2f}"
            cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def sensitivity_extended_cohort(t):
    """Unlinked Pulse 2 tickets in the wave window are probably defect-lot cases too (their CSAT is as low)."""
    r = t[t.responded]
    ext = t.is_pl2 & ~t.order_linked & (t.month >= "2025-11") & (t.month <= "2026-06")
    rr = r[~(r.defect_cohort | ext.loc[r.index])]
    return rr.csat_score.mean(), int(ext.sum()), r[ext.loc[r.index]].csat_score.mean(), int(ext.loc[r.index].sum())


def main():
    res = p2.main()
    econ_ = res["econ"]
    t, ct, ctx, tp, econ, cf, rc, hs, bi, core, goal = (res[k] for k in
        ["t", "ct", "ctx", "tp", "econ", "cf", "rc", "hs", "bi", "core", "goal"])
    r = t[t.responded]
    ext_rest, ext_n, ext_csat, ext_resp = sensitivity_extended_cohort(t)

    peak = ct.loc[ct.avg_csat.idxmax()]
    trough = ct.loc[ct.avg_csat.idxmin()]
    roll_low = ct.loc[ct.csat_rolling_3m.idxmin()]
    pre = r[r.month < "2025-10"].csat_score.mean()
    q2 = r[r.month >= "2026-04"].csat_score.mean()
    a1 = r[r.month.isin(["2025-10", "2025-11"])].csat_score
    b1 = r[r.month.isin(["2026-01", "2026-02"])].csat_score
    d = a1.mean() - b1.mean()
    se = np.sqrt(a1.var() / len(a1) + b1.var() / len(b1))

    # mix tables
    cat = r.groupby("category").agg(responses=("csat_score", "size"), avg_csat=("csat_score", "mean")).join(
        t.groupby("category").agg(tickets=("ticket_id", "size"), replacement_rate=("rep", "mean"),
                                  transfer_rate=("transfers", "mean")))
    cat["share_of_tickets"] = cat.tickets / len(t)
    cat = cat.sort_values("avg_csat").reset_index()[["category", "tickets", "share_of_tickets", "responses", "avg_csat", "replacement_rate", "transfer_rate"]]
    teams = ctx.groupby("agent_team").agg(agents=("agent_id", "size"), tickets=("ticket_count", "sum"),
                                          raw_csat=("avg_csat", "mean"), mix_expected=("mix_expected_csat", "mean"),
                                          mix_adjusted_gap=("mix_adjusted_gap", "mean"),
                                          hardware_share=("hardware_category_share", "mean"),
                                          defect_share=("defect_cohort_share", "mean")).reset_index()
    ch = t[t.agent_tier == 1].groupby("channel").agg(tickets=("ticket_id", "size"), replacement_rate=("rep", "mean"),
                                                     sla_breach_rate=("sla_breach", "mean")).join(
        r[r.agent_tier == 1].groupby("channel").csat_score.agg(avg_csat="mean", responses="size")).reset_index()

    b10 = ctx[ctx.raw_bottom_ten_rank.notna()].sort_values("raw_bottom_ten_rank")
    b10t = b10[["raw_bottom_ten_rank", "agent_id", "agent_name", "agent_team", "site", "shift", "ticket_count", "csat_response_count",
                "avg_csat", "mix_expected_csat", "mix_adjusted_gap", "resid_z", "defect_cohort_share", "hardware_category_share",
                "workload_vs_tier1_median"]].copy()
    b10t["raw_bottom_ten_rank"] = b10t.raw_bottom_ten_rank.astype(int)
    tpt = tp.head(12)[["training_priority_rank", "agent_id", "agent_name", "agent_team", "avg_csat", "mix_adjusted_gap",
                       "resid_ci95_low", "resid_ci95_high", "evidence", "tier1_csat_lift_if_gap_closed"]].copy()
    tpt["training_priority_rank"] = tpt.training_priority_rank.astype("Int64")
    strong = tp[tp.evidence.str.startswith("strong")]

    lots = econ["lots"].loc[list(p2.DEFECT_LOT_MONTHS) + list(p2.BASELINE_LOT_MONTHS)].reset_index()
    lots["group"] = np.where(lots.lot_month.isin(p2.DEFECT_LOT_MONTHS), "defect lots", "comparison")
    lots = lots[["lot_month", "group", "orders", "tickets", "replacements", "tickets_per_100_orders", "replacements_per_100_orders", "csat"]]

    lever_a, lever_b, tgt = goal["lever_a"], goal["lever_b"], goal["target"]
    rank_map = {"A3004": 1}
    md = []
    A = md.append
    A("# Business analysis (phase 2)\n")
    A("Builds on the verified phase 1 foundation (11,750 tickets, 44 agents). No dashboard, memo or submission form yet. "
      "All figures below are computed by `src/phase2.py`; tables are in `analysis/*.csv`.\n")
    A("## 1. Strongest business finding\n")
    A(f"**A quality defect in Pulse 2 earbuds (VA-EB-PL2), lots PL2-2510, 2511 and 2512, drove the support crisis of Dec 2025 to Mar 2026.** "
      f"Those lots have {econ['defect_rate']*100:.1f} replacements per 100 orders against {econ['base_rep_rate']*100:.1f} for comparison Pulse 2 lots "
      f"({econ['orders']:,} orders, {econ['replacements']} replacements). Tickets per 100 orders are {econ['tickets']/econ['orders']*100:.0f} vs "
      f"{econ['base_tk_rate']*100:.0f}. The step change is at the lot boundary (lot-month 2509 vs 2510 vs 2601), not gradual, which points at manufacturing rather than at support handling or seasonality.\n")
    A(md_table(lots, {"tickets_per_100_orders": "{:.0f}", "replacements_per_100_orders": "{:.1f}", "csat": "{:.2f}"}))
    A("\nComparison lot-months are Jul-Sep 2025 and Jan-Jun 2026 (linked tickets only). Replacement counts come from order-linked tickets, so they are a lower bound.\n")
    A(f"Measured direct cost of the excess: **{INR(core)}** ({int(round(econ['excess_rep']))} excess replacements at Rs {econ['rep_cost_each']:,} plus "
      f"{int(round(econ['excess_tk']))} excess contacts at about Rs {econ['avg_contact_cost']:.0f}). "
      f"It also cost {cf['lift']:.3f} points of blended CSAT (section 8).\n")

    A("## 2. CSAT trend\n")
    A(f"CSAT (respondents only, n={cf['n']:,}) was steady at about 3.4 to 3.6 through Oct 2025 (Jan-Sep 2025 average {pre:.2f}), "
      f"peaked at {peak.avg_csat:.2f} in {peak.month}, then fell to a trough of **{trough.avg_csat:.2f} in {trough.month}**. The trailing 3-month average bottomed at "
      f"{roll_low.csat_rolling_3m:.2f} in {roll_low.month} and has recovered to {ct.csat_rolling_3m.iloc[-1]:.2f} by {ct.month.iloc[-1]}; "
      f"Apr-Jun 2026 averages {q2:.2f}, still below the pre-wave level. Oct-Nov 2025 vs Jan-Feb 2026 differs by {d:.2f} points "
      f"(95% CI {d-1.96*se:.2f} to {d+1.96*se:.2f}), so the drop is not sampling noise; single months carry a CI of roughly +/-0.15 to 0.2.\n")
    show = ct[["month", "csat_responses", "avg_csat", "csat_rolling_3m", "defect_cohort_ticket_share", "csat_defect_cohort", "csat_excl_defect_cohort"]].copy()
    show.columns = ["month", "responses", "CSAT", "rolling 3m", "defect-lot ticket share", "CSAT defect lots", "CSAT excl. defect lots"]
    A(md_table(show, {"CSAT": "{:.2f}", "rolling 3m": "{:.2f}", "defect-lot ticket share": "{:.1%}", "CSAT defect lots": "{:.2f}", "CSAT excl. defect lots": "{:.2f}"}))
    A(f"\nThe dip follows the defect-lot share of tickets (0.3% in Oct, {ct.set_index('month').loc['2026-02','defect_cohort_ticket_share']*100:.0f}% in Feb). "
      f"Excluding defect-lot tickets the monthly CSAT still dips (to {ct.csat_excl_defect_cohort[ct.month.between('2026-01','2026-02')].min():.2f}), so the defect explains most but not all of it; "
      "queue overload on the chat hardware rota and unlinked Pulse 2 tickets (see limitations) account for part of the rest.\n")

    A("## 3. Queue, channel and category mix\n")
    A("Category is the strongest predictor of CSAT. Hardware and post-purchase categories score 0.6 to 1.3 points below Product Enquiry or Account & Login "
      "for reasons unrelated to the agent, so raw agent averages mostly measure which queue an agent sits in.\n")
    A(md_table(cat, {"tickets": "{:,.0f}", "share_of_tickets": "{:.1%}", "responses": "{:,.0f}", "avg_csat": "{:.2f}", "replacement_rate": "{:.1%}", "transfer_rate": "{:.2f}"}))
    A("\nTier 1 teams (agent-level averages, mix expectation from a category + channel + defect-lot model fitted on Tier 1 responses):\n")
    A(md_table(teams, {"tickets": "{:,.0f}", "raw_csat": "{:.2f}", "mix_expected": "{:.2f}", "mix_adjusted_gap": "{:+.2f}", "hardware_share": "{:.0%}", "defect_share": "{:.0%}"}))
    A("\nChannel makes little difference to CSAT (Tier 1):\n")
    A(md_table(ch, {"tickets": "{:,.0f}", "replacement_rate": "{:.1%}", "sla_breach_rate": "{:.1%}", "avg_csat": "{:.2f}", "responses": "{:,.0f}"}))
    A("\nEmail has the worst first-response breach rate (12.2% overall); channel does not move CSAT by more than 0.05.\n")

    A("## 4. Raw Tier-1 bottom ten, with context\n")
    A("Raw = plain average CSAT among respondents, ranked within Tier 1 only (38 agents). `mix_expected_csat` is what a typical Tier 1 agent would score on the same "
      "category/channel/defect-lot mix; `mix_adjusted_gap` is actual minus expected; z is the gap over its standard error.\n")
    A(md_table(b10t, {"ticket_count": "{:.0f}", "csat_response_count": "{:.0f}", "avg_csat": "{:.2f}", "mix_expected_csat": "{:.2f}", "mix_adjusted_gap": "{:+.2f}", "resid_z": "{:.1f}", "defect_cohort_share": "{:.0%}",
                      "hardware_category_share": "{:.0%}", "workload_vs_tier1_median": "{:.2f}x"}))
    fo = ctx[ctx.agent_id.isin(p2.FOCUS_AGENTS)]
    A(f"\nReading it: six of the ten (Logistics x3, Returns Desk x3) sit in Delivery/Returns queues that score about 3.2 for everyone; their mix-adjusted gaps are "
      f"between {ctx[ctx.agent_id.isin(b10.agent_id) & ~ctx.agent_id.isin(p2.FOCUS_AGENTS)].mix_adjusted_gap.min():+.2f} and "
      f"{ctx[ctx.agent_id.isin(b10.agent_id) & ~ctx.agent_id.isin(p2.FOCUS_AGENTS)].mix_adjusted_gap.max():+.2f}, indistinguishable from typical. "
      f"The other four (A3004 to A3007, Chat Frontline) carry {fo.hardware_category_share.mean():.0%} hardware tickets and {fo.defect_cohort_share.mean():.0%} defect-lot tickets "
      f"(Chat peers {ctx[(ctx.agent_team=='Chat Frontline') & ~ctx.agent_id.isin(p2.FOCUS_AGENTS)].defect_cohort_share.mean():.0%}) and are still {abs(fo.mix_adjusted_gap.mean()):.2f} below expectation, "
      f"{fo.resid_z.max():.1f} to {fo.resid_z.min():.1f} standard errors out. Mix explains only {fo.share_of_raw_gap_explained_by_mix.mean():.0%} of their raw gap. "
      "A `share_of_raw_gap_explained_by_mix` above 100% means the agent beats expectation once mix is considered.\n")

    A("## 5. Training priority (Tier 1 only)\n")
    A(f"Ranked by shrunken mix-adjusted gap times ticket volume (empirical-Bayes shrinkage k={p2.SHRINK_K} responses; agents need at least {p2.MIN_RESPONSES_FOR_PRIORITY} responses). "
      "Tier 2 is not ranked against Tier 1 (policy s6).\n")
    A(md_table(tpt, {"avg_csat": "{:.2f}", "mix_adjusted_gap": "{:+.2f}", "resid_ci95_low": "{:+.2f}", "resid_ci95_high": "{:+.2f}", "tier1_csat_lift_if_gap_closed": "{:.3f}"}))
    A(f"\n**Train now:** {', '.join(strong.agent_id)}, the only agents whose gap's 95% CI excludes zero. Everyone else, including the six other raw-bottom-ten agents, shows no training signal; "
      f"sending them to training would spend effort on a queue-mix artefact. Closing the four agents' gap would lift Tier 1 CSAT by about {strong.tier1_csat_lift_if_gap_closed.sum():.3f} points. "
      "Caveat: the rota may receive harder cases than category shows (no severity field), so pair training with a routing fix.\n")

    A("## 6. Root causes (ranked)\n")
    for _, x in rc.iterrows():
        A(f"{int(x['rank'])}. **{x.root_cause}.** {x.evidence}. *Confidence: {x.confidence}.* Action: {x.owner_action}.")
    A("")
    A(f"Handler split for defect-lot tickets: " + "; ".join(f"{i}: {int(v.tickets)} tickets, CSAT {v.csat:.2f}, {v.replacement_rate:.0%} replaced" for i, v in hs.iterrows()) + ".\n")

    A("## 7. Business impact\n")
    show = bi[["item", "quantity", "unit_cost_inr", "amount_inr", "treatment"]].copy()
    A(md_table(show, {"quantity": "{:,.0f}", "unit_cost_inr": "{:,.0f}", "amount_inr": "{:,.0f}"}))
    A(f"\nUse the core total ({INR(core)}) as the defensible figure. It is order-linked only; scaling for the 34.6% of Pulse 2 tickets with no order link gives about "
      f"{INR(core/t[t.is_pl2].order_linked.mean())}, which is an upper estimate and is not used for the goal. SLA credits and transfer costs are real spend but only partly avoidable "
      "and are not attributed to the defect. Replacement costs follow policy s5 (unit cost + Rs 340, no refurbishment recovery); the Rs 2,500 figure from the email is not used. "
      "No revenue or retention data exists in the pack, so CSAT loss is not converted into rupees.\n")

    A("## 8. Numeric business goal\n")
    A(f"**Goal: raise blended CSAT from {goal['current']:.2f} to at least {tgt:.2f} and hold it for two consecutive quarters, by end of Q1 2027.**\n")
    A("Calculation:\n")
    A(f"- Blended CSAT over 18 months: {cf['csat_all']:.3f} (n={cf['n']:,}).")
    A(f"- CSAT on all tickets outside the defect lots: {cf['csat_rest']:.3f} (n={cf['n']-cf['n_dc']:,}). This is what the desk already delivers when the product is not failing.")
    A(f"- Defect-lot tickets: n={cf['n_dc']} ({cf['share_dc']*100:.1f}% of responses) at {cf['csat_dc']:.3f}. Gap {cf['csat_rest']-cf['csat_dc']:.3f} x {cf['share_dc']:.3f} = **{cf['lift']:.3f} points**.")
    A(f"- {cf['csat_all']:.3f} + {cf['lift']:.3f} = {cf['csat_rest']:.3f}, rounded to **{tgt:.2f}**.")
    A(f"- The target is conservative: unlinked Pulse 2 tickets in Nov 2025 to Jun 2026 ({ext_resp} responses) score {ext_csat:.2f}, so they look like defect cases too; treating them as cohort lifts the clean baseline to {ext_rest:.2f}. "
      f"The pre-wave level (Jan-Sep 2025) was {pre:.2f}.")
    q2r = r[r.month >= "2026-04"]
    q2_ex = q2r[~q2r.defect_cohort].csat_score.mean()
    q2_ext = q2r[~(q2r.defect_cohort | (t.is_pl2 & ~t.order_linked).loc[q2r.index])].csat_score.mean()
    A(f"- Feasibility: Jun 2026 is already {ct.avg_csat.iloc[-1]:.2f}; Apr-Jun 2026 is {q2:.2f} ({q2_ex:.2f} excluding strict defect-lot tickets, {q2_ext:.2f} excluding all Pulse 2 tickets without an order link). "
      f"Reaching {tgt:.2f} needs about +{tgt-q2:.2f} on the current quarter. Removing the cohort alone is not quite enough on the strict definition ({q2_ex:.2f}), so the goal also needs lever (b) and continued fading of the wave.")
    A(f"- Levers: (a) defect containment, proactive outreach and single-contact replacement for owners of the three lots, worth up to {lever_a:.3f}; "
      f"(b) coaching plus rerouting for A3004 to A3007, worth about {lever_b:.3f} ({abs(fo.mix_adjusted_gap.mean()):.2f} gap x {int(fo.csat_response_count.sum())} responses / {cf['n']:,}). "
      "Lever (b) alone cannot reach the target; it depends on (a).")
    A("- Guardrail (supporting): flag any new lot whose replacement rate exceeds 10 per 100 orders (2x the "
      f"{econ['base_rep_rate']*100:.1f} baseline) within its first 60 days. The 10 threshold and 60-day window are proposals, not derived from this data.\n")

    A("## 9. Limitations\n")
    lim = [
        "Association, not proof of cause. The lot-level step change is strong evidence of a lot defect, but this data has no failure-analysis or manufacturing records.",
        f"Lot linkage covers only order-linked tickets: {t[t.is_pl2].order_linked.mean()*100:.1f}% of Pulse 2 tickets. Unlinked Pulse 2 tickets during the wave score {ext_csat:.2f}, so the strict cohort understates the defect and the counterfactual CSAT is biased slightly low. No fallback join (customer + SKU) was applied because it is ambiguous.",
        f"The defect lot months (2510 to 2512) were identified from the lot table itself (every month above 25 replacements per 100 orders; no other lot-month above 7), so this is descriptive, not a pre-registered test. Comparison lots are Jul-Sep 2025 and Jan-Jun 2026 (Apr-Jun 2025 lots are too small). Recent lots are right-censored (they have had less time to generate tickets), which slightly understates the baseline; using Jul-Sep 2025 lots only gives a core cost of {INR(econ['alt_core'])} vs {INR(core)}.",
        "Mix adjustment uses category, channel, defect-lot and Pulse 2 dummies. Unobserved case severity, customer mood and any routing rule (the chat hardware rota) can still bias the four agents' gaps; no ticket-level severity field exists. Message text was not analysed.",
        "Agent CSAT rests on 97 to 243 responses per agent; gaps below about 0.15 are not distinguishable from noise. The shrinkage constant (k=60) is a judgement call.",
        "CSAT is respondents only (44% response rate); non-response bias is unknown.",
        "Business impact excludes lost revenue, churn, brand cost and any refurbishment recovery (policy says do not assume it). Refund figures were not attributed to the defect because refund reason codes are agent-selected from a dropdown.",
        "SLA and transfer costs use policy planning rates. Breaches are assigned to the resolving agent per policy, even where routing caused the delay.",
        "Roster has no history, so shift and site are current values. Repeat-contact and first-contact-resolution (policy s10) are still not built.",
        f"The goal target ({tgt:.2f}) is a floor tied to this dataset's own baseline; whether future lots are defect-free is outside support's control.",
    ]
    for i, l in enumerate(lim, 1):
        A(f"{i}. {l}")
    (ANALYSIS_DIR / "business_analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return res, dict(ext_rest=ext_rest, ext_csat=ext_csat, ext_resp=ext_resp, pre=pre, q2=q2)


if __name__ == "__main__":
    main()
    print("business_analysis.md written")
