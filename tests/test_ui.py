"""
Unit tests for Auroraa R&D Streamlit UI components, sample data, and API client.
"""

import json
from types import SimpleNamespace
from streamlit.testing.v1 import AppTest

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
    clean_report_markdown,
    extract_file_content,
    render_report_markdown,
)


def test_sample_data_validity():
    """Verify that sample cases load and conform to ExplainRequest schema."""
    # Test ABC Textile Industries
    req_abc = ExplainRequest.model_validate(ABC_TEXTILE_DATA)
    assert req_abc.business_profile.business_name == "ABC Textile Industries"

    # Test JSON string parsing
    parsed = json.loads(ABC_TEXTILE_JSON)
    assert parsed["business_profile"]["business_name"] == "ABC Textile Industries"

    # Test Trading Case
    req_trade = ExplainRequest.model_validate(SUNRISE_TRADING_DATA)
    assert req_trade.business_profile.business_name == "Sunrise Electronics Trading"

    # Test Services Case
    req_serv = ExplainRequest.model_validate(APEX_SERVICES_DATA)
    assert req_serv.business_profile.business_name == "Apex Software Consulting"

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

    success, res = run_inference({}, base_url="http://127.0.0.1:9999")
    assert success is False
    assert "Connection failed" in res["error"] or "Unable to connect" in res["error"]


def test_report_markdown_removes_orphan_bold_markers_only():
    report = "**\n\n**Verified** operations.\n\n**"
    assert clean_report_markdown(report) == "**Verified** operations."


def test_clean_report_markdown_removes_br_tags():
    table_sample = "| Category | Supporting Evidence |\n| Purchases | Invoice PUR-001 <br> Consumption log |"
    cleaned = clean_report_markdown(table_sample)
    assert "<br>" not in cleaned
    assert "Invoice PUR-001 · Consumption log" in cleaned


def test_full_report_is_rendered_as_markdown():
    report = (
        "## Evidence matching\n\n"
        "| Category | Status |\n"
        "| --- | --- |\n"
        "| Purchases | MISMATCH |"
    )
    app = AppTest.from_string(
        "from ui.components import render_report_markdown\n"
        f"render_report_markdown({report!r})"
    ).run()
    assert not app.exception
    assert app.markdown[0].value == report


def test_media_uploads_do_not_create_unverified_observations():
    """Raw media is not analyzed by the API client and must not become fake evidence."""
    for filename in ("inspection.jpg", "premises.mp4"):
        text, parsed_json, file_type = extract_file_content(
            SimpleNamespace(name=filename, getvalue=lambda: b"media-bytes")
        )
        assert text is None
        assert parsed_json is None
        assert "not analyzed" in file_type


def test_json_file_upload_requires_an_object_payload():
    text, parsed_json, file_type = extract_file_content(
        SimpleNamespace(name="case.json", getvalue=lambda: b"[]")
    )
    assert text is None
    assert parsed_json is None
    assert file_type == "Invalid JSON: the payload must be an object"
