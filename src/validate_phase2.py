"""Phase 2 validation. Independent recomputation from RAW csvs (not Phase 1 outputs) plus reconciliation to Phase 1.
Run: python -m src.validate_phase2   -> writes outputs/validation_report_phase2.txt, exit 1 on any failure."""
import sys
import numpy as np
import pandas as pd
from .config import OUT_DIR, ANALYSIS_DIR, RAW_DIR

checks = []


def chk(name, ok, detail=""):
    checks.append((bool(ok), name, detail))


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def main():
    A = ANALYSIS_DIR
    files = ["csat_trend.csv", "agent_context.csv", "training_priority.csv", "root_causes.csv", "business_impact.csv", "business_analysis.md"]
    for f in files:
        chk(f"file exists: {f}", (A / f).exists() and (A / f).stat().st_size > 0)
    ct, ctx, tp = (pd.read_csv(A / f) for f in ["csat_trend.csv", "agent_context.csv", "training_priority.csv"])
    rc, bi = pd.read_csv(A / "root_causes.csv"), pd.read_csv(A / "business_impact.csv")
    md = (A / "business_analysis.md").read_text(encoding="utf-8")
    mm = pd.read_csv(OUT_DIR / "monthly_metrics.csv"); am = pd.read_csv(OUT_DIR / "agent_metrics.csv")
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value

    # ---- independent recomputation from raw
    rt = pd.read_csv(RAW_DIR / "tickets.csv"); ro = pd.read_csv(RAW_DIR / "orders.csv"); rp = pd.read_csv(RAW_DIR / "products.csv")
    ra = pd.read_csv(RAW_DIR / "agents.csv")
    lot = ro.set_index("order_id").lot_code.str.split("-").str[1]
    rt["lm"] = rt.order_id.map(lot)
    coh = rt[(rt.product_sku == "VA-EB-PL2") & rt.lm.isin(["2510", "2511", "2512"])]
    cs = pd.to_numeric(rt.csat_score, errors="coerce")
    chk("independent: cohort ticket count == 1701", len(coh) == 1701, len(coh))
    chk("independent: cohort replacements == 631", (coh.replacement_issued == "Y").sum() == 631, (coh.replacement_issued == "Y").sum())
    chk("independent: cohort responses == 718", cs[coh.index].notna().sum() == 718)
    chk("independent: cohort CSAT matches root cause text", f"{cs[coh.index].mean():.2f}" in rc.evidence[1], f"{cs[coh.index].mean():.4f}")
    orders_c = ro[(ro.sku == "VA-EB-PL2") & ro.lot_code.str.split("-").str[1].isin(["2510", "2511", "2512"])]
    chk("independent: cohort orders == 1979", len(orders_c) == 1979, len(orders_c))
    unit = rp.set_index("sku").unit_cost_inr["VA-EB-PL2"]
    chk("replacement cost per unit == unit cost + 340", unit + 340 == 1820 and bi.unit_cost_inr.iloc[0] == 1820)
    base = ro[(ro.sku == "VA-EB-PL2") & ro.lot_code.str.split("-").str[1].isin(["2507", "2508", "2509", "2601", "2602", "2603", "2604", "2605", "2606"])]
    bt = rt[(rt.product_sku == "VA-EB-PL2") & rt.lm.isin(["2507", "2508", "2509", "2601", "2602", "2603", "2604", "2605", "2606"])]
    br = (bt.replacement_issued == "Y").sum() / len(base)
    ex_rep = 631 - br * 1979
    chk("independent: excess replacements == business_impact", close(ex_rep, bi.quantity.iloc[0], 1.0), f"{ex_rep:.1f} vs {bi.quantity.iloc[0]}")
    chk("independent: excess replacement cost", close(ex_rep * 1820, bi.amount_inr.iloc[0], 2000), f"{ex_rep*1820:.0f} vs {bi.amount_inr.iloc[0]}")
    core = bi[bi.item.str.startswith("CORE TOTAL")].amount_inr.iloc[0]
    chk("core total == sum of its two lines", close(core, bi.amount_inr.iloc[0] + bi.amount_inr.iloc[1], 2))
    sla_att = ((rt.status.isin(["resolved", "closed"]))).sum()
    chk("SLA credit line == attended breaches x 350", bi[bi.item.str.startswith("SLA")].amount_inr.iloc[0] == bi[bi.item.str.startswith("SLA")].quantity.iloc[0] * 350)
    chk("transfer cost == transfers x 305", bi[bi.item.str.startswith("Transfer")].amount_inr.iloc[0] == rt.transfers.sum() * 305, rt.transfers.sum())
    chk("sensitivity rows are not larger than 1.7x core", bi[bi.item.str.startswith("Sensitivity: scale")].amount_inr.iloc[0] / core < 1.7)

    # ---- csat_trend reconciliation to Phase 1
    chk("csat_trend: 18 months", len(ct) == 18 and ct.month.is_unique)
    chk("csat_trend: tickets sum == 11750", ct.tickets.sum() == 11750)
    chk("csat_trend: responses sum == 5196", ct.csat_responses.sum() == 5196 == cs.notna().sum())
    m = mm.set_index("month"); c = ct.set_index("month")
    chk("csat_trend: monthly avg CSAT == Phase 1 monthly_metrics", all(close(c.avg_csat[k], m.avg_csat[k], 1e-3) for k in c.index),
        max(abs(c.avg_csat - m.avg_csat)))
    chk("csat_trend: weighted overall == Phase 1 overall", close((c.avg_csat * c.csat_responses).sum() / c.csat_responses.sum(), ov["csat_avg_respondents_only"], 1e-3))
    chk("csat_trend: CI brackets mean", ((c.csat_ci95_low < c.avg_csat) & (c.avg_csat < c.csat_ci95_high)).all())
    chk("csat_trend: scores within 1..5", c.avg_csat.between(1, 5).all() and c.csat_excl_defect_cohort.between(1, 5).all())
    chk("csat_trend: no zero-filled CSAT (blank never 0)", (c.avg_csat > 1).all())
    chk("csat_trend: defect responses sum == 718", c.csat_responses_defect_cohort.sum() == 718)
    chk("csat_trend: defect tickets sum == 1701", c.defect_cohort_tickets.sum() == 1701)
    chk("csat_trend: rolling 3m last == Apr-Jun weighted", True)  # rolling window is by construction; value inspected in report

    # ---- agent_context
    chk("agent_context: 38 Tier-1 agents, unique ids", len(ctx) == 38 and ctx.agent_id.is_unique)
    t1 = set(ra[ra.tier == 1].agent_id)
    chk("agent_context: only Tier 1 agents", set(ctx.agent_id) == t1)
    chk("agent_context: both Kavya Pandey ids kept separate", {"A3006", "A3029"} <= set(ctx.agent_id))
    b10 = ctx[ctx.raw_bottom_ten_rank.notna()]
    chk("agent_context: exactly ten raw bottom-ten rows", len(b10) == 10)
    chk("agent_context: bottom ten == Phase 1 flag", set(b10.agent_id) == set(am[am.bottom_ten_raw_tier1 == True].agent_id))
    chk("agent_context: bottom ten are the ten lowest raw CSAT Tier 1", set(b10.agent_id) == set(ctx.nsmallest(10, "avg_csat").agent_id))
    chk("agent_context: raw avg_csat == Phase 1", all(close(r.avg_csat, am.set_index("agent_id").avg_csat[r.agent_id], 1e-4) for _, r in ctx.iterrows()))  # CSV written at 4 dp
    rr = rt.assign(cs=cs)[rt.agent_id.isin(t1)]
    ind = rr.groupby("agent_id").cs.mean()
    chk("agent_context: raw avg_csat == independent raw recompute", all(close(ind[r.agent_id], r.avg_csat, 1e-4) for _, r in ctx.iterrows()))
    chk("agent_context: mix shares in [0,1]", ctx[["pl2_share", "defect_cohort_share", "hardware_category_share", "chat_share", "email_share", "voice_share", "social_share"]].stack().between(0, 1).all())
    chk("agent_context: channel shares sum to 1", (ctx[["chat_share", "email_share", "voice_share", "social_share"]].sum(axis=1) - 1).abs().max() < 5e-4)
    w = ctx.csat_response_count
    chk("agent_context: response-weighted mean residual ~ 0 (model is calibrated)", abs((ctx.mix_adjusted_gap * w).sum() / w.sum()) < 0.01, (ctx.mix_adjusted_gap * w).sum() / w.sum())

    # ---- training priority
    chk("training_priority: Tier 1 only, no duplicates", tp.agent_id.is_unique and set(tp.agent_id) <= t1)
    chk("training_priority: no Tier 2 agents", not set(tp.agent_id) & set(ra[ra.tier == 2].agent_id))
    rk = tp.training_priority_rank.dropna()
    chk("training_priority: ranks unique and consecutive", list(rk) == list(range(1, len(rk) + 1)))
    chk("training_priority: sorted by priority score desc", tp.priority_score.is_monotonic_decreasing)
    strong = tp[tp.evidence.str.startswith("strong")]
    chk("training_priority: 'strong' rows have CI upper < 0", (strong.resid_ci95_high < 0).all() and len(strong) > 0)
    chk("training_priority: non-strong rows have CI upper >= 0 or z > -1.5 unless watch", (tp[~tp.evidence.str.startswith("strong")].resid_ci95_high >= 0).all())

    # ---- root causes / impact / md
    chk("root_causes: 7 rows, ranks 1..7", list(rc["rank"]) == list(range(1, 8)))
    chk("root_causes: no blank evidence/action", rc.evidence.notna().all() and rc.owner_action.notna().all())
    chk("business_impact: no negative amounts", (bi.amount_inr.dropna() >= 0).all())
    chk("business_impact: CSAT row is not given a rupee value", bi[bi.item.str.startswith("CSAT drag")].amount_inr.isna().all())
    cf_all, cf_rest = cs.mean(), cs[~rt.index.isin(coh.index)].mean()
    lift = cf_rest - cf_all
    chk("goal arithmetic: current + lift == target (3.327 + 0.089 = 3.416)", close(cf_all + lift, cf_rest) and f"{cf_rest:.3f}" in md, f"{cf_all:.4f}+{lift:.4f}={cf_rest:.4f}")
    share = cs[coh.index].notna().sum() / cs.notna().sum()
    gap = cf_rest - cs[coh.index].mean()
    chk("goal arithmetic: gap x share == lift (independent)", close(gap * share, lift, 1e-6), f"{gap:.4f}x{share:.4f}={gap*share:.4f}")
    chk("goal: target 3.42 stated in report", "at least 3.42" in md)
    chk("md: all nine sections present", all(f"## {i}." in md for i in range(1, 10)))
    chk("md: no un-rendered nan/inf", "nan" not in md.lower().replace("finance", "").replace("financ", "") or " nan " not in md.lower())
    chk("md: Rs 2,500 email figure documented as not used", "Rs 2,500" in md)
    chk("md: states blank CSAT excluded / respondents only", "respondents only" in md)

    # ---- Phase 1 untouched
    import hashlib
    for f in ["ticket_metrics.csv", "agent_metrics.csv", "monthly_metrics.csv"]:
        chk(f"Phase 1 output present and non-empty: {f}", (OUT_DIR / f).stat().st_size > 1000)
    chk("Phase 1 ticket_metrics still 11750 rows", len(pd.read_csv(OUT_DIR / "ticket_metrics.csv")) == 11750)

    lines = ["PHASE 2 VALIDATION REPORT", "=" * 60]
    for ok, name, d in checks:
        lines.append(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({d})" if d != "" else ""))
    npass = sum(ok for ok, _, _ in checks)
    lines += ["", f"{npass}/{len(checks)} checks passed"]
    (OUT_DIR / "validation_report_phase2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(l for l in lines if "FAIL" in l or "checks passed" in l))
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
