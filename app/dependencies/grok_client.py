import os
import time
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(60)

async def get_groq_completion(system_prompt, user_message):

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
        "max_completion_tokens": 1024,
        "response_format": {
            "type": "json_object"
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('GROK_CLOUD_API')}",
        "Content-Type": "application/json",
    }

    start = time.perf_counter()

    try:

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        usage = data.get("usage", {})
        print("Input tokens:", usage.get("prompt_tokens"))
        print("Output tokens:", usage.get("completion_tokens"))
        print("Total tokens:", usage.get("total_tokens"))

        return data["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        print(f"Groq elapsed: {time.perf_counter()-start:.2f}s")