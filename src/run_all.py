"""One-command reproduction of the whole submission from raw data (works on Windows, macOS, Linux).
Run from the project root:  python -m src.run_all
Runs every stage in order, stops at the first failure, prints a one-line result per stage. No network, no API keys, no paid calls."""
import subprocess
import sys
import time

STAGES = [
    ("Phase 1 pipeline", ["-m", "src.pipeline"]),
    ("Phase 1 validation", ["-m", "src.validate"]),
    ("Unit + integration tests", ["tests/run_tests.py"]),
    ("Phase 2 analysis", ["-m", "src.phase2_report"]),
    ("Phase 2 validation", ["-m", "src.validate_phase2"]),
    ("Dashboard build", ["-m", "src.dashboard"]),
    ("Dashboard validation", ["-m", "src.validate_task4"]),
    ("Detailed memo (FINAL_MEMO.md)", ["-m", "src.memo"]),
    ("One-page memo (MEMO_TO_PRIYA.md)", ["-m", "src.memo_priya"]),
    ("Final validation", ["-m", "src.validate_final"]),
]


def main():
    t0 = time.time()
    for name, args in STAGES:
        r = subprocess.run([sys.executable, "-B", *args], capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        print(f"{'OK  ' if r.returncode == 0 else 'FAIL'} {name}: {last}")
        if r.returncode:
            print(r.stdout[-3000:], r.stderr[-3000:])
            return 1
    print(f"\nAll {len(STAGES)} stages passed in {time.time() - t0:.1f}s. Open dashboard/index.html and read MEMO_TO_PRIYA.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
