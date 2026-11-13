"""
Inference CRUD Module
---------------------
Orchestrates lightweight, token-optimized abductive reasoning for MSME business verification.
- Performs deterministic Python arithmetic for reconciliations.
- Formats input to cleanly distinguish declared claims from observed evidence.
- Executes a single LLM inference call with concise prompt.
- Returns a structured, human-readable 5-section verification report with token tracking.
"""

import os
import re
import time
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException

from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplainResponse, TokenMetrics
from app.dependencies.grok_client import get_groq_completion, get_last_usage

# ---------------------------------------------------------------------------
# Global Token Tracker Log
# ---------------------------------------------------------------------------
_token_history: list[dict] = []


def get_token_history() -> list[dict]:
    """Retrieve full history of inference calls and token consumption."""
    return list(_token_history)


def clear_token_history() -> None:
    """Clear inference history."""
    _token_history.clear()


# ---------------------------------------------------------------------------
# Deterministic Arithmetic Pre-calculations
# ---------------------------------------------------------------------------
def compute_deterministic_reconciliations(req: ExplainRequest) -> list[str]:
    """
    Perform exact Python arithmetic for reconciliations so the LLM doesn't waste
    tokens or introduce math errors.
    """
    facts = []

    # 1. Purchase totals
    total_purchase_qty: Dict[str, float] = {}
    total_purchase_val = 0.0
    if req.purchase_evidence and req.purchase_evidence.bills:
        for bill in req.purchase_evidence.bills:
            if bill.total_amount:
                total_purchase_val += bill.total_amount
            for item in bill.items:
                total_purchase_qty[item.item_name] = (
                    total_purchase_qty.get(item.item_name, 0.0) + item.quantity
                )
                if not bill.total_amount and item.total_amount:
                    total_purchase_val += item.total_amount

    # 2. Raw material consumption
    total_consumed_qty: Dict[str, float] = {}
    if req.production_evidence and req.production_evidence.raw_material_consumption:
        for entry in req.production_evidence.raw_material_consumption:
            mat = entry.get("material") or entry.get("item_name") or "Raw Material"
            qty = float(entry.get("quantity") or 0.0)
            total_consumed_qty[mat] = total_consumed_qty.get(mat, 0.0) + qty

    # Compare purchases vs consumption
    if total_consumed_qty and total_purchase_qty:
        for mat, c_qty in total_consumed_qty.items():
            p_qty = total_purchase_qty.get(mat, 0.0)
            diff = c_qty - p_qty
            if diff > 0:
                facts.append(
                    f"Material Deficit: Documented purchases of {mat} are {p_qty:,.0f} units, "
                    f"but recorded consumption is {c_qty:,.0f} units ({diff:,.0f} units consumed in excess of documented purchases)."
                )
            elif diff < 0:
                facts.append(
                    f"Material Surplus: Documented purchases of {mat} are {p_qty:,.0f} units vs "
                    f"consumption of {c_qty:,.0f} units ({abs(diff):,.0f} units remaining or in stock)."
                )
            else:
                facts.append(f"Material Match: Documented purchases of {mat} exactly match consumption ({p_qty:,.0f} units).")

    # 3. Production vs Capacity & Declared
    declared_prod = (req.business_profile.declared_monthly_production if req.business_profile else None)
    capacity = (req.business_profile.declared_production_capacity if req.business_profile else None)
    recorded_prod = 0.0
    if req.production_evidence and req.production_evidence.production_records:
        for pr in req.production_evidence.production_records:
            recorded_prod += float(pr.get("quantity") or 0.0)

    if recorded_prod > 0 and declared_prod:
        if recorded_prod == declared_prod:
            facts.append(f"Production Match: Recorded production ({recorded_prod:,.0f} units) exactly matches declared monthly production ({declared_prod:,.0f} units).")
        else:
            facts.append(f"Production Variance: Recorded production ({recorded_prod:,.0f} units) vs declared production ({declared_prod:,.0f} units).")

    if recorded_prod > 0 and capacity and capacity > 0:
        util = (recorded_prod / capacity) * 100
        facts.append(f"Capacity Utilization: Operating at {util:.1f}% of declared capacity ({recorded_prod:,.0f} / {capacity:,.0f} units).")

    # 4. Sales invoices vs Declared turnover
    total_sales = 0.0
    if req.sales_evidence and req.sales_evidence.sales_bills:
        total_sales = sum(float(b.get("total_amount") or 0.0) for b in req.sales_evidence.sales_bills)
    elif req.sales_evidence and req.sales_evidence.sales_summary:
        total_sales = float(req.sales_evidence.sales_summary.get("total_sales_value") or 0.0)

    declared_turnover = (req.business_profile.declared_monthly_turnover if req.business_profile else None)
    if declared_turnover and total_sales > 0:
        gap = declared_turnover - total_sales
        facts.append(
            f"Turnover Disparity: Declared monthly turnover is ₹{declared_turnover:,.0f}, "
            f"while documented sales invoices total ₹{total_sales:,.0f} (Gap: ₹{gap:,.0f} / {(total_sales/declared_turnover)*100:.1f}% documented)."
        )

    # 5. Bank transactions vs Sales bills
    bank_credits = 0.0
    if req.financial_evidence and req.financial_evidence.bank_transactions:
        for tx in req.financial_evidence.bank_transactions:
            if tx.get("transaction_type") == "credit":
                bank_credits += float(tx.get("amount") or 0.0)

    if bank_credits > 0 and total_sales > 0:
        if bank_credits == total_sales:
            facts.append(f"Banking Match: Documented bank credits (₹{bank_credits:,.0f}) exactly match documented sales invoices (₹{total_sales:,.0f}).")
        else:
            facts.append(f"Banking Comparison: Documented bank credits are ₹{bank_credits:,.0f} vs documented sales of ₹{total_sales:,.0f}.")

    # 6. Physical equipment & electricity
    if req.physical_evidence and req.physical_evidence.machinery_analysis:
        for m in req.physical_evidence.machinery_analysis:
            facts.append(f"Physical Equipment: {m.get('observed_count', 1)} unit(s) of {m.get('machine_name', 'Machinery')} observed in '{m.get('condition', 'operational')}' condition.")

    if req.financial_evidence and req.financial_evidence.electricity_bills:
        for eb in req.financial_evidence.electricity_bills:
            facts.append(f"Utility Consumption: {eb.get('units_consumed', 0):,} electricity units consumed (Bill: ₹{eb.get('bill_amount', 0):,}) for period {eb.get('billing_month', 'N/A')}.")

    return facts


