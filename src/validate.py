"""Validation of raw inputs and pipeline outputs.  python -m src.validate
Most output checks recompute the quantity through a different code path (raw files + plain pandas/numpy)
and compare with what the pipeline wrote to outputs/. Writes outputs/validation_report.txt."""
import sys
import numpy as np
import pandas as pd
from .config import (OUT_DIR, RAW_DIR, EXPECTED_ROWS, REQUIRED_COLUMNS, ID_COLUMNS, SLA_TARGET_MIN,
                     REPLACEMENT_LOGISTICS_INR, TS_COLS, TS_FORMAT, IST_OFFSET, LOW_CSAT_MAX)
from .load import TABLES, raw_path, raw_record_count

RESULTS = []


def check(section, name, ok, detail=""):
    RESULTS.append((section, name, bool(ok), detail))


def close(a, b, tol=1e-6):
    return bool(np.isclose(a, b, rtol=tol, atol=tol, equal_nan=True))


def run_checks(raw_dir=RAW_DIR, out_dir=OUT_DIR):
    RESULTS.clear()
    raw = {n: pd.read_csv(raw_path(n, raw_dir)) for n in TABLES}
    t, ag, pr, od, cu = raw["tickets"], raw["agents"], raw["products"], raw["orders"], raw["customers"]
    tm = pd.read_csv(out_dir / "ticket_metrics.csv")
    am = pd.read_csv(out_dir / "agent_metrics.csv")
    mo = pd.read_csv(out_dir / "monthly_metrics.csv")
    ch = pd.read_csv(out_dir / "channel_metrics.csv")
    ov = pd.read_csv(out_dir / "overall_metrics.csv").set_index("metric")["value"]

    # 1. source row counts, required columns, duplicate ids
    for n in TABLES:
        rc = raw_record_count(raw_path(n, raw_dir))
        check("source", f"{n}: dataframe rows == raw CSV records", len(raw[n]) == rc, f"{len(raw[n])} vs {rc}")
        check("source", f"{n}: rows == documented expected count", len(raw[n]) == EXPECTED_ROWS[n], f"{len(raw[n])}")
        check("source", f"{n}: required columns present", all(c in raw[n].columns for c in REQUIRED_COLUMNS[n]))
        check("source", f"{n}: no duplicate {ID_COLUMNS[n]}", not raw[n][ID_COLUMNS[n]].duplicated().any(),
              f"{int(raw[n][ID_COLUMNS[n]].duplicated().sum())} dups")
    for c in ["ticket_id", "created_at", "first_response_at", "status", "channel", "customer_id", "agent_id",
              "product_sku", "source_system", "transfers"]:
        check("keys", f"tickets.{c} has no missing values", t[c].notna().all(), f"{int(t[c].isna().sum())} missing")

    # 2. join integrity
    check("joins", "tickets.customer_id in customers", t.customer_id.isin(cu.customer_id).all())
    check("joins", "tickets.agent_id in agents", t.agent_id.isin(ag.agent_id).all())
    check("joins", "tickets.product_sku in products", t.product_sku.isin(pr.sku).all())
    has = t.order_id.notna()
    check("joins", "tickets.order_id (when present) in orders", t.loc[has, "order_id"].isin(od.order_id).all())
    j = t[has].merge(od, on="order_id", suffixes=("", "_o"))
    check("joins", "ticket customer_id/sku agree with linked order", ((j.customer_id == j.customer_id_o) & (j.product_sku == j.sku)).all())
    check("joins", "orders.sku in products and orders.customer_id in customers", od.sku.isin(pr.sku).all() and od.customer_id.isin(cu.customer_id).all())
    check("joins", "agents.agent_id unique (so agent_id join is 1:1)", ag.agent_id.is_unique)
    dup_names = ag.name[ag.name.duplicated(keep=False)].nunique()
    check("joins", "shared-name agents exist and are distinct agent_ids", dup_names >= 1 and am.agent_id.is_unique, f"{dup_names} shared name(s)")
    check("joins", "ticket_metrics has one row per source ticket, none dropped",
          len(tm) == len(t) and set(tm.ticket_id) == set(t.ticket_id), f"{len(tm)} vs {len(t)}")

    # 3. missing CSAT handling
    check("csat", "csat_responded == raw csat_score notna", (tm.csat_responded == t.csat_score.notna().values).all())
    check("csat", "no zero CSAT scores; all responses in 1..5", tm.csat_score.dropna().between(1, 5).all())
    check("csat", "blank CSAT stays blank in output (not zero)", tm.loc[~tm.csat_responded, "csat_score"].isna().all())
    ind = t.csat_score.dropna().mean()
    check("csat", "overall CSAT == mean of non-blank raw scores", close(ov["csat_avg_respondents_only"], ind), f"{ind:.4f}")
    check("csat", "overall CSAT differs from blank-as-zero mean (guards against zero fill)",
          not close(ov["csat_avg_respondents_only"], t.csat_score.fillna(0).mean()))
    check("csat", "low_csat blank exactly where CSAT blank", (tm.low_csat.isna() == ~tm.csat_responded).all())
    check("csat", f"low_csat == (score <= {LOW_CSAT_MAX})", (tm.loc[tm.csat_responded, "low_csat"] == (tm.loc[tm.csat_responded, "csat_score"] <= LOW_CSAT_MAX).astype(int)).all())

    # 4. timestamp normalization (recomputed from raw strings)
    p = {c: pd.to_datetime(t[c], format=TS_FORMAT, errors="coerce") for c in TS_COLS}
    check("timestamps", "all non-blank timestamps parse", all((t[c].notna() == p[c].notna()).all() for c in TS_COLS))
    legacy = (t.source_system == "legacy_fd") & t.resolved_at.notna()
    raw_neg = ((p["resolved_at"] - p["created_at"]).dt.total_seconds() < 0)
    check("timestamps", "un-normalized legacy data has negative durations (proves shift is needed)", raw_neg[legacy].mean() > 0.5, f"{raw_neg[legacy].mean():.1%}")
    check("timestamps", "un-normalized helpdesk data has no negative durations (proves helpdesk is already IST)", not raw_neg[~legacy].any())
    exp_res = p["resolved_at"].where(~legacy, p["resolved_at"] + IST_OFFSET)
    got_res = pd.to_datetime(tm.resolved_at)
    check("timestamps", "output resolved_at == raw (+5:30 for legacy only)", ((exp_res == got_res) | (exp_res.isna() & got_res.isna())).all())
    check("timestamps", "shifted row count == legacy rows with resolved_at", int(tm.resolved_tz_shifted.sum()) == int(legacy.sum()), f"{int(legacy.sum())}")
    check("timestamps", "created_at / first_response_at unchanged", (pd.to_datetime(tm.created_at) == p["created_at"]).all() and (pd.to_datetime(tm.first_response_at) == p["first_response_at"]).all())
    check("timestamps", "no negative durations after normalization (created->resolved)", not ((got_res - p["created_at"]).dt.total_seconds() < 0).any())
    check("timestamps", "open/pending have no resolved_at; resolved/closed all have one",
          t[t.status.isin(["open", "pending"])].resolved_at.isna().all() and t[t.status.isin(["resolved", "closed"])].resolved_at.notna().all())
    check("timestamps", "open/pending tickets have no handle time; not silently dropped from ticket_metrics",
          tm[tm.is_open_pending].handle_time_minutes.isna().all() and int(tm.is_open_pending.sum()) == int(t.status.isin(["open", "pending"]).sum()))

    # 5. handle time / first response / negatives
    check("handle_time", "no negative handle_time_minutes", not (tm.handle_time_minutes < 0).any())
    check("handle_time", "no negative first_response_minutes", not (tm.first_response_minutes < 0).any())
    check("handle_time", "first response never after resolution", not tm.dq_response_after_resolution.any())
    ht = (exp_res - p["first_response_at"]).dt.total_seconds() / 60
    att = t.status.isin(["resolved", "closed"])
    check("handle_time", "handle_time == resolved(IST) - first_response, recomputed", np.allclose(tm.handle_time_minutes[att.values], ht[att], equal_nan=True))
    check("handle_time", "handle-time ticket count == attended count", int(tm.handle_time_minutes.notna().sum()) == int(att.sum()), f"{int(att.sum())}")
    check("handle_time", "no impossible handle time (> 30 days)", not tm.dq_impossible_handle.any())
    fr = (p["first_response_at"] - p["created_at"]).dt.total_seconds() / 60
    check("handle_time", "first_response_minutes recomputed", np.allclose(tm.first_response_minutes, fr))

    # 6. SLA (independent np.select path)
    tgt = np.select([t.channel == k for k in SLA_TARGET_MIN], list(SLA_TARGET_MIN.values()), default=-1)
    check("sla", "every channel has a policy target", (tgt > 0).all())
    breach = fr.values > tgt
    check("sla", "sla_breach flag == independent recomputation", (tm.sla_breach.astype(bool).values == breach).all())
    check("sla", "sla_target_minutes matches policy per channel", (tm.sla_target_minutes.values == tgt).all())
    check("sla", "breach is strictly greater than target (boundary tickets not breached)", not tm.loc[fr.values == tgt, "sla_breach"].astype(bool).any())
    check("sla", "overall breach count == independent count", int(ov["sla_breach_count"]) == int(breach.sum()), f"{int(breach.sum())}")
    check("sla", "channel breach counts sum to overall", int(ch.sla_breach_count.sum()) == int(breach.sum()))

    # 7. agent aggregation
    tier = ag.set_index("agent_id").tier
    check("agents", "one agent_metrics row per roster agent", len(am) == len(ag) and set(am.agent_id) == set(ag.agent_id))
    check("agents", "agent ticket_count sums to total tickets", int(am.ticket_count.sum()) == len(t))
    check("agents", "agent CSAT response counts sum to total responses", int(am.csat_response_count.sum()) == int(t.csat_score.notna().sum()))
    check("agents", "agent breach counts sum to overall", int(am.sla_breach_count.sum()) == int(breach.sum()))
    check("agents", "agent transfer_count sums to total transfers", int(am.transfer_count.sum()) == int(t.transfers.sum()))
    check("agents", "agent replacement counts sum to total", int(am.replacement_ticket_count.sum()) == int((t.replacement_issued == "Y").sum()))
    wavg = (am.avg_csat * am.csat_response_count).sum() / am.csat_response_count.sum()
    check("agents", "response-weighted agent CSAT == overall CSAT", close(wavg, ind, 1e-9))
    spot = t.groupby("agent_id").csat_score.mean()
    check("agents", "per-agent avg_csat == groupby mean on raw", np.allclose(am.set_index("agent_id").avg_csat, spot.reindex(am.agent_id).values, equal_nan=True))
    check("agents", "tier column matches roster for every agent", (am.set_index("agent_id").tier == tier.reindex(am.agent_id)).all())
    check("agents", "Tier 2 has no bottom-ten flag and ranks are within tier",
          not am[am.tier == 2].bottom_ten_raw_tier1.any() and am[am.tier == 1].csat_rank_within_tier.min() == 1 and am[am.tier == 2].csat_rank_within_tier.min() == 1)
    check("agents", "bottom-ten flag marks exactly 10 Tier 1 agents", int(am.bottom_ten_raw_tier1.sum()) == 10, f"{int(am.bottom_ten_raw_tier1.sum())}")
    for f in ["agent_metrics_tier1.csv", "agent_metrics_tier2.csv"]:
        s = pd.read_csv(out_dir / f)
        check("agents", f"{f} contains a single tier", s.tier.nunique() == 1)

    # 8. economics and roll-ups
    unit = pr.set_index("sku").unit_cost_inr
    repl = t[t.replacement_issued == "Y"]
    exp_cost = (repl.product_sku.map(unit) + REPLACEMENT_LOGISTICS_INR).sum()
    check("economics", "replacement cost == sum(unit cost + Rs 340)", close(ov["replacement_cost_policy_inr"], exp_cost), f"Rs {exp_cost:,.0f}")
    check("economics", "Rs 2,500 estimate not used (avg cost != 2500)", not close(ov["replacement_avg_cost_policy_inr"], 2500, 1e-3), f"avg Rs {exp_cost/len(repl):,.0f}")
    check("economics", "refund total == sum of raw refund_amount_inr", close(ov["refund_total_inr"], t.refund_amount_inr.sum()))
    check("economics", "monthly ticket volume sums to total", int(mo.ticket_volume.sum()) == len(t))
    check("economics", "monthly replacement cost sums to total", close(mo.replacement_cost_inr.sum(), exp_cost))
    check("economics", "monthly refunds sum to total", close(mo.refund_total_inr.sum(), t.refund_amount_inr.sum()))
    check("economics", "channel volume sums to total", int(ch.ticket_volume.sum()) == len(t))
    lr = t.merge(pr, left_on="product_sku", right_on="sku")
    lr = lr[lr.refund_amount_inr.notna()]
    ratio = lr.assign(r=lr.refund_amount_inr / lr.retail_price_inr).groupby("source_system").r.mean()
    check("economics", "refund/retail ratio similar in legacy and helpdesk (no unit mismatch)", abs(ratio["legacy_fd"] - ratio["helpdesk"]) < 0.05, f"{ratio.round(3).to_dict()}")
    return RESULTS


def main():
    res = run_checks()
    fails = [r for r in res if not r[2]]
    lines = ["VALIDATION REPORT", "=" * 60]
    section = None
    for s, n, ok, d in res:
        if s != section:
            lines += ["", f"[{s}]"]; section = s
        lines.append(f"  {'PASS' if ok else 'FAIL'}  {n}" + (f"  ({d})" if d else ""))
    lines += ["", "=" * 60, f"Checks performed: {len(res)}", f"Passed: {len(res) - len(fails)}", f"Failed: {len(fails)}"]
    text = "\n".join(lines)
    (OUT_DIR / "validation_report.txt").write_text(text, encoding="utf-8")
    print(text)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
