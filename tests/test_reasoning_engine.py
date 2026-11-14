"""
Unit and regression tests for Auroraa Abductive Reasoning Engine.
Tests deterministic math calculations, payload synthesis, section parsing,
and multi-industry case handling.
"""

import os
import json
import pytest
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
from app.schemas.response_schemas import ExplainResponse, TokenMetrics
from app.crud.inferance_crud import (
    compute_deterministic_reconciliations,
    build_user_payload,
    parse_report_sections,
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
                    bill_id="PUR-201",
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
                {"invoice_number": "SEL-101", "customer_name": "Retail Hub Delhi", "total_amount": 1500000},
                {"invoice_number": "SEL-102", "customer_name": "Metro Gadgets", "total_amount": 1200000},
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
