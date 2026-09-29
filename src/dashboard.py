"""Task 4 core deliverable: a self-contained, static support dashboard (no JS, no network, no LLM calls).

Reads ONLY existing verified outputs (Phase 1 outputs/, Phase 2 analysis/*.csv) and reuses src.phase2 helpers for the
lot table and goal arithmetic. Writes dashboard/index.html and dashboard/dashboard_data.json.
Run: python -m src.dashboard
"""
import json
from html import escape

import pandas as pd

from . import phase2 as p2
from .config import OUT_DIR, ANALYSIS_DIR, ROOT

DASH = ROOT / "dashboard"
TRAIN_NOW_PREFIX = "strong"


def gather():
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value
    ct = pd.read_csv(ANALYSIS_DIR / "csat_trend.csv")
    ctx = pd.read_csv(ANALYSIS_DIR / "agent_context.csv")
    tp = pd.read_csv(ANALYSIS_DIR / "training_priority.csv")
    bi = pd.read_csv(ANALYSIS_DIR / "business_impact.csv")
    t, o, _ = p2.load_base()
    econ, cf = p2.cohort_economics(t, o), p2.csat_counterfactual(t)
    lots = econ["lots"].loc[list(p2.BASELINE_LOT_MONTHS[:3]) + list(p2.DEFECT_LOT_MONTHS) + list(p2.BASELINE_LOT_MONTHS[3:])]
    core = float(bi[bi.item.str.startswith("CORE TOTAL")].amount_inr.iloc[0])
    b10 = ctx[ctx.raw_bottom_ten_rank.notna()].sort_values("raw_bottom_ten_rank")
    train = tp[tp.evidence.str.startswith(TRAIN_NOW_PREFIX)]
    agents = agent_frame()
    b10 = b10.merge(agents[["agent_id", "handle_n", "median_ht", "mean_ht", "team_median_ht"]], on="agent_id", how="left")
    return dict(ov=ov, ct=ct, b10=b10, train=train, lots=lots, econ=econ, cf=cf, core=core, agents=agents,
                target=round(cf["csat_rest"], 2), current=cf["csat_all"])


def agent_frame():
    """One row per agent (all 44) from the verified Phase 1 agent_metrics.csv: CSAT and handle time side by side.
    team_median_ht = median of the agents' median handle times in the same team (a peer benchmark; no new ticket-level maths)."""
    am = pd.read_csv(OUT_DIR / "agent_metrics.csv")
    a = pd.DataFrame(dict(agent_id=am.agent_id, agent_name=am.agent_name, tier=am.tier, agent_team=am.agent_team,
                          tickets=am.ticket_count.astype(int), csat_n=am.csat_response_count.astype(int), avg_csat=am.avg_csat,
                          csat_rank=am.csat_rank_within_tier.astype(int), handle_n=am.handle_time_count.astype(int),
                          median_ht=am.median_handle_time, mean_ht=am.avg_handle_time, bottom_ten=am.bottom_ten_raw_tier1.astype(bool)))
    a["team_median_ht"] = a.groupby("agent_team").median_ht.transform("median")
    return a.sort_values(["tier", "csat_rank"]).reset_index(drop=True)


