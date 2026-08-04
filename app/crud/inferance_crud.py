import os
import json
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplanationResponse

load_dotenv()

async def generate(request: ExplainRequest) -> ExplanationResponse:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read system prompt: {str(e)}")

    shap_list = [{"feature": sf.feature, "contribution": sf.contribution} for sf in request.shap_feature]
    user_message = (
        f"Document Type: {request.document_type}\n"
        f"Verdict: {request.verdict}\n"
        f"Forgery Score: {request.forgery_score}\n\n"
        f"SHAP Features:\n{json.dumps(shap_list, indent=2)}\n\n"
        f"Features:\n{json.dumps(request.features, indent=2)}"
    )

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

    content = data["message"]["content"]
    
    try:
        parsed_json = json.loads(content)
        return ExplanationResponse(**parsed_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)}\nResponse was: {content}")
