import os
import time
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = httpx.Timeout(
    connect=30.0,
    read=300.0,
    write=30.0,
    pool=30.0,
)


async def get_ollama_completion(system_prompt: str, user_message: str) -> str:
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 1024,
        },
    }

    start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{ollama_host}/api/chat",
                json=payload,
            )

        response.raise_for_status()

    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=504,
            detail="Ollama inference timed out.",
        )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama.",
        )

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
        print(f"Ollama elapsed: {time.perf_counter() - start:.2f}s")

    data = response.json()

    return data["message"]["content"]