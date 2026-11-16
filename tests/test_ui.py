"""
Unit tests for Auroraa R&D Streamlit UI components, sample data, and API client.
"""

import json
from types import SimpleNamespace
from unittest.mock import patch
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


def test_inference_history_loads_and_refreshes_from_metrics_endpoint():
    history = [{"timestamp": "2026-11-16 09:00:00", "total_tokens": 42}]
    with (
        patch(
            "ui.api_client.check_health",
            return_value={"ok": True, "status": "healthy"},
        ),
        patch(
            "ui.api_client.get_metrics",
            return_value={"ok": True, "metrics": {"call_history": history}},
        ) as metrics,
    ):
        app = AppTest.from_file("../ui/app.py").run()

        assert not app.exception
        assert app.session_state["history_entries"] == history
        metrics.assert_called_once_with("http://localhost:8000")

        app.session_state["backend_url"] = "http://127.0.0.1:8000"
        app.run()
        metrics.assert_called_with("http://127.0.0.1:8000")

        app.button(key="refresh_history").click().run()
        assert metrics.call_count == 3


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


def test_text_input_collects_categorized_business_evidence():
    with (
        patch(
            "ui.api_client.check_health",
            return_value={"ok": False, "error": "Backend unavailable"},
        ),
        patch(
            "ui.api_client.get_metrics",
            return_value={"ok": True, "metrics": {"call_history": []}},
        ),
        patch(
            "ui.api_client.run_inference",
            return_value=(True, {"status": "completed", "report": "Test report"}),
        ) as inference,
    ):
        app = AppTest.from_file("../ui/app.py")
        app.session_state["input_mode"] = "Text input"
        app.session_state["backend_url"] = "http://127.0.0.1:9999"
        app.run()

        assert not app.exception
        assert app.text_area(key="text_purchase_bills").value
        assert app.text_area(key="text_inventory_images").value
        assert app.text_area(key="text_physical_video").value

        app.text_area(key="text_purchase_bills").set_value(
            "Bill INV-10 from Cotton Supply, total INR 500"
        )
        app.text_area(key="text_sales_bills").set_value(
            "Invoice SALE-10 to Fabric House, total INR 800"
        )
        app.segmented_control(key="input_mode").set_value("JSON input").run()
        app.segmented_control(key="input_mode").set_value("Text input").run()

        assert (
            app.text_area(key="text_purchase_bills").value
            == "Bill INV-10 from Cotton Supply, total INR 500"
        )
        app.button(key="run_inference").click().run()

        assert not app.exception
        payload = inference.call_args.args[0]
        assert "Bill INV-10" in payload["observed_evidence"]
        assert "Purchase evidence" in payload["observed_evidence"]
        assert "Sales evidence" in payload["observed_evidence"]
        assert "Declared claims" in payload["declared_information"]


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