def line_chart(ct):
    W, H, L, B, T = 620, 230, 36, 26, 12
    xs = lambda i: L + i * (W - L - 10) / (len(ct) - 1)
    ys = lambda v: T + (4.2 - v) / (4.2 - 2.6) * (H - T - B)
    def path(col):
        return " ".join(f"{'M' if i == 0 else 'L'}{xs(i):.1f},{ys(v):.1f}" for i, v in enumerate(ct[col]))
    bars = "".join(f'<rect x="{xs(i)-4:.1f}" y="{H-B-s*40:.1f}" width="8" height="{s*40:.1f}" class="bar"/>'
                   for i, s in enumerate(ct.defect_cohort_ticket_share))
    grid = "".join(f'<line x1="{L}" x2="{W-10}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" class="grid"/><text x="4" y="{ys(v)+4:.1f}" class="ax">{v:.1f}</text>'
                   for v in (2.8, 3.2, 3.6, 4.0))
    lab = "".join(f'<text x="{xs(i):.1f}" y="{H-8}" class="ax" text-anchor="middle">{m[2:4]}-{m[5:]}</text>'
                  for i, m in enumerate(ct.month) if i % 3 == 0)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Monthly CSAT">{grid}{bars}'
            f'<path d="{path("csat_excl_defect_cohort")}" class="l2"/><path d="{path("avg_csat")}" class="l1"/>{lab}</svg>'
            '<p class="note"><b class="k1">Blue</b> CSAT (respondents) · <b class="k2">grey</b> CSAT excluding defect-lot tickets · '
            'red bars = defect-lot share of tickets (scaled to 40%)</p>')


