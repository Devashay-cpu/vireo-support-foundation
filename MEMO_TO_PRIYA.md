# Memo: why CSAT slid, who to retrain, and the target

**To:** Priya Raman, Head of Customer Experience  |  **From:** Vireo support analytics review  |  **Data:** 11,750 tickets, Jan 2025 to Jun 2026, 44 agents

**Short answer.** Point the training budget at **four agents, not ten**. Most of the CSAT slide comes from one faulty product batch, not from the team.

**What happened.** CSAT averaged 3.49 from Jan to Sep 2025, fell to 2.95 in Feb 2026, and was back at 3.40 in Jun 2026 (only the 44% of customers who answer the survey are counted). The fall follows Pulse 2 earbuds from three production lots (PL2-2510, 2511, 2512): 31.9 replacements per 100 orders, against 5.1 for other Pulse 2 lots. Customers with those lots rate us 2.77; everyone else 3.42. The extra replacements and contacts cost about **Rs 11.84 lakh** (Rs 1,184,099). It is a floor: only 65% of Pulse 2 tickets can be tied to a lot.

**The bottom ten.** The dashboard flags the ten Tier 1 agents with the lowest CSAT. Six of them work Logistics or Returns, where delivery and returns tickets score lower for whoever handles them. Compared with what their own mix of tickets normally scores, those six are within the normal range (gap -0.09 to +0.07 points). Four chat agents are still 0.28 to 0.38 points below what their tickets predict: **Siddharth Kapoor (A3004), Zaid Khanna (A3005), Kavya Pandey (A3006), Siddharth Trivedi (A3007)**. That is your training list. Two cautions: nothing in the data records how hard a case was, and these four received 317 of the 1,701 defect-lot tickets, so pair the coaching with a fix to how hardware cases are routed.

**Handle time.** It is on the dashboard for all 44 agents, but it reflects the queue more than the person. Typical (median) handle time is 19 to 27 minutes for chat, email, voice and billing agents, about 24 hours for Logistics and Returns, and 3 to 5 days for Tier 2 escalations. Compare an agent only with their own team. The four chat agents above sit at 25 to 27 minutes against a chat median of 23, in line with peers. Speed does not pick the training list; the mix-adjusted CSAT gap does.

**Target.** Raise CSAT from 3.33 to **at least 3.42** and hold it for two quarters, by end of Q1 2027. Tickets from the faulty lots are 13.8% of survey answers and score 0.64 lower, so containing them is worth 0.089 points; coaching the four agents adds about 0.03. The money figure is the Rs 11.84 lakh above, a one-off cost of this episode rather than a per-quarter run rate. There is no revenue data, so CSAT itself is not converted into rupees.

**Do next.**

1. Book the four agents for coaching and QA sampling; do not send the other six. Re-measure after one quarter.
2. Ask Quality/Manufacturing to investigate the three lots, and contact those customers proactively with one-touch replacement.
3. Review email capacity: 12.2% of email first replies miss target, against 9.1% overall.

**How far to trust this.** The lot pattern is strong evidence, not proof of cause. Each agent's CSAT rests on 42 to 243 survey answers (118 to 142 for the four above), so small gaps are noise. Full detail and checks: `FINAL_MEMO.md`, `outputs/validation_report*.txt`.
