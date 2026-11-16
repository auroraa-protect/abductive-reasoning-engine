"""Auroraa R&D inference workspace."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# Ensure both repository root and ui directory are present in sys.path
_ROOT = Path(__file__).resolve().parent.parent
_UI_DIR = Path(__file__).resolve().parent

for _p in (str(_ROOT), str(_UI_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from ui.api_client import (
        DEFAULT_BACKEND_URL,
        check_health,
        get_metrics,
        normalize_url,
        run_inference,
    )
    from ui.components import extract_file_content, render_report_markdown
    from ui.sample_data import ABC_TEXTILE_JSON, SAMPLE_CASES
except ImportError:
    from api_client import (
        DEFAULT_BACKEND_URL,
        check_health,
        get_metrics,
        normalize_url,
        run_inference,
    )
    from components import extract_file_content, render_report_markdown
    from sample_data import ABC_TEXTILE_JSON, SAMPLE_CASES


# ---------------------------------------------------------------------------
# Structured text-input helpers
# ---------------------------------------------------------------------------

def _skey(section: str, idx: int, field: str) -> str:
    """Build a stable session-state key for a structured field entry."""
    return f"sf__{section}__{idx}__{field}"


def _get_count(section: str) -> int:
    return st.session_state.get(f"sf_count__{section}", 1)


def _add_entry(section: str) -> None:
    st.session_state[f"sf_count__{section}"] = _get_count(section) + 1


def _remove_entry(section: str, idx: int) -> None:
    count = _get_count(section)
    # Shift all entries above idx down by one
    for i in range(idx, count - 1):
        for field in _SECTION_FIELDS.get(section, []):
            k_src = _skey(section, i + 1, field[0])
            k_dst = _skey(section, i, field[0])
            st.session_state[k_dst] = st.session_state.get(k_src, "")
    # Clear the last entry
    for field in _SECTION_FIELDS.get(section, []):
        k = _skey(section, count - 1, field[0])
        st.session_state.pop(k, None)
    st.session_state[f"sf_count__{section}"] = max(1, count - 1)


def _clear_section(section: str) -> None:
    count = _get_count(section)
    for i in range(count):
        for field in _SECTION_FIELDS.get(section, []):
            st.session_state.pop(_skey(section, i, field[0]), None)
    st.session_state[f"sf_count__{section}"] = 1


def _render_structured_section(section: str, label: str) -> None:
    """Render labelled input fields for every entry in a structured section."""
    fields = _SECTION_FIELDS.get(section, [])
    if not fields:
        return
    count = _get_count(section)
    for i in range(count):
        if count > 1:
            col_title, col_del = st.columns([10, 1])
            with col_title:
                st.markdown(f"**{label} {i + 1}**")
            with col_del:
                st.button(
                    "✕",
                    key=f"del_{section}_{i}",
                    on_click=_remove_entry,
                    args=(section, i),
                    help="Remove this entry",
                )
        cols_per_row = 2
        field_groups = [fields[j:j+cols_per_row] for j in range(0, len(fields), cols_per_row)]
        for group in field_groups:
            cols = st.columns(len(group))
            for col, (fname, ftype, fhelp) in zip(cols, group):
                key = _skey(section, i, fname)
                with col:
                    if ftype == "text":
                        st.text_input(fname, key=key, help=fhelp, placeholder=fhelp)
                    elif ftype == "number":
                        st.text_input(fname, key=key, help=fhelp, placeholder="e.g. 150000")
                    elif ftype == "date":
                        st.text_input(fname, key=key, help=fhelp, placeholder="YYYY-MM-DD")
                    elif ftype == "area":
                        st.text_area(fname, key=key, help=fhelp, height=80, placeholder=fhelp)
        if i < count - 1:
            st.divider()

    st.button(
        f"＋ Add another {label.lower()}",
        key=f"add_{section}",
        on_click=_add_entry,
        args=(section,),
    )


def _collect_section_text(section: str, label: str) -> str:
    """Collect all filled entries in a section into a human-readable string."""
    fields = _SECTION_FIELDS.get(section, [])
    if not fields:
        return ""
    count = _get_count(section)
    lines = []
    for i in range(count):
        parts = []
        for fname, _ftype, _fhelp in fields:
            val = st.session_state.get(_skey(section, i, fname), "").strip()
            if val:
                parts.append(f"{fname}: {val}")
        if parts:
            lines.append(f"{label} {i+1}: " + "; ".join(parts) if count > 1 else "; ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Field definitions: (field_name, input_type, placeholder_hint)
# input_type: "text" | "number" | "date" | "area"
# ---------------------------------------------------------------------------
_SECTION_FIELDS: dict = {
    # Business profile
    "business_details": [
        ("Business name", "text", "e.g. ABC Textile Industries"),
        ("Business type", "text", "e.g. manufacturing / trading / service"),
        ("Industry", "text", "e.g. textile"),
        ("Business activity", "text", "e.g. Cotton fabric manufacturing"),
        ("Business age (years)", "number", "e.g. 5"),
        ("Number of employees", "number", "e.g. 15"),
    ],
    "business_claims": [
        ("Declared monthly turnover (₹)", "number", "e.g. 1500000"),
        ("Declared monthly production", "text", "e.g. 8000 meters"),
        ("Declared production capacity", "text", "e.g. 10000 meters/month"),
    ],
    # Purchase evidence
    "purchase_bills": [
        ("Supplier name", "text", "e.g. XYZ Cotton Traders"),
        ("Invoice date", "date", "YYYY-MM-DD"),
        ("Total amount (₹)", "number", "e.g. 150000"),
    ],
    "purchase_items": [
        ("Item name", "text", "e.g. Raw Cotton"),
        ("Quantity", "number", "e.g. 1000"),
        ("Unit", "text", "e.g. kg"),
        ("Unit price (₹)", "number", "e.g. 150"),
        ("Total amount (₹)", "number", "e.g. 150000"),
    ],
    # Inventory evidence
    "inventory_declared": [
        ("Item name", "text", "e.g. Raw Cotton"),
        ("Quantity", "number", "e.g. 500"),
        ("Unit", "text", "e.g. kg"),
        ("Estimated value (₹)", "number", "e.g. 75000"),
    ],
    "inventory_images": [
        ("Observed objects", "text", "e.g. Cotton bags × 20, Fabric rolls × 35"),
        ("Observations", "area", "e.g. Inventory stored inside warehouse"),
        ("Analysis confidence", "number", "0.0 – 1.0"),
    ],
    # Production evidence
    "production_records": [
        ("Date", "date", "YYYY-MM-DD"),
        ("Product", "text", "e.g. Cotton Fabric"),
        ("Quantity", "number", "e.g. 8000"),
        ("Unit", "text", "e.g. meters"),
    ],
    "production_consumption": [
        ("Material", "text", "e.g. Raw Cotton"),
        ("Quantity consumed", "number", "e.g. 1600"),
        ("Unit", "text", "e.g. kg"),
    ],
    "production_finished_goods": [
        ("Product", "text", "e.g. Cotton Fabric"),
        ("Quantity", "number", "e.g. 8000"),
        ("Unit", "text", "e.g. meters"),
    ],
    # Sales evidence
    "sales_bills": [
        ("Customer name", "text", "e.g. ABC Garments"),
        ("Invoice date", "date", "YYYY-MM-DD"),
        ("Total amount (₹)", "number", "e.g. 250000"),
    ],
    "sales_customers": [
        ("Customer name", "text", "e.g. ABC Garments"),
        ("Relationship", "text", "e.g. Retailer"),
    ],
    "sales_summary": [
        ("Total sales value (₹)", "number", "e.g. 250000"),
        ("Period", "text", "e.g. October 2026"),
    ],
    # Physical evidence
    "physical_video": [
        ("Duration (seconds)", "number", "e.g. 120"),
        ("Observed activities", "area", "e.g. Workers operating machinery"),
        ("Observed machinery", "text", "e.g. Power loom, Fabric cutting machine"),
        ("Analysis confidence", "number", "0.0 – 1.0"),
    ],
    "physical_machinery": [
        ("Machine name", "text", "e.g. Power Loom"),
        ("Observed count", "number", "e.g. 5"),
        ("Condition", "text", "e.g. Operational"),
    ],
    "physical_premises": [
        ("Area", "text", "e.g. Production floor"),
        ("Observations", "area", "e.g. Manufacturing equipment and fabric rolls observed"),
    ],
    # Financial evidence
    "financial_bank": [
        ("Transaction date", "date", "YYYY-MM-DD"),
        ("Type", "text", "credit / debit"),
        ("Amount (₹)", "number", "e.g. 250000"),
        ("Description", "text", "e.g. ABC Garments payment"),
    ],
    "financial_electricity": [
        ("Billing month", "text", "e.g. October 2026"),
        ("Units consumed", "number", "e.g. 4500"),
        ("Bill amount (₹)", "number", "e.g. 38000"),
    ],
    "financial_gst": [
        ("Period", "text", "e.g. October 2026"),
        ("Declared turnover (₹)", "number", "e.g. 1500000"),
    ],
    # Additional evidence
    "additional_documents": [
        ("Document name / type", "text", "e.g. Lease agreement"),
        ("Description", "area", "e.g. Office lease for 1,200 sq ft"),
    ],
    "additional_observations": [
        ("Observation", "area", "e.g. Business claims monthly production capacity of 10,000 meters"),
    ],
}

# Map of section-key → (display label, section id)
_STRUCTURED_SECTIONS = [
    ("Purchase evidence", [
        ("Bill", "purchase_bills"),
        ("Purchased item", "purchase_items"),
    ]),
    ("Inventory evidence", [
        ("Inventory item", "inventory_declared"),
        ("Image analysis", "inventory_images"),
    ]),
    ("Production evidence", [
        ("Production record", "production_records"),
        ("Material consumption", "production_consumption"),
        ("Finished goods", "production_finished_goods"),
    ]),
    ("Sales evidence", [
        ("Sales bill", "sales_bills"),
        ("Customer", "sales_customers"),
        ("Sales summary", "sales_summary"),
    ]),
    ("Physical evidence", [
        ("Video analysis", "physical_video"),
        ("Machinery", "physical_machinery"),
        ("Premises observation", "physical_premises"),
    ]),
    ("Financial evidence", [
        ("Bank transaction", "financial_bank"),
        ("Electricity bill", "financial_electricity"),
        ("GST record", "financial_gst"),
    ]),
    ("Additional evidence", [
        ("Document", "additional_documents"),
        ("Observation", "additional_observations"),
    ]),
]

# TEXT_INPUT_DEFAULTS: only the extra context textarea remains as free text
TEXT_INPUT_DEFAULTS = {
    "text_business_context": "",
}


st.set_page_config(
    page_title="Auroraa | R&D Inference",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-contrast CSS to guarantee crisp typography and correct colors
st.markdown(
    """
    <style>
    /* Workspace typography */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Ensure all headings in the main workspace are crisp and high-contrast */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
    [data-testid="stHeadingWithActionElements"] h1,
    [data-testid="stHeadingWithActionElements"] h2,
    [data-testid="stHeadingWithActionElements"] h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    
    .main p, .main span, .main li, .main [data-testid="stMarkdownContainer"] p {
        color: #1e293b !important;
        opacity: 1 !important;
    }
    
    .main label, .main [data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    /* Text areas and inputs */
    .main textarea, .main input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Dark Navy Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b1329 !important;
    }

    /* =================================
   AURORAA SIDEBAR TEXT VISIBILITY
================================= */

