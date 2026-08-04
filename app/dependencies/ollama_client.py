import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

async def get_ollama_completion(system_prompt: str, user_message: str) -> str:
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "format": "json",
        "stream": False
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ollama_host}/api/chat",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Ollama API error: {str(e)}")

    data = response.json()
    if "message" not in data or "content" not in data["message"]:
        raise HTTPException(status_code=500, detail="Invalid response format from Ollama")

    return data["message"]["content"]
