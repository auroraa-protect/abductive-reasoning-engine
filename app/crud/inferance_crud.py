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
from app.schemas.response_schemas import ExplainResponse, ReportSections, TokenMetrics
from app.dependencies.grok_client import get_groq_completion

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
    tokens or introduce math errors. Ground all gaps without making unsupported conclusions.
    """
    facts = []

    def _norm(text: str) -> str:
        return "".join(c for c in text.lower() if c.isalnum())

    # -----------------------------------------------------------------------
    # 1. Purchases & Procurement Totals
    # -----------------------------------------------------------------------
    total_purchase_val = 0.0
    purchased_items: Dict[str, Dict[str, Any]] = {}
    if req.purchase_evidence and req.purchase_evidence.bills:
        for bill in req.purchase_evidence.bills:
            if bill.total_amount:
                total_purchase_val += bill.total_amount
            for item in bill.items:
                nk = _norm(item.item_name)
                if nk not in purchased_items:
                    purchased_items[nk] = {
                        "name": item.item_name,
                        "qty": 0.0,
                        "unit": item.unit,
                        "val": 0.0,
                    }
                purchased_items[nk]["qty"] += item.quantity
                if item.total_amount:
                    purchased_items[nk]["val"] += item.total_amount
                if not bill.total_amount and item.total_amount:
                    total_purchase_val += item.total_amount

    # -----------------------------------------------------------------------
    # 2. Inventory on Hand
    # -----------------------------------------------------------------------
    inventory_items: Dict[str, Dict[str, Any]] = {}
    if req.inventory_evidence and req.inventory_evidence.declared_inventory:
        for it in req.inventory_evidence.declared_inventory:
            nk = _norm(it.item_name)
            inventory_items[nk] = {
                "name": it.item_name,
                "qty": float(it.quantity or 0.0),
                "unit": it.unit or "",
                "val": float(it.estimated_value or 0.0),
            }

    # -----------------------------------------------------------------------
    # 3. Raw Material Consumption vs Purchases & Closing Stock
    # -----------------------------------------------------------------------
    consumed_items: Dict[str, Dict[str, Any]] = {}
    if req.production_evidence and req.production_evidence.raw_material_consumption:
        for entry in req.production_evidence.raw_material_consumption:
            raw_m = entry.get("material") or entry.get("item_name") or "Raw Material"
            nk = _norm(raw_m)
            if nk not in consumed_items:
                consumed_items[nk] = {
                    "name": raw_m,
                    "qty": 0.0,
                    "unit": entry.get("unit", ""),
                }
            consumed_items[nk]["qty"] += float(entry.get("quantity") or 0.0)

    if consumed_items:
        for nk, c_info in consumed_items.items():
            c_name = c_info["name"]
            c_qty = c_info["qty"]
            c_unit = c_info["unit"]

            # Lookup matching purchased item
            p_match = purchased_items.get(nk)
            if not p_match:
                for pk, pv in purchased_items.items():
                    if pk in nk or nk in pk:
                        p_match = pv
                        break
            p_qty = p_match["qty"] if p_match else 0.0

            # Lookup matching inventory item
            inv_match = inventory_items.get(nk)
            if not inv_match:
                for ik, iv in inventory_items.items():
                    if ik in nk or nk in ik:
                        inv_match = iv
                        break
            inv_qty = inv_match["qty"] if inv_match else 0.0

            inv_note = f", with declared closing stock of {inv_qty:,.0f} {c_unit} on site" if inv_qty > 0 else ""
            diff = c_qty - p_qty

            if diff > 0:
                facts.append(
                    f"Raw Material Reconciliation (Deficit): Documented purchases of {c_name} are {p_qty:,.0f} {c_unit}, "
                    f"while recorded consumption is {c_qty:,.0f} {c_unit} (unreconciled difference: {diff:,.0f} {c_unit} consumed in excess of documented purchases{inv_note}). "
                    f"Without an opening stock register or prior purchase records, the source of excess material remains unverified."
                )
            elif diff < 0:
                surplus = abs(diff)
                facts.append(
                    f"Raw Material Reconciliation (Surplus): Documented purchases of {c_name} are {p_qty:,.0f} {c_unit} vs "
                    f"consumption of {c_qty:,.0f} {c_unit} ({surplus:,.0f} {c_unit} remaining unconsumed{inv_note})."
                )
            else:
                facts.append(
                    f"Raw Material Match: Documented purchases of {c_name} ({p_qty:,.0f} {c_unit}) exactly match recorded consumption{inv_note}."
                )
    elif total_purchase_val > 0:
        item_strs = [
            f"{v['qty']:,.0f} {v['unit']} of {v['name']}" for v in purchased_items.values() if v["qty"] > 0
        ]
        items_desc = f" ({', '.join(item_strs)})" if item_strs else ""
        facts.append(
            f"Documented Purchases: Total documented procurement is ₹{total_purchase_val:,.0f}{items_desc}."
        )

    # -----------------------------------------------------------------------
    # 4. Production vs Declared Output & Capacity
    # -----------------------------------------------------------------------
    declared_prod = (req.business_profile.declared_monthly_production if req.business_profile else None)
    capacity = (req.business_profile.declared_production_capacity if req.business_profile else None)
    recorded_prod = 0.0
    prod_unit = "units"
    if req.production_evidence and req.production_evidence.production_records:
        for pr in req.production_evidence.production_records:
            recorded_prod += float(pr.get("quantity") or 0.0)
            if pr.get("unit"):
                prod_unit = pr.get("unit")

    if recorded_prod > 0 and declared_prod:
        if recorded_prod == declared_prod:
            facts.append(
                f"Production Alignment: Recorded production ({recorded_prod:,.0f} {prod_unit}) exactly matches declared monthly production ({declared_prod:,.0f} {prod_unit})."
            )
        else:
            p_diff = abs(recorded_prod - declared_prod)
            p_pct = (p_diff / declared_prod) * 100
            facts.append(
                f"Production Variance: Recorded production ({recorded_prod:,.0f} {prod_unit}) vs declared monthly production ({declared_prod:,.0f} {prod_unit}) "
                f"(variance of {p_diff:,.0f} {prod_unit} / {p_pct:.1f}%)."
            )

    if recorded_prod > 0 and capacity and capacity > 0:
        util = (recorded_prod / capacity) * 100
        facts.append(
            f"Capacity Utilization: Operating at {util:.1f}% of declared monthly capacity ({recorded_prod:,.0f} / {capacity:,.0f} {prod_unit})."
        )

    # -----------------------------------------------------------------------
    # 5. Sales Invoices vs Declared Turnover
    # -----------------------------------------------------------------------
    total_sales = 0.0
    n_sales_bills = 0
    if req.sales_evidence and req.sales_evidence.sales_bills:
        total_sales = sum(float(b.get("total_amount") or 0.0) for b in req.sales_evidence.sales_bills)
        n_sales_bills = len(req.sales_evidence.sales_bills)
    elif req.sales_evidence and req.sales_evidence.sales_summary:
        total_sales = float(req.sales_evidence.sales_summary.get("total_sales_value") or 0.0)
        n_sales_bills = 1

    declared_turnover = (req.business_profile.declared_monthly_turnover if req.business_profile else None)
    if declared_turnover and declared_turnover > 0:
        if total_sales > 0:
            sales_gap = declared_turnover - total_sales
            coverage = (total_sales / declared_turnover) * 100
            if abs(sales_gap) < 1:
                facts.append(
                    f"Turnover Reconciliation (Full Match): Documented sales invoices (₹{total_sales:,.0f}) exactly match declared monthly turnover."
                )
            elif sales_gap > 0:
                facts.append(
                    f"Sales vs Declared Turnover Gap: Documented sales total ₹{total_sales:,.0f} across {n_sales_bills} bill(s), "
                    f"representing {coverage:.1f}% of declared monthly turnover of ₹{declared_turnover:,.0f} "
                    f"(documentation gap: ₹{sales_gap:,.0f}). The submitted records represent a partial sample of total declared business volume."
                )
            else:
                excess_sales = abs(sales_gap)
                facts.append(
                    f"Sales vs Declared Turnover: Documented sales invoices (₹{total_sales:,.0f}) exceed declared monthly turnover (₹{declared_turnover:,.0f}) by ₹{excess_sales:,.0f}."
                )
        else:
            facts.append(
                f"Sales Invoices Unverified: Declared monthly turnover is ₹{declared_turnover:,.0f}, but zero itemized sales bills are submitted in the file."
            )

    # -----------------------------------------------------------------------
    # 6. Commercial / Trading Gross Margin (when both sales and purchases exist)
    # -----------------------------------------------------------------------
    if total_sales > 0 and total_purchase_val > 0 and not consumed_items:
        spread = total_sales - total_purchase_val
        margin_pct = (spread / total_sales) * 100
        facts.append(
            f"Commercial Spread / Trading Margin: Documented sales (₹{total_sales:,.0f}) against documented purchases (₹{total_purchase_val:,.0f}) "
            f"indicates an operating gross spread of ₹{spread:,.0f} ({margin_pct:.1f}% gross margin on sales)."
        )

    # -----------------------------------------------------------------------
    # 7. GST Records Reconciliation
    # -----------------------------------------------------------------------
    gst_turnover = 0.0
    gst_period = None
    if req.financial_evidence and req.financial_evidence.gst_records:
        for gst in req.financial_evidence.gst_records:
            gst_turnover += float(gst.get("declared_turnover") or 0.0)
            if gst.get("period"):
                gst_period = gst.get("period")

    if gst_turnover > 0:
        period_str = f" for period {gst_period}" if gst_period else ""
        if declared_turnover and declared_turnover > 0:
            if abs(gst_turnover - declared_turnover) < 1:
                facts.append(
                    f"GST vs Declared Turnover (Alignment): GST return{period_str} declares turnover of ₹{gst_turnover:,.0f}, "
                    f"which aligns 100% with declared business turnover (₹{declared_turnover:,.0f})."
                )
            else:
                gst_diff = abs(declared_turnover - gst_turnover)
                facts.append(
                    f"GST vs Declared Turnover (Variance): GST return{period_str} reports ₹{gst_turnover:,.0f} vs declared business turnover of ₹{declared_turnover:,.0f} "
                    f"(variance of ₹{gst_diff:,.0f})."
                )

        if total_sales > 0:
            if abs(gst_turnover - total_sales) < 1:
                facts.append(
                    f"GST vs Sales Invoices (Alignment): GST return turnover (₹{gst_turnover:,.0f}) exactly matches documented sales invoices."
                )
            elif gst_turnover > total_sales:
                gst_sales_gap = gst_turnover - total_sales
                facts.append(
                    f"GST vs Sales Invoices (Sample Gap): GST turnover (₹{gst_turnover:,.0f}) exceeds documented sales invoices (₹{total_sales:,.0f}) by ₹{gst_sales_gap:,.0f}. "
                    f"Documented invoices account for {(total_sales/gst_turnover)*100:.1f}% of GST-reported activity."
                )
            else:
                facts.append(
                    f"GST vs Sales Invoices: Documented sales invoices (₹{total_sales:,.0f}) exceed GST reported turnover (₹{gst_turnover:,.0f}) by ₹{abs(total_sales - gst_turnover):,.0f}."
                )

    # -----------------------------------------------------------------------
    # 8. Banking Cash-Flow Reconciliation
    # -----------------------------------------------------------------------
    bank_credits = 0.0
    bank_debits = 0.0
    if req.financial_evidence and req.financial_evidence.bank_transactions:
        for tx in req.financial_evidence.bank_transactions:
            ttype = (tx.get("transaction_type") or "").lower()
            amt = float(tx.get("amount") or 0.0)
            if ttype == "credit":
                bank_credits += amt
            elif ttype == "debit":
                bank_debits += amt

    if bank_credits > 0:
        if total_sales > 0:
            if abs(bank_credits - total_sales) < 1:
                facts.append(
                    f"Banking vs Sales Match: Documented bank credits (₹{bank_credits:,.0f}) exactly match documented sales invoices "
                    f"(100% collection reconciliation for submitted invoices)."
                )
            elif bank_credits < total_sales:
                uncollected = total_sales - bank_credits
                col_pct = (bank_credits / total_sales) * 100
                facts.append(
                    f"Banking vs Sales (Receivables Gap): Documented bank credits of ₹{bank_credits:,.0f} cover {col_pct:.1f}% of documented sales (₹{total_sales:,.0f}). "
                    f"The difference of ₹{uncollected:,.0f} reflects outstanding trade receivables, unbanked cash collections, or payment timing differences."
                )
            else:
                excess_credit = bank_credits - total_sales
                facts.append(
                    f"Banking vs Sales (Excess Credits): Documented bank credits (₹{bank_credits:,.0f}) exceed documented sales invoices (₹{total_sales:,.0f}) by ₹{excess_credit:,.0f}. "
                    f"This may reflect customer advances, collections on older invoices, or non-operating receipts."
                )

        if declared_turnover and declared_turnover > 0:
            bank_cov = (bank_credits / declared_turnover) * 100
            facts.append(
                f"Bank Turnover Coverage: Documented bank credits (₹{bank_credits:,.0f}) reflect {bank_cov:.1f}% of declared monthly turnover (₹{declared_turnover:,.0f})."
            )

    # -----------------------------------------------------------------------
    # 9. Physical Assets & Utilities
    # -----------------------------------------------------------------------
    if req.physical_evidence and req.physical_evidence.machinery_analysis:
        for m in req.physical_evidence.machinery_analysis:
            facts.append(
                f"Physical Equipment: {m.get('observed_count', 1)} unit(s) of {m.get('machine_name', 'Machinery')} observed in '{m.get('condition', 'operational')}' condition."
            )

    if req.financial_evidence and req.financial_evidence.electricity_bills:
        for eb in req.financial_evidence.electricity_bills:
            facts.append(
                f"Utility Consumption: {eb.get('units_consumed', 0):,} electricity units consumed (Bill: ₹{eb.get('bill_amount', 0):,}) for period {eb.get('billing_month', 'N/A')}."
            )

    return facts


# ---------------------------------------------------------------------------
# Input Payload Synthesis
# ---------------------------------------------------------------------------
def build_user_payload(req: ExplainRequest) -> str:
    """
    Format case details so declared claims and observed evidence are clearly
    distinguishable, with pre-computed facts appended.
    """
    parts = []

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
            obs_lines.append(f"Purchase Bill: From {b.supplier_name or 'Supplier'} on {b.invoice_date or 'N/A'} ({items_str}, Total: ₹{b.total_amount or 0:,.0f})")

    if req.inventory_evidence:
        if req.inventory_evidence.declared_inventory:
            inv_str = ", ".join(f"{item.quantity or 0:,.0f} {item.unit or ''} {item.item_name}" for item in req.inventory_evidence.declared_inventory)
            obs_lines.append(f"Declared Inventory: {inv_str}")
        if req.inventory_evidence.image_analysis:
            for img in req.inventory_evidence.image_analysis:
                objs = ", ".join(f"{o.estimated_count or 0} {o.object}" for o in img.observed_objects)
                obs_lines.append(f"Inventory Visual Evidence: Observed {objs}. Notes: {'; '.join(img.observations)}")

    if req.production_evidence:
        pe = req.production_evidence
        for pr in pe.production_records:
            obs_lines.append(f"Production Record: {pr.get('quantity', 0):,} {pr.get('unit', '')} of {pr.get('product', '')} on {pr.get('date', 'N/A')}")
        for rmc in pe.raw_material_consumption:
            obs_lines.append(f"Material Consumption: {rmc.get('quantity', 0):,} {rmc.get('unit', '')} of {rmc.get('material', rmc.get('item_name', ''))}")

    if req.sales_evidence:
        se = req.sales_evidence
        for sb in se.sales_bills:
            obs_lines.append(f"Sales Invoice: To {sb.get('customer_name', 'Customer')} on {sb.get('invoice_date', 'N/A')} for ₹{sb.get('total_amount', 0):,.0f}")
        if se.sales_summary:
            obs_lines.append(f"Sales Summary: Total ₹{se.sales_summary.get('total_sales_value', 0):,.0f} for period {se.sales_summary.get('period', 'N/A')}")

    if req.physical_evidence:
        phy = req.physical_evidence
        for v in phy.video_analysis:
            obs_lines.append(f"Video Inspection: {v.duration_seconds or 0}s duration. Observed: {', '.join(v.observed_activities)}. Machinery: {', '.join(v.observed_machinery)}")
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
        parts.append(
            "\n=== ABDUCTIVE HYPOTHESIS DIRECTIVE ===\n"
            "- Focus on the primary 2 to 3 material discrepancies; formulate 2 to 3 competing, plausible commercial/operational explanations for each.\n"
            "- Keep table cells strictly concise (1-2 sentences, under 35 words per cell) so all 5 sections finish cleanly without truncation.\n"
            "- Actively consider real-world MSME conditions: opening inventory, informal trade credit (30-90 days), walk-in cash transactions, batching, and reporting cutoffs.\n"
            "- Never speculate on fraud, tax evasion, shell operations, or bad faith without explicit forensic proof."
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section Parser Helpers
# ---------------------------------------------------------------------------
REPORT_SECTION_HEADERS = (
    "BUSINESS UNDERSTANDING",
    "EVIDENCE MATCHING",
    "POSSIBLE EXPLANATIONS",
    "ADDITIONAL INFORMATION REQUIRED",
    "OVERALL ASSESSMENT",
)

_SECTION_HEADER_RE = re.compile(
    rf"^[ \t]*(?:#{{1,6}}[ \t]*)?(?:\*\*|__)?"
    rf"(?:(?:SECTION[ \t]+\d+[ \t]*[:.)-]?[ \t]*)|(?:\d+[ \t]*[.)][ \t]*))?"
    rf"(?P<header>{'|'.join(re.escape(header) for header in REPORT_SECTION_HEADERS)})"
    rf"(?:\*\*|__)?[ \t]*:?[ \t]*$",
    flags=re.IGNORECASE | re.MULTILINE,
)

_ASSESSMENT_STATUS_RE = re.compile(
    r"\b(INSUFFICIENT EVIDENCE|PARTIAL MATCH|MISMATCH|MATCH)\b",
    flags=re.IGNORECASE,
)
_ASSESSMENT_LABEL_RE = re.compile(
    r"\b(?:final\s+)?(?:overall\s+)?"
    r"(?:conclusion|assessment|verdict|decision)\b",
    flags=re.IGNORECASE,
)


def _extract_overall_status(overall_text: str) -> Optional[str]:
    for label in _ASSESSMENT_LABEL_RE.finditer(overall_text):
        remainder = overall_text[label.end():]
        first_line, separator, following_text = remainder.partition("\n")
        candidate = first_line.strip(" \t:*_`-–—")
        candidate = re.sub(r"^(?:is\b\s*)?(?:a\b\s*)?", "", candidate, flags=re.IGNORECASE)

        direct_match = _ASSESSMENT_STATUS_RE.match(candidate)
        if direct_match:
            next_status = re.match(
                r"\s*[/,]\s*(?:INSUFFICIENT EVIDENCE|PARTIAL MATCH|MISMATCH|MATCH)\b",
                candidate[direct_match.end():],
                flags=re.IGNORECASE,
            )
            if next_status:
                return None
            return direct_match.group(1).upper()

        line_statuses = list(_ASSESSMENT_STATUS_RE.finditer(first_line))
        unique_statuses = {match.group(1).upper() for match in line_statuses}
        if len(unique_statuses) == 1:
            return unique_statuses.pop()
        if len(unique_statuses) > 1:
            return None

        if not candidate and separator:
            next_line = following_text.splitlines()[0] if following_text else ""
            next_line = next_line.strip(" \t:*_`-–—")
            next_statuses = {
                match.group(1).upper()
                for match in _ASSESSMENT_STATUS_RE.finditer(next_line)
            }
            if len(next_statuses) == 1:
                return next_statuses.pop()
            if len(next_statuses) > 1:
                return None

    first_content_line = next(
        (line.strip(" \t*`#") for line in overall_text.splitlines() if line.strip()),
        "",
    )
    status_match = _ASSESSMENT_STATUS_RE.match(first_content_line)
    return status_match.group(1).upper() if status_match else None


def parse_report_sections(report_text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Split a report using standalone section-heading lines."""
    matches = list(_SECTION_HEADER_RE.finditer(report_text))
    sections: Dict[str, str] = {}
    for index, match in enumerate(matches):
        header = match.group("header").upper()
        if header in sections:
            raise ValueError(f"Report contains a duplicate section: {header}.")

        end = matches[index + 1].start() if index + 1 < len(matches) else len(report_text)
        sections[header] = report_text[match.end():end].strip()

    overall_status = _extract_overall_status(sections.get("OVERALL ASSESSMENT", ""))
    return sections, overall_status


