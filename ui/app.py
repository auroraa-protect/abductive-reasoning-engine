"""Auroraa R&D inference workspace."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# Keep the repository root ahead of imports; the UI directory contains app.py
# and must not shadow the backend's app package.
_ROOT = Path(__file__).resolve().parent.parent
_UI_DIR = Path(__file__).resolve().parent

for _p in (str(_UI_DIR), str(_ROOT)):
    while _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, str(_ROOT))

from ui.api_client import (
    DEFAULT_BACKEND_URL,
    check_health,
    get_metrics,
    normalize_url,
    run_inference,
)
from ui.components import extract_file_content, render_report_markdown
from ui.sample_data import (
    ABC_TEXTILE_DATA,
    ABC_TEXTILE_JSON,
    SAMPLE_CASES,
    SAMPLE_TEXT_NARRATIVE,
)
from app.schemas.request_schemas import ExplainRequest as _ExplainRequest


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
    prefix = f"sf__{section}__"
    for k in [k for k in list(st.session_state.keys()) if k.startswith(prefix)]:
        st.session_state.pop(k, None)
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

# Load external stylesheet
_CSS_PATH = _UI_DIR / "style.css"
if _CSS_PATH.exists():
    with open(_CSS_PATH, "r", encoding="utf-8") as _css_file:
        st.markdown(f"<style>\n{_css_file.read()}\n</style>", unsafe_allow_html=True)


def _populate_text_fields_from_data(data: Dict[str, Any], narrative: str = "") -> None:
    """Populate all structured text input fields from case evidence data."""
    # 1. Clear existing section entries first
    for section_key in _SECTION_FIELDS:
        _clear_section(section_key)

    # 2. Narrative context
    st.session_state["text_business_context"] = narrative or ""
    st.session_state["_text_business_context"] = narrative or ""

    if not data or not isinstance(data, dict):
        return

    def _format_val(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    def _set_val(sec: str, idx: int, field_name: str, val: Any) -> None:
        if val is not None and val != "":
            st.session_state[_skey(sec, idx, field_name)] = _format_val(val)

    def _set_count(sec: str, count: int) -> None:
        st.session_state[f"sf_count__{sec}"] = max(1, count)

    # 1. Business Profile
    bp = data.get("business_profile") or {}
    if bp:
        _set_val("business_details", 0, "Business name", bp.get("business_name"))
        _set_val("business_details", 0, "Business type", bp.get("business_type"))
        _set_val("business_details", 0, "Industry", bp.get("industry"))
        _set_val("business_details", 0, "Business activity", bp.get("business_activity"))
        _set_val("business_details", 0, "Business age (years)", bp.get("business_age_years"))
        _set_val("business_details", 0, "Number of employees", bp.get("number_of_employees"))

        _set_val("business_claims", 0, "Declared monthly turnover (₹)", bp.get("declared_monthly_turnover"))
        _set_val("business_claims", 0, "Declared monthly production", bp.get("declared_monthly_production"))
        _set_val("business_claims", 0, "Declared production capacity", bp.get("declared_production_capacity"))

    # 2. Purchase Evidence
    pe = data.get("purchase_evidence") or {}
    bills = pe.get("bills") or []
    if bills:
        _set_count("purchase_bills", len(bills))
        items_collected = []
        for i, b in enumerate(bills):
            _set_val("purchase_bills", i, "Supplier name", b.get("supplier_name"))
            _set_val("purchase_bills", i, "Invoice date", b.get("invoice_date"))
            _set_val("purchase_bills", i, "Total amount (₹)", b.get("total_amount"))
            for it in b.get("items") or []:
                items_collected.append(it)
        if items_collected:
            _set_count("purchase_items", len(items_collected))
            for j, it in enumerate(items_collected):
                _set_val("purchase_items", j, "Item name", it.get("item_name"))
                _set_val("purchase_items", j, "Quantity", it.get("quantity"))
                _set_val("purchase_items", j, "Unit", it.get("unit"))
                _set_val("purchase_items", j, "Unit price (₹)", it.get("unit_price"))
                _set_val("purchase_items", j, "Total amount (₹)", it.get("total_amount"))

    # 3. Inventory Evidence
    ie = data.get("inventory_evidence") or {}
    dinv = ie.get("declared_inventory") or []
    if dinv:
        _set_count("inventory_declared", len(dinv))
        for i, it in enumerate(dinv):
            _set_val("inventory_declared", i, "Item name", it.get("item_name"))
            _set_val("inventory_declared", i, "Quantity", it.get("quantity"))
            _set_val("inventory_declared", i, "Unit", it.get("unit"))
            _set_val("inventory_declared", i, "Estimated value (₹)", it.get("estimated_value"))

    imgs = ie.get("image_analysis") or []
    if imgs:
        _set_count("inventory_images", len(imgs))
        for i, img in enumerate(imgs):
            objs = img.get("observed_objects") or []
            objs_list = []
            for o in objs:
                cnt = o.get("estimated_count")
                name = o.get("object", "")
                objs_list.append(f"{name} × {cnt}" if cnt is not None else name)
            _set_val("inventory_images", i, "Observed objects", ", ".join(objs_list))
            obs = img.get("observations") or []
            _set_val("inventory_images", i, "Observations", "; ".join(obs) if isinstance(obs, list) else str(obs))
            _set_val("inventory_images", i, "Analysis confidence", img.get("analysis_confidence"))

    # 4. Production Evidence
    prod = data.get("production_evidence") or {}
    precords = prod.get("production_records") or []
    if precords:
        _set_count("production_records", len(precords))
        for i, r in enumerate(precords):
            _set_val("production_records", i, "Date", r.get("date"))
            _set_val("production_records", i, "Product", r.get("product"))
            _set_val("production_records", i, "Quantity", r.get("quantity"))
            _set_val("production_records", i, "Unit", r.get("unit"))

    pcons = prod.get("raw_material_consumption") or []
    if pcons:
        _set_count("production_consumption", len(pcons))
        for i, c in enumerate(pcons):
            _set_val("production_consumption", i, "Material", c.get("material") or c.get("item_name"))
            _set_val("production_consumption", i, "Quantity consumed", c.get("quantity"))
            _set_val("production_consumption", i, "Unit", c.get("unit"))

    pfg = prod.get("finished_goods") or []
    if pfg:
        _set_count("production_finished_goods", len(pfg))
        for i, f in enumerate(pfg):
            _set_val("production_finished_goods", i, "Product", f.get("product"))
            _set_val("production_finished_goods", i, "Quantity", f.get("quantity"))
            _set_val("production_finished_goods", i, "Unit", f.get("unit"))

    # 5. Sales Evidence
    se = data.get("sales_evidence") or {}
    sbills = se.get("sales_bills") or []
    if sbills:
        _set_count("sales_bills", len(sbills))
        for i, b in enumerate(sbills):
            _set_val("sales_bills", i, "Customer name", b.get("customer_name"))
            _set_val("sales_bills", i, "Invoice date", b.get("invoice_date"))
            _set_val("sales_bills", i, "Total amount (₹)", b.get("total_amount"))

    scust = se.get("customer_details") or []
    if scust:
        _set_count("sales_customers", len(scust))
        for i, c in enumerate(scust):
            _set_val("sales_customers", i, "Customer name", c.get("customer_name"))
            _set_val("sales_customers", i, "Relationship", c.get("relationship"))

    ssum = se.get("sales_summary") or {}
    if ssum:
        _set_val("sales_summary", 0, "Total sales value (₹)", ssum.get("total_sales_value"))
        _set_val("sales_summary", 0, "Period", ssum.get("period"))

    # 6. Physical Evidence
    phy = data.get("physical_evidence") or {}
    pvids = phy.get("video_analysis") or []
    if pvids:
        _set_count("physical_video", len(pvids))
        for i, v in enumerate(pvids):
            _set_val("physical_video", i, "Duration (seconds)", v.get("duration_seconds"))
            acts = v.get("observed_activities") or []
            _set_val("physical_video", i, "Observed activities", "; ".join(acts) if isinstance(acts, list) else str(acts))
            mach = v.get("observed_machinery") or []
            _set_val("physical_video", i, "Observed machinery", ", ".join(mach) if isinstance(mach, list) else str(mach))
            _set_val("physical_video", i, "Analysis confidence", v.get("analysis_confidence"))

    pmach = phy.get("machinery_analysis") or []
    if pmach:
        _set_count("physical_machinery", len(pmach))
        for i, m in enumerate(pmach):
            _set_val("physical_machinery", i, "Machine name", m.get("machine_name"))
            _set_val("physical_machinery", i, "Observed count", m.get("observed_count"))
            _set_val("physical_machinery", i, "Condition", m.get("condition"))

    prem = phy.get("premises_analysis") or []
    if prem:
        _set_count("physical_premises", len(prem))
        for i, p in enumerate(prem):
            _set_val("physical_premises", i, "Area", p.get("area"))
            obs_text = p.get("observation") or p.get("observations") or ""
            if isinstance(obs_text, list):
                obs_text = "; ".join(obs_text)
            _set_val("physical_premises", i, "Observations", obs_text)

    # 7. Financial Evidence
    fe = data.get("financial_evidence") or {}
    btx = fe.get("bank_transactions") or []
    if btx:
        _set_count("financial_bank", len(btx))
        for i, t in enumerate(btx):
            _set_val("financial_bank", i, "Transaction date", t.get("transaction_date"))
            _set_val("financial_bank", i, "Type", t.get("transaction_type"))
            _set_val("financial_bank", i, "Amount (₹)", t.get("amount"))
            _set_val("financial_bank", i, "Description", t.get("description"))

    elec = fe.get("electricity_bills") or []
    if elec:
        _set_count("financial_electricity", len(elec))
        for i, e in enumerate(elec):
            _set_val("financial_electricity", i, "Billing month", e.get("billing_month"))
            _set_val("financial_electricity", i, "Units consumed", e.get("units_consumed"))
            _set_val("financial_electricity", i, "Bill amount (₹)", e.get("bill_amount"))

    gst = fe.get("gst_records") or []
    if gst:
        _set_count("financial_gst", len(gst))
        for i, g in enumerate(gst):
            _set_val("financial_gst", i, "Period", g.get("period"))
            _set_val("financial_gst", i, "Declared turnover (₹)", g.get("declared_turnover"))

    # 8. Additional Evidence
    ae = data.get("additional_evidence") or {}
    docs = ae.get("documents") or []
    if docs:
        _set_count("additional_documents", len(docs))
        for i, d in enumerate(docs):
            if isinstance(d, dict):
                _set_val("additional_documents", i, "Document name / type", d.get("name") or d.get("type") or "")
                _set_val("additional_documents", i, "Description", d.get("description") or "")
            else:
                _set_val("additional_documents", i, "Document name / type", str(d))

    aobs = ae.get("observations") or []
    if aobs:
        _set_count("additional_observations", len(aobs))
        for i, o in enumerate(aobs):
            _set_val("additional_observations", i, "Observation", str(o))


def _start_new_test() -> None:
    st.session_state.last_response = None
    st.session_state.last_error = None
    st.session_state.json_input = ""
    # Clear all structured evidence and context fields
    _clear_text_input()
    st.session_state.file_notes = ""
    st.session_state.upload_generation += 1


def _load_sample_case(sample: Dict[str, Any]) -> None:
    st.session_state.json_input = sample["json_str"]
    _populate_text_fields_from_data(sample.get("data", {}), sample.get("text_narrative", ""))
    st.session_state.last_error = None
    st.session_state.last_response = None
    current_mode = st.session_state.get("input_mode")
    if current_mode not in ("Text input", "JSON input", "File upload"):
        st.session_state.input_mode = "JSON input"


def _load_abc_textile() -> None:
    st.session_state.json_input = ABC_TEXTILE_JSON
    _populate_text_fields_from_data(ABC_TEXTILE_DATA, SAMPLE_TEXT_NARRATIVE)
    st.session_state.last_error = None
    st.session_state.last_response = None


def _clear_text_input() -> None:
    for key in TEXT_INPUT_DEFAULTS:
        st.session_state[key] = ""
        st.session_state[f"_{key}"] = ""
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
if not st.session_state.get("_text_initialized"):
    _populate_text_fields_from_data(ABC_TEXTILE_DATA, SAMPLE_TEXT_NARRATIVE)
    st.session_state["_text_initialized"] = True
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
                st.markdown(
                    f"<div style='background-color: #162447; border: 1px solid #253663; border-radius: 6px; padding: 6px 10px; margin-bottom: 6px;'>"
                    f"<span style='color: #ffffff !important; font-size: 0.82rem; font-weight: 600; font-family: monospace;'>{entry.get('timestamp', '')}</span>"
                    f"<span style='color: #cbd5e1 !important; margin: 0 6px;'>·</span>"
                    f"<span style='color: #60a5fa !important; font-size: 0.82rem; font-weight: 600; font-family: monospace;'>{entry.get('total_tokens', '—')} tokens</span>"
                    f"</div>",
                    unsafe_allow_html=True,
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
validate_json = False
json_input = st.session_state.get("json_input", "")

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
        if not json_input.strip():
            st.warning("Paste a JSON payload first before validating.")
        else:
            # Step 1 — JSON syntax check
            try:
                parsed_json = json.loads(json_input)
            except json.JSONDecodeError as error:
                st.error(f"❌ **Invalid JSON syntax:** {error}")
                parsed_json = None

            if parsed_json is not None:
                if not isinstance(parsed_json, dict):
                    st.error("❌ **The JSON payload must be a top-level object `{}`**, not a list or primitive.")
                else:
                    # Step 2 — Pydantic schema validation
                    if _ExplainRequest is not None:
                        try:
                            from pydantic import ValidationError
                            _ExplainRequest(**parsed_json)
                            st.success(
                                "✅ **Valid!** JSON is well-formed and passes full schema validation. "
                                "It is ready to submit."
                            )
                        except ValidationError as ve:
                            field_errors = ve.errors()
                            st.error(
                                f"❌ **Schema validation failed** — "
                                f"{len(field_errors)} field error(s) found:"
                            )
                            for err in field_errors:
                                loc = " → ".join(str(x) for x in err["loc"])
                                msg = err["msg"]
                                inp = err.get("input", "")
                                inp_str = f" (got: `{repr(inp)[:80]}`)" if inp != "" else ""
                                st.markdown(
                                    f"- **`{loc}`**: {msg}{inp_str}"
                                )
                        except Exception as exc:
                            st.warning(
                                f"⚠️ JSON is syntactically valid but schema check raised: `{exc}`"
                            )
                    else:
                        # Schema not importable — fall back to syntax-only check
                        st.success("✅ **Valid JSON object.** (Schema validator not available — syntax check only.)")


elif input_mode == "Text input":
    action_columns = st.columns(3)
    with action_columns[0]:
        selected_case_name = st.session_state.get("sample_selection", list(SAMPLE_CASES.keys())[0])
        st.button(
            "Load selected sample",
            icon=":material/folder_open:",
            on_click=_load_sample_case,
            args=(SAMPLE_CASES.get(selected_case_name, SAMPLE_CASES[list(SAMPLE_CASES.keys())[0]]),),
            key="load_selected_sample_text",
            help=f"Load '{selected_case_name}' into these text fields.",
        )
    with action_columns[1]:
        st.button(
            "Load ABC Textile sample",
            icon=":material/description:",
            on_click=_load_abc_textile,
            key="load_abc_textile_text",
        )
    with action_columns[2]:
        st.button(
            "Clear text",
            icon=":material/delete:",
            on_click=_clear_text_input,
            key="clear_text",
        )

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
        key="clear_text_bottom",
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
