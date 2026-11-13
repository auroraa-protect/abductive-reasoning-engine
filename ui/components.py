"""Reusable Streamlit renderers and file parsing helpers for the Auroraa UI."""

import io
import json
from typing import Any, Dict, Optional, Tuple

import streamlit as st


def clean_report_markdown(markdown: str) -> str:
    """Drop orphan bold markers while preserving valid Markdown formatting."""
    return "\n".join(
        line for line in markdown.splitlines() if line.strip() != "**"
    ).strip()


def status_badge_markdown(status: Optional[str]) -> str:
    """Return a colored badge for known API assessment values."""
    badges = {
        "MATCH": ":green-badge[MATCH]",
        "PARTIAL MATCH": ":orange-badge[PARTIAL MATCH]",
        "MISMATCH": ":red-badge[MISMATCH]",
        "INSUFFICIENT EVIDENCE": ":gray-badge[INSUFFICIENT EVIDENCE]",
    }
    if not status:
        return ":gray-badge[Assessment not provided]"
    return badges.get(status.strip().upper(), ":gray-badge[Assessment not provided]")


def render_metrics_panel(token_usage: Optional[Dict[str, Any]]) -> None:
    """Render only the token and latency metrics returned by the API."""
    if not token_usage:
        return

    if hasattr(token_usage, "model_dump"):
        usage = token_usage.model_dump()
    elif isinstance(token_usage, dict):
        usage = token_usage
    else:
        usage = {}

    def format_count(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)

    latency_ms = usage.get("latency_ms")
    try:
        latency = f"{float(latency_ms) / 1000:.2f} s" if latency_ms is not None else "—"
    except (TypeError, ValueError):
        latency = "—"

    metrics = [
        ("Model", usage.get("model") or "—"),
        ("Total tokens", format_count(usage.get("total_tokens"))),
        ("Latency", latency),
        ("Inference calls", format_count(usage.get("inference_calls"))),
    ]
    for column, (label, value) in zip(st.columns(4), metrics):
        with column:
            with st.container(border=True):
                st.metric(label, value)

    st.caption("Token breakdown")
    token_metrics = [
        ("Input tokens", usage.get("input_tokens")),
        ("Output tokens", usage.get("output_tokens")),
    ]
    for column, (label, value) in zip(st.columns(2), token_metrics):
        with column:
            with st.container(border=True):
                st.metric(label, format_count(value))


def render_results_panel(
    response: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> None:
    """Render API-provided sections as Markdown without inferring report data."""
    if not response:
        return

    sections = response.get("sections")
    if not isinstance(sections, dict):
        sections = {}

    section_titles = [
        ("BUSINESS UNDERSTANDING", "Business understanding"),
        ("EVIDENCE MATCHING", "Evidence matching"),
        ("POSSIBLE EXPLANATIONS", "Abductive reasoning"),
        ("ADDITIONAL INFORMATION REQUIRED", "Additional information required"),
    ]
    known_keys = {key for key, _ in section_titles}
    known_keys.add("OVERALL ASSESSMENT")

    business_text = sections.get("BUSINESS UNDERSTANDING")
    if (isinstance(business_text, str) and business_text.strip()) or business_profile:
        with st.container(border=True):
            st.subheader("Business understanding")
            if business_profile:
                _render_business_profile(business_profile)
            if isinstance(business_text, str) and business_text.strip():
                st.markdown(clean_report_markdown(business_text))

    for key, title in section_titles[1:]:
        content = sections.get(key)
        if isinstance(content, str) and content.strip():
            with st.container(border=True):
                st.subheader(title)
                st.markdown(clean_report_markdown(content))

    for key, content in sections.items():
        if key not in known_keys and isinstance(content, str) and content.strip():
            with st.container(border=True):
                st.subheader(str(key))
                st.markdown(clean_report_markdown(content))

    report = response.get("report")
    if not sections and isinstance(report, str) and report.strip():
        with st.container(border=True):
            st.subheader("Inference report")
            st.markdown(clean_report_markdown(report))

    with st.container(border=True):
        st.subheader("Overall assessment")
        st.markdown(status_badge_markdown(response.get("overall_assessment")))
        assessment_text = sections.get("OVERALL ASSESSMENT")
        if isinstance(assessment_text, str) and assessment_text.strip():
            st.markdown(clean_report_markdown(assessment_text))


def _render_business_profile(profile: Dict[str, Any]) -> None:
    """Show declared business attributes present in the submitted payload."""
    fields = [
        ("Business name", "business_name"),
        ("Industry", "industry"),
        ("Business activity", "business_activity"),
        ("Business age", "business_age_years"),
        ("Employees", "number_of_employees"),
        ("Declared turnover", "declared_monthly_turnover"),
        ("Monthly production", "declared_monthly_production"),
        ("Production capacity", "declared_production_capacity"),
    ]
    displayed_fields = []
    for label, key in fields:
        value = profile.get(key)
        if value is None or value == "":
            continue
        if key == "declared_monthly_turnover" and isinstance(value, (int, float)):
            display_value = f"₹{value:,.0f}"
        elif isinstance(value, (int, float)):
            display_value = f"{value:,}"
        else:
            display_value = str(value)
        displayed_fields.append((label, display_value))

    for start in range(0, len(displayed_fields), 4):
        columns = st.columns(4)
        for column, (label, value) in zip(
            columns, displayed_fields[start : start + 4]
        ):
            with column:
                st.caption(label)
                st.markdown(f"**{value}**")


def extract_file_content(
    uploaded_file: Any,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    """Extract text or structured JSON without fabricating media observations."""
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if filename.endswith(".json"):
        try:
            parsed = json.loads(file_bytes.decode("utf-8"))
            if not isinstance(parsed, dict):
                return None, None, "Invalid JSON: the payload must be an object"
            return json.dumps(parsed, indent=2), parsed, "JSON data"
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return None, None, f"Invalid JSON: {error}"

    if filename.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8"), None, "Text document"
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore"), None, "Text document"

    if filename.endswith(".pdf"):
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for index, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(f"--- Page {index + 1} ---\n{page_text}")
            full_text = "\n\n".join(pages_text).strip()
            if not full_text:
                return None, None, f"PDF has no selectable text ({len(reader.pages)} pages)"
            return full_text, None, f"PDF document ({len(reader.pages)} pages)"
        except Exception as error:
            return None, None, f"Could not read PDF: {error}"

    if filename.endswith(".docx"):
        try:
            import docx

            document = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]
            return "\n".join(paragraphs).strip(), None, "Word document"
        except Exception as error:
            return None, None, f"Could not read DOCX: {error}"

    if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return None, None, "Image attachment (not analyzed)"

    if filename.endswith((".mp4", ".mov", ".avi", ".mkv")):
        return None, None, "Video attachment (not analyzed)"

    return None, None, f"Unsupported file ({len(file_bytes)} bytes)"
