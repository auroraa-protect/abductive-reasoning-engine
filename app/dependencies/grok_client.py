import asyncio
import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(60)
MAX_RETRIES = 3


@dataclass(frozen=True)
class GroqCompletionResult:
    content: str
    finish_reason: Optional[str]
    usage: Dict[str, Any]
    model: str


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
    max_tokens: int = 4000,
    temperature: float = 0.0,
) -> GroqCompletionResult:
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
            if not isinstance(data, dict):
                raise HTTPException(
                    status_code=502,
                    detail="Groq API returned an invalid completion response.",
                )

            choices = data.get("choices")
            if (
                not isinstance(choices, list)
                or not choices
                or not isinstance(choices[0], dict)
            ):
                raise HTTPException(
                    status_code=502,
                    detail="Groq API returned no completion choice.",
                )

            choice = choices[0]
            message = choice.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise HTTPException(
                    status_code=502,
                    detail="Groq API returned an empty or invalid completion.",
                )

            usage = data.get("usage")
            if not isinstance(usage, dict):
                usage = {}

            finish_reason = choice.get("finish_reason")
            return GroqCompletionResult(
                content=_strip_markdown_fences(content),
                finish_reason=finish_reason if isinstance(finish_reason, str) else None,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                model=model_name,
            )

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