# ---------------------------------------------------------------------------
# Input Payload Synthesis
# ---------------------------------------------------------------------------
def build_user_payload(req: ExplainRequest) -> str:
    """
    Format case details so declared claims and observed evidence are clearly
    distinguishable, with pre-computed facts appended.
    """
    parts = [f"CASE IDENTIFIER: {req.case_id}"]

    # 1. Natural language direct text if supplied
    if req.text:
        parts.append(f"\n=== CASE NARRATIVE & INPUT EVIDENCE ===\n{req.text.strip()}")

    if req.declared_information:
        parts.append(f"\n=== DECLARED BUSINESS CLAIMS ===\n{req.declared_information}")

    if req.observed_evidence:
        parts.append(f"\n=== OBSERVED EVIDENCE & RECORDS ===\n{req.observed_evidence}")

    # 2. Structured Profile
    if req.business_profile:
        bp = req.business_profile
        parts.append(
            f"\n=== DECLARED BUSINESS PROFILE ===\n"
            f"- Business Name: {bp.business_name or 'N/A'}\n"
            f"- Industry / Activity: {bp.industry or 'N/A'} ({bp.business_activity or bp.business_type or 'N/A'})\n"
            f"- Age: {bp.business_age_years or 'N/A'} years | Employees: {bp.number_of_employees or 'N/A'}\n"
            f"- Declared Monthly Turnover: ₹{bp.declared_monthly_turnover:,.0f}" if bp.declared_monthly_turnover else ""
        )
        if bp.declared_monthly_production:
            parts.append(f"- Declared Monthly Production: {bp.declared_monthly_production:,.0f} units")
        if bp.declared_production_capacity:
            parts.append(f"- Declared Production Capacity: {bp.declared_production_capacity:,.0f} units/month")

    # 3. Structured Observed Evidence
    obs_lines = []
    if req.purchase_evidence and req.purchase_evidence.bills:
        for b in req.purchase_evidence.bills:
            items_str = ", ".join(f"{it.quantity:,.0f} {it.unit} of {it.item_name} @ ₹{it.unit_price or 0}/unit" for it in b.items)
            obs_lines.append(f"Purchase Bill [{b.bill_id or 'PUR'}]: From {b.supplier_name or 'Supplier'} on {b.invoice_date or 'N/A'} ({items_str}, Total: ₹{b.total_amount or 0:,.0f})")

    if req.inventory_evidence:
        if req.inventory_evidence.declared_inventory:
            inv_str = ", ".join(f"{item.quantity or 0:,.0f} {item.unit or ''} {item.item_name}" for item in req.inventory_evidence.declared_inventory)
            obs_lines.append(f"Declared Inventory: {inv_str}")
        if req.inventory_evidence.image_analysis:
            for img in req.inventory_evidence.image_analysis:
                objs = ", ".join(f"{o.estimated_count or 0} {o.object}" for o in img.observed_objects)
                obs_lines.append(f"Inventory Visual Evidence [{img.evidence_id or 'IMG'}]: Observed {objs}. Notes: {'; '.join(img.observations)}")

    if req.production_evidence:
        pe = req.production_evidence
        for pr in pe.production_records:
            obs_lines.append(f"Production Record: {pr.get('quantity', 0):,} {pr.get('unit', '')} of {pr.get('product', '')} on {pr.get('date', 'N/A')}")
        for rmc in pe.raw_material_consumption:
            obs_lines.append(f"Material Consumption: {rmc.get('quantity', 0):,} {rmc.get('unit', '')} of {rmc.get('material', rmc.get('item_name', ''))}")

    if req.sales_evidence:
        se = req.sales_evidence
        for sb in se.sales_bills:
            obs_lines.append(f"Sales Invoice [{sb.get('invoice_number', 'SALE')}]: To {sb.get('customer_name', 'Customer')} on {sb.get('invoice_date', 'N/A')} for ₹{sb.get('total_amount', 0):,.0f}")
        if se.sales_summary:
            obs_lines.append(f"Sales Summary: Total ₹{se.sales_summary.get('total_sales_value', 0):,.0f} for period {se.sales_summary.get('period', 'N/A')}")

    if req.physical_evidence:
        phy = req.physical_evidence
        for v in phy.video_analysis:
            obs_lines.append(f"Video Inspection [{v.evidence_id or 'VID'}]: {v.duration_seconds or 0}s duration. Observed: {', '.join(v.observed_activities)}. Machinery: {', '.join(v.observed_machinery)}")
        for m in phy.machinery_analysis:
            obs_lines.append(f"Machinery Analysis: {m.get('observed_count', 1)} {m.get('machine_name', '')} in condition '{m.get('condition', '')}'")

    if req.financial_evidence:
        fe = req.financial_evidence
        for tx in fe.bank_transactions:
            obs_lines.append(f"Bank Transaction: {tx.get('transaction_date', 'N/A')} {tx.get('transaction_type', '')} of ₹{tx.get('amount', 0):,.0f} ({tx.get('description', '')})")
        for eb in fe.electricity_bills:
            obs_lines.append(f"Electricity Bill: Period {eb.get('billing_month', 'N/A')}: {eb.get('units_consumed', 0):,} units, Bill: ₹{eb.get('bill_amount', 0):,.0f}")
        for gst in fe.gst_records:
            obs_lines.append(f"GST Record: Period {gst.get('period', 'N/A')}: Declared turnover ₹{gst.get('declared_turnover', 0):,.0f}")

    if req.additional_evidence and req.additional_evidence.observations:
        for obs in req.additional_evidence.observations:
            obs_lines.append(f"Additional Field Observation: {obs}")

    if obs_lines:
        parts.append("\n=== OBSERVED EVIDENCE & RECORDS ===\n" + "\n".join(f"- {line}" for line in obs_lines))

    # 4. Deterministic Pre-calculated Reconciliations
    facts = compute_deterministic_reconciliations(req)
    if facts:
        parts.append(
            "\n=== DETERMINISTIC FACT CHECK (Python-Verified Math) ===\n"
            + "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(facts))
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section Parser Helper
# ---------------------------------------------------------------------------
def parse_report_sections(report_text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Parse the 5 standardized report sections and overall assessment."""
    headers = [
        "BUSINESS UNDERSTANDING",
        "EVIDENCE MATCHING",
        "POSSIBLE EXPLANATIONS",
        "ADDITIONAL INFORMATION REQUIRED",
        "OVERALL ASSESSMENT",
    ]
    pattern = rf"({'|'.join(re.escape(h) for h in headers)})"
    splits = re.split(pattern, report_text, flags=re.IGNORECASE)

    sections: Dict[str, str] = {}
    current_header = "INTRODUCTION"
    for part in splits:
        clean_part = part.strip()
        matched = False
        for h in headers:
            if clean_part.upper() == h:
                current_header = h
                matched = True
                break
        if not matched and clean_part:
            sections[current_header] = clean_part

    # Extract overall assessment status
    overall_text = sections.get("OVERALL ASSESSMENT", "")
    overall_status = None
    for cand in ["INSUFFICIENT EVIDENCE", "PARTIAL MATCH", "MISMATCH", "MATCH"]:
        if cand in overall_text.upper():
            overall_status = cand
            break

    return sections, overall_status


# ---------------------------------------------------------------------------
# Main Orchestration Function
# ---------------------------------------------------------------------------
async def generate(request: ExplainRequest) -> ExplainResponse:
    """
    Generate an abductive reasoning explanation report for an MSME verification case.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read system prompt: {str(e)}")

    # Build concise, distinction-preserving user payload with pre-computed math
    user_message = build_user_payload(request)

    t_start = time.perf_counter()
    report = await get_groq_completion(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="text",
        max_tokens=2000,
        temperature=0.0,
    )
    latency_ms = round((time.perf_counter() - t_start) * 1000)

    # Collect usage metrics
    usage = get_last_usage()
    token_metrics = TokenMetrics(
        model=usage.get("model", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")),
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        latency_ms=latency_ms,
        inference_calls=1,
    )

    # Record in history log
    _token_history.append({
        "case_id": request.case_id or "CASE-001",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        **token_metrics.model_dump(),
    })

    # Parse sections
    sections, overall_status = parse_report_sections(report)

    return ExplainResponse(
        case_id=request.case_id or "CASE-001",
        status="completed",
        overall_assessment=overall_status,
        report=report,
        token_usage=token_metrics,
        sections=sections,
    )
