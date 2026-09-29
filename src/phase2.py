"""Phase 2 business analysis. Reads Phase 1 outputs (outputs/*.csv) plus raw orders/products/agents.

Writes: analysis/csat_trend.csv, agent_context.csv, training_priority.csv, root_causes.csv,
        business_impact.csv, business_analysis.md (the .md is written by phase2_report.py).
Run:    python -m src.phase2
No per-ticket LLM/API calls. Phase 1 code and outputs are not modified.
"""
import numpy as np
import pandas as pd

from .config import OUT_DIR, ANALYSIS_DIR, RAW_DIR, REPLACEMENT_LOGISTICS_INR

# ---- policy s4 cost standards (support-policy.pdf v3.2) ----
CONTACT_COST = {"chat": 210, "email": 260, "voice": 520, "social": 240}
TRANSFER_COST = 305
SLA_CREDIT = 350

# ---- analyst definitions ----
DEFECT_SKU = "VA-EB-PL2"
DEFECT_LOT_MONTHS = ("2510", "2511", "2512")           # lot code PL2-YYMM-n; found from lot-level rates
BASELINE_LOT_MONTHS = ("2507", "2508", "2509", "2601", "2602", "2603", "2604", "2605", "2606")
HW_CATEGORIES = ("Charging & Battery", "Audio Quality", "Connectivity", "Warranty & Repair", "App & Firmware")
SHRINK_K = 60          # empirical-Bayes prior strength, in CSAT responses
MIN_RESPONSES_FOR_PRIORITY = 80


def load_base():
    t = pd.read_csv(OUT_DIR / "ticket_metrics.csv")
    o = pd.read_csv(RAW_DIR / "orders.csv")
    a = pd.read_csv(OUT_DIR / "agent_metrics.csv")
    t = t.merge(o[["order_id", "lot_code", "order_date"]], on="order_id", how="left")
    t["lot_month"] = t.lot_code.str.split("-").str[1]
    t["is_pl2"] = t.product_sku == DEFECT_SKU
    t["defect_cohort"] = t.is_pl2 & t.lot_month.isin(DEFECT_LOT_MONTHS)
    t["rep"] = t.replacement_issued == "Y"
    t["responded"] = t.csat_score.notna()
    t["hw_cat"] = t.category.isin(HW_CATEGORIES)
    t["created_at"] = pd.to_datetime(t.created_at)
    return t, o, a


def ci95(mean, sd, n):
    se = sd / np.sqrt(n) if n > 1 else np.nan
    return mean - 1.96 * se, mean + 1.96 * se


# --------------------------------------------------------------------------- CSAT trend
def csat_trend(t):
    rows = []
    for m, g in t.groupby("month"):
        r = g[g.responded]
        rd = r[r.defect_cohort]
        rn = r[~r.defect_cohort]
        lo, hi = ci95(r.csat_score.mean(), r.csat_score.std(), len(r))
        rows.append({
            "month": m, "tickets": len(g), "csat_responses": len(r),
            "avg_csat": r.csat_score.mean(), "csat_ci95_low": lo, "csat_ci95_high": hi,
            "low_csat_rate": (r.csat_score <= 2).mean(),
            "defect_cohort_tickets": int(g.defect_cohort.sum()),
            "defect_cohort_ticket_share": g.defect_cohort.mean(),
            "csat_defect_cohort": rd.csat_score.mean() if len(rd) else np.nan,
            "csat_responses_defect_cohort": len(rd),
            "csat_excl_defect_cohort": rn.csat_score.mean(),
            "csat_tier1": r[r.agent_tier == 1].csat_score.mean(),
            "csat_tier2": r[r.agent_tier == 2].csat_score.mean(),
            "replacement_rate": g.rep.mean(),
            "sla_breach_rate": g.sla_breach.mean(),
        })
    d = pd.DataFrame(rows)
    # response-weighted trailing 3-month CSAT
    s = t[t.responded].copy()
    months = list(d.month)
    roll = []
    for i, m in enumerate(months):
        w = s[s.month.isin(months[max(0, i - 2): i + 1])]
        roll.append(w.csat_score.mean())
    d["csat_rolling_3m"] = roll
    d["csat_gap_excl_defect_minus_actual"] = d.csat_excl_defect_cohort - d.avg_csat
    return d


