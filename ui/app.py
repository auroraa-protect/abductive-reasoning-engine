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
    st.session_state.text_declared = ""
    st.session_state.text_observed = ""
    st.session_state.file_notes = ""
    st.session_state.upload_generation += 1


def _load_sample_case(sample: Dict[str, Any]) -> None:
    st.session_state.input_mode = "JSON input"
    st.session_state.json_input = sample["json_str"]
    st.session_state.text_declared = sample.get("text_narrative", "")
    st.session_state.text_observed = ""
    st.session_state.last_error = None


def _load_abc_textile() -> None:
    st.session_state.input_mode = "JSON input"
    st.session_state.json_input = ABC_TEXTILE_JSON


def _clear_text_input() -> None:
    st.session_state.text_declared = ""
    st.session_state.text_observed = ""


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
st.session_state.setdefault(
    "text_declared",
    "ABC Textile Industries (Surat). 5 years operational, 15 workers. "
    "Declared monthly turnover: ₹15,00,000. Declared monthly production: "
    "8,000 meters fabric. Production capacity: 10,000 meters/month.",
)
st.session_state.setdefault(
    "text_observed",
    "1. Purchase bill PUR-001: 1,000 kg cotton @ ₹150/kg (₹1,50,000).\n"
    "2. Production records: 1,600 kg cotton consumed to produce 8,000 meters fabric.\n"
    "3. Sales invoice SALE-001: ₹2,50,000 to ABC Garments.\n"
    "4. Bank statement: ₹2,50,000 incoming credit from ABC Garments.\n"
    "5. Premises video VID-001: 5 power looms operational, fabric rolls stacked.\n"
    "6. Electricity bill: 4,500 units consumed (₹38,000).",
)
st.session_state.setdefault("file_notes", "")
st.session_state.setdefault("upload_generation", 0)
st.session_state.setdefault("history_entries", None)
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
        if st.button("Refresh history", key="refresh_history"):
            metrics_result = get_metrics(backend_url)
            if metrics_result.get("ok"):
                st.session_state.history_entries = metrics_result.get(
                    "metrics", {}
                ).get("call_history", [])
            else:
                st.error(metrics_result.get("error", "Could not load history."))

        history = st.session_state.history_entries
        if history is None:
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
    text_declared = st.text_area(
        "Business information and declared claims",
        key="text_declared",
        height=150,
        placeholder="Describe the business activity, age, employees, turnover, production, or capacity.",
    )
    text_observed = st.text_area(
        "Observations and supporting evidence",
        key="text_observed",
        height=220,
        placeholder="Add observed invoices, bank records, inventory, production, machinery, or utilities evidence.",
    )
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
        combined_text = "\n\n".join(
            value.strip()
            for value in (text_declared, text_observed)
            if value and value.strip()
        )
        if combined_text:
            payload = {
                "declared_information": text_declared.strip() or None,
                "observed_evidence": text_observed.strip() or None,
                "text": combined_text,
            }
        else:
            st.warning("Add business information or observations before running inference.")
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
