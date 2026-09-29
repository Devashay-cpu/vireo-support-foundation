"""Task 4 validation: dashboard reconciles to verified Phase 1/2 outputs. Run: python -m src.validate_task4"""
import json
import re
import sys

import pandas as pd

from .config import ANALYSIS_DIR, OUT_DIR, ROOT

checks = []
chk = lambda name, ok, d="": checks.append((bool(ok), name, d))


def main():
    D = ROOT / "dashboard"
    h_path, j_path = D / "index.html", D / "dashboard_data.json"
    chk("dashboard/index.html exists, non-empty", h_path.exists() and h_path.stat().st_size > 2000)
    chk("dashboard/dashboard_data.json exists", j_path.exists())
    html, j = h_path.read_text(encoding="utf-8"), json.loads(j_path.read_text())
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value
    bi = pd.read_csv(ANALYSIS_DIR / "business_impact.csv")
    ctx = pd.read_csv(ANALYSIS_DIR / "agent_context.csv")
    tp = pd.read_csv(ANALYSIS_DIR / "training_priority.csv")
    ct = pd.read_csv(ANALYSIS_DIR / "csat_trend.csv")
    core = bi[bi.item.str.startswith("CORE TOTAL")].amount_inr.iloc[0]

    chk("html: no 'nan'/'None'/'inf' text", not re.search(r"\b(nan|None|inf)\b", re.sub(r"<style.*?</style>", "", html, flags=re.S), re.I))
    chk("html: self-contained (no external URLs, no <script>, no <link>)", not re.search(r"https?://|<script|<link", html))
    chk("html: size under 25 KB", h_path.stat().st_size < 25_000, h_path.stat().st_size)
    chk("html: viewport meta + dark-mode css", "viewport" in html and "prefers-color-scheme" in html)
    chk("json: tickets == Phase 1 (11750)", j["tickets"] == 11750 == int(ov["tickets_total"]))
    chk("json: CSAT == Phase 1 overall", abs(j["csat"] - ov["csat_avg_respondents_only"]) < 1e-3)
    chk("json: core cost == business_impact core total", j["core_cost_inr"] == round(core), j["core_cost_inr"])
    chk("html: shows core cost as exact rupees", f"{int(round(core)):,}" in html)
    chk("json: goal target 3.42 and arithmetic current+lift=target", j["goal"]["target"] == 3.42 and abs(j["goal"]["current"] + 0.089 - 3.416) < 2e-3, j["goal"])
    chk("json: bottom ten == agent_context (10 ids)", len(j["bottom_ten"]) == 10 and set(j["bottom_ten"]) == set(ctx[ctx.raw_bottom_ten_rank.notna()].agent_id))
    chk("json: train-now == {A3004,A3005,A3006,A3007}", set(j["train_now"]) == {"A3004", "A3005", "A3006", "A3007"} == set(tp[tp.evidence.str.startswith("strong")].agent_id))
    chk("html: every bottom-ten agent id appears", all(a in html for a in j["bottom_ten"]))
    chk("html: only 4 rows labelled Coach", html.count(">Coach<") == 4, html.count(">Coach<"))
    chk("html: six 'Queue mix' rows", html.count("Queue mix, no signal") == 6)
    chk("html: 18 monthly CSAT points in trend path", len(ct) == 18 == j["months"])
    chk("html: both lines + 12 lot bars + defect bars", html.count('class="l1"') == 1 and html.count('class="l2"') == 1 and html.count('class="bar"') >= 18 + 3)
    chk("html: limitations section present", "Limitations" in html and "Association, not proven cause" in html)
    chk("html: Rs 2,500 email figure not used", "2,500" not in html)

    # ---- handle time (client ask: "CSAT and handle time per agent and flag the bottom ten") ----
    am = pd.read_csv(OUT_DIR / "agent_metrics.csv").set_index("agent_id")
    tm = pd.read_csv(OUT_DIR / "ticket_metrics.csv")
    f = lambda x: f"{x:,.0f}"

    def row_of(aid, h2):
        sec = html.split(h2)[1].split("<h2>")[0]
        m = re.search(rf"<tr[^>]*>(?:(?!</tr>).)*{aid} (?:(?!</tr>).)*</tr>", sec, re.S)
        return re.sub(r"<[^>]+>", "|", m.group(0)) if m else ""

    S3, S2 = "3. CSAT and handle time for all 44 agents", "2. Raw Tier-1 bottom ten"
    chk("handle: independent recompute per agent (median, mean, n) from ticket_metrics == agent_metrics",
        all(abs(g.handle_time_minutes.median() - am.loc[a, "median_handle_time"]) < 1e-6 and abs(g.handle_time_minutes.mean() - am.loc[a, "avg_handle_time"]) < 1e-6
            and g.handle_time_minutes.notna().sum() == am.loc[a, "handle_time_count"] for a, g in tm.groupby("agent_id")))
    chk("handle: all-agents section present with Median + Mean handle columns", S3 in html and "Median handle (min)" in html and "Mean handle (min)" in html)
    chk("handle: all 44 agents listed in the all-agents table", len(am) == 44 and all(f"{a} " in html.split(S3)[1].split("<h2>")[0] for a in am.index))
    chk("handle: every agent's median AND mean handle time in the all-agents table equals agent_metrics.csv",
        all(f"|{f(am.loc[a,'median_handle_time'])}|" in row_of(a, S3) and f"|{f(am.loc[a,'avg_handle_time'])}|" in row_of(a, S3) for a in am.index))
    chk("handle: every bottom-ten row shows median AND mean handle time equal to agent_metrics.csv",
        all(f"|{f(am.loc[a,'median_handle_time'])}|" in row_of(a, S2) and f"|{f(am.loc[a,'avg_handle_time'])}|" in row_of(a, S2) for a in j["bottom_ten"]))
    chk("handle: exactly 10 flagged rows in all-agents table, same ten as json/agent_context", html.count("BOTTOM 10 (raw CSAT)") == 10 and
        all("BOTTOM 10" in row_of(a, S3) for a in j["bottom_ten"]))
    chk("handle: Tier 2 agents listed but not flagged", all("BOTTOM 10" not in row_of(a, S3) for a in am[am.tier == 2].index) and (am.tier == 2).sum() == 6)
    chk("handle: json records 44 agents with handle time", j.get("handle_time_agents") == 44 == j.get("agents_in_table"))
    chk("handle: interpretation note present (median first, queue-driven)", "Reading handle time" in html and "Read the median first" in html)
    for ok, n, d in checks:
        print(("PASS " if ok else "FAIL ") + n + (f" ({d})" if d != "" else ""))
    (OUT_DIR / "validation_report_task4.txt").write_text(
        "\n".join(("PASS  " if ok else "FAIL  ") + n for ok, n, _ in checks) + f"\n\n{sum(o for o,_,_ in checks)}/{len(checks)} checks passed\n")
    print(f"{sum(o for o,_,_ in checks)}/{len(checks)} checks passed")
    return 0 if all(o for o, _, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
