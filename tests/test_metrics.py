import numpy as np
import pandas as pd
from src.metrics import build_ticket_metrics, build_agent_metrics

PRODUCTS = pd.DataFrame({"sku": ["S1"], "unit_cost_inr": [1000]})
AGENTS = pd.DataFrame({"agent_id": ["A1", "A2"], "name": ["Same Name", "Same Name"], "site": ["X", "Y"],
                       "team": ["Chat Frontline", "Escalations & Warranty"], "shift": ["Day", "Day"], "tier": [1, 2]})


def _t(**kw):
    base = dict(ticket_id="T1", created_at="2026-01-01 10:00", first_response_at="2026-01-01 10:10",
                resolved_at="2026-01-01 11:10", status="resolved", channel="chat", customer_id="C", order_id=None,
                product_sku="S1", category="Other", priority="Normal", assigned_team="Chat Frontline",
                agent_id="A1", transfers=0, csat_score=np.nan, refund_amount_inr=np.nan, refund_reason_code=None,
                replacement_issued="N", customer_message="x", agent_notes="y", source_system="helpdesk")
    base.update(kw)
    return base


def build(rows):
    return build_ticket_metrics(pd.DataFrame(rows), AGENTS, PRODUCTS)


def test_handle_time_is_first_response_to_resolution():
    tm = build([_t()])
    assert tm.loc[0, "first_response_minutes"] == 10 and tm.loc[0, "handle_time_minutes"] == 60


def test_sla_boundary_equal_to_target_is_not_a_breach():
    tm = build([_t(ticket_id="a", first_response_at="2026-01-01 10:15"),
                _t(ticket_id="b", first_response_at="2026-01-01 10:16")])
    assert list(tm.sla_breach.astype(bool)) == [False, True]     # chat target = 15 min


def test_sla_targets_by_channel():
    tm = build([_t(ticket_id=c, channel=c, first_response_at="2026-01-01 12:01") for c in ["chat", "voice", "social", "email"]])
    assert list(tm.sla_target_minutes) == [15, 120, 240, 480]
    assert list(tm.sla_breach.astype(bool)) == [True, True, False, False]   # 121 min


def test_blank_csat_is_not_zero_and_excluded_from_average():
    tm = build([_t(ticket_id="a", csat_score=4.0), _t(ticket_id="b"), _t(ticket_id="c", csat_score=2.0)])
    assert list(tm.csat_responded) == [True, False, True]
    assert tm.csat_score.isna().sum() == 1
    am = build_agent_metrics(tm, AGENTS)
    r = am[am.agent_id == "A1"].iloc[0]
    assert r.avg_csat == 3.0 and r.csat_response_count == 2 and r.low_csat_rate == 0.5


def test_open_ticket_kept_but_no_handle_time():
    tm = build([_t(status="open", resolved_at=None)])
    assert len(tm) == 1 and pd.isna(tm.loc[0, "handle_time_minutes"]) and bool(tm.loc[0, "is_open_pending"])


def test_legacy_ticket_gets_positive_handle_time_after_normalization():
    tm = build([_t(source_system="legacy_fd", created_at="2025-01-01 08:22", first_response_at="2025-01-01 08:30",
                   resolved_at="2025-01-01 03:05")])
    assert tm.loc[0, "handle_time_minutes"] == 5.0 and not tm.loc[0, "dq_negative_handle"]


def test_replacement_cost_is_unit_cost_plus_340():
    tm = build([_t(replacement_issued="Y"), _t(ticket_id="T2")])
    assert list(tm.replacement_cost_inr) == [1340, 0]


def test_agent_join_uses_id_not_name_and_tiers_are_separate():
    tm = build([_t(ticket_id="a", agent_id="A1"), _t(ticket_id="b", agent_id="A2", csat_score=5.0)])
    am = build_agent_metrics(tm, AGENTS)
    assert len(am) == 2 and am.set_index("agent_id").loc["A2", "tier"] == 2
    assert not am[am.tier == 2].bottom_ten_raw_tier1.any()
    assert (am.groupby("tier").csat_rank_within_tier.min() == 1).all() or am.avg_csat.isna().any()


def test_refund_and_replacement_flagged():
    tm = build([_t(replacement_issued="Y", refund_amount_inr=500.0)])
    assert bool(tm.loc[0, "dq_refund_and_replacement"])
