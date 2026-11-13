"""
Unit tests for Auroraa R&D Streamlit UI components, sample data, and API client.
"""

import json
import pytest
from app.schemas.request_schemas import ExplainRequest
from ui.sample_data import (
    ABC_TEXTILE_DATA,
    ABC_TEXTILE_JSON,
    SUNRISE_TRADING_DATA,
    APEX_SERVICES_DATA,
    SAMPLE_CASES,
)
from ui.api_client import normalize_url, check_health, run_inference
from ui.components import (
    get_status_badge_html,
    parse_evidence_items,
    parse_abductive_hypotheses,
)


def test_sample_data_validity():
    """Verify that sample cases load and conform to ExplainRequest schema."""
    # Test ABC Textile Industries
    req_abc = ExplainRequest.model_validate(ABC_TEXTILE_DATA)
    assert req_abc.case_id == "AUR-CASE-001"
    assert req_abc.business_profile.business_name == "ABC Textile Industries"

    # Test JSON string parsing
    parsed = json.loads(ABC_TEXTILE_JSON)
    assert parsed["case_id"] == "AUR-CASE-001"

    # Test Trading Case
    req_trade = ExplainRequest.model_validate(SUNRISE_TRADING_DATA)
    assert req_trade.case_id == "AUR-CASE-002"

    # Test Services Case
    req_serv = ExplainRequest.model_validate(APEX_SERVICES_DATA)
    assert req_serv.case_id == "AUR-CASE-003"

    assert len(SAMPLE_CASES) == 3


def test_api_client_normalize_url():
    """Verify URL normalization logic."""
    assert normalize_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_url("http://127.0.0.1:8000///") == "http://127.0.0.1:8000"
    assert normalize_url("") == "http://localhost:8000"
    assert normalize_url(None) == "http://localhost:8000"


def test_api_client_offline_handling():
    """Verify graceful error reporting when backend is unreachable."""
    health = check_health("http://127.0.0.1:9999")
    assert health["ok"] is False
    assert "Cannot connect" in health["error"] or "refused" in health["error"].lower()

    success, res = run_inference({"case_id": "TEST"}, base_url="http://127.0.0.1:9999")
    assert success is False
    assert "Connection failed" in res["error"] or "Unable to connect" in res["error"]


def test_status_badge_rendering():
    """Verify badge HTML styling conforms to color specification."""
    b_match = get_status_badge_html("MATCH")
    assert "badge-match" in b_match

    b_part = get_status_badge_html("PARTIAL MATCH")
    assert "badge-partial" in b_part

    b_mis = get_status_badge_html("MISMATCH")
    assert "badge-mismatch" in b_mis

    b_ins = get_status_badge_html("INSUFFICIENT EVIDENCE")
    assert "badge-insufficient" in b_ins


def test_evidence_matching_parser():
    """Verify parser extracts categories and statuses correctly."""
    sample_text = """
    - Category: Purchases & Consumption
      Status: MISMATCH
      Supporting Evidence: Invoice PUR-001 (1,000 kg cotton) vs production consumption (1,600 kg cotton).
      Observation: Recorded consumption exceeds purchases by 600 kg.
      Explanation: The business consumed more raw cotton than accounted for in current period invoices.

    - Category: Production & Capacity
      Status: MATCH
      Supporting Evidence: Production log of 8,000 meters matches declared production.
      Observation: Capacity utilization is 80%.
      Explanation: Operations align with infrastructure capacity.
    """
    items = parse_evidence_items(sample_text)
    assert len(items) == 2
    assert items[0]["category"] == "Purchases & Consumption"
    assert items[0]["status"] == "MISMATCH"
    assert "600 kg" in items[0]["observation"]

    assert items[1]["category"] == "Production & Capacity"
    assert items[1]["status"] == "MATCH"


def test_abductive_hypotheses_parser():
    """Verify parser extracts hypotheses and supporting/missing info."""
    sample_text = """
    Hypothesis 1: The additional 600 kg cotton was sourced from unrecorded opening warehouse inventory.
    Supporting: 20 storage bags observed in warehouse image IMG-001.
    Contradicting: No opening inventory recorded in purchase bills.
    Missing: Opening inventory stock register.
    Plausibility: High plausibility due to physical visual evidence.
    """
    hypotheses = parse_abductive_hypotheses(sample_text)
    assert len(hypotheses) == 1
    assert "600 kg" in hypotheses[0]["title"]
    assert "20 storage bags" in hypotheses[0]["supporting"]
    assert "Opening inventory stock register" in hypotheses[0]["missing"]
