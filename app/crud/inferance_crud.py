import os
import json
from fastapi import HTTPException

from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplanationResponse
from app.dependencies.ollama_client import get_ollama_completion
from app.dependencies.grok_client import get_groq_completion
from app.service.registry_service import resolve, build_registry_context_block

async def generate(request: ExplainRequest) -> ExplanationResponse:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read system prompt: {str(e)}")

    # Resolve SHAP features against the salary-slip registry
    registry_ctx = resolve(request.shap_feature)
    registry_block = build_registry_context_block(registry_ctx)

    shap_list = [{"feature": sf.feature, "contribution": sf.contribution} for sf in request.shap_feature]
    user_message = (
        f"Document Type: {request.document_type}\n"
        f"Verdict: {request.verdict}\n"
        f"Forgery Score: {request.forgery_score}\n\n"
        f"SHAP Features:\n{json.dumps(shap_list, indent=2)}\n\n"
        f"Features:\n{json.dumps(request.features, indent=2)}"
        f"{registry_block}"
    )

    content = await get_groq_completion(system_prompt, user_message)

    try:
        parsed_json = json.loads(content)
        return ExplanationResponse(**parsed_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)}\nResponse was: {content}")
