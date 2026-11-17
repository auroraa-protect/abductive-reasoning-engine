"""
Unit and regression tests for Auroraa Abductive Reasoning Engine.
Tests deterministic math calculations, payload synthesis, section parsing,
and multi-industry case handling.
"""

import asyncio
import json
import pytest
import httpx
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch
from app.dependencies.grok_client import GroqCompletionResult, get_groq_completion
from app.schemas.request_schemas import (
    ExplainRequest,
    BusinessProfile,
    PurchaseEvidence,
    PurchaseBill,
    PurchaseItem,
    ProductionEvidence,
    SalesEvidence,
    FinancialEvidence,
    PhysicalEvidence,
    InventoryEvidence,
    InventoryItem,
)
from app.schemas.response_schemas import ExplainResponse, ReportSections
from app.crud.inferance_crud import (
    compute_deterministic_reconciliations,
    build_user_payload,
    parse_report_sections,
    generate,
    REPORT_SECTION_HEADERS,
)


# ---------------------------------------------------------------------------
# Test Case 1: ABC Textile Industries (Manufacturing)
# ---------------------------------------------------------------------------
def test_abc_textile_deterministic_reconciliation():
    with open("app/model/request_example.txt", "r") as f:
        req = ExplainRequest.model_validate_json(f.read())

    facts = compute_deterministic_reconciliations(req)
    facts_str = " ".join(facts)

    # 1. Physical evidence / equipment
    assert "5 unit(s) of Power Loom observed in 'Operational' condition" in facts_str

    # 2. Raw cotton consumption exceeds purchases
    assert "Material Deficit" in facts_str
    assert "600 units consumed in excess of documented purchases" in facts_str

    # 3. Production records match declared production
    assert "Production Match" in facts_str
    assert "8,000 units" in facts_str

    # 4. Declared turnover is significantly higher than documented sales
    assert "Turnover Disparity" in facts_str
    assert "1,500,000" in facts_str
    assert "250,000" in facts_str

    # 5. Bank transactions match sales
    assert "Banking Match" in facts_str
    assert "250,000" in facts_str

    # 6. Electricity consumption present
    assert "Utility Consumption" in facts_str
    assert "4,500 electricity units" in facts_str


def test_abc_textile_payload_structure():
    with open("app/model/request_example.txt", "r") as f:
        req = ExplainRequest.model_validate_json(f.read())

    payload = build_user_payload(req)

    # Declared vs observed distinction
    assert "=== DECLARED BUSINESS PROFILE ===" in payload
    assert "=== OBSERVED EVIDENCE & RECORDS ===" in payload
    assert "=== DETERMINISTIC FACT CHECK (Python-Verified Math) ===" in payload

    # Compact token size check (< 750 tokens estimated)
    assert len(payload) < 3000


# ---------------------------------------------------------------------------
# Test Case 2: Sunrise Electronics Trading (Trading / Wholesale)
# ---------------------------------------------------------------------------
def test_trading_industry_case():
    req = ExplainRequest(
        business_profile=BusinessProfile(
            business_name="Sunrise Electronics Trading",
            business_type="trading",
            industry="electronics",
            business_activity="Wholesale mobile accessories",
            declared_monthly_turnover=3000000.0,
            number_of_employees=6,
        ),
        purchase_evidence=PurchaseEvidence(
            bills=[
                PurchaseBill(
                    supplier_name="Global Tech Imports",
                    items=[
                        PurchaseItem(item_name="Wireless Earbuds", quantity=2000, unit="pcs", unit_price=600, total_amount=1200000),
                        PurchaseItem(item_name="Fast Chargers", quantity=5000, unit="pcs", unit_price=200, total_amount=1000000),
                    ],
                    total_amount=2200000,
                )
            ]
        ),
        sales_evidence=SalesEvidence(
            sales_bills=[
                {"customer_name": "Retail Hub Delhi", "total_amount": 1500000},
                {"customer_name": "Metro Gadgets", "total_amount": 1200000},
            ]
        ),
        financial_evidence=FinancialEvidence(
            bank_transactions=[
                {"transaction_type": "credit", "amount": 2700000, "description": "Client collections"},
            ]
        ),
    )

    facts = compute_deterministic_reconciliations(req)
    facts_str = " ".join(facts)

    assert "Turnover Disparity" in facts_str
    assert "3,000,000" in facts_str
    assert "2,700,000" in facts_str
    assert "Banking Match" in facts_str


