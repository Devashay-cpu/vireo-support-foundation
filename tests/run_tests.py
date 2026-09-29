"""Fallback runner when pytest is unavailable:  python tests/run_tests.py"""
import importlib, pathlib, sys, traceback
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
passed = failed = 0
for f in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(f"tests.{f.stem}")
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        try:
            getattr(mod, name)(); passed += 1; print(f"PASS {f.stem}::{name}")
        except Exception:
            failed += 1; print(f"FAIL {f.stem}::{name}"); traceback.print_exc()
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