# --------------------------------------------------------------------------- mix-adjusted expectation
def mix_model(t):
    """Expected CSAT per Tier-1 ticket from category + channel + defect-cohort + PL2 dummies (OLS).
    Agent-controlled outcomes (transfers, SLA breach, replacement decision, handle time) are deliberately
    NOT controlled, so they stay in the agent's residual."""
    r = t[(t.agent_tier == 1) & t.responded].copy()
    X = pd.get_dummies(r[["category", "channel"]], drop_first=True).astype(float)
    X["defect_cohort"] = r.defect_cohort.astype(float)
    X["is_pl2"] = r.is_pl2.astype(float)
    X.insert(0, "const", 1.0)
    b, *_ = np.linalg.lstsq(X.values, r.csat_score.values, rcond=None)
    r["expected"] = X.values @ b
    r["resid"] = r.csat_score - r.expected
    return r, dict(zip(X.columns, b))


# --------------------------------------------------------------------------- agent context
def agent_context(t, a):
    r, coefs = mix_model(t)
    t1 = t[t.agent_tier == 1]
    ag = a[a.tier == 1].set_index("agent_id")
    res = r.groupby("agent_id").agg(n_resp=("csat_score", "size"), resid=("resid", "mean"),
                                    resid_sd=("resid", "std"), expected=("expected", "mean"))
    res["resid_se"] = res.resid_sd / np.sqrt(res.n_resp)
    res["resid_z"] = res.resid / res.resid_se
    # empirical-Bayes shrinkage toward 0 (agents' residuals average ~0 by construction)
    res["resid_shrunk"] = res.resid * res.n_resp / (res.n_resp + SHRINK_K)
    res["resid_ci95_low"] = res.resid - 1.96 * res.resid_se
    res["resid_ci95_high"] = res.resid + 1.96 * res.resid_se

    mix = t1.groupby("agent_id").agg(
        tickets=("ticket_id", "size"),
        pl2_share=("is_pl2", "mean"), defect_cohort_share=("defect_cohort", "mean"),
        hardware_category_share=("hw_cat", "mean"),
        charging_share=("category", lambda s: (s == "Charging & Battery").mean()),
        delivery_returns_share=("category", lambda s: s.isin(["Delivery & Shipping", "Returns & Refunds"]).mean()),
        chat_share=("channel", lambda s: (s == "chat").mean()), email_share=("channel", lambda s: (s == "email").mean()),
        voice_share=("channel", lambda s: (s == "voice").mean()), social_share=("channel", lambda s: (s == "social").mean()),
        replacement_rate=("rep", "mean"), transfer_rate=("transfers", "mean"),
    )
    # routed-in share: ticket first routed to a different team than the agent's own team
    tt = t1.merge(a[["agent_id", "agent_team"]], on="agent_id")
    mix["share_first_routed_elsewhere"] = tt.groupby("agent_id").apply(
        lambda g: (g.assigned_team != g.agent_team).mean(), include_groups=False)
    # peer benchmark inside the same team (chat rota vs other chat agents)
    df = ag[["agent_name", "site", "shift", "agent_team", "ticket_count", "csat_response_count", "avg_csat",
             "low_csat_rate", "sla_breach_rate", "csat_rank_within_tier", "tier_agent_count",
             "bottom_ten_raw_tier1"]].join(mix.drop(columns="tickets")).join(res)
    df["mix_expected_csat"] = df.expected
    df["mix_adjusted_gap"] = df.avg_csat - df.expected
    tier_avg = r.csat_score.mean()
    df["tier1_avg_csat"] = tier_avg
    df["raw_gap_vs_tier1_avg"] = df.avg_csat - tier_avg
    df["share_of_raw_gap_explained_by_mix"] = np.where(
        df.raw_gap_vs_tier1_avg < 0, 1 - (df.mix_adjusted_gap / df.raw_gap_vs_tier1_avg), np.nan)
    df["workload_vs_tier1_median"] = df.ticket_count / df.ticket_count.median()
    df = df.drop(columns=["expected", "resid", "resid_sd", "n_resp"])
    df = df.reset_index().sort_values("csat_rank_within_tier")
    df.insert(df.columns.get_loc("bottom_ten_raw_tier1") + 1, "raw_bottom_ten_rank",
              df.csat_rank_within_tier.where(df.bottom_ten_raw_tier1).rank(method="first"))
    return df, r, coefs