def lot_chart(lots):
    W, H, B = 620, 170, 24
    mx = max(lots.replacements_per_100_orders.max(), 1)
    n, bw = len(lots), (W - 20) / len(lots)
    out = []
    for i, (m, r) in enumerate(lots.iterrows()):
        h = r.replacements_per_100_orders / mx * (H - B - 14)
        cls = "bar" if m in p2.DEFECT_LOT_MONTHS else "bar2"
        out.append(f'<rect x="{10+i*bw+3:.1f}" y="{H-B-h:.1f}" width="{bw-6:.1f}" height="{h:.1f}" class="{cls}"/>'
                   f'<text x="{10+i*bw+bw/2:.1f}" y="{H-B-h-3:.1f}" class="ax" text-anchor="middle">{r.replacements_per_100_orders:.0f}</text>'
                   f'<text x="{10+i*bw+bw/2:.1f}" y="{H-8}" class="ax" text-anchor="middle">{m}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Replacements per 100 orders by lot month">{"".join(out)}</svg>'


def table(cols, rows, flags=None):
    h = "".join(f"<th>{escape(c)}</th>" for c in cols)
    flags = flags or [False] * len(rows)
    b = "".join(('<tr class="fl">' if f else "<tr>") + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r, f in zip(rows, flags))
    return f'<div class="sc"><table><tr>{h}</tr>{b}</table></div>'


def mins(x):
    return f"{x:,.0f}"


def handle_note(b10):
    """Plain-language reading of handle time for the bottom ten, generated from the numbers shown in the table."""
    lg = b10[b10.agent_team.isin(["Logistics", "Returns Desk"])]
    ch = b10[b10.agent_team == "Chat Frontline"]
    d = ch.median_ht - ch.team_median_ht
    return (f"<b>Reading handle time:</b> it tracks the queue more than the person. The {len(lg)} Logistics/Returns Desk agents in the bottom ten sit at "
            f"{mins(lg.median_ht.min())} to {mins(lg.median_ht.max())} min median (about {lg.median_ht.median()/60:.0f} hours), the same as their teams. "
            f"The {len(ch)} Chat Frontline agents are {d.min():+.0f} to {d.max():+.0f} min against the chat team median of {mins(ch.team_median_ht.iloc[0])} min: "
            "speed is not what sets them apart. Read the median first; the mean is pulled up by a minority of very long cases "
            "(and, on auto-closed tickets, the 72-hour customer-silence wait in policy s8).")


def all_agents_table(a):
    rows = [(("Tier " + str(r.tier)), r.csat_rank, f"{r.agent_id} {r.agent_name}", r.agent_team, r.tickets, r.csat_n, f"{r.avg_csat:.2f}",
             mins(r.median_ht), mins(r.mean_ht), mins(r.team_median_ht), "BOTTOM 10 (raw CSAT)" if r.bottom_ten else "")
            for r in a.itertuples()]
    t = table(["Tier", "Rank in tier (1 = lowest CSAT)", "Agent", "Team", "Tickets", "CSAT responses", "CSAT", "Median handle (min)",
               "Mean handle (min)", "Team median handle (min)", "Flag"], rows, flags=list(a.bottom_ten))
    return t


CSS = """:root{--bg:#fff;--fg:#1a1a1a;--mu:#666;--bd:#ddd;--ac:#1f5fbf;--rd:#c0392b;--gr:#999}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171a;--fg:#e8e8e8;--mu:#9aa;--bd:#333;--ac:#6ea8ff;--rd:#ff7a6b;--gr:#777}}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:860px;margin:auto}
h1{font-size:22px;margin:0}h2{font-size:17px;margin:26px 0 6px;border-bottom:1px solid var(--bd);padding-bottom:4px}
.sub,.note{color:var(--mu);font-size:13px}.kp{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.kp div{border:1px solid var(--bd);border-radius:6px;padding:8px}.kp b{display:block;font-size:20px}.kp span{font-size:12px;color:var(--mu)}
svg{width:100%;height:auto}.grid{stroke:var(--bd)}.ax{fill:var(--mu);font-size:10px}.l1{fill:none;stroke:var(--ac);stroke-width:2.5}
.l2{fill:none;stroke:var(--gr);stroke-width:1.5;stroke-dasharray:4 3}.bar{fill:var(--rd);opacity:.75}.bar2{fill:var(--gr);opacity:.6}
.k1{color:var(--ac)}.k2{color:var(--gr)}.sc{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}
tr.fl td{font-weight:600;background:rgba(192,57,43,.10)}th,td{border-bottom:1px solid var(--bd);padding:4px 6px;text-align:left;white-space:nowrap}li{margin:3px 0}"""


def render(d):
    ov, ct, e, cf = d["ov"], d["ct"], d["econ"], d["cf"]
    k = [(f"{ov['csat_avg_respondents_only']:.2f}", "CSAT, respondents only"), (f"{int(ov['tickets_total']):,}", "tickets, 18 months"),
         (f"{ov['sla_breach_rate']*100:.1f}%", "first-response SLA breaches"), (f"Rs {d['core']/1e5:.1f} lakh", "excess cost of Pulse 2 defect"),
         (f"{d['current']:.2f} → {d['target']:.2f}", "CSAT goal")]
    kp = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in k)
    trough = ct.loc[ct.avg_csat.idxmin()]
    b10 = table(["#", "Agent", "Team", "Raw CSAT", "Median handle (min)", "Mean handle (min)", "Team median handle (min)", "Mix-expected", "Gap", "z", "Read"],
                [(int(r.raw_bottom_ten_rank), f"{r.agent_id} {r.agent_name}", r.agent_team, f"{r.avg_csat:.2f}", mins(r.median_ht), mins(r.mean_ht),
                  mins(r.team_median_ht), f"{r.mix_expected_csat:.2f}",
                  f"{r.mix_adjusted_gap:+.2f}", f"{r.resid_z:.1f}", "Coach" if r.resid_ci95_high < 0 else "Queue mix, no signal")
                 for r in d["b10"].assign(resid_ci95_high=d["b10"].agent_id.map(d["train"].set_index("agent_id").resid_ci95_high).fillna(1)).itertuples()])
    tr = d["train"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vireo Audio: Support Dashboard</title><style>{CSS}</style></head><body>
<h1>Vireo Audio: Customer Support Dashboard</h1>
<p class="sub">Jan 2025 to Jun 2026 · {int(ov['tickets_total']):,} tickets · 44 agents · generated from verified Phase 1/2 outputs</p>
<div class="kp">{kp}</div>
<h2>1. The story: a Pulse 2 lot defect, not a support-team collapse</h2>
<p>CSAT fell from about 3.5 to a trough of <b>{trough.avg_csat:.2f} in {trough.month}</b> as tickets from Pulse 2 lots PL2-2510/2511/2512 rose from 0.3% to
{ct.defect_cohort_ticket_share.max()*100:.0f}% of volume. Those lots run at <b>{e['defect_rate']*100:.1f}</b> replacements per 100 orders vs {e['base_rep_rate']*100:.1f} for other Pulse 2 lots.</p>
{line_chart(ct)}
<h2>Replacements per 100 orders, Pulse 2 lot-months (red = defect lots)</h2>{lot_chart(d["lots"])}
<h2>2. Raw Tier-1 bottom ten (lowest CSAT), with handle time and queue-mix context</h2>
{b10}<p class="note">Gap = actual minus CSAT expected for the same category/channel mix; z = gap over its standard error. Tier 1 only; Tier 2 is not ranked against Tier 1 (policy s6).
Handle time = first human response to resolution, attended tickets only; team median = median of that team's agent medians.</p>
<p>{handle_note(d["b10"])}</p>
<h2>3. CSAT and handle time for all 44 agents</h2>
{all_agents_table(d["agents"])}<p class="note">Sorted by tier, then lowest CSAT first. CSAT is respondents only. Tier 2 (Escalations &amp; Warranty) handle times run in days; Tier 2 is ranked only against Tier 2.
The 10 flagged rows are the same ten as in section 2.</p>
<h2>4. Training priority</h2>
<p><b>Train now:</b> {", ".join(f"{r.agent_id} ({r.agent_name})" for r in tr.itertuples())}: the only agents whose mix-adjusted gap excludes zero.
The other six raw-bottom-ten agents show no training signal; their low raw score reflects Delivery/Returns queues. Closing the four gaps lifts Tier 1 CSAT by about {tr.tier1_csat_lift_if_gap_closed.sum():.3f}.</p>
<h2>5. Business impact and goal</h2>
<ul><li><b>Rs {d['core']:,.0f}</b> measured direct cost: {e['excess_rep']:.0f} excess replacements at Rs {e['rep_cost_each']:,} (unit cost + Rs 340, policy s5) plus {e['excess_tk']:.0f} excess contacts at about Rs {e['avg_contact_cost']:.0f}. Lower bound: order-linked tickets only.</li>
<li><b>Goal: blended CSAT {d['current']:.2f} → at least {d['target']:.2f}</b>, held two quarters, by end Q1 2027. Defect-lot tickets are {cf['share_dc']*100:.1f}% of responses at {cf['csat_dc']:.2f} vs {cf['csat_rest']:.2f} elsewhere:
{cf['csat_rest']-cf['csat_dc']:.3f} × {cf['share_dc']:.3f} = {cf['lift']:.3f}.</li></ul>
<h2>Limitations</h2><p class="note">Association, not proven cause. Only 65% of Pulse 2 tickets link to an order/lot. No case-severity field, so the four agents' gap may partly reflect harder cases.
CSAT is respondents only (44%). No revenue data, so CSAT loss is not monetised. Full detail: analysis/business_analysis.md.</p>
</body></html>"""


def main():
    d = gather()
    DASH.mkdir(exist_ok=True)
    (DASH / "index.html").write_text(render(d), encoding="utf-8")
    data = dict(tickets=int(d["ov"]["tickets_total"]), csat=round(float(d["ov"]["csat_avg_respondents_only"]), 3),
                sla_breach_rate=round(float(d["ov"]["sla_breach_rate"]), 4), core_cost_inr=round(d["core"]),
                goal=dict(current=round(d["current"], 3), target=d["target"]), months=len(d["ct"]),
                bottom_ten=list(d["b10"].agent_id), train_now=list(d["train"].agent_id),
                defect_lots=list(p2.DEFECT_LOT_MONTHS), handle_time_agents=int(d["agents"].median_ht.notna().sum()),
                agents_in_table=len(d["agents"]))
    (DASH / "dashboard_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("dashboard/index.html + dashboard_data.json written")


if __name__ == "__main__":
    main()
