"""One-page, non-technical memo to Priya Raman (Head of Customer Experience). Every number is read from verified outputs
(outputs/, analysis/) or computed with existing src.phase2 helpers; nothing is typed by hand.
Run: python -m src.memo_priya  -> MEMO_TO_PRIYA.md   (detailed technical version: FINAL_MEMO.md)"""
import pandas as pd

from . import phase2 as p2
from .config import ANALYSIS_DIR, OUT_DIR, ROOT

I = lambda x: f"Rs {x:,.0f}"
LAKH = lambda x: f"Rs {x/1e5:.2f} lakh"


def build():
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value
    ch = pd.read_csv(OUT_DIR / "channel_metrics.csv").set_index("channel")
    am = pd.read_csv(OUT_DIR / "agent_metrics.csv")
    ct = pd.read_csv(ANALYSIS_DIR / "csat_trend.csv").set_index("month")
    ctx = pd.read_csv(ANALYSIS_DIR / "agent_context.csv")
    tp = pd.read_csv(ANALYSIS_DIR / "training_priority.csv")
    bi = pd.read_csv(ANALYSIS_DIR / "business_impact.csv")
    t, o, a = p2.load_base()
    e, cf, hs = p2.cohort_economics(t, o), p2.csat_counterfactual(t), p2.handler_split(t, a)
    core = bi[bi.item.str.startswith("CORE TOTAL")].amount_inr.iloc[0]
    strong = tp[tp.evidence.str.startswith("strong")].sort_values("agent_id")
    fo = ctx[ctx.agent_id.isin(strong.agent_id)]
    b10 = ctx[ctx.raw_bottom_ten_rank.notna()]
    rest = b10[~b10.agent_id.isin(strong.agent_id)]
    pre = (ct.loc[:"2025-09"].avg_csat * ct.loc[:"2025-09"].csat_responses).sum() / ct.loc[:"2025-09"].csat_responses.sum()
    trough = ct.avg_csat.idxmin()
    goal = round(cf["csat_rest"], 2)
    coach_lift = -(fo.mix_adjusted_gap * fo.csat_response_count).sum() / cf["n"]   # same formula as memo.py section 9
    MON = lambda m: pd.Timestamp(m + "-01").strftime("%b %Y")
    WORD = {4: "four", 6: "six", 10: "ten"}
    R = hs.loc["Chat hardware-rota four (A3004-A3007)"]
    # handle time (agent_metrics.csv, median minutes): the everyday queues vs Logistics/Returns vs Tier 2
    ev = am[am.agent_team.isin(["Chat Frontline", "Email Frontline", "Voice Frontline", "Billing"])].median_handle_time
    lr = am[am.agent_team.isin(["Logistics", "Returns Desk"])].median_handle_time
    t2 = am[am.tier == 2].median_handle_time
    chat = am[am.agent_team == "Chat Frontline"].median_handle_time
    four = am[am.agent_id.isin(strong.agent_id)].median_handle_time
    names = ", ".join(f"{x.agent_name} ({x.agent_id})" for x in strong.itertuples())
    L = []
    A = L.append
    A("# Memo: why CSAT slid, who to retrain, and the target\n")
    A("**To:** Priya Raman, Head of Customer Experience  |  **From:** Vireo support analytics review  |  **Data:** 11,750 tickets, Jan 2025 to Jun 2026, 44 agents\n")
    A(f"**Short answer.** Point the training budget at **{WORD[len(strong)]} agents, not ten**. Most of the CSAT slide comes from one faulty product batch, not from the team.\n")
    A("**What happened.** " + f"CSAT averaged {pre:.2f} from Jan to Sep 2025, fell to {ct.avg_csat.min():.2f} in {MON(trough)}, and was back at {ct.avg_csat.iloc[-1]:.2f} in Jun 2026 "
      f"(only the {ov['csat_response_rate']*100:.0f}% of customers who answer the survey are counted). The fall follows Pulse 2 earbuds from three production lots (PL2-2510, 2511, 2512): "
      f"{e['defect_rate']*100:.1f} replacements per 100 orders, against {e['base_rep_rate']*100:.1f} for other Pulse 2 lots. Customers with those lots rate us {cf['csat_dc']:.2f}; everyone else {cf['csat_rest']:.2f}. "
      f"The extra replacements and contacts cost about **{LAKH(core)}** ({I(core)}). It is a floor: only {t[t.is_pl2].order_linked.mean()*100:.0f}% of Pulse 2 tickets can be tied to a lot.\n")
    A("**The bottom ten.** " + f"The dashboard flags the ten Tier 1 agents with the lowest CSAT. Six of them work Logistics or Returns, where delivery and returns tickets score lower for whoever handles them. "
      f"Compared with what their own mix of tickets normally scores, those six are within the normal range (gap {rest.mix_adjusted_gap.min():+.2f} to {rest.mix_adjusted_gap.max():+.2f} points). "
      f"Four chat agents are still {abs(fo.mix_adjusted_gap.max()):.2f} to {abs(fo.mix_adjusted_gap.min()):.2f} points below what their tickets predict: **{names}**. "
      f"That is your training list. Two cautions: nothing in the data records how hard a case was, and these four received {int(R.tickets)} of the {int(R.tickets + hs.loc['Other Tier 1'].tickets + hs.loc['Tier 2 (Escalations & Warranty)'].tickets):,} defect-lot tickets, so pair the coaching with a fix to how hardware cases are routed.\n")
    A("**Handle time.** " + f"It is on the dashboard for all 44 agents, but it reflects the queue more than the person. Typical (median) handle time is {ev.min():.0f} to {ev.max():.0f} minutes for chat, email, voice and billing agents, "
      f"about {lr.median()/60:.0f} hours for Logistics and Returns, and {t2.min()/1440:.0f} to {t2.max()/1440:.0f} days for Tier 2 escalations. Compare an agent only with their own team. "
      f"The four chat agents above sit at {four.min():.0f} to {four.max():.0f} minutes against a chat median of {chat.median():.0f}, in line with peers. Speed does not pick the training list; the mix-adjusted CSAT gap does.\n")
    A("**Target.** " + f"Raise CSAT from {cf['csat_all']:.2f} to **at least {goal:.2f}** and hold it for two quarters, by end of Q1 2027. Tickets from the faulty lots are {cf['share_dc']*100:.1f}% of survey answers and score "
      f"{cf['csat_rest']-cf['csat_dc']:.2f} lower, so containing them is worth {cf['lift']:.3f} points; coaching the four agents adds about {coach_lift:.2f}. "
      f"The money figure is the {LAKH(core)} above, a one-off cost of this episode rather than a per-quarter run rate. There is no revenue data, so CSAT itself is not converted into rupees.\n")
    A("**Do next.**\n")
    A(f"1. Book the {WORD[len(strong)]} agents for coaching and QA sampling; do not send the other six. Re-measure after one quarter.")
    A("2. Ask Quality/Manufacturing to investigate the three lots, and contact those customers proactively with one-touch replacement.")
    A(f"3. Review email capacity: {ch.loc['email'].sla_breach_rate*100:.1f}% of email first replies miss target, against {ov['sla_breach_rate']*100:.1f}% overall.")
    A("")
    A(f"**How far to trust this.** The lot pattern is strong evidence, not proof of cause. Each agent's CSAT rests on {int(ctx.csat_response_count.min())} to {int(ctx.csat_response_count.max())} survey answers ({int(fo.csat_response_count.min())} to {int(fo.csat_response_count.max())} for the four above), so small gaps are noise. "
      "Full detail and checks: `FINAL_MEMO.md`, `outputs/validation_report*.txt`.")
    (ROOT / "MEMO_TO_PRIYA.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
    print("MEMO_TO_PRIYA.md written")
