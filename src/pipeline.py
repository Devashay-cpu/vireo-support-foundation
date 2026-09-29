"""Run the full foundation pipeline:  python -m src.pipeline
Reads data/raw/*.csv (read-only) and writes outputs/*.csv plus analysis/foundation_summary.md."""
import pandas as pd
from .config import OUT_DIR, ANALYSIS_DIR, RAW_DIR
from .load import load_all
from . import metrics as M
from .summary import write_summary

TS_OUT = ["created_at", "first_response_at", "resolved_at", "resolved_at_raw"]


def run(raw_dir=RAW_DIR, out_dir=OUT_DIR, analysis_dir=ANALYSIS_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    d = load_all(raw_dir)
    tm = M.build_ticket_metrics(d["tickets"], d["agents"], d["products"])
    am = M.build_agent_metrics(tm, d["agents"])
    mo = M.build_monthly_metrics(tm)
    ch = M.build_channel_metrics(tm)
    ov = M.build_overall_metrics(tm)
    rs = M.build_replacement_by_sku(tm, d["products"])
    rr = M.build_refund_by_reason(tm)

    tm_out = tm.copy()
    for c in TS_OUT:
        tm_out[c] = tm_out[c].dt.strftime("%Y-%m-%d %H:%M")   # IST, timezone-naive
    tm_out.to_csv(out_dir / "ticket_metrics.csv", index=False)
    am.to_csv(out_dir / "agent_metrics.csv", index=False)
    am[am.tier == 1].to_csv(out_dir / "agent_metrics_tier1.csv", index=False)
    am[am.tier == 2].to_csv(out_dir / "agent_metrics_tier2.csv", index=False)
    mo.to_csv(out_dir / "monthly_metrics.csv", index=False)
    ch.to_csv(out_dir / "channel_metrics.csv", index=False)
    ov.to_csv(out_dir / "overall_metrics.csv", index=False)
    rs.to_csv(out_dir / "replacement_by_sku.csv", index=False)
    rr.to_csv(out_dir / "refund_by_reason.csv", index=False)
    write_summary(analysis_dir / "foundation_summary.md", d, tm, am, mo, ch, ov, rs)
    return d, tm, am, mo, ch, ov


if __name__ == "__main__":
    _, tm, am, *_ = run()
    print(f"ticket_metrics: {len(tm)} rows | agent_metrics: {len(am)} rows | outputs -> {OUT_DIR}")
