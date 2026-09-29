"""Central configuration: paths and policy constants (support-policy.pdf v3.2)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"          # read-only copies of the client exports
OUT_DIR = ROOT / "outputs"
ANALYSIS_DIR = ROOT / "analysis"

# Policy s3: first-response targets in minutes, by channel
SLA_TARGET_MIN = {"chat": 15, "voice": 120, "social": 240, "email": 480}

# Policy s5: replacement cost for planning = unit cost + Rs 340 (reverse pickup + forward shipping)
REPLACEMENT_LOGISTICS_INR = 340

# Policy s8/s10: attendance = status resolved or closed
ATTENDED_STATUSES = ("resolved", "closed")
OPEN_STATUSES = ("open", "pending")

# Policy s9: legacy (Freshdesk) resolution timestamps come from a UTC event log; helpdesk is IST
LEGACY_SOURCE = "legacy_fd"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)
HELPDESK_CUTOVER = pd.Timestamp("2025-09-14")

# Analyst choices (documented in analysis/foundation_summary.md)
LOW_CSAT_MAX = 2                          # CSAT <= 2 counts as "low"
MAX_PLAUSIBLE_HANDLE_MIN = 30 * 24 * 60   # anything longer than 30 days is flagged impossible

TS_COLS = ["created_at", "first_response_at", "resolved_at"]
TS_FORMAT = "%Y-%m-%d %H:%M"

# Row counts observed in the delivered pack (used as a regression check only)
EXPECTED_ROWS = {"tickets": 11750, "agents": 44, "customers": 9500, "orders": 15500, "products": 14}

REQUIRED_COLUMNS = {
    "tickets": ["ticket_id", "created_at", "first_response_at", "resolved_at", "status", "channel",
                "customer_id", "order_id", "product_sku", "category", "priority", "assigned_team",
                "agent_id", "transfers", "csat_score", "refund_amount_inr", "refund_reason_code",
                "replacement_issued", "customer_message", "agent_notes", "source_system"],
    "agents": ["agent_id", "name", "site", "team", "shift", "tier", "from_date", "to_date"],
    "customers": ["customer_id", "name", "city", "state", "signup_date", "care_plus"],
    "orders": ["order_id", "customer_id", "sku", "order_date", "channel", "qty", "order_value_inr", "lot_code"],
    "products": ["sku", "product_name", "family", "launch_date", "unit_cost_inr", "retail_price_inr", "warranty_months"],
}
ID_COLUMNS = {"tickets": "ticket_id", "agents": "agent_id", "customers": "customer_id",
              "orders": "order_id", "products": "sku"}
