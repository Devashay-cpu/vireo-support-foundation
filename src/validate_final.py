"""Final delivery checks. Run: python -m src.validate_final [path/to/package.zip]
Checks the memo against verified CSVs, required files, portability and (optionally) the package contents."""
import re
import sys
import zipfile

import pandas as pd

from .config import ANALYSIS_DIR, OUT_DIR, ROOT

checks = []
chk = lambda n, ok, d="": checks.append((bool(ok), n, d))
REQUIRED = ["README.md", "requirements.txt", "FINAL_MEMO.md", "data/raw/tickets.csv", "data/raw/agents.csv", "data/raw/orders.csv",
            "data/raw/customers.csv", "data/raw/products.csv", "data/raw/support-policy.pdf", "analysis/foundation_summary.md", "analysis/business_analysis.md",
            "analysis/csat_trend.csv", "analysis/agent_context.csv", "analysis/training_priority.csv", "analysis/root_causes.csv", "analysis/business_impact.csv",
            "dashboard/index.html", "dashboard/dashboard_data.json", "outputs/ticket_metrics.csv", "outputs/validation_report.txt",
            "outputs/validation_report_phase2.txt", "outputs/validation_report_task4.txt", "src/pipeline.py", "src/phase2.py", "src/dashboard.py",
            "src/memo.py", "src/validate.py", "src/validate_phase2.py", "src/validate_task4.py", "tests/run_tests.py",
            "MEMO_TO_PRIYA.md", "src/memo_priya.py", "src/run_all.py", "VALIDATION.md", "submission-form.md", "SCREEN_RECORDING_OUTLINE.md", ".gitignore"]


