"""
Auroraa R&D Inference Engine - Streamlit Testing Interface
-----------------------------------------------------------
R&D experimentation interface for testing Auroraa's LLM-based abductive reasoning engine.
Communicates with the existing FastAPI backend via HTTP.
"""

import os
import json
import streamlit as st

from ui.api_client import (
    DEFAULT_BACKEND_URL,
    normalize_url,
    check_health,
    run_inference,
    get_metrics,
    reset_metrics,
)
from ui.sample_data import (
    ABC_TEXTILE_JSON,
    SAMPLE_CASES,
    SAMPLE_TEXT_NARRATIVE,
)
from ui.components import (
    inject_custom_styles,
    render_metrics_panel,
    render_results_panel,
    extract_file_content,
)

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Auroraa R&D | Abductive Reasoning Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom styles for dark navy sidebar and readable light workspace
inject_custom_styles()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "json_input" not in st.session_state:
    # Preload ABC Textile Industries test case by default
    st.session_state.json_input = ABC_TEXTILE_JSON

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "text_case_id" not in st.session_state:
    st.session_state.text_case_id = "AUR-CASE-001"

if "text_declared" not in st.session_state:
    st.session_state.text_declared = (
        "ABC Textile Industries (Surat). 5 years operational, 15 workers. "
        "Declared monthly turnover: ₹15,00,000. Declared monthly production: 8,000 meters fabric. "
        "Production capacity: 10,000 meters/month."
    )

if "text_observed" not in st.session_state:
    st.session_state.text_observed = (
        "1. Purchase bill PUR-001: 1,000 kg cotton @ ₹150/kg (₹1,50,000).\n"
        "2. Production records: 1,600 kg cotton consumed to produce 8,000 meters fabric.\n"
        "3. Sales invoice SALE-001: ₹2,50,000 to ABC Garments.\n"
        "4. Bank statement: ₹2,50,000 incoming credit from ABC Garments.\n"
        "5. Premises video VID-001: 5 power looms operational, fabric rolls stacked.\n"
        "6. Electricity bill: 4,500 units consumed (₹38,000)."
    )

# ---------------------------------------------------------------------------
# Sidebar: Backend Architecture & Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Auroraa R&D Engine")
    st.caption("LLM Abductive Reasoning Testing Suite")
    st.markdown("---")

    st.markdown("#### 🔌 Backend Connection")
    backend_url = st.text_input(
        "FastAPI Service URL",
        value=os.getenv("AURORAA_BACKEND_URL") or os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL,
        help="Configurable via AURORAA_BACKEND_URL or BACKEND_URL environment variable.",
    )
    backend_url = normalize_url(backend_url)

    # Health check button & status
    col_h1, col_h2 = st.columns([1, 1])
    with col_h1:
        if st.button("Ping Backend", use_container_width=True):
            st.session_state.health_status = check_health(backend_url)

    health = st.session_state.get("health_status") or check_health(backend_url)
    if health.get("ok"):
        st.success(f"Online: {health.get('status', 'healthy')}")
    else:
        st.error("Offline: Backend unreachable")
        st.caption("Run: `uvicorn app.main:app --port 8000`")

    st.markdown("---")

    # Sample Case Quick Selector
    st.markdown("#### 📂 Preloaded Test Cases")
    selected_sample = st.selectbox(
        "Choose Industry Case",
        options=list(SAMPLE_CASES.keys()),
        index=0,  # Default: ABC Textile Industries
    )
    sample_info = SAMPLE_CASES[selected_sample]
    st.caption(f"**Industry:** {sample_info['industry']}")
    st.caption(f"*{sample_info['description']}*")

    if st.button("Load This Case Into JSON Input", use_container_width=True):
        st.session_state.json_input = sample_info["json_str"]
        st.session_state.text_case_id = sample_info["case_id"]
        st.toast(f"Loaded {sample_info['case_id']} into input panel!")
        st.rerun()

    st.markdown("---")

    # Cumulative Metrics Overview
    with st.expander("📊 Cumulative Engine Metrics", expanded=False):
        cum_metrics = get_metrics(backend_url)
        if cum_metrics.get("ok"):
            m = cum_metrics.get("metrics", {})
            st.write(f"**Total Calls:** {m.get('total_calls', 0)}")
            st.write(f"**Total Tokens:** {m.get('total_tokens', 0):,}")
            st.write(f"**Prompt Tokens:** {m.get('total_input_tokens', 0):,}")
            st.write(f"**Completion Tokens:** {m.get('total_output_tokens', 0):,}")
            st.write(f"**Avg Latency:** {m.get('average_latency_ms', 0)} ms")
            st.write(f"**Est. Cost:** ${m.get('estimated_cost_usd', 0):.5f}")
            if st.button("Reset Metrics Log"):
                reset_metrics(backend_url)
                st.toast("Cumulative metrics reset.")
                st.rerun()
        else:
            st.caption("Cumulative metrics unavailable (connect to backend).")

    st.markdown("---")
    st.caption("Strictly for R&D evaluation. Streamlit UI → FastAPI → LLM Reasoning Pipeline.")


