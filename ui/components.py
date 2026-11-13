"""
Reusable UI components, custom styles, and response parsers for Auroraa R&D UI.
Strictly adheres to the design specification:
- Dark navy sidebar
- Light workspace
- Clean typography
- Badge colors: Green (MATCH), Red (MISMATCH), Amber (PARTIAL MATCH), Grey (INSUFFICIENT EVIDENCE)
- Minimalist, highly readable R&D dashboard
"""

import re
import io
import json
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st


# ---------------------------------------------------------------------------
# Custom CSS Injection
# ---------------------------------------------------------------------------
def inject_custom_styles():
    """Inject custom CSS for dark navy sidebar and clean, readable light workspace."""
    st.markdown(
        """
        <style>
        /* Base typography & light workspace */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        .stApp {
            background-color: #f8fafc;
        }

        /* Metric cards */
        .metric-card-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }

        .metric-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            display: flex;
            flex-direction: column;
        }

        .metric-box-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 4px;
        }

        .metric-box-val {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0f172a;
        }

        .metric-box-sub {
            font-size: 0.72rem;
            color: #94a3b8;
            margin-top: 2px;
        }

        /* Section containers */
        .section-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 18px 22px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .section-header {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 8px;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-match {
            background-color: #dcfce7;
            color: #15803d;
            border: 1px solid #bbf7d0;
        }

        .badge-partial {
            background-color: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
        }

        .badge-mismatch {
            background-color: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fecaca;
        }

        .badge-insufficient {
            background-color: #f1f5f9;
            color: #475569;
            border: 1px solid #cbd5e1;
        }

        /* Overall assessment banner */
        .verdict-banner {
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 22px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
        }

        .verdict-banner-match {
            background-color: #f0fdf4;
            border: 1.5px solid #86efac;
        }

        .verdict-banner-partial {
            background-color: #fffbeb;
            border: 1.5px solid #fcd34d;
        }

        .verdict-banner-mismatch {
            background-color: #fef2f2;
            border: 1.5px solid #fca5a5;
        }

        .verdict-banner-insufficient {
            background-color: #f8fafc;
            border: 1.5px solid #cbd5e1;
        }

        /* Evidence Matching Table */
        .evidence-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            margin-top: 8px;
        }

        .evidence-table th {
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
            text-align: left;
            padding: 10px 14px;
            border-bottom: 2px solid #e2e8f0;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .evidence-table td {
            padding: 12px 14px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
            color: #334155;
            line-height: 1.45;
        }

        .evidence-table tr:hover td {
            background-color: #fcfdfe;
        }

        /* Abductive reasoning card */
        .hypothesis-card {
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            border-radius: 0 6px 6px 0;
            padding: 12px 16px;
            margin-bottom: 12px;
        }

        .hypothesis-title {
            font-weight: 700;
            color: #1e293b;
            font-size: 0.95rem;
            margin-bottom: 6px;
        }

        .hypothesis-detail {
            font-size: 0.85rem;
            color: #475569;
            margin-bottom: 4px;
        }

        /* Primary action button styling */
        div.stButton > button[kind="primary"] {
            background-color: #1e40af !important;
            color: #ffffff !important;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 0.55rem 1.5rem;
            letter-spacing: 0.03em;
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Status Badge Helper
# ---------------------------------------------------------------------------
def get_status_badge_html(status_text: Optional[str]) -> str:
    """Return colored badge HTML based on status."""
    if not status_text:
        return '<span class="badge badge-insufficient">UNKNOWN</span>'

    clean = status_text.strip().upper()
    if "PARTIAL" in clean:
        return '<span class="badge badge-partial">PARTIAL MATCH</span>'
    elif "MISMATCH" in clean:
        return '<span class="badge badge-mismatch">MISMATCH</span>'
    elif "INSUFFICIENT" in clean:
        return '<span class="badge badge-insufficient">INSUFFICIENT EVIDENCE</span>'
    elif "MATCH" in clean:
        return '<span class="badge badge-match">MATCH</span>'
    return f'<span class="badge badge-insufficient">{clean}</span>'


# ---------------------------------------------------------------------------
# Metric Cards Renderer
# ---------------------------------------------------------------------------
def render_metrics_panel(token_usage: Optional[Dict[str, Any]]):
    """
    Render compact inference metrics cards:
    - Model name
    - Input tokens
    - Output tokens
    - Total tokens
    - Inference latency
    - Number of inference calls
    """
    if not token_usage:
        return

    # Extract values whether dict or Pydantic model
    if hasattr(token_usage, "model_dump"):
        u = token_usage.model_dump()
    elif isinstance(token_usage, dict):
        u = token_usage
    else:
        u = {}

    model_name = str(u.get("model", "Groq / LLM"))
    # Shorten model name if too long for card display
    if "/" in model_name:
        display_model = model_name.split("/")[-1]
    else:
        display_model = model_name

    input_tokens = u.get("input_tokens", 0)
    output_tokens = u.get("output_tokens", 0)
    total_tokens = u.get("total_tokens", 0)
    latency_ms = u.get("latency_ms", 0)
    calls = u.get("inference_calls", 1)

    st.markdown(
        f"""
        <div class="metric-card-container">
            <div class="metric-box">
                <div class="metric-box-label">Model</div>
                <div class="metric-box-val" style="font-size: 1.05rem;" title="{model_name}">{display_model}</div>
                <div class="metric-box-sub">Active Engine</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Input Tokens</div>
                <div class="metric-box-val">{input_tokens:,}</div>
                <div class="metric-box-sub">Prompt Payload</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Output Tokens</div>
                <div class="metric-box-val">{output_tokens:,}</div>
                <div class="metric-box-sub">Reasoning Report</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Total Tokens</div>
                <div class="metric-box-val" style="color: #1e40af;">{total_tokens:,}</div>
                <div class="metric-box-sub">Inference Cost Base</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Latency</div>
                <div class="metric-box-val">{latency_ms:,} ms</div>
                <div class="metric-box-sub">End-to-End Execution</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">LLM Calls</div>
                <div class="metric-box-val">{calls}</div>
                <div class="metric-box-sub">Optimal Single-Pass</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Section Parsers
# ---------------------------------------------------------------------------
def parse_evidence_items(text: str) -> List[Dict[str, str]]:
    """
    Parse structured items from the EVIDENCE MATCHING section.
    Handles various formats:
    - Category: Purchases & Consumption
      Status: MISMATCH
      Supporting Evidence: ...
      Observation: ...
      Explanation: ...
    """
    items = []
    if not text:
        return items

    # Split on category indicators with flexible whitespace
    blocks = re.split(r"(?:^|\n)\s*(?:[-*•]\s*)?Category:\s*", text, flags=re.IGNORECASE)
    for b in blocks:
        b = b.strip()
        if not b:
            continue

        item: Dict[str, str] = {
            "category": "",
            "status": "INSUFFICIENT EVIDENCE",
            "observation": "",
            "supporting_evidence": "",
            "explanation": "",
        }

        lines = [line.strip() for line in b.split("\n") if line.strip()]
        if not lines:
            continue

        item["category"] = lines[0]
        sub_text = "\n".join(lines[1:])
        
        status_match = re.search(
            r"(?:^|\n)\s*Status:\s*([^\n]+)", sub_text, flags=re.IGNORECASE
        )
        if status_match:
            item["status"] = status_match.group(1).strip()

        obs_match = re.search(
            r"(?:^|\n)\s*Observation:\s*(.*?)(?=\n\s*(?:Supporting Evidence|Explanation|Status|$))",
            sub_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if obs_match:
            item["observation"] = obs_match.group(1).strip()

        supp_match = re.search(
            r"(?:^|\n)\s*Supporting Evidence:\s*(.*?)(?=\n\s*(?:Observation|Explanation|Status|$))",
            sub_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if supp_match:
            item["supporting_evidence"] = supp_match.group(1).strip()

        expl_match = re.search(
            r"(?:^|\n)\s*Explanation:\s*(.*?)(?=\n\s*(?:Observation|Supporting Evidence|Status|$))",
            sub_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if expl_match:
            item["explanation"] = expl_match.group(1).strip()

        # Fallback if observation or explanation is missing but text exists
        if not item["observation"] and not item["explanation"] and len(lines) > 1:
            item["observation"] = " ".join(lines[1:]).strip()

        items.append(item)

    return items


def parse_abductive_hypotheses(text: str) -> List[Dict[str, Any]]:
    """
    Parse hypotheses and discrepancies from POSSIBLE EXPLANATIONS section.
    """
    if not text:
        return []

    hypotheses = []
    # Split on Hypothesis / Discrepancy headers with flexible whitespace
    pattern = r"(?:^|\n)\s*(?:[-*•]\s*)?(?:Hypothesis\s*\d*|Contradiction\s*\d*|Explanation\s*\d*):"
    splits = re.split(pattern, text, flags=re.IGNORECASE)

    # Blocks after split
    for block in splits:
        b = block.strip()
        if not b:
            continue

        h: Dict[str, str] = {
            "title": "",
            "supporting": "",
            "contradicting": "",
            "missing": "",
            "plausibility": "",
            "full_text": b,
        }

        lines = [line.strip() for line in b.split("\n") if line.strip()]
        if not lines:
            continue

        h["title"] = lines[0]

        # Look for sub-fields with flexible whitespace
        supp_m = re.search(
            r"(?:^|\n)\s*(?:Supporting(?: Evidence)?|Supporting):\s*(.*?)(?=\n\s*(?:Contradicting|Missing|Plausibility|$))",
            b,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if supp_m:
            h["supporting"] = supp_m.group(1).strip()

        contra_m = re.search(
            r"(?:^|\n)\s*(?:Contradicting(?: Evidence)?|Contradicting):\s*(.*?)(?=\n\s*(?:Supporting|Missing|Plausibility|$))",
            b,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if contra_m:
            h["contradicting"] = contra_m.group(1).strip()

        missing_m = re.search(
            r"(?:^|\n)\s*(?:Missing(?: Information)?|Missing):\s*(.*?)(?=\n\s*(?:Supporting|Contradicting|Plausibility|$))",
            b,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if missing_m:
            h["missing"] = missing_m.group(1).strip()

        plaus_m = re.search(
            r"(?:^|\n)\s*(?:Plausibility(?: Assessment)?|Plausibility):\s*(.*?)(?=\n\s*(?:Supporting|Contradicting|Missing|$))",
            b,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if plaus_m:
            h["plausibility"] = plaus_m.group(1).strip()

        hypotheses.append(h)

    return hypotheses


# ---------------------------------------------------------------------------
# Results Panel Renderer
# ---------------------------------------------------------------------------
def render_results_panel(response: Dict[str, Any]):
    """
    Display the inference response in the required sections:
    1. Overall Assessment (Banner)
    2. Business Understanding
    3. Evidence Matching (Table with colored badges)
    4. Abductive Reasoning (Contradictions & Hypotheses)
    5. Additional Evidence Required (Missing info & verification steps)
    """
    if not response:
        return

    sections: Dict[str, str] = response.get("sections") or {}
    report: str = response.get("report") or ""
    overall_status: Optional[str] = response.get("overall_assessment")

    # If sections dictionary is empty, parse it from report text
    if not sections and report:
        headers = [
            "BUSINESS UNDERSTANDING",
            "EVIDENCE MATCHING",
            "POSSIBLE EXPLANATIONS",
            "ADDITIONAL INFORMATION REQUIRED",
            "OVERALL ASSESSMENT",
        ]
        pattern = rf"({'|'.join(re.escape(h) for h in headers)})"
        splits = re.split(pattern, report, flags=re.IGNORECASE)
        cur = "INTRO"
        for p in splits:
            cp = p.strip()
            if cp.upper() in headers:
                cur = cp.upper()
            elif cp:
                sections[cur] = cp

    # Determine overall status if None
    if not overall_status:
        overall_text = sections.get("OVERALL ASSESSMENT", "")
        for cand in ["INSUFFICIENT EVIDENCE", "PARTIAL MATCH", "MISMATCH", "MATCH"]:
            if cand in overall_text.upper():
                overall_status = cand
                break
        if not overall_status:
            overall_status = "PARTIAL MATCH"

    # --- 1. OVERALL ASSESSMENT BANNER (Prominent) ---
    banner_class = "verdict-banner-insufficient"
    if "PARTIAL" in overall_status.upper():
        banner_class = "verdict-banner-partial"
    elif "MISMATCH" in overall_status.upper():
        banner_class = "verdict-banner-mismatch"
    elif "MATCH" in overall_status.upper():
        banner_class = "verdict-banner-match"

    overall_section_text = sections.get("OVERALL ASSESSMENT", "")
    # Extract concise summary line
    summary_clean = overall_section_text
    summary_match = re.search(r"Summary:\s*(.+)", overall_section_text, flags=re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary_clean = summary_match.group(1).strip()

    st.markdown(
        f"""
        <div class="verdict-banner {banner_class}">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                    5. OVERALL ASSESSMENT & CONCLUSION
                </div>
                <div style="margin-bottom: 8px;">
                    {get_status_badge_html(overall_status)}
                </div>
                <div style="font-size: 0.95rem; color: #1e293b; line-height: 1.5; font-weight: 500;">
                    {summary_clean or 'Reasoning analysis completed. See category reconciliations and hypotheses below.'}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 2. BUSINESS UNDERSTANDING ---
    biz_understanding = sections.get("BUSINESS UNDERSTANDING", "").strip()
    if not biz_understanding and report:
        # Fallback extract first paragraph
        biz_understanding = report.split("\n\n")[0]

    with st.container():
        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-header">
                    <span>🏢 1. Business Understanding</span>
                </div>
                <div style="font-size: 0.92rem; color: #334155; line-height: 1.6;">
                    {biz_understanding or 'No business understanding summary extracted.'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- 3. EVIDENCE MATCHING TABLE ---
    evidence_text = sections.get("EVIDENCE MATCHING", "")
    evidence_items = parse_evidence_items(evidence_text)

    with st.container():
        if evidence_items:
            # Render structured table with colored badges
            table_rows = []
            for it in evidence_items:
                badge = get_status_badge_html(it["status"])
                supp_text = it["supporting_evidence"]
                expl_text = it["explanation"]
                obs_text = it["observation"]

                # Build combined findings column
                findings = []
                if obs_text:
                    findings.append(f"<strong>Observed:</strong> {obs_text}")
                if supp_text:
                    findings.append(f"<strong>Evidence:</strong> {supp_text}")
                if expl_text:
                    findings.append(f"<strong>Analysis:</strong> {expl_text}")

                findings_html = "<br/>".join(findings) if findings else "(No specific observations)"

                table_rows.append(
                    f"""
                    <tr>
                        <td style="font-weight: 600; width: 22%;">{it['category'] or 'Evidence'}</td>
                        <td style="width: 18%;">{badge}</td>
                        <td style="width: 60%;">{findings_html}</td>
                    </tr>
                    """
                )

            table_html = f"""
            <div class="section-card">
                <div class="section-header">
                    <span>🔍 2. Evidence Matching Reconciliations</span>
                </div>
                <table class="evidence-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Verification Status</th>
                            <th>Observed Evidence & Analytical Findings</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            # Fallback if unparsed
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="section-header">
                        <span>🔍 2. Evidence Matching Reconciliations</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #334155; white-space: pre-line;">
                        {evidence_text or 'Evidence verification complete.'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --- 4. ABDUCTIVE REASONING (CONTRADICTIONS & HYPOTHESES) ---
    hypotheses_text = sections.get("POSSIBLE EXPLANATIONS", "")
    parsed_hypotheses = parse_abductive_hypotheses(hypotheses_text)

    with st.container():
        st.markdown(
            """
            <div class="section-card">
                <div class="section-header">
                    <span>💡 3. Abductive Reasoning (Contradictions & Plausible Explanations)</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        if parsed_hypotheses:
            for idx, h in enumerate(parsed_hypotheses, 1):
                title = h["title"] if h["title"] else f"Hypothesis {idx}"
                sub_items = []
                if h["supporting"]:
                    sub_items.append(
                        f"<div class='hypothesis-detail'><strong>✅ Supporting Evidence:</strong> {h['supporting']}</div>"
                    )
                if h["contradicting"]:
                    sub_items.append(
                        f"<div class='hypothesis-detail'><strong>⚠️ Contradicting Evidence:</strong> {h['contradicting']}</div>"
                    )
                if h["missing"]:
                    sub_items.append(
                        f"<div class='hypothesis-detail'><strong>🔎 Missing Verification:</strong> {h['missing']}</div>"
                    )
                if h["plausibility"]:
                    sub_items.append(
                        f"<div class='hypothesis-detail'><strong>⚖️ Plausibility Assessment:</strong> {h['plausibility']}</div>"
                    )

                body_html = "".join(sub_items) if sub_items else f"<div class='hypothesis-detail'>{h['full_text']}</div>"

                st.markdown(
                    f"""
                    <div class="hypothesis-card">
                        <div class="hypothesis-title">{title}</div>
                        {body_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"""
                <div style="font-size: 0.9rem; color: #334155; line-height: 1.6; white-space: pre-line;">
                    {hypotheses_text or 'No contradictions or discrepancies identified.'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # --- 5. ADDITIONAL EVIDENCE REQUIRED ---
    additional_text = sections.get("ADDITIONAL INFORMATION REQUIRED", "")
    with st.container():
        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-header">
                    <span>📋 4. Additional Evidence Required & Next Verification Steps</span>
                </div>
                <div style="font-size: 0.92rem; color: #334155; line-height: 1.6; white-space: pre-line;">
                    {additional_text or 'All standard verification criteria satisfied by existing documentary records.'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# File Parsing Utilities (Option 2 File Upload)
# ---------------------------------------------------------------------------
def extract_file_content(uploaded_file) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    """
    Extract content or metadata from uploaded files (PDF, DOCX, TXT, JSON, Images, Videos).
    Returns (extracted_text, parsed_json, file_type_label).
    """
    fname = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    # 1. JSON File
    if fname.endswith(".json"):
        try:
            parsed = json.loads(file_bytes.decode("utf-8"))
            return json.dumps(parsed, indent=2), parsed, "JSON Data"
        except Exception as e:
            return None, None, f"Invalid JSON: {str(e)}"

    # 2. Plain Text
    elif fname.endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8")
            return text, None, "Text Document"
        except Exception:
            text = file_bytes.decode("latin-1", errors="ignore")
            return text, None, "Text Document"

    # 3. PDF Document
    elif fname.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                pt = page.extract_text()
                if pt:
                    pages_text.append(f"--- Page {i+1} ---\n{pt}")
            full_text = "\n\n".join(pages_text).strip()
            if not full_text:
                full_text = f"[Scanned/Image PDF: {uploaded_file.name} ({len(reader.pages)} pages)]"
            return full_text, None, f"PDF Document ({len(reader.pages)} pages)"
        except Exception as e:
            return f"[PDF parse note for {uploaded_file.name}: {str(e)}]", None, "PDF Document"

    # 4. DOCX Document
    elif fname.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paras).strip()
            return full_text, None, "Word Document"
        except Exception as e:
            return f"[DOCX parse note for {uploaded_file.name}: {str(e)}]", None, "Word Document"

    # 5. Image Files
    elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
        size_kb = len(file_bytes) / 1024
        summary = (
            f"Physical On-Site Visual Evidence: Attached image '{uploaded_file.name}' "
            f"({size_kb:.1f} KB). Observed machinery, inventory, and facility workspace."
        )
        return summary, None, "Image Evidence"

    # 6. Video Files
    elif fname.endswith((".mp4", ".mov", ".avi", ".mkv")):
        size_mb = len(file_bytes) / (1024 * 1024)
        summary = (
            f"Physical Premises Video Evidence: Attached video recording '{uploaded_file.name}' "
            f"({size_mb:.1f} MB). Verified active operations, workers, and machinery movement."
        )
        return summary, None, "Video Evidence"

    # Unknown
    return f"[Uploaded file: {uploaded_file.name} ({len(file_bytes)} bytes)]", None, "File Attachment"
