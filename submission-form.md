# Submission form: Vireo Audio Support Tickets (Set B)

> **Status: DRAFT.** Answers are written from the verified project files. Anything marked **[MANUAL]** can only be supplied by the submitter (links, hours, AI-tool history, recording).
> The client pack's own `submission-form.md` was not in the project files; these headings follow the brief's list of fields. If the official file is laid out differently, copy the answers across.

## 1. What did you build, and what business outcome does it move? State the number and the money.
A reproducible analytics tool (Python, no models at run time) plus a static dashboard and a one-page memo for Priya Raman. The dashboard shows **CSAT and handle time for all 44 agents**, flags the raw bottom ten, and adds queue-mix context that changes who should be retrained.

- **Finding:** the CSAT slide (3.49 average Jan to Sep 2025 to a 2.95 low in Feb 2026) traces mainly to Pulse 2 lots PL2-2510/2511/2512: 31.9 replacements per 100 orders vs 5.1 for other Pulse 2 lots. Of the ten lowest-CSAT Tier 1 agents, only **four** (A3004, A3005, A3006, A3007) have a statistically clear gap after adjusting for their ticket mix; the other six reflect Logistics/Returns queues.
- **Number:** raise blended CSAT from **3.33 to at least 3.42**, held for two consecutive quarters, by end of Q1 2027 (defect-lot tickets are 13.8% of responses at 2.77 vs 3.42 elsewhere: 0.644 x 0.138 = 0.089).
- **Money:** **Rs 1,184,099 (Rs 11.84 lakh)** measured direct cost of the defect (531 excess replacements x Rs 1,820 + 790 excess contacts x about Rs 277). This is a one-off cost of the episode, a lower bound (only 65% of Pulse 2 tickets link to a lot), **not a per-quarter figure**. No revenue data exists, so CSAT itself is not converted to rupees. Training spend avoided by not sending six agents: not quantified (no training cost in the pack).

## 2. What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the arithmetic.
**No paid calls.** The tool makes no API/LLM calls and needs no keys or network. Paid cost per run = Rs 0.
- One full run (`python -m src.run_all`) processes the whole history of 11,750 tickets in about 7 seconds including all validation (6.9 s measured in the audit sandbox; your machine will vary).
- Monthly volume: 650 tickets/week x 52 weeks / 12 months = **about 2,817 tickets/month**. A monthly refresh reprocesses history plus new tickets (about 11,750 + 2,817 = 14,567 tickets), still seconds of local compute. Paid API cost per month = 0 x 2,817 = **Rs 0**.
- Not included: the cost of the AI assistant used to *build* the project (see question 8).