# --------------------------------------------------------------------------- training priority
def training_priority(ctx, r):
    d = ctx[ctx.csat_response_count >= MIN_RESPONSES_FOR_PRIORITY].copy()
    d["customers_affected_per_18m"] = d.csat_response_count / 0.4422  # responses / response rate -> attended tickets
    d["priority_score"] = (-d.resid_shrunk).clip(lower=0) * d.ticket_count
    d["evidence"] = np.select(
        [(d.resid_ci95_high < 0), (d.resid_z <= -1.5)],
        ["strong: mix-adjusted gap, 95% CI excludes 0", "watch: gap present, CI includes 0"], "no evidence of gap after mix")
    d = d.sort_values("priority_score", ascending=False).reset_index(drop=True)
    d["training_priority_rank"] = np.where(d.priority_score > 0, np.arange(1, len(d) + 1), np.nan)
    # tier: A = train now, B = watch, C = none
    d["recommendation"] = np.select(
        [d.evidence.str.startswith("strong"), d.evidence.str.startswith("watch")],
        ["Train now (coaching + QA on hardware/charging tickets)", "Watch: re-check next quarter"],
        "No training signal; raw score is queue mix")
    # what would fixing the strong group buy?
    lift = {}
    resp_total = len(r)
    for aid in d.loc[d.evidence.str.startswith("strong"), "agent_id"]:
        row = d.set_index("agent_id").loc[aid]
        lift[aid] = -row.mix_adjusted_gap * row.csat_response_count / resp_total
    d["tier1_csat_lift_if_gap_closed"] = d.agent_id.map(lift)
    cols = ["training_priority_rank", "agent_id", "agent_name", "agent_team", "site", "shift", "ticket_count",
            "csat_response_count", "avg_csat", "raw_gap_vs_tier1_avg", "mix_expected_csat", "mix_adjusted_gap",
            "resid_ci95_low", "resid_ci95_high", "resid_z", "resid_shrunk", "defect_cohort_share",
            "hardware_category_share", "workload_vs_tier1_median", "csat_rank_within_tier", "bottom_ten_raw_tier1",
            "priority_score", "evidence", "recommendation", "tier1_csat_lift_if_gap_closed"]
    return d[cols]


# --------------------------------------------------------------------------- root causes / cohort economics
def lot_table(t, o):
    p = o[o.sku == DEFECT_SKU].copy()
    p["lot_month"] = p.lot_code.str.split("-").str[1]
    tk = t[t.is_pl2 & t.order_id.notna()]
    g = tk.groupby("lot_month").agg(tickets=("ticket_id", "size"), replacements=("rep", "sum"),
                                    csat=("csat_score", "mean"))
    g["orders"] = p.groupby("lot_month").size()
    g["tickets_per_100_orders"] = g.tickets / g.orders * 100
    g["replacements_per_100_orders"] = g.replacements / g.orders * 100
    return g


def cohort_economics(t, o):
    g = lot_table(t, o)
    d = g.loc[list(DEFECT_LOT_MONTHS)]
    b = g.loc[list(BASELINE_LOT_MONTHS)]
    base_rep = b.replacements.sum() / b.orders.sum()
    base_tk = b.tickets.sum() / b.orders.sum()
    orders = int(d.orders.sum())
    rep_actual = int(d.replacements.sum())
    tk_actual = int(d.tickets.sum())
    rep_expected = base_rep * orders
    tk_expected = base_tk * orders
    unit = 1480
    rep_cost_each = unit + REPLACEMENT_LOGISTICS_INR
    dc = t[t.defect_cohort]
    contact_cost = dc.channel.map(CONTACT_COST).mean()
    b2 = g.loc[["2507", "2508", "2509"]]          # sensitivity: fully matured pre-wave lots only
    alt_rep, alt_tk = b2.replacements.sum() / b2.orders.sum(), b2.tickets.sum() / b2.orders.sum()
    alt_core = (rep_actual - alt_rep * orders) * rep_cost_each + (tk_actual - alt_tk * orders) * contact_cost
    return dict(alt_rep_rate=alt_rep, alt_tk_rate=alt_tk, alt_core=alt_core,
                orders=orders, tickets=tk_actual, replacements=rep_actual, base_rep_rate=base_rep, base_tk_rate=base_tk,
                rep_expected=rep_expected, tk_expected=tk_expected, excess_rep=rep_actual - rep_expected,
                excess_tk=tk_actual - tk_expected, rep_cost_each=rep_cost_each, avg_contact_cost=contact_cost,
                defect_rate=rep_actual / orders, lots=g)


