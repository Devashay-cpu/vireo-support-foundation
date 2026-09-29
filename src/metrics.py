"""Ticket-, agent-, monthly- and channel-level metrics. All definitions follow support-policy.pdf v3.2."""
import numpy as np
import pandas as pd
from .config import (ATTENDED_STATUSES, OPEN_STATUSES, SLA_TARGET_MIN, REPLACEMENT_LOGISTICS_INR,
                     LOW_CSAT_MAX, MAX_PLAUSIBLE_HANDLE_MIN)
from .timestamps import normalize_timestamps

TICKET_COLUMNS = [
    "ticket_id", "agent_id", "channel", "category", "priority", "assigned_team", "status", "source_system",
    "created_at", "first_response_at", "resolved_at", "first_response_minutes", "handle_time_minutes",
    "csat_score", "csat_responded", "low_csat", "sla_target_minutes", "sla_breach", "transfers",
    "replacement_issued", "refund_amount_inr", "order_id", "product_sku",
    # supporting columns (kept so nothing is silently dropped or hidden)
    "month", "agent_tier", "refund_reason_code", "order_linked", "unit_cost_inr", "replacement_cost_inr",
    "resolved_at_raw", "resolved_tz_shifted", "is_attended", "is_open_pending",
    "dq_ts_unparseable", "dq_missing_first_response", "dq_missing_resolved_attended",
    "dq_negative_first_response", "dq_negative_handle", "dq_impossible_handle", "dq_response_after_resolution",
    "dq_refund_and_replacement",
]