def validate_report_sections(
    report_text: str,
) -> Tuple[Dict[str, str], str]:
    """Require all five non-empty sections and an explicit conclusion and summary."""
    sections, overall_status = parse_report_sections(report_text)
    missing = [
        header for header in REPORT_SECTION_HEADERS if not sections.get(header, "").strip()
    ]
    if missing:
        raise ValueError(
            "LLM report is incomplete; missing or empty sections: "
            + ", ".join(missing)
        )

    if overall_status is None:
        raise ValueError(
            "LLM report is incomplete; OVERALL ASSESSMENT must contain a valid Conclusion."
        )

    summary = re.search(
        r"(?:\*\*)?Summary(?:\*\*)?\s*:\s*(?:\*\*)?(\S[\s\S]*)",
        sections["OVERALL ASSESSMENT"],
        flags=re.IGNORECASE,
    )
    if summary is None:
        raise ValueError(
            "LLM report is incomplete; OVERALL ASSESSMENT must contain a non-empty Summary."
        )

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
    completion = await get_groq_completion(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="text",
        max_tokens=6000,
        temperature=0.0,
    )
    latency_ms = round((time.perf_counter() - t_start) * 1000)

    # Collect usage metrics
    usage = completion.usage
    token_metrics = TokenMetrics(
        model=completion.model,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        latency_ms=latency_ms,
        inference_calls=1,
    )

    # Record in history log
    _token_history.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        **token_metrics.model_dump(),
    })

    report = completion.content
    try:
        sections, overall_status = validate_report_sections(report)
    except ValueError as error:
        if completion.finish_reason == "length":
            detail = (
                "LLM response was truncated after reaching the completion token limit. "
                "The report could not be fully generated."
            )
        else:
            reason = completion.finish_reason or "missing"
            detail = f"LLM report validation failed: {str(error)} (finish_reason={reason})."
        raise HTTPException(status_code=502, detail=detail) from error

    return ExplainResponse(
        status="completed",
        overall_assessment=overall_status,
        report=report,
        token_usage=token_metrics,
        sections=ReportSections(**sections),
    )