def csat_counterfactual(t):
    r = t[t.responded]
    dc = r[r.defect_cohort]
    rn = r[~r.defect_cohort]
    return dict(n=len(r), n_dc=len(dc), share_dc=len(dc) / len(r), csat_all=r.csat_score.mean(),
                csat_dc=dc.csat_score.mean(), csat_rest=rn.csat_score.mean(),
                lift=r.csat_score.mean() * -1 + rn.csat_score.mean())


def handler_split(t, a):
    ag = a.set_index("agent_id")
    h = np.where(t.agent_id.isin(FOCUS_AGENTS), "Chat hardware-rota four (A3004-A3007)",
                 np.where(t.agent_tier == 2, "Tier 2 (Escalations & Warranty)", "Other Tier 1"))
    x = t.assign(handler=h)
    out = x[x.defect_cohort].groupby("handler").agg(
        tickets=("ticket_id", "size"), responses=("csat_score", "count"), csat=("csat_score", "mean"),
        replacement_rate=("rep", "mean"))
    return out


FOCUS_AGENTS = ["A3004", "A3005", "A3006", "A3007"]


def build_root_causes(t, o, a, ctx, econ, cf):
    hs = handler_split(t, a)
    r = t[t.responded]
    rows = []
    fr_rep = t[t.defect_cohort & t.agent_id.isin(FOCUS_AGENTS)].rep.mean()
    ot_rep = t[t.defect_cohort & (t.agent_tier == 1) & ~t.agent_id.isin(FOCUS_AGENTS)].rep.mean()
    teams = a.set_index("agent_id").agent_team
    lg = ctx[ctx.agent_team == "Logistics"].mix_adjusted_gap
    rd = ctx[ctx.agent_team == "Returns Desk"].mix_adjusted_gap
    t1nd = t[(t.agent_tier == 1) & ~t.defect_cohort & (t.category == "Charging & Battery") & t.responded]
    is4 = t1nd.agent_id.isin(FOCUS_AGENTS)
    fr_cb, ot_cb = t1nd[is4].csat_score.mean(), t1nd[~is4 & t1nd.agent_id.map(teams).isin(["Chat Frontline", "Email Frontline", "Voice Frontline"])].csat_score.mean()
    chat_other = t[(t.agent_tier == 1) & (t.agent_id.map(teams) == "Chat Frontline") & t.responded & ~t.agent_id.isin(FOCUS_AGENTS)]
    fr_all = t[t.agent_id.isin(FOCUS_AGENTS) & t.responded]
    pre = lambda d: d[d.month < "2025-10"].csat_score.mean()
    wave = lambda d: d[d.month.isin(["2025-12", "2026-01", "2026-02", "2026-03"])].csat_score.mean()
    gap_pre, gap_wave = pre(chat_other) - pre(fr_all), wave(chat_other) - wave(fr_all)
    dl_ret = r[r.category.isin(["Delivery & Shipping", "Returns & Refunds"]) & ~r.defect_cohort].csat_score.mean()
    mo = t[t.is_attended & (t.channel == "email")]
    wd = mo.groupby(mo.created_at.dt.dayofweek).sla_breach.mean()
    hr = mo.groupby(pd.cut(mo.created_at.dt.hour, [-1, 5, 9, 13, 17, 21, 23])).sla_breach.mean()
    mm = mo.groupby("month").sla_breach.mean()
    lots = econ["lots"]
    base_tk = econ["base_tk_rate"] * 100

    def add(rank, rc, ev, metric, value, comp, cost, confidence, action):
        rows.append(dict(rank=rank, root_cause=rc, evidence=ev, key_metric=metric, key_value=value,
                         comparison=comp, est_annual_or_period_cost_inr=cost, confidence=confidence,
                         owner_action=action))

    add(1, "Pulse 2 (VA-EB-PL2) quality defect in lots PL2-2510/2511/2512",
        f"Replacement rate {econ['defect_rate']*100:.1f} per 100 orders in these three lot-months vs {econ['base_rep_rate']*100:.1f} in comparison Pulse 2 lot-months; "
        f"tickets per 100 orders {econ['tickets']/econ['orders']*100:.0f} vs {base_tk:.0f}; concentrated in Charging & Battery, Audio Quality, Warranty & Repair; "
        "volume wave Dec 2025 to Mar 2026 tracks the sales of those lots",
        "replacements per 100 orders (defect lots)", round(econ["defect_rate"] * 100, 1),
        f"baseline {econ['base_rep_rate']*100:.1f}", round(econ["excess_rep"] * econ["rep_cost_each"]),
        "High (lot-level, clear step change, dose-response by lot; causal mechanism not observable in this data)",
        "Quality/Manufacturing: root-cause the three lots and contain field stock; Support: lot-level early-warning trigger")
    add(2, "Defect-cohort tickets scored much lower on CSAT and drag the blended score",
        f"CSAT {cf['csat_dc']:.2f} on defect-cohort tickets (n={cf['n_dc']}) vs {cf['csat_rest']:.2f} on all other "
        f"tickets; cohort is {cf['share_dc']*100:.1f}% of responses, worth {cf['lift']:.3f} CSAT points overall",
        "blended CSAT lift if cohort scored like the rest", round(cf["lift"], 3),
        f"actual {cf['csat_all']:.3f} vs counterfactual {cf['csat_rest']:.3f}", np.nan,
        "High for size of effect; medium for attribution (some of the cohort's low CSAT is handler/queue driven, see #3)",
        "Proactive outreach to owners of lots 2510-2512; fast-track replacement without a second contact")
    fr = hs.loc["Chat hardware-rota four (A3004-A3007)"]
    ot = hs.loc["Other Tier 1"]
    t2 = hs.loc["Tier 2 (Escalations & Warranty)"]
    add(3, "Defect tickets were routed disproportionately to four Chat Frontline agents and to Tier 2",
        f"Of {int(hs.tickets.sum())} defect-cohort tickets, {int(fr.tickets)} went to A3004-A3007 (4 of 44 agents) and {int(t2.tickets)} to Tier 2; "
        f"CSAT on those tickets {fr.csat:.2f} (rota four) and {t2.csat:.2f} (Tier 2) vs {ot.csat:.2f} for other Tier 1; "
        f"rota four replaced {fr_rep*100:.0f}% of them vs {ot_rep*100:.0f}% for other Tier 1 agents",
        "share of defect tickets on 4 agents", round(fr.tickets / hs.tickets.sum(), 3),
        f"4/44 agents = 9% of headcount", np.nan,
        "Medium: routing concentration is observed; whether the rota got harder cases cannot be tested (no severity field)",
        "Spread hardware triage across the chat pool; give the rota a defect playbook (script, replace-or-repair rule)")
    strong = ctx[ctx.agent_id.isin(FOCUS_AGENTS)]
    add(4, "Residual coaching gap on the same four agents after adjusting for queue mix",
        f"Mix-adjusted CSAT gap {strong.mix_adjusted_gap.min():.2f} to {strong.mix_adjusted_gap.max():.2f} "
        f"(z {strong.resid_z.max():.1f} to {strong.resid_z.min():.1f}); gap is also present on non-defect charging tickets "
        f"(non-defect Charging & Battery CSAT {fr_cb:.2f} vs {ot_cb:.2f} for other frontline agents); their CSAT gap to other chat agents was {gap_pre:.2f} before Oct 2025, widening to {gap_wave:.2f} in Dec 2025 to Mar 2026",
        "avg mix-adjusted gap, four agents", round(strong.mix_adjusted_gap.mean(), 3), "peer avg 0.0", np.nan,
        "Medium: statistically clear, but unobserved case severity could explain part of it",
        "Targeted coaching + QA sampling for these four; re-measure after one quarter")
    add(5, "Low raw CSAT for Logistics and Returns Desk agents is queue mix, not performance",
        f"Their mix-adjusted gap is small (Logistics {lg.min():+.2f} to {lg.max():+.2f}; Returns Desk {rd.min():+.2f} to {rd.max():+.2f}), inside noise; "
        f"Delivery & Shipping and Returns & Refunds tickets average {dl_ret:.2f} CSAT for all handlers vs {cf['csat_rest']:.2f} overall",
        "raw bottom-ten agents whose gap is explained by mix", int((ctx.raw_bottom_ten_rank.notna() & ~ctx.agent_id.isin(FOCUS_AGENTS)).sum()),
        "of 10 raw bottom-ten", np.nan, "High",
        "Do not send these six agents to training; fix delivery/returns process instead")
    # SLA
    att = t[t.is_attended]
    breaches = int(att.sla_breach.sum())
    add(6, "Email first-response SLA misses (12.2% vs 6.4 to 8.6% elsewhere)",
        f"Breach rate by weekday {wd.min()*100:.0f} to {wd.max()*100:.0f}%, by time-of-day block {hr.min()*100:.0f} to {hr.max()*100:.0f}%, by month {mm.min()*100:.0f} to {mm.max()*100:.0f}% (small monthly n): no clear peak-time driver, so capacity/queue order is the working hypothesis; "
        f"breached tickets score CSAT {r[r.sla_breach].csat_score.mean():.2f} vs {r[~r.sla_breach].csat_score.mean():.2f}; {breaches} attended breaches trigger Rs {SLA_CREDIT} credits each",
        "SLA credit cost (attended breaches x Rs 350)", breaches * SLA_CREDIT, "policy s3", breaches * SLA_CREDIT,
        "Medium (association only)", "Capacity review of Email Frontline; consider priority ordering by SLA age")
    trs = int(t.transfers.sum())
    add(7, "Hand-offs between teams (transfers)",
        f"{trs} transfers cost Rs {TRANSFER_COST} each; tickets with a transfer score CSAT 2.98 to 3.10 vs 3.36 with none; Tier 2 transfer rate is double Tier 1",
        "transfer cost", trs * TRANSFER_COST, "policy s4", trs * TRANSFER_COST,
        "Medium (association only)", "Fix first-touch routing for Charging/Warranty categories")
    return pd.DataFrame(rows), hs