def build_ticket_metrics(tickets: pd.DataFrame, agents: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """One row per ticket (no rows dropped). Problem rows are flagged in dq_* columns, not removed."""
    t = normalize_timestamps(tickets)

    # --- first response (policy s3: from creation to first human reply) ---
    fr = (t["first_response_at"] - t["created_at"]).dt.total_seconds() / 60
    t["dq_missing_first_response"] = fr.isna()
    t["dq_negative_first_response"] = fr < 0
    t["first_response_minutes"] = fr.where(fr >= 0)

    # --- handle time (policy s10: first human response -> resolution), attended tickets only ---
    t["is_attended"] = t["status"].isin(ATTENDED_STATUSES)
    t["is_open_pending"] = t["status"].isin(OPEN_STATUSES)
    ht = (t["resolved_at"] - t["first_response_at"]).dt.total_seconds() / 60
    t["dq_missing_resolved_attended"] = t["is_attended"] & t["resolved_at"].isna()
    t["dq_negative_handle"] = ht < 0
    t["dq_impossible_handle"] = ht > MAX_PLAUSIBLE_HANDLE_MIN
    t["dq_response_after_resolution"] = t["first_response_at"] > t["resolved_at"]
    t["handle_time_minutes"] = ht.where(t["is_attended"] & (ht >= 0) & (ht <= MAX_PLAUSIBLE_HANDLE_MIN))
    t["dq_ts_unparseable"] = t["ts_unparseable"]

    # --- CSAT: blank = no response, never zero (policy s8) ---
    t["csat_responded"] = t["csat_score"].notna()
    t["low_csat"] = pd.array(np.where(t["csat_responded"], (t["csat_score"] <= LOW_CSAT_MAX).astype(int), np.nan),
                             dtype="Int8")

    # --- SLA (policy s3): breach = first response strictly later than target ---
    t["sla_target_minutes"] = t["channel"].map(SLA_TARGET_MIN)
    t["sla_breach"] = (t["first_response_minutes"] > t["sla_target_minutes"]).where(t["first_response_minutes"].notna())

    # --- joins on ids only ---
    ag = agents[["agent_id", "tier"]].rename(columns={"tier": "agent_tier"})
    t = t.merge(ag, on="agent_id", how="left", validate="m:1")
    pr = products[["sku", "unit_cost_inr"]].rename(columns={"sku": "product_sku"})
    t = t.merge(pr, on="product_sku", how="left", validate="m:1")

    # --- replacement cost (policy s5): unit cost + Rs 340; independent of order link ---
    is_repl = t["replacement_issued"].eq("Y")
    t["replacement_cost_inr"] = np.where(is_repl, t["unit_cost_inr"] + REPLACEMENT_LOGISTICS_INR, 0.0)
    t["dq_refund_and_replacement"] = t["refund_amount_inr"].notna() & is_repl   # policy s5 exception

    t["order_linked"] = t["order_id"].notna()
    t["month"] = t["created_at"].dt.to_period("M").astype(str)
    return t[TICKET_COLUMNS].copy()


def _agg_agent(g: pd.DataFrame) -> pd.Series:
    resp = g.loc[g["csat_responded"], "csat_score"]
    ht = g["handle_time_minutes"].dropna()
    return pd.Series({
        "ticket_count": len(g),
        "attended_count": int(g["is_attended"].sum()),
        "csat_response_count": int(g["csat_responded"].sum()),
        "avg_csat": resp.mean() if len(resp) else np.nan,
        "median_csat": resp.median() if len(resp) else np.nan,
        "low_csat_rate": (resp <= LOW_CSAT_MAX).mean() if len(resp) else np.nan,
        "handle_time_count": len(ht),
        "avg_handle_time": ht.mean() if len(ht) else np.nan,
        "median_handle_time": ht.median() if len(ht) else np.nan,
        "sla_breach_count": int(g["sla_breach"].fillna(False).astype(bool).sum()),
        "sla_breach_rate": g["sla_breach"].dropna().astype(bool).mean(),
        "transfer_count": int(g["transfers"].sum()),
        "replacement_ticket_count": int(g["replacement_issued"].eq("Y").sum()),
    })


def build_agent_metrics(ticket_metrics: pd.DataFrame, agents: pd.DataFrame) -> pd.DataFrame:
    """One row per agent_id. Tiers are kept apart: ranks are computed WITHIN tier only, and the
    'raw bottom ten' flag exists for Tier 1 only. No cross-tier ranking of any metric is produced."""
    stats = (ticket_metrics.groupby("agent_id")
             .apply(_agg_agent, include_groups=False).reset_index())
    a = agents.rename(columns={"name": "agent_name", "team": "agent_team"})[
        ["agent_id", "agent_name", "tier", "site", "shift", "agent_team"]]
    out = a.merge(stats, on="agent_id", how="left", validate="1:1")
    out["csat_rank_within_tier"] = out.groupby("tier")["avg_csat"].rank(method="min", ascending=True)  # 1 = lowest
    out["tier_agent_count"] = out.groupby("tier")["agent_id"].transform("size")
    out["bottom_ten_raw_tier1"] = (out["tier"] == 1) & (out["csat_rank_within_tier"] <= 10)
    return out.sort_values(["tier", "csat_rank_within_tier", "agent_id"]).reset_index(drop=True)


def _period_agg(g: pd.DataFrame) -> pd.Series:
    resp = g.loc[g["csat_responded"], "csat_score"]
    br = g["sla_breach"].dropna().astype(bool)
    return pd.Series({
        "ticket_volume": len(g),
        "attended_count": int(g["is_attended"].sum()),
        "csat_response_count": len(resp),
        "avg_csat": resp.mean() if len(resp) else np.nan,
        "avg_handle_time_min": g["handle_time_minutes"].mean(),
        "median_handle_time_min": g["handle_time_minutes"].median(),
        "avg_first_response_min": g["first_response_minutes"].mean(),
        "sla_breach_count": int(br.sum()),
        "sla_breach_rate": br.mean() if len(br) else np.nan,
        "replacement_count": int(g["replacement_issued"].eq("Y").sum()),
        "replacement_cost_inr": g["replacement_cost_inr"].sum(),
        "refund_ticket_count": int(g["refund_amount_inr"].notna().sum()),
        "refund_total_inr": g["refund_amount_inr"].sum(),
    })


def build_monthly_metrics(tm: pd.DataFrame) -> pd.DataFrame:
    """Grouped by ticket creation month (IST)."""
    return tm.groupby("month").apply(_period_agg, include_groups=False).reset_index()


def build_channel_metrics(tm: pd.DataFrame) -> pd.DataFrame:
    out = tm.groupby("channel").apply(_period_agg, include_groups=False).reset_index()
    out.insert(1, "sla_target_minutes", out["channel"].map(SLA_TARGET_MIN))
    return out


def build_overall_metrics(tm: pd.DataFrame) -> pd.DataFrame:
    resp = tm.loc[tm["csat_responded"], "csat_score"]
    br = tm["sla_breach"].dropna().astype(bool)
    repl = tm["replacement_issued"].eq("Y")
    rows = [
        ("tickets_total", len(tm)),
        ("tickets_attended_resolved_or_closed", int(tm["is_attended"].sum())),
        ("tickets_open_or_pending", int(tm["is_open_pending"].sum())),
        ("csat_response_count", len(resp)),
        ("csat_response_rate", tm["csat_responded"].mean()),
        ("csat_avg_respondents_only", resp.mean()),
        ("csat_median_respondents_only", resp.median()),
        ("low_csat_rate_respondents", (resp <= LOW_CSAT_MAX).mean()),
        ("handle_time_ticket_count", int(tm["handle_time_minutes"].notna().sum())),
        ("avg_handle_time_min", tm["handle_time_minutes"].mean()),
        ("median_handle_time_min", tm["handle_time_minutes"].median()),
        ("avg_first_response_min", tm["first_response_minutes"].mean()),
        ("sla_breach_count", int(br.sum())),
        ("sla_breach_rate", br.mean()),
        ("replacement_count", int(repl.sum())),
        ("replacement_cost_policy_inr", tm["replacement_cost_inr"].sum()),
        ("replacement_avg_cost_policy_inr", tm.loc[repl, "replacement_cost_inr"].mean()),
        ("refund_ticket_count", int(tm["refund_amount_inr"].notna().sum())),
        ("refund_total_inr", tm["refund_amount_inr"].sum()),
        ("tickets_refund_and_replacement_both", int(tm["dq_refund_and_replacement"].sum())),
        ("tickets_without_order_link", int((~tm["order_linked"]).sum())),
        ("legacy_resolved_at_shifted_utc_to_ist", int(tm["resolved_tz_shifted"].sum())),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def build_replacement_by_sku(tm: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    r = tm[tm["replacement_issued"].eq("Y")]
    g = r.groupby("product_sku").agg(replacement_count=("ticket_id", "size"),
                                     replacement_cost_inr=("replacement_cost_inr", "sum")).reset_index()
    tk = tm.groupby("product_sku").size().rename("ticket_count").reset_index()
    out = products[["sku", "product_name", "family", "unit_cost_inr"]].rename(columns={"sku": "product_sku"}) \
        .merge(tk, on="product_sku", how="left").merge(g, on="product_sku", how="left").fillna(
        {"replacement_count": 0, "replacement_cost_inr": 0})
    out["replacement_per_100_tickets"] = 100 * out["replacement_count"] / out["ticket_count"]
    return out.sort_values("replacement_count", ascending=False)


def build_refund_by_reason(tm: pd.DataFrame) -> pd.DataFrame:
    r = tm[tm["refund_amount_inr"].notna()]
    return (r.groupby("refund_reason_code").agg(refund_ticket_count=("ticket_id", "size"),
                                                refund_total_inr=("refund_amount_inr", "sum"))
            .reset_index().sort_values("refund_total_inr", ascending=False))
