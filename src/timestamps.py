"""Timestamp normalization.

Policy s9 facts used here:
  * The helpdesk displays/exports timestamps in IST.
  * Resolution timestamps of migrated (legacy_fd) tickets were reconstructed from the legacy
    event log, which stores UTC.
Evidence in the data: with no correction, ~63% of legacy tickets resolve BEFORE they were created;
adding +5h30 removes every negative duration. created_at and first_response_at are consistent
with each other in both systems, so only legacy resolved_at is shifted.

Canonical timezone for this project: IST, stored as timezone-naive datetimes.
"""
import pandas as pd
from .config import IST_OFFSET, LEGACY_SOURCE, TS_COLS, TS_FORMAT


def normalize_timestamps(tickets: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with parsed datetimes, all in IST.

    Adds:
      resolved_at_raw     resolved_at exactly as exported (parsed, not shifted)
      resolved_tz_shifted True where a UTC->IST shift was applied (legacy rows with resolved_at)
      ts_unparseable      True where a non-blank timestamp string failed to parse (kept as NaT, flagged)
    """
    df = tickets.copy()
    unparse = pd.Series(False, index=df.index)
    for col in TS_COLS:
        parsed = pd.to_datetime(df[col], format=TS_FORMAT, errors="coerce")
        unparse |= df[col].notna() & parsed.isna()
        df[col] = parsed
    df["ts_unparseable"] = unparse
    df["resolved_at_raw"] = df["resolved_at"]
    shift = (df["source_system"] == LEGACY_SOURCE) & df["resolved_at"].notna()
    df.loc[shift, "resolved_at"] = df.loc[shift, "resolved_at"] + IST_OFFSET
    df["resolved_tz_shifted"] = shift
    return df