# ---------------------------------------------------------------------------
# Main Header
# ---------------------------------------------------------------------------
st.title("Auroraa Abductive Reasoning Engine")
st.markdown(
    "Automated MSME business claim verification using deterministic Python reconciliations and single-pass LLM abductive reasoning."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Section A: Input Panel
# ---------------------------------------------------------------------------
st.subheader("1. Case Input Panel")

input_tab1, input_tab2, input_tab3 = st.tabs([
    "📝 Option 1: JSON Input (Structured)",
    "📁 Option 2: File Upload (Multi-Format)",
    "💬 Option 3: Text Input (Natural Language)",
])

payload_to_send = None
validation_error = None

# --- TAB 1: JSON INPUT ---
with input_tab1:
    col_t1_top, col_t1_btns = st.columns([3, 1])
    with col_t1_top:
        st.markdown(
            "Paste structured business evidence JSON. Preloaded by default with **ABC Textile Industries** test case."
        )
    with col_t1_btns:
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Load ABC Textile", use_container_width=True, help="Reset to standard ABC Textile Industries test case"):
                st.session_state.json_input = ABC_TEXTILE_JSON
                st.rerun()
        with c_btn2:
            if st.button("Clear JSON", use_container_width=True):
                st.session_state.json_input = ""
                st.rerun()

    json_area = st.text_area(
        "Business Evidence JSON Payload",
        value=st.session_state.json_input,
        height=320,
        placeholder="{\n  \"case_id\": \"AUR-CASE-001\",\n  \"business_profile\": { ... },\n  \"purchase_evidence\": { ... }\n}",
    )
    # Sync edited text into session state
    st.session_state.json_input = json_area


# --- TAB 2: FILE UPLOAD ---
with input_tab2:
    st.markdown("Upload documentary, financial, or physical inspection files to evaluate:")
    uploaded_files = st.file_uploader(
        "Supported formats: PDF, DOCX, TXT, JSON, Images, Videos",
        type=["pdf", "docx", "txt", "json", "png", "jpg", "jpeg", "webp", "mp4", "mov", "avi"],
        accept_multiple_files=True,
    )

    file_extracted_texts = []
    file_json_candidate = None

    if uploaded_files:
        st.markdown("##### Extracted File Observations & Content Preview:")
        for uf in uploaded_files:
            text_cont, parsed_j, ftype = extract_file_content(uf)
            with st.expander(f"📄 {uf.name} ({ftype})", expanded=False):
                if parsed_j:
                    st.json(parsed_j)
                    file_json_candidate = parsed_j
                    if st.button(f"Load '{uf.name}' into Option 1 JSON tab", key=f"load_j_{uf.name}"):
                        st.session_state.json_input = json.dumps(parsed_j, indent=2)
                        st.success("Loaded into JSON tab!")
                elif text_cont:
                    st.text_area(f"Extracted content ({uf.name})", value=text_cont, height=140, disabled=True)
                    file_extracted_texts.append(f"=== File: {uf.name} ({ftype}) ===\n{text_cont}")

    file_case_id = st.text_input("Case ID for File Evidence", value="AUR-CASE-UPLOAD-001")
    file_narrative_notes = st.text_area(
        "Additional Inspector Notes / Declared Profile (Optional)",
        placeholder="Enter any declared turnover, production figures, or notes not present in the files...",
        height=100,
    )


# --- TAB 3: TEXT INPUT ---
with input_tab3:
    st.markdown(
        "Paste free-form natural language business descriptions and extracted evidence. Users are not forced to fill every field."
    )
    col_txt_id, col_txt_preset = st.columns([2, 1])
    with col_txt_id:
        text_case_id = st.text_input("Verification Case ID", value=st.session_state.text_case_id)
    with col_txt_preset:
        if st.button("Load Narrative Sample", use_container_width=True):
            st.session_state.text_case_id = "AUR-CASE-001"
            st.session_state.text_declared = (
                "ABC Textile Industries (Surat). 5 years operational, 15 workers. "
                "Declared monthly turnover: ₹15,00,000. Declared monthly production: 8,000 meters fabric. "
                "Production capacity: 10,000 meters/month."
            )
            st.session_state.text_observed = (
                "1. Purchase bill PUR-001: 1,000 kg cotton @ ₹150/kg (₹1,50,000).\n"
                "2. Production records: 1,600 kg cotton consumed to produce 8,000 meters fabric.\n"
                "3. Sales invoice SALE-001: ₹2,50,000 to ABC Garments.\n"
                "4. Bank statement: ₹2,50,000 incoming credit from ABC Garments.\n"
                "5. Premises video VID-001: 5 power looms operational, fabric rolls stacked.\n"
                "6. Electricity bill: 4,500 units consumed (₹38,000)."
            )
            st.rerun()

    text_declared = st.text_area(
        "Declared Business Claims & Profile",
        value=st.session_state.text_declared,
        height=110,
        placeholder="e.g. Business activity, declared monthly turnover, production capacity, number of employees...",
    )
    st.session_state.text_declared = text_declared

    text_observed = st.text_area(
        "Observed Documentary, Financial & Physical Evidence",
        value=st.session_state.text_observed,
        height=140,
        placeholder="e.g. Observed purchase invoices, bank credit transactions, inventory photos, machinery inspections...",
    )
    st.session_state.text_observed = text_observed


# ---------------------------------------------------------------------------
# Action Buttons: RUN INFERENCE & CLEAR
# ---------------------------------------------------------------------------
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
col_run, col_clear, col_space = st.columns([2, 1, 4])

with col_run:
    run_clicked = st.button("🚀 RUN INFERENCE", type="primary", use_container_width=True)

with col_clear:
    if st.button("🗑️ Clear Inputs", use_container_width=True):
        st.session_state.json_input = ""
        st.session_state.text_declared = ""
        st.session_state.text_observed = ""
        st.rerun()

# ---------------------------------------------------------------------------
# Inference Execution Logic
# ---------------------------------------------------------------------------
if run_clicked:
    # Determine which payload to use based on which input has data
    # Priority: If JSON input is populated, use it. If files exist, construct from files. If text fields exist, construct from text.
    payload = None

    # Check JSON Area
    if st.session_state.json_input and st.session_state.json_input.strip():
        try:
            payload = json.loads(st.session_state.json_input)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in Option 1: {str(e)}")
            payload = None

    # Fallback to File Uploads if JSON was empty
    elif uploaded_files:
        if file_json_candidate:
            payload = file_json_candidate
        else:
            combined_file_text = "\n\n".join(file_extracted_texts)
            if file_narrative_notes:
                combined_file_text += f"\n\n=== Inspector Notes ===\n{file_narrative_notes}"
            payload = {
                "case_id": file_case_id or "AUR-CASE-UPLOAD",
                "text": combined_file_text.strip(),
                "observed_evidence": f"Uploaded {len(uploaded_files)} verification evidence files.",
            }

    # Fallback to Text Input
    elif st.session_state.text_declared or st.session_state.text_observed:
        payload = {
            "case_id": st.session_state.text_case_id or "AUR-CASE-TEXT",
            "declared_information": st.session_state.text_declared.strip() if st.session_state.text_declared else None,
            "observed_evidence": st.session_state.text_observed.strip() if st.session_state.text_observed else None,
            "text": f"{st.session_state.text_declared}\n\n{st.session_state.text_observed}".strip(),
        }

    else:
        st.warning("Please provide input in either Option 1 (JSON), Option 2 (Files), or Option 3 (Text) before running inference.")

    if payload:
        with st.spinner("Executing Abductive Reasoning Engine... (Deterministic Math Reconciliations + LLM Inference)"):
            success, result = run_inference(payload, base_url=backend_url)
            if success:
                # Keep previous results visible until a new inference completes successfully!
                st.session_state.last_response = result
                st.session_state.last_error = None
                st.toast("Inference completed successfully!")
            else:
                st.session_state.last_error = result.get("error", "Unknown inference failure.")
                st.error(f"Inference Failed:\n\n{st.session_state.last_error}")

# If previous inference error is active, display warning
if st.session_state.last_error and not run_clicked:
    st.error(f"Last Inference Error: {st.session_state.last_error}")

# ---------------------------------------------------------------------------
# Section B & C: Results Panel & Inference Metrics
# ---------------------------------------------------------------------------
if st.session_state.last_response:
    resp = st.session_state.last_response
    st.markdown("---")

    # Header with Case ID and Status
    col_res_title, col_res_status = st.columns([3, 1])
    with col_res_title:
        st.subheader(f"Inference Report: {resp.get('case_id', 'AUR-CASE')}")
    with col_res_status:
        st.markdown(
            f"<div style='text-align: right; padding-top: 8px;'>Status: <strong>{resp.get('status', 'completed').upper()}</strong></div>",
            unsafe_allow_html=True,
        )

    # Section B: Compact Metrics Cards
    render_metrics_panel(resp.get("token_usage"))

    # Section C: 5 Standardized Verification Sections
    render_results_panel(resp)

    # Export & Download Options
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_d1, col_d2, col_d3 = st.columns([1.5, 1.5, 3])
    
    report_text = resp.get("report", "")
    case_id_clean = resp.get("case_id", "AUR-CASE").replace(" ", "_")

    with col_d1:
        st.download_button(
            label="📥 Download Report (.TXT)",
            data=report_text,
            file_name=f"{case_id_clean}_reasoning_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_d2:
        st.download_button(
            label="📥 Download JSON Response",
            data=json.dumps(resp, indent=2),
            file_name=f"{case_id_clean}_inference_result.json",
            mime="application/json",
            use_container_width=True,
        )

    # Expandable Raw JSON Viewer
    with st.expander("🔍 View Raw API JSON Response", expanded=False):
        st.json(resp)