# --------------------------------------------------------------------------- business impact
def build_impact(t, econ, cf):
    att = t[t.is_attended]
    rows = []

    def add(item, basis, qty, unit, total, treatment):
        rows.append(dict(item=item, basis=basis, quantity=qty, unit_cost_inr=unit,
                         amount_inr=(round(total) if pd.notna(total) else np.nan), treatment=treatment))

    ex_rep = econ["excess_rep"]
    core_ = ex_rep * econ["rep_cost_each"] + econ["excess_tk"] * econ["avg_contact_cost"]
    add("Excess replacements, defective Pulse 2 lots",
        f"actual {econ['replacements']} minus expected {econ['rep_expected']:.0f} at baseline {econ['base_rep_rate']*100:.1f}/100 orders; "
        f"cost = unit Rs 1,480 + Rs {REPLACEMENT_LOGISTICS_INR} (policy s5), no refurbishment recovery",
        round(ex_rep), econ["rep_cost_each"], ex_rep * econ["rep_cost_each"], "core, order-linked tickets only (lower bound)")
    ex_tk = econ["excess_tk"]
    add("Excess contacts, defective Pulse 2 lots",
        f"actual {econ['tickets']} minus expected {econ['tk_expected']:.0f} at baseline {econ['base_tk_rate']*100:.0f} tickets/100 orders; "
        "cost = channel contact cost (policy s4) weighted by cohort channel mix",
        round(ex_tk), round(econ["avg_contact_cost"], 1), ex_tk * econ["avg_contact_cost"], "core, order-linked tickets only (lower bound)")
    core = ex_rep * econ["rep_cost_each"] + ex_tk * econ["avg_contact_cost"]
    add("CORE TOTAL: measured direct cost of the defect", "sum of the two lines above", np.nan, np.nan, core, "headline")

    add("Sensitivity: baseline from Jul-Sep 2025 lots only (fully matured, excludes recent right-censored lots)",
        f"baseline {econ['alt_rep_rate']*100:.1f} replacements and {econ['alt_tk_rate']*100:.0f} tickets per 100 orders",
        np.nan, np.nan, econ["alt_core"], f"robustness check; {abs(econ['alt_core']/core_-1)*100:.1f}% from core")
    # sensitivity: unlinked Pulse 2 tickets
    pl2_all = t[t.is_pl2]
    link = pl2_all.order_linked.mean()
    add("Sensitivity: scale core total for the 34.6% of Pulse 2 tickets with no order link",
        f"only {link*100:.1f}% of Pulse 2 tickets can be tied to a lot; if unlinked tickets behave the same, core / link rate",
        np.nan, np.nan, core / link, "upper estimate, assumption-dependent, not used in the goal")

    sla_n = int(att.sla_breach.sum())
    add("SLA credits paid on attended breaches", f"{sla_n} attended breaches x Rs {SLA_CREDIT}, issued regardless of reason (policy s3)",
        sla_n, SLA_CREDIT, sla_n * SLA_CREDIT, "context: not defect-specific, only partly avoidable")
    trs = int(t.transfers.sum())
    add("Transfer handling cost", f"{trs} transfers x Rs {TRANSFER_COST} (policy s4)", trs, TRANSFER_COST, trs * TRANSFER_COST,
        "context: not defect-specific, only partly avoidable")
    dbl = t[t.dq_refund_and_replacement]
    dbl_amt = dbl.refund_amount_inr.fillna(0).sum() + dbl.replacement_cost_inr.fillna(0).sum()
    add("Tickets with refund AND replacement (policy s5 breach)", f"{len(dbl)} tickets; refund + replacement cost", len(dbl), np.nan, dbl_amt,
        "control failure; small, escalate to Finance")

    # CSAT effect, unmonetised
    add("CSAT drag from the defect cohort (not monetised)",
        f"{cf['share_dc']*100:.1f}% of responses at {cf['csat_dc']:.2f} vs {cf['csat_rest']:.2f} for the rest; blended CSAT {cf['csat_all']:.3f} would be {cf['csat_rest']:.3f}",
        np.nan, np.nan, np.nan, "no revenue/retention data in the pack, so no rupee value is claimed")
    return pd.DataFrame(rows), core