# ---------------------------------------------------------------------------
# Test Case 3: Apex Software Consulting (Services)
# ---------------------------------------------------------------------------
def test_services_industry_case():
    req = ExplainRequest(
        text="""
        Apex Software Consulting provides custom web development and enterprise cloud consulting.
        The firm declares annual revenue of Rs 1.2 Crore (Rs 10 Lakhs/month) with 8 full-time software engineers.
        Client contracts show two active retainers: FinCorp Inc ($8,000/mo ~ Rs 6.6 Lakhs) and HealthCare Ltd ($3,000/mo ~ Rs 2.5 Lakhs).
        Bank account statement shows monthly credits of Rs 9.1 Lakhs matching invoices.
        Office lease shows 1,200 sq ft rented in Bengaluru IT park.
        """
    )
    payload = build_user_payload(req)
    assert "=== CASE NARRATIVE & INPUT EVIDENCE ===" in payload
    assert "Apex Software Consulting" in payload
    assert len(payload) < 1500


# ---------------------------------------------------------------------------
# Section Parser & Report Validation Test
# ---------------------------------------------------------------------------
def test_section_parsing():
    sample_report = """
    BUSINESS UNDERSTANDING
    ABC Textile Industries is a 5-year-old cotton fabric manufacturer operating in Surat with 15 employees.
    The business claims 8,000 meters monthly production and 10,000 meters capacity.

    EVIDENCE MATCHING
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

    POSSIBLE EXPLANATIONS
    Hypothesis 1: The additional 600 kg cotton was sourced from unrecorded opening warehouse inventory.
    Supporting: 20 storage bags observed in warehouse image IMG-001.
    Missing: Opening inventory stock register.

    ADDITIONAL INFORMATION REQUIRED
    1. Previous month opening inventory stock register.
    2. Additional purchase invoices if any.

    OVERALL ASSESSMENT
    Conclusion: PARTIAL MATCH
    Summary: Physical manufacturing operations are verified by machinery and production output, but stock reconciliation requires opening inventory records.
    """

    sections, status = parse_report_sections(sample_report)
    assert "BUSINESS UNDERSTANDING" in sections
    assert "EVIDENCE MATCHING" in sections
    assert "POSSIBLE EXPLANATIONS" in sections
    assert "ADDITIONAL INFORMATION REQUIRED" in sections
    assert "OVERALL ASSESSMENT" in sections
    assert status == "PARTIAL MATCH"


def test_section_parser_handles_formatted_headings_without_splitting_body_text():
    report = """
    ## **BUSINESS UNDERSTANDING**
    This company discusses the phrase OVERALL ASSESSMENT in its internal policy.

    **EVIDENCE MATCHING**
    Evidence aligns with the supplied claim.

    3. POSSIBLE EXPLANATIONS
    No material discrepancies were identified.

    ### Section 4: ADDITIONAL INFORMATION REQUIRED
    No additional records are needed.

    ## Section 5: OVERALL ASSESSMENT
    Conclusion: MATCH
    Summary: The supplied claims are supported by the available evidence.
    """

    sections, status = parse_report_sections(report)

    assert tuple(sections) == REPORT_SECTION_HEADERS
    assert "OVERALL ASSESSMENT in its internal policy" in sections["BUSINESS UNDERSTANDING"]
    assert status == "MATCH"


_COMPLETE_REPORT = """BUSINESS UNDERSTANDING
The business provides the declared products and services.

EVIDENCE MATCHING
Available records support the supplied claims.

POSSIBLE EXPLANATIONS
No material discrepancy requires an alternative explanation.

ADDITIONAL INFORMATION REQUIRED
No additional records are required for this assessment.

OVERALL ASSESSMENT
Conclusion: MATCH
Summary: The supplied claims are supported by available evidence.
"""


def _completion_result(content, finish_reason="stop"):
    return GroqCompletionResult(
        content=content,
        finish_reason=finish_reason,
        usage={
            "prompt_tokens": 20,
            "completion_tokens": 30,
            "total_tokens": 50,
        },
        model="test-model",
    )


