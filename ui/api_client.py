"""
API client for Auroraa Abductive Reasoning Engine FastAPI backend.
Communicates via HTTP requests with configurable backend URL.
"""

import os
import requests
from typing import Dict, Any, Optional, Tuple

DEFAULT_BACKEND_URL = (
    os.getenv("AURORAA_BACKEND_URL")
    or os.getenv("BACKEND_URL")
    or "http://localhost:8000"
)


def normalize_url(url: Optional[str]) -> str:
    """Ensure base URL is trimmed and does not end with trailing slash."""
    if not url or not url.strip():
        url = DEFAULT_BACKEND_URL
    return url.strip().rstrip("/")


def check_health(base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if the FastAPI backend service is reachable and healthy.
    Returns a dict with 'ok': bool, and either service data or error description.
    """
    url = f"{normalize_url(base_url)}/health"
    try:
        resp = requests.get(url, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "data": data, "status": data.get("status", "healthy")}
        return {
            "ok": False,
            "error": f"Server returned status {resp.status_code}: {resp.text}",
            "status_code": resp.status_code,
        }
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": f"Cannot connect to FastAPI backend at {url}. Is the backend running? Start with: uvicorn app.main:app --port 8000",
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "error": f"Connection timed out while reaching {url}.",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_inference(
    payload: Dict[str, Any],
    base_url: Optional[str] = None,
    timeout: float = 90.0,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Send an inference request to the POST /explain endpoint.
    Returns (success: bool, response_or_error_dict).
    """
    url = f"{normalize_url(base_url)}/explain"
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            return True, resp.json()
        
        # Try to parse error details
        error_msg = f"HTTP {resp.status_code}"
        try:
            err_data = resp.json()
            if isinstance(err_data, dict):
                error_msg = err_data.get("detail", str(err_data))
        except Exception:
            error_msg = resp.text or f"HTTP {resp.status_code} Error"

        return False, {
            "error": f"Backend Error ({resp.status_code}): {error_msg}",
            "status_code": resp.status_code,
        }

    except requests.exceptions.ConnectionError:
        return False, {
            "error": (
                f"Connection failed: Unable to connect to backend at {url}.\n\n"
                "Please verify that the FastAPI backend is running:\n"
                "  uvicorn app.main:app --port 8000"
            )
        }
    except requests.exceptions.Timeout:
        return False, {
            "error": f"Inference request timed out after {timeout} seconds. The LLM provider may be slow or overloaded."
        }
    except Exception as e:
        return False, {"error": f"Unexpected client error: {str(e)}"}


def get_metrics(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve cumulative token usage and latency metrics from GET /metrics."""
    url = f"{normalize_url(base_url)}/metrics"
    try:
        resp = requests.get(url, timeout=4.0)
        if resp.status_code == 200:
            return {"ok": True, "metrics": resp.json()}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def reset_metrics(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Reset cumulative metrics tracking via POST /metrics/reset."""
    url = f"{normalize_url(base_url)}/metrics/reset"
    try:
        resp = requests.post(url, timeout=4.0)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