/* Main sidebar title */
section[data-testid="stSidebar"] h1 {
    color: #ffffff !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}

/* Section headings: Sample cases, Backend */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}

/* Descriptions and markdown text */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #cbd5e1 !important;
    opacity: 1 !important;
}

/* Captions and supporting descriptions */
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #cbd5e1 !important;
    opacity: 1 !important;
}

/* Input labels */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #f1f5f9 !important;
    opacity: 1 !important;
}

/* Status and informational text */
section[data-testid="stSidebar"] .stMarkdown {
    color: #cbd5e1 !important;
}

/* Sidebar divider */
section[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}

    section[data-testid="stSidebar"] hr {
        border-color: #1e293b !important;
    }

    /* Segmented Control */
    div[data-testid="stSegmentedControl"] button p {
        color: #334155 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] p {
        color: #1e40af !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _start_new_test() -> None:
    st.session_state.last_response = None
    st.session_state.last_error = None
    st.session_state.json_input = ""
    st.session_state.input_mode = "JSON input"
    for key in TEXT_INPUT_DEFAULTS:
        st.session_state[key] = ""
        st.session_state[f"_{key}"] = ""
    # Clear all structured evidence fields
    for section_key in _SECTION_FIELDS:
        _clear_section(section_key)
    st.session_state.file_notes = ""
    st.session_state.upload_generation += 1


def _load_sample_case(sample: Dict[str, Any]) -> None:
    st.session_state.input_mode = "JSON input"
    st.session_state.json_input = sample["json_str"]
    st.session_state.last_error = None
    for key, default_value in TEXT_INPUT_DEFAULTS.items():
        st.session_state[key] = default_value
        st.session_state[f"_{key}"] = default_value


def _load_abc_textile() -> None:
    st.session_state.input_mode = "JSON input"
    st.session_state.json_input = ABC_TEXTILE_JSON


def _clear_text_input() -> None:
    for key in TEXT_INPUT_DEFAULTS:
        st.session_state[key] = ""
        st.session_state[f"_{key}"] = ""
    for section_key in ("business_details", "business_claims"):
        _clear_section(section_key)
    for section_key in _SECTION_FIELDS:
        _clear_section(section_key)


def _save_text_input(key: str) -> None:
    st.session_state[f"_{key}"] = st.session_state[key]


def _clear_file_input() -> None:
    st.session_state.file_notes = ""
    st.session_state.upload_generation += 1


@st.cache_data(ttl=15, show_spinner=False)
def _backend_health(base_url: str) -> Dict[str, Any]:
    return check_health(base_url)


st.session_state.setdefault("json_input", ABC_TEXTILE_JSON)
st.session_state.setdefault("input_mode", "JSON input")
st.session_state.setdefault("last_response", None)
st.session_state.setdefault("last_error", None)
for key, default_value in TEXT_INPUT_DEFAULTS.items():
    st.session_state.setdefault(f"_{key}", default_value)
    st.session_state.setdefault(key, st.session_state[f"_{key}"])
st.session_state.setdefault("file_notes", "")
st.session_state.setdefault("upload_generation", 0)
st.session_state.setdefault("history_entries", None)
st.session_state.setdefault("history_backend_url", None)
st.session_state.setdefault("history_error", None)
st.session_state.setdefault(
    "backend_url",
    os.getenv("AURORAA_BACKEND_URL")
    or os.getenv("BACKEND_URL")
    or DEFAULT_BACKEND_URL,
)


with st.sidebar:
    st.title("Auroraa")
    st.caption("R&D inference engine")
    st.button(
        "New test",
        icon=":material/add:",
        on_click=_start_new_test,
        key="new_test",
    )

    st.subheader("Sample cases")
    selected_sample = st.selectbox(
        "Choose a sample case",
        options=list(SAMPLE_CASES.keys()),
        label_visibility="collapsed",
        key="sample_selection",
    )
    sample_info = SAMPLE_CASES[selected_sample]
    st.caption(f"{sample_info['industry']} · {sample_info['description']}")
    st.button(
        "Load sample",
        icon=":material/folder_open:",
        on_click=_load_sample_case,
        args=(sample_info,),
        key="load_sample",
    )

    st.subheader("Backend")
    backend_url = normalize_url(
        st.text_input("FastAPI URL", key="backend_url")
    )
    if st.button("Check connection", icon=":material/wifi:", key="check_connection"):
        _backend_health.clear()
    health = _backend_health(backend_url)
    if health.get("ok"):
        st.markdown(":green[● Online]")
    else:
        st.markdown(":red[● Offline]")
        st.caption("Start the API with `uvicorn app.main:app --port 8000`.")

    model_info = st.session_state.last_response or {}
    usage_info = model_info.get("token_usage") or {}
    provider = usage_info.get("model", "Shown after inference")
    st.caption(f"Current provider: {provider}")

    with st.expander("Inference history"):
        refresh_history = st.button("Refresh history", key="refresh_history")
        if (
            refresh_history
            or st.session_state.history_backend_url != backend_url
        ):
            metrics_result = get_metrics(backend_url)
            if metrics_result.get("ok"):
                metrics = metrics_result.get("metrics")
                history = (
                    metrics.get("call_history")
                    if isinstance(metrics, dict)
                    else None
                )
                if isinstance(history, list):
                    st.session_state.history_entries = history
                    st.session_state.history_error = None
                else:
                    st.session_state.history_entries = None
                    st.session_state.history_error = (
                        "The metrics endpoint returned an invalid history response."
                    )
            else:
                st.session_state.history_entries = None
                st.session_state.history_error = metrics_result.get(
                    "error", "Could not load history."
                )
            st.session_state.history_backend_url = backend_url

        history = st.session_state.history_entries
        if st.session_state.history_error:
            st.error(st.session_state.history_error)
        if history is None:
            if not st.session_state.history_error:
                st.caption("History is available from the backend metrics endpoint.")
        elif not history:
            st.caption("No inference calls recorded yet.")
        else:
            for entry in reversed(history[-5:]):
                st.text(
                    f"{entry.get('timestamp', '')} · "
                    f"{entry.get('total_tokens', '—')} tokens"
                )


st.title("Auroraa")
st.subheader("Business Intelligence & Abductive Reasoning")
st.markdown(
    "Understand businesses through evidence, discover contradictions and explore possible explanations."
)

last_response = st.session_state.last_response
if last_response:
    inference_status = str(last_response.get("status", "completed")).replace("_", " ").title()
else:
    inference_status = "Ready"
st.text(f"Inference status: {inference_status}")

st.header("Submit business evidence")
input_mode = st.segmented_control(
    "Input method",
    options=["JSON input", "Text input", "File upload"],
    key="input_mode",
)
input_mode = input_mode or "JSON input"

uploaded_files = []
file_extracted_texts = []
file_json_candidate = None

if input_mode == "JSON input":
    action_columns = st.columns(3)
    with action_columns[0]:
        st.button(
            "Load ABC Textile sample",
            icon=":material/description:",
            on_click=_load_abc_textile,
            key="load_abc_textile",
        )
    with action_columns[1]:
        if st.button("Clear JSON", icon=":material/delete:", key="clear_json"):
            st.session_state.json_input = ""
    with action_columns[2]:
        validate_json = st.button(
            "Validate JSON",
            icon=":material/check_circle:",
            key="validate_json",
        )

    json_input = st.text_area(
        "Business evidence JSON",
        key="json_input",
        height=360,
        placeholder='{\n  "business_profile": {}\n}',
    )
    if validate_json:
        try:
            parsed_json = json.loads(json_input)
            if not isinstance(parsed_json, dict):
                st.error("The JSON payload must be an object.")
            else:
                st.success("Valid JSON object.")
        except json.JSONDecodeError as error:
            st.error(f"Invalid JSON: {error}")

elif input_mode == "Text input":
    st.caption(
        "Fill in each field separately. Use **+ Add another** to add multiple entries. Leave unknown fields blank."
    )
    with st.expander("Business profile", expanded=True):
        st.markdown("##### Business details")
        _render_structured_section("business_details", "Business details")
        st.write("")
        st.markdown("##### Declared claims")
        _render_structured_section("business_claims", "Declared claims")
        st.write("")
        st.text_area(
            "Additional business context",
            key="text_business_context",
            on_change=_save_text_input,
            args=("text_business_context",),
            height=80,
            help="Optional context that does not fit the fields above.",
            placeholder="Any extra context, notes, or background not captured above.",
        )

    for section_name, subsections in _STRUCTURED_SECTIONS:
        with st.expander(section_name, expanded=section_name == "Purchase evidence"):
            for label, section_key in subsections:
                st.markdown(f"##### {label}s")
                _render_structured_section(section_key, label)
                st.write("")

    st.button(
        "Clear text",
        icon=":material/delete:",
        on_click=_clear_text_input,
        key="clear_text",
    )

else:
    uploaded_files = st.file_uploader(
        "Upload business evidence",
        type=[
            "pdf",
            "docx",
            "txt",
            "json",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "mp4",
            "mov",
            "avi",
            "mkv",
        ],
        accept_multiple_files=True,
        key=f"evidence_files_{st.session_state.upload_generation}",
        help="Supported inputs: PDF, DOCX, TXT, JSON, images, and video.",
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            text_content, parsed_json, file_type = extract_file_content(uploaded_file)
            with st.expander(f"{uploaded_file.name} · {file_type}"):
                if parsed_json is not None:
                    st.json(parsed_json)
                    file_json_candidate = parsed_json
                elif text_content:
                    st.text_area(
                        f"Extracted content from {uploaded_file.name}",
                        value=text_content,
                        height=140,
                        disabled=True,
                        key=f"preview_{uploaded_file.name}",
                    )
                    file_extracted_texts.append(
                        f"=== File: {uploaded_file.name} ({file_type}) ===\n{text_content}"
                    )
                elif file_type.startswith(("Invalid JSON", "Could not read")):
                    st.error(file_type)
                elif file_type.startswith(
                    ("Image attachment", "Video attachment")
                ):
                    st.info(
                        "The FastAPI request accepts structured image/video analysis, "
                        "but does not receive raw media files. Add verified observations "
                        "in the notes or provide analysis in JSON."
                    )
                elif file_type.startswith("PDF has no selectable text"):
                    st.warning(
                        "No text could be extracted from this PDF. Add verified observations "
                        "in the notes or provide a text-searchable document."
                    )

    file_notes = st.text_area(
        "Additional business information or inspector notes",
        key="file_notes",
        height=120,
    )
    st.button(
        "Clear file inputs",
        icon=":material/delete:",
        on_click=_clear_file_input,
        key="clear_files",
    )

run_clicked = st.button(
    "Run inference",
    type="primary",
    icon=":material/psychology:",
    key="run_inference",
)

if run_clicked:
    payload: Optional[Dict[str, Any]] = None
    if input_mode == "JSON input":
        if not json_input.strip():
            st.warning("Add a JSON payload or load a sample case before running inference.")
        else:
            try:
                parsed_payload = json.loads(json_input)
                if isinstance(parsed_payload, dict):
                    payload = parsed_payload
                else:
                    st.error("The JSON payload must be an object.")
            except json.JSONDecodeError as error:
                st.error(f"Invalid JSON: {error}")
    elif input_mode == "Text input":
        _biz_details = _collect_section_text("business_details", "Business details")
        _biz_claims = _collect_section_text("business_claims", "Declared claims")
        _biz_context = st.session_state.get("text_business_context", "").strip()
        business_profile = "\n\n".join(
            part for part in (
                f"Business details:\n{_biz_details}" if _biz_details else "",
                f"Declared claims:\n{_biz_claims}" if _biz_claims else "",
                f"Additional business context:\n{_biz_context}" if _biz_context else "",
            )
            if part
        )
        observed_sections = []
        for section_name, subsections in _STRUCTURED_SECTIONS:
            section_lines = []
            for label, section_key in subsections:
                block = _collect_section_text(section_key, label)
                if block.strip():
                    section_lines.append(f"{label}s:\n{block}")
            if section_lines:
                observed_sections.append(f"{section_name}\n" + "\n\n".join(section_lines))

        observed_evidence = "\n\n".join(observed_sections)
        if business_profile or observed_evidence:
            payload = {
                "declared_information": business_profile or None,
                "observed_evidence": observed_evidence or None,
            }
        else:
            st.warning("Add business information or evidence before running inference.")
    elif uploaded_files:
        if file_json_candidate is not None:
            payload = file_json_candidate
        else:
            combined_file_text = "\n\n".join(file_extracted_texts)
            if file_notes.strip():
                combined_file_text += f"\n\n=== Inspector Notes ===\n{file_notes.strip()}"
            if combined_file_text.strip():
                payload = {
                    "text": combined_file_text.strip(),
                }
            else:
                st.warning("No readable content was found in the uploaded files.")
    else:
        st.warning("Upload one or more files before running inference.")

    if payload is not None:
        with st.spinner("Running abductive reasoning…"):
            success, result = run_inference(payload, base_url=backend_url)
        if success:
            if isinstance(result, dict):
                st.session_state.last_response = result
                st.session_state.last_error = None
                st.session_state.history_backend_url = None
                st.toast("Inference completed.")
            else:
                error_message = "The backend returned a non-object inference response."
                st.session_state.last_error = error_message
                st.error(error_message)
        else:
            error_message = result.get("error", "Inference failed without an error message.")
            st.session_state.last_error = error_message
            st.error(f"Inference failed: {error_message}")

if st.session_state.last_error and not run_clicked:
    st.error(f"Last inference error: {st.session_state.last_error}")

if st.session_state.last_response:
    response = st.session_state.last_response
    st.header("Inference results")
    status_text = str(response.get("status", "completed")).replace("_", " ").title()
    st.caption(f"Inference status: {status_text}")

    report = response.get("report", "")
    if not render_report_markdown(report):
        st.warning("The inference response did not contain a Markdown report.")

    download_columns = st.columns(2)
    with download_columns[0]:
        st.download_button(
            "Download inference response",
            data=json.dumps(response, ensure_ascii=False, indent=2),
            file_name="inference_response.json",
            mime="application/json",
            icon=":material/download:",
        )
    with download_columns[1]:
        st.download_button(
            "Download Markdown report",
            data=report if isinstance(report, str) else "",
            file_name="reasoning_report.md",
            mime="text/markdown",
            icon=":material/description:",
        )

    with st.expander("View raw inference response"):
        st.json(response)
