"""Reusable Streamlit renderers and file parsing helpers for the Auroraa UI."""

import io
import json
from typing import Any, Dict, Optional, Tuple

import streamlit as st

__all__ = [
    "clean_report_markdown",
    "render_report_markdown",
    "extract_file_content",
]


def clean_report_markdown(markdown: str) -> str:
    """Drop orphan bold markers while preserving valid Markdown formatting."""
    return "\n".join(
        line for line in markdown.splitlines() if line.strip() != "**"
    ).strip()


def render_report_markdown(report: Any) -> bool:
    """Render the complete API report with Streamlit's Markdown renderer."""
    if not isinstance(report, str):
        return False
    content = clean_report_markdown(report)
    if not content:
        return False
    st.markdown(content)
    return True


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
