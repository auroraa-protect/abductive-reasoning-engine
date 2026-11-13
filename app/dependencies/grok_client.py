import os
import re
import time
import asyncio
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(60)
MAX_RETRIES = 3

_last_usage: Dict[str, Any] = {}


def get_last_usage() -> Dict[str, Any]:
    """Retrieve the token usage metrics from the most recent LLM completion call."""
    return dict(_last_usage)


def _strip_markdown_fences(text: str) -> str:
    """Remove accidental ``` wrappers the model may emit."""
    text = text.strip()
    text = re.sub(r"^```(?:[a-zA-Z]+)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def get_groq_completion(
    system_prompt: str,
    user_message: str,
    response_format: Optional[str] = "text",
    max_tokens: int = 2000,
    temperature: float = 0.0,
) -> str:
    """
    Execute an inference call to Groq Cloud API with automated retry and usage tracking.
    """
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_key = os.getenv("GROK_CLOUD_API") or os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Groq Cloud API key is missing. Set GROK_CLOUD_API or GROQ_API_KEY in .env.",
        )

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }

    if response_format == "json_object":
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.perf_counter()
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )

            if response.status_code == 400:
                body = response.json()
                err_code = body.get("error", {}).get("code", "")
                if err_code == "json_validate_failed":
                    wait = 2 ** (attempt - 1)
                    await asyncio.sleep(wait)
                    last_error = HTTPException(status_code=400, detail=response.text)
                    continue

            response.raise_for_status()
            data = response.json()

            global _last_usage
            usage = data.get("usage", {})
            _last_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency_ms": round((time.perf_counter() - start) * 1000),
                "model": model_name,
            }

            raw = data["choices"][0]["message"]["content"]
            return _strip_markdown_fences(raw)

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text,
            )
        except HTTPException:
            raise
        except Exception as e:
            last_error = HTTPException(
                status_code=500,
                detail=f"Groq API connection error: {str(e)}",
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1)

    raise last_error or HTTPException(status_code=500, detail="Groq request failed after retries")
