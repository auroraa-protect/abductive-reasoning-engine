import os
import time
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(60.0)


async def get_vllm_completion(system_prompt, user_message):

    payload = {
        "model": os.getenv("VLLM_MODEL"),
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
        "max_tokens": 1024,
        "response_format": {
            "type": "json_object"
        }
    }

    headers = {
        "Content-Type": "application/json",
    }

    # Only add API key if your vLLM server is configured with one
    vllm_api_key = os.getenv("VLLM_API_KEY")

    if vllm_api_key:
        headers["Authorization"] = f"Bearer {vllm_api_key}"

    start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{os.getenv('VLLM_BASE_URL')}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to vLLM server: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        print(
            f"vLLM elapsed: "
            f"{time.perf_counter() - start:.2f}s"
        )