# --------------------------------------------------------------------------- goal
def goal_numbers(t, ctx, cf, r):
    tgt = round(cf["csat_rest"], 2)
    strong = ctx[ctx.agent_id.isin(FOCUS_AGENTS)]
    lever_b = float(-(strong.mix_adjusted_gap * strong.csat_response_count).sum() / cf["n"])
    return dict(target=tgt, current=cf["csat_all"], lever_a=cf["lift"], lever_b=lever_b, n=cf["n"])


def main():
    t, o, a = load_base()
    ct = csat_trend(t)
    ctx, r, coefs = agent_context(t, a)
    tp = training_priority(ctx, r)
    econ = cohort_economics(t, o)
    cf = csat_counterfactual(t)
    rc, hs = build_root_causes(t, o, a, ctx, econ, cf)
    bi, core = build_impact(t, econ, cf)
    goal = goal_numbers(t, ctx, cf, r)

    ANALYSIS_DIR.mkdir(exist_ok=True)
    ct.to_csv(ANALYSIS_DIR / "csat_trend.csv", index=False, float_format="%.4f")
    ctx.to_csv(ANALYSIS_DIR / "agent_context.csv", index=False, float_format="%.4f")
    tp.to_csv(ANALYSIS_DIR / "training_priority.csv", index=False, float_format="%.4f")
    rc.to_csv(ANALYSIS_DIR / "root_causes.csv", index=False, float_format="%.4f")
    bi.to_csv(ANALYSIS_DIR / "business_impact.csv", index=False, float_format="%.2f")
    return dict(t=t, ct=ct, ctx=ctx, tp=tp, econ=econ, cf=cf, rc=rc, hs=hs, bi=bi, core=core, goal=goal, coefs=coefs, r=r)


if __name__ == "__main__":
    res = main()
    print("phase 2 tables written to analysis/")