def main(pkg=None):
    memo = (ROOT / "FINAL_MEMO.md").read_text(encoding="utf-8")
    ov = pd.read_csv(OUT_DIR / "overall_metrics.csv").set_index("metric").value
    bi = pd.read_csv(ANALYSIS_DIR / "business_impact.csv")
    ct = pd.read_csv(ANALYSIS_DIR / "csat_trend.csv")
    tp = pd.read_csv(ANALYSIS_DIR / "training_priority.csv")
    core = int(bi[bi.item.str.startswith("CORE TOTAL")].amount_inr.iloc[0])
    for f in REQUIRED:
        chk(f"required file present: {f}", (ROOT / f).exists() and (ROOT / f).stat().st_size > 0)
    chk("memo: 11 numbered sections", all(re.search(rf"^## {i}\. ", memo, re.M) for i in range(1, 12)))
    chk("memo: no nan/None/inf", not re.search(r"\b(nan|None|inf)\b", memo, re.I))
    for name, s in [("CSAT 3.33", f"{ov['csat_avg_respondents_only']:.2f}"), ("n=5,196", f"n={int(ov['csat_response_count']):,}"),
                    ("trough", f"{ct.avg_csat.min():.2f} in {ct.loc[ct.avg_csat.idxmin(), 'month']}"),
                    ("core cost", f"Rs {core:,}"), ("SLA breaches", f"{int(ov['sla_breach_count']):,} breaches ({ov['sla_breach_rate']*100:.2f}%)"),
                    ("goal 3.42", "at least 3.42"), ("replacement rate 31.9", "31.9 replacements per 100 orders"),
                    ("1,979 orders", "1,979 orders"), ("cohort CSAT n=718", "(n=718)")]:
        chk(f"memo contains verified figure: {name}", s in memo, s)
    chk("memo: train-now agents are exactly A3004-A3007", all(a in memo for a in tp[tp.evidence.str.startswith('strong')].agent_id) and "4 of 38" in memo)
    chk("memo: addressed to Priya Raman; no stale 'brief unavailable' claim", "Priya Raman" in memo and "assessment brief and any submission form were not available" not in memo)
    chk("memo: mentions handle time and the free-text exclusion", "Handle time" in memo and "Free-text fields" in memo)
    chk("memo: Rs 2,500 only mentioned as not applicable", memo.count("2,500") == 1 and "does not apply" not in memo and "applies" in memo)
    chk("memo agrees with business_analysis.md on core cost", f"{core:,}" in (ANALYSIS_DIR / "business_analysis.md").read_text(encoding="utf-8"))
    mp = (ROOT / "MEMO_TO_PRIYA.md").read_text(encoding="utf-8")
    words = len(mp.split())
    chk("priya memo: addressed to Priya Raman", "Priya Raman" in mp)
    chk("priya memo: one page (<= 600 words)", words <= 600, words)
    chk("priya memo: no nan/None/inf", not re.search(r"\b(nan|None|inf)\b", mp, re.I))
    chk("priya memo: non-technical (no z-score / CI / policy section refs)", not re.search(r"z-score|confidence interval|95%|\bpolicy s\d|\bCI\b", mp, re.I))
    for name, sub in [("CSAT now", f"{ov['csat_avg_respondents_only']:.2f}"), ("goal", "at least 3.42"), ("core cost lakh", f"Rs {core/1e5:.2f} lakh"),
                      ("core cost exact", f"{core:,}"), ("replacement rate", "31.9 replacements per 100 orders"), ("trough", f"{ct.avg_csat.min():.2f}"),
                      ("handle time section", "**Handle time.**"), ("bottom ten section", "**The bottom ten.**"), ("target section", "**Target.**")]:
        chk(f"priya memo contains: {name}", sub in mp, sub)
    chk("priya memo names exactly the four train-now agents", all(f"({a})" in mp for a in tp[tp.evidence.str.startswith('strong')].agent_id) and "four agents, not ten" in mp)
    chk("priya memo: does not use the email's Rs 2,500", "2,500" not in mp)
    rd = (ROOT / "README.md").read_text(encoding="utf-8")
    chk("README: no stale 'brief not available' / 'Phase 1 only' claims", "not** available" not in rd and "Phase 1 only" not in rd)
    chk("README: documents run_all and both memos", "python -m src.run_all" in rd and "MEMO_TO_PRIYA.md" in rd)
    sf = (ROOT / "submission-form.md").read_text(encoding="utf-8")
    chk("submission form: every brief question present", all(q in sf for q in ["What did you build", "What does one run cost", "How do you know it works", "Did you change, narrow, or push back",
        "What is wrong with what you are handing us", "What did you deliberately leave out", "Anything you built or found that nobody asked for", "What did you use AI for",
        "Public Google Drive Link", "Someone picks this up on Monday", "Honest hours spent", "Github Repo Link"]))
    chk("submission form: manual items explicitly marked", sf.count("[MANUAL") >= 5, sf.count("[MANUAL"))
    chk("submission form: figures match verified outputs", f"{core:,}" in sf and "3.42" in sf and f"{int(ov['tickets_total']):,}" in sf)
    dash = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    chk("dashboard: shows per-agent handle time (median + mean) for all 44 agents", dash.count("Median handle (min)") == 2 and "CSAT and handle time for all 44 agents" in dash)
    chk("dashboard: standalone (no http, script, link, img src)", not re.search(r"https?://|<script|<link|<img", dash))
    chk("dashboard core cost matches memo", f"{core:,}" in dash)
    bad = [p for p in list((ROOT / "src").glob("*.py")) + list((ROOT / "tests").glob("*.py")) if re.search("/" + "mnt/|/" + "home/claude", p.read_text(encoding="utf-8"))]
    chk("no hard-coded sandbox paths in code", not bad, [b.name for b in bad])
    if pkg:
        names = zipfile.ZipFile(pkg).namelist()
        chk("package: no caches/temp files", not [n for n in names if re.search(r"__pycache__|\.pytest_cache|\.pyc$|\.DS_Store|\.zip$|~$", n)])
        top = {n.split("/")[0] for n in names}
        chk("package: single top-level folder", len(top) == 1, top)
        chk("package: contains every required file", all(any(n.endswith("/" + f) for n in names) for f in REQUIRED),
            [f for f in REQUIRED if not any(n.endswith("/" + f) for n in names)])
    for ok, n, d in checks:
        print(("PASS " if ok else "FAIL ") + n + (f" ({d})" if d != "" else ""))
    line = f"{sum(o for o,_,_ in checks)}/{len(checks)} checks passed"
    print(line)
    if not pkg:
        (OUT_DIR / "validation_report_final.txt").write_text("\n".join(("PASS  " if o else "FAIL  ") + n for o, n, _ in checks) + f"\n\n{line}\n")
    return 0 if all(o for o, _, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
