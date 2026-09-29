import pandas as pd
from src.timestamps import normalize_timestamps


def _row(source, created, fr, res):
    return {"ticket_id": "T", "created_at": created, "first_response_at": fr, "resolved_at": res, "source_system": source}


def test_legacy_resolved_at_shifted_utc_to_ist():
    df = pd.DataFrame([_row("legacy_fd", "2025-01-01 08:22", "2025-01-01 08:30", "2025-01-01 03:05")])
    out = normalize_timestamps(df)
    assert out.loc[0, "resolved_at"] == pd.Timestamp("2025-01-01 08:35")   # 03:05 UTC + 5:30
    assert out.loc[0, "resolved_at_raw"] == pd.Timestamp("2025-01-01 03:05")
    assert bool(out.loc[0, "resolved_tz_shifted"])


def test_helpdesk_timestamps_unchanged():
    df = pd.DataFrame([_row("helpdesk", "2026-01-01 10:00", "2026-01-01 10:05", "2026-01-01 12:00")])
    out = normalize_timestamps(df)
    assert out.loc[0, "resolved_at"] == pd.Timestamp("2026-01-01 12:00")
    assert not bool(out.loc[0, "resolved_tz_shifted"])


def test_only_resolved_at_is_shifted_and_blank_stays_blank():
    df = pd.DataFrame([_row("legacy_fd", "2025-02-01 09:00", "2025-02-01 09:10", None)])
    out = normalize_timestamps(df)
    assert pd.isna(out.loc[0, "resolved_at"]) and not bool(out.loc[0, "resolved_tz_shifted"])
    assert out.loc[0, "created_at"] == pd.Timestamp("2025-02-01 09:00")
    assert out.loc[0, "first_response_at"] == pd.Timestamp("2025-02-01 09:10")


def test_unparseable_timestamp_is_flagged_not_dropped():
    df = pd.DataFrame([_row("helpdesk", "not a date", "2026-01-01 10:05", "2026-01-01 12:00")])
    out = normalize_timestamps(df)
    assert len(out) == 1 and bool(out.loc[0, "ts_unparseable"]) and pd.isna(out.loc[0, "created_at"])