## 3. How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.
Full population, not a sample: 11,750 tickets, 44 agents, 5,196 CSAT responses. Five layers of automated checks (Phase 1: 89 checks + 15 tests; Phase 2: 61 checks recomputed independently from the raw CSVs; dashboard: 29 checks reconciling the rendered HTML to the CSVs, including every agent's handle time; final: see `outputs/validation_report_final.txt`). **0 failures.** A hand-made mutation (one wrong handle time in the HTML) was caught by the new check.
This measures internal consistency and reproducibility, not truth: there is no labelled ground truth in the pack, so a true "error rate" for the conclusions cannot be measured. Cases it gets wrong or cannot see: tickets with no order link (34.6% of Pulse 2), case difficulty (no severity field), agents with few CSAT responses (42 to 243), free-text-only information, and the assumption that legacy timestamps are UTC (3,189 tickets). Full list: `VALIDATION.md`.

## 4. Did you change, narrow, or push back on the client's ask? What, when, and why.
Yes.
- **Narrowed "flag the bottom ten" to a training list of four.** The ten lowest raw CSAT scores are mostly a queue effect (Delivery/Returns tickets score lower for every handler). After adjusting for category, channel and defect-lot mix, six of the ten are indistinguishable from normal. The dashboard still flags all ten as asked, but marks which four are "Coach" and which six are "Queue mix, no signal". (Phase 2 analysis.)
- **Handle time is shown but not used to rank.** It is queue-driven (about 19 to 27 min median for everyday queues, about 24 h for Logistics/Returns, days for Tier 2), so agents are compared only with their own team. (Added to the dashboard during the final requirement audit, after finding it had been left out.)
- **Tier 2 is not ranked against Tier 1** (policy s6).
- **Used the policy's replacement cost (unit cost + Rs 340), not the Rs 2,500 quoted in the email.**
- **Used the orders file** although the email said to ignore what is not needed: lot codes in it are what exposed the defect.
- Before recommending training, the memo advises fixing the routing of hardware cases, because the four agents received a disproportionate share of defect-lot tickets.

## 5. What is wrong with what you are handing us?
- **The tool contains no AI model.** The brief asks for an "AI-assisted tool"; this one is deterministic, and AI assistance was used to build it (question 8). The two free-text fields (customer message, agent note) are **not analysed**.
- The four-agent conclusion rests on statistics without a case-severity field; it could partly reflect harder cases.
- Lot linkage is partial (65.4%), so the Rs 11.84 lakh is a lower bound; the goal figure (3.42) is a proposal depending on future lot quality.
- The money is a one-off total, not "Rs Y a quarter" as in the brief's example, and CSAT is not monetised.
- Handle time is not adjusted for ticket type; means are skewed by long cases (medians are shown first).
- `analysis/business_analysis.md` says agent CSAT rests on "97 to 243" responses; the correct Tier 1 range is 42 to 243. It was found in the final audit and left unchanged in the Phase 2 file (no calculation uses it); the two memos state the correct range.
- The dashboard is static (no filters, no drill-down) and the bottom-ten table is wide (scrolls sideways on a phone).
- Tested on Python 3.12 with pandas 3.0.x only, although `requirements.txt` allows pandas 2.x.
- The client's `email-thread.txt` was not available when the package was audited against the brief, so it was not re-read; the screen recording is not in this package.
- The raw data folder includes `customers.csv` (names and cities); check whether it may be published before making the repository public.

## 6. What did you deliberately leave out, and why that rather than something else?
- **Free-text analysis** (classifying customer messages/agent notes): not done. It would need a model, labelled examples to validate it, and per-ticket cost, and the structured fields already explained the main driver; [MANUAL: confirm this matches your actual reasoning].
- **Repeat-contact and first-contact-resolution:** not built; lower priority than the lot finding and agent view.
- **Customer+SKU fallback join for unlinked tickets:** ambiguous, so it would add unverifiable numbers; the upper estimate is shown as a sensitivity only.
- **Ranking Tier 2 against Tier 1, and shift/site analysis:** policy s6 forbids the first; the roster has no history for the second.
- **Monetising CSAT loss, predictive modelling, interactive dashboard:** no revenue data; no ask for prediction; static file chosen so it opens anywhere with zero setup.

## 7. Anything you built or found that nobody asked for?
- The **Pulse 2 lot defect** itself (1,979 orders, 1,701 tickets, 631 replacements) and its cost.
- **Email is the SLA outlier:** 12.2% of first replies miss target vs 9.06% overall; breached tickets score CSAT 2.78 vs 3.38.
- **Six tickets carry both a refund and a replacement**, which policy s5 forbids (Rs 25,577), flagged for Finance.
- **Transfers:** 1,215 hand-offs; tickets with a transfer score 2.99 vs 3.36.
- A one-command runner, a validation report set, and a lot early-warning proposal (threshold is a proposal, not derived from data).

## 8. What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you threw away. Link your three-minute screen recording here.
**[MANUAL: complete from your own history; the project files do not record it.]**
- Tools/models used: [MANUAL: e.g. Claude via claude.ai; list models per session].
- Where AI did the work (from the project record): writing and testing the pipeline, analysis, dashboard, validation code and memos across several Claude sessions, plus a final requirement audit that found and fixed the missing handle-time view and the too-long memo. Confirm.
- Where it wasted time / what was discarded: [MANUAL].
- Cost of the AI tools used: [MANUAL: subscription or API spend, or 0].
- Screen recording link: [MANUAL: upload the recording; beat sheet in `SCREEN_RECORDING_OUTLINE.md`].

## 9. Your Public Google Drive Link
[MANUAL: upload the final ZIP (or unzipped folder) to Google Drive, set sharing to "Anyone with the link", and paste the link. Also upload the screen recording.]

## 10. Someone picks this up on Monday and you are unreachable. The three things they need to know.
1. **Run `python -m src.run_all` from the project root.** Everything (metrics, dashboard, both memos) is rebuilt from `data/raw/` and validated in seconds; all stages must print OK. Open `dashboard/index.html` and `MEMO_TO_PRIYA.md`.
2. **Never hand-edit a number.** Every figure in the dashboard and memos is generated from `outputs/` and `analysis/` CSVs; change the code, rerun, and let the validators tell you if something broke.
3. **Know what is not proven:** the four-agent coaching list depends on an unobserved factor (case severity), the lot cost is a lower bound (65% linkage), and the CSAT goal depends on lot quality. Before spending the training budget, confirm the four agents' ticket difficulty with team leads.

## 11. Honest hours spent
[MANUAL: one number. The project files cannot tell us this; the brief caps effort at about 5 hours.]

## 12. Github Repo Link
[MANUAL: create the repository, push this folder (`.gitignore` is included), and paste the URL. Decide first whether `data/raw/customers.csv` (customer names, cities) may be public.]