@pytest.mark.parametrize(
    ("conclusion", "expected_status"),
    (
        ("Final conclusion is **PARTIAL MATCH** based on available records.", "PARTIAL MATCH"),
        ("Conclusion:\nINSUFFICIENT EVIDENCE", "INSUFFICIENT EVIDENCE"),
        (
            "Conclusion:\nThe available records indicate a PARTIAL MATCH.",
            "PARTIAL MATCH",
        ),
        (
            "Conclusion: MATCH / PARTIAL MATCH / MISMATCH / INSUFFICIENT EVIDENCE",
            None,
        ),
    ),
)
def test_parser_extracts_explicit_conclusion_variants(conclusion, expected_status):
    report = _COMPLETE_REPORT.replace("Conclusion: MATCH", conclusion)

    _, status = parse_report_sections(report)

    assert status == expected_status


def test_generate_returns_valid_structured_response_with_all_sections():
    with patch(
        "app.crud.inferance_crud.get_groq_completion",
        new=AsyncMock(return_value=_completion_result(_COMPLETE_REPORT)),
    ):
        response = asyncio.run(generate(ExplainRequest(text="Test case")))

    assert isinstance(response.sections, ReportSections)
    assert response.overall_assessment == "MATCH"
    response_json = response.model_dump_json(by_alias=True)
    parsed_json = json.loads(response_json)
    assert set(parsed_json["sections"]) == set(REPORT_SECTION_HEADERS)
    ExplainResponse.model_validate_json(response_json)


def test_generate_rejects_token_limited_completion():
    with patch(
        "app.crud.inferance_crud.get_groq_completion",
        new=AsyncMock(
            return_value=_completion_result(_COMPLETE_REPORT, finish_reason="length")
        ),
    ):
        with pytest.raises(HTTPException) as error:
            asyncio.run(generate(ExplainRequest(text="Test case")))

    assert error.value.status_code == 502
    assert "truncated" in error.value.detail.lower()


def test_generate_rejects_missing_report_sections():
    incomplete_report = _COMPLETE_REPORT.replace(
        "POSSIBLE EXPLANATIONS\nNo material discrepancy requires an alternative explanation.\n\n",
        "",
    )
    with patch(
        "app.crud.inferance_crud.get_groq_completion",
        new=AsyncMock(return_value=_completion_result(incomplete_report)),
    ):
        with pytest.raises(HTTPException) as error:
            asyncio.run(generate(ExplainRequest(text="Test case")))

    assert error.value.status_code == 502
    assert "POSSIBLE EXPLANATIONS" in error.value.detail


def test_generate_rejects_missing_conclusion_or_summary():
    incomplete_reports = (
        (
            _COMPLETE_REPORT.replace("Conclusion: MATCH", "Conclusion: UNKNOWN"),
            "valid Conclusion",
        ),
        (
            _COMPLETE_REPORT.replace(
                "Summary: The supplied claims are supported by available evidence.",
                "Summary:",
            ),
            "non-empty Summary",
        ),
    )

    for report, expected_error in incomplete_reports:
        with patch(
            "app.crud.inferance_crud.get_groq_completion",
            new=AsyncMock(return_value=_completion_result(report)),
        ):
            with pytest.raises(HTTPException) as error:
                asyncio.run(generate(ExplainRequest(text="Test case")))

        assert error.value.status_code == 502
        assert expected_error in error.value.detail


def test_groq_client_preserves_finish_reason_and_usage(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            return False

        async def post(self, *args, **kwargs):
            return httpx.Response(
                200,
                request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
                json={
                    "choices": [
                        {
                            "message": {"content": "Partial report"},
                            "finish_reason": "length",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 11,
                        "completion_tokens": 22,
                        "total_tokens": 33,
                    },
                },
            )

    monkeypatch.delenv("GROK_CLOUD_API", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.dependencies.grok_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    completion = asyncio.run(
        get_groq_completion(system_prompt="system", user_message="request")
    )

    assert completion.finish_reason == "length"
    assert completion.content == "Partial report"
    assert completion.usage["total_tokens"] == 33
