import os
import re
import time
import asyncio
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(60)
MAX_RETRIES = 3  # retry on transient json_validate_failed


def _strip_markdown_fences(text: str) -> str:
    """Remove accidental ```json ... ``` wrappers the model may emit."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def get_groq_completion(system_prompt: str, user_message: str) -> str:

    payload = {
        "model": os.getenv("GROQ_MODEL"),
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "temperature": 0,
        "max_completion_tokens": 4096,
        "response_format": {
            "type": "json_object"
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('GROK_CLOUD_API')}",
        "Content-Type": "application/json",
    }

    start = time.perf_counter()
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )

            # Groq returns 400 with code=json_validate_failed on transient
            # JSON-mode failures — retry these automatically.
            if response.status_code == 400:
                body = response.json()
                err_code = body.get("error", {}).get("code", "")
                if err_code == "json_validate_failed":
                    wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
                    print(
                        f"[Groq] json_validate_failed on attempt {attempt}/{MAX_RETRIES}, "
                        f"retrying in {wait}s..."
                    )
                    last_error = HTTPException(status_code=400, detail=response.text)
                    await asyncio.sleep(wait)
                    continue

            response.raise_for_status()

            data = response.json()

            usage = data.get("usage", {})
            print("Input tokens:", usage.get("prompt_tokens"))
            print("Output tokens:", usage.get("completion_tokens"))
            print("Total tokens:", usage.get("total_tokens"))

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
            raise HTTPException(
                status_code=500,
                detail=str(e),
            )

        finally:
            if attempt >= MAX_RETRIES:
                print(f"Groq elapsed: {time.perf_counter()-start:.2f}s")

    # All retries exhausted
    print(f"Groq elapsed: {time.perf_counter()-start:.2f}s")
    raise last_error or HTTPException(status_code=500, detail="Groq request failed after retries")