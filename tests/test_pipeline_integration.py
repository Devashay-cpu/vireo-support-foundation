"""End-to-end check on the real data pack (returns early if data/raw is absent).
Plain functions with bare asserts so they run under pytest or tests/run_tests.py."""
from src.config import RAW_DIR
from src.load import raw_path, raw_record_count


def _have_data():
    return (RAW_DIR / "tickets.csv").exists()


def test_pipeline_and_validation_have_zero_failures():
    if not _have_data():
        return
    from src import pipeline, validate
    pipeline.run()
    results = validate.run_checks()
    failed = [r for r in results if not r[2]]
    assert len(results) >= 80
    assert not failed, failed


def test_raw_files_still_have_documented_row_counts():
    if not _have_data():
        return
    assert raw_record_count(raw_path("tickets")) == 11750
    assert raw_record_count(raw_path("orders")) == 15500